"""Judgment half: the critic step. Eight separate axes, never one overall score.

The only part of Tastee that calls a model. Returns structured JSON so apps
can use each axis on its own. Model and effort are configurable:
TASTEE_MODEL (default claude-opus-5-5) and TASTEE_EFFORT (default low,
since this runs on every draft and speed is an open critique).
"""
import json
import os

CHECKABLE = ("clarity", "proof", "why_you", "ask")
TASTE = ("hook", "voice", "boldness", "rhythm")
AXES = CHECKABLE + TASTE

_AXIS_HELP = {
    "clarity": "Can a stranger say what this is about after one read?",
    "proof": "Is every claim backed by something specific (a number, a name, a result)?",
    "why_you": "Does it say something only this person or company could say?",
    "ask": "Does the reader know the one next action?",
    "hook": "Does line one earn line two, the way this person opens?",
    "voice": "Does it sound like this person on their best day (compare the samples)?",
    "boldness": "Does it take the position this person would take?",
    "rhythm": "Do sentence length and cadence match this person?",
}

_axis_schema = {"type": "object", "additionalProperties": False, "required": ["score", "why", "quote"],
                "properties": {"score": {"type": "integer"}, "why": {"type": "string"},
                               "quote": {"type": "string"}}}

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["axes", "slop_found", "weakest_axis", "rewrite", "missing_proof"],
    "properties": {
        "axes": {"type": "object", "additionalProperties": False, "required": list(AXES),
                 "properties": {a: _axis_schema for a in AXES}},
        "slop_found": {"type": "array", "items": {"type": "string"}},
        "weakest_axis": {"type": "string", "enum": list(AXES)},
        "rewrite": {"type": "object", "additionalProperties": False, "required": ["before", "after"],
                    "properties": {"before": {"type": "string"}, "after": {"type": "string"}}},
        "missing_proof": {"type": "string"},
    },
}

SYSTEM = """You are Tastee's critic step. You score one draft against one person's taste profile.

Score each of the 8 axes from 1 to 10, separately. Never produce an overall score.
Checkable axes (clarity, proof, why_you, ask) are judged the same way for everyone.
Taste axes (hook, voice, boldness, rhythm) are judged against this person's samples and rules, which win over general writing advice.
Every "why" must cite words from the draft in "quote".
Pick the weakest axis and rewrite only the part of the draft that fixes it. The person stays the author.
Never invent facts, numbers, names, stories or experience. If proof is weak, put the specific missing number, name or result in "missing_proof"; otherwise leave it empty.
List generic or AI-sounding phrases you found in "slop_found", quoted exactly."""


def build_prompt(text, profile, surface):
    rules = [r.text for r in profile.rules if r.approved]
    lines = ["<profile>",
             f"Writes as: {profile.who_i_write_as or 'unknown'}",
             f"Audience: {profile.audience or 'unknown'}",
             f"Goal: {profile.goal or 'unknown'}",
             "Rules (theirs, these win):"] + [f"- {r}" for r in rules] + ["Samples of their writing:"]
    lines += [f"<sample>{s}</sample>" for s in profile.samples[:5]]
    lines += ["Approved facts (the only numbers they may use):"] + [f"- {f}" for f in profile.approved_facts]
    lines += ["</profile>", "", "<axes>"] + [f"{a}: {q}" for a, q in _AXIS_HELP.items()] + ["</axes>", "",
              f"<surface>{surface}</surface>", f"<draft>{text}</draft>"]
    return "\n".join(lines)


def critique(text, profile, surface="linkedin", model=None, effort=None, client=None):
    """Score a draft on 8 axes. Requires the anthropic SDK and a credential."""
    import anthropic  # imported here so the deterministic half has no dependency

    client = client or anthropic.Anthropic()
    model = model or os.environ.get("TASTEE_MODEL", "claude-opus-5-5")
    effort = effort or os.environ.get("TASTEE_EFFORT", "low")
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM,
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": build_prompt(text, profile, surface)}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("The model declined to critique this draft.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Critique was cut off (max_tokens). Retry with a shorter draft.")
    data = json.loads(next(b.text for b in response.content if b.type == "text"))
    for a in AXES:  # clamp: the schema can't express 1..10 for every model
        data["axes"][a]["score"] = max(1, min(10, int(data["axes"][a]["score"])))
    data["groups"] = {"checkable": list(CHECKABLE), "taste": list(TASTE)}
    data["model"] = model
    data["usage"] = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    return data
