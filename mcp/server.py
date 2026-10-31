#!/usr/bin/env python3
"""Coulis MCP server (stdio). The universal taste layer for Claude, Cursor and
any MCP client. Zero dependencies beyond the standard library; coulis_critique
also needs the anthropic SDK and a credential.

Profile: the folder in COULIS_PROFILE_DIR (default: the current folder), i.e.
the same TASTE.md + claims.md the Claude plug-in uses.

    claude mcp add coulis -- python3 /path/to/coulis/mcp/server.py
"""
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coulis_core import __version__, check, critique, learn, profile_from_folder  # noqa: E402

PROTOCOL = "2025-06-18"
PROFILE_DIR = {"type": "string", "description": "Optional: folder with the TASTE.md and claims.md to use for this call (e.g. a company or client profile). Defaults to the user's own profile."}
SURFACE = {"type": "string", "enum": ["linkedin", "x", "reddit", "instagram", "youtube", "cold_email", "investor_update", "bio"], "default": "linkedin"}

TOOLS = [
    {"name": "coulis_check",
     "description": "The gate. Check a draft against the user's approved facts, banned phrases and house rules before it is shown or posted. Deterministic, no model call. Returns Hold, Revise or Send with each issue quoted.",
     "inputSchema": {"type": "object", "required": ["text"], "additionalProperties": False,
                     "properties": {"profile_dir": PROFILE_DIR, "text": {"type": "string"}, "surface": SURFACE,
                                    "max_sameness": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Optional team gate: Hold when the sameness score is above this."}}}},
    {"name": "coulis_critique",
     "description": "The critic step. Score a draft on 8 separate axes (clarity, proof, why_you, ask, hook, voice, boldness, rhythm) against the user's taste profile, and rewrite only the weakest part. Never one overall score. With ANTHROPIC_API_KEY set it scores via the API; otherwise it returns the rubric and profile (mode: host_model) for you to score in this chat.",
     "inputSchema": {"type": "object", "required": ["text"], "additionalProperties": False,
                     "properties": {"profile_dir": PROFILE_DIR, "text": {"type": "string"}, "surface": SURFACE}}},
    {"name": "coulis_learn",
     "description": "Propose taste rules from the difference between an AI draft and what the user actually posted. Rules are proposals only; the user must approve each one before it is saved.",
     "inputSchema": {"type": "object", "required": ["draft", "final"], "additionalProperties": False,
                     "properties": {"profile_dir": PROFILE_DIR, "draft": {"type": "string"}, "final": {"type": "string"}}}},
    {"name": "coulis_add",
     "description": "Add one entry to the user's claims.md (created if missing): a legacy fact note requiring migration to claims.json (e.g. '1,200 users'), or a banned phrase with a reason. Only call this after the user explicitly says to add it.",
     "inputSchema": {"type": "object", "required": ["kind", "text"], "additionalProperties": False,
                     "properties": {"profile_dir": PROFILE_DIR, "kind": {"type": "string", "enum": ["approved_fact", "banned_phrase"]},
                                    "text": {"type": "string", "description": "The fact, or the phrase to ban"},
                                    "reason": {"type": "string", "description": "Why it's banned (banned_phrase only)"}}}},
    {"name": "coulis_skip",
     "description": "Record that Coulis was considered for a piece of writing but didn't make sense to use, and why (e.g. 'internal Slack reply, no public claims', 'code comment'). Call this whenever you decide not to run the gate or critique on writing the user will send or post.",
     "inputSchema": {"type": "object", "required": ["reason"], "additionalProperties": False,
                     "properties": {"profile_dir": PROFILE_DIR, "reason": {"type": "string"},
                                    "kind": {"type": "string", "description": "What the writing was, e.g. 'Slack reply', 'email', 'LinkedIn post'"}}}},
    {"name": "coulis_pick",
     "description": "Record which of several variants (e.g. 3 alternative hooks) the user picked. Each pick is saved as pairwise taste data (picked beats each rejected) in picks.jsonl next to the profile, for learning and the benchmark. Call only after the user picks.",
     "inputSchema": {"type": "object", "required": ["picked", "rejected"], "additionalProperties": False,
                     "properties": {"profile_dir": PROFILE_DIR, "picked": {"type": "string"},
                                    "rejected": {"type": "array", "items": {"type": "string"}},
                                    "surface": SURFACE, "context": {"type": "string", "description": "What the variants were for, e.g. 'hook for launch post'"}}}},
    {"name": "coulis_doctor",
     "description": "Health check of the user's taste profile: are TASTE.md and claims.md present, complete and recent? Returns problems with one-line fixes.",
     "inputSchema": {"type": "object", "properties": {"profile_dir": PROFILE_DIR}, "additionalProperties": False}},
    {"name": "coulis_profile",
     "description": "Return the user's taste profile (TASTE.md + claims.md) as structured JSON.",
     "inputSchema": {"type": "object", "properties": {"profile_dir": PROFILE_DIR}, "additionalProperties": False}},
]


CONTEXT = {"type": "object", "additionalProperties": False, "properties": {
    "audience": {"type": "string"}, "purpose": {"type": "string"}}}
for tool in TOOLS:
    if tool['name'] in ('coulis_check', 'coulis_critique', 'coulis_learn'):
        tool['inputSchema']['properties']['context'] = CONTEXT
        tool['inputSchema']['properties']['surface'] = SURFACE
TOOLS += [
    {"name": "coulis_approve_claim", "description": "Save a structured claim only after the human approves its complete wording, source and validity. Does not verify its truth.",
     "inputSchema": {"type": "object", "required": ["claim", "approved"], "additionalProperties": False,
        "properties": {"profile_dir": PROFILE_DIR, "approved": {"type": "boolean"}, "claim": {"type": "object"}}}},
    {"name": "coulis_preference", "description": "Save one explicitly human-approved scoped preference, or retire an existing id. Never infer approval from sent text. Use the same key for mutually exclusive preferences so conflicts are exposed.",
     "inputSchema": {"type": "object", "additionalProperties": False,
        "properties": {"profile_dir": PROFILE_DIR, "rule": {"type": "object"}, "retire_id": {"type": "string"}}}},
]


_ARG_DIR = {"dir": None}  # per-call override from the optional profile_dir argument


def profile_dir():
    """profile_dir argument if given; else COULIS_PROFILE_DIR; else the current folder if it has a profile;
    else ~/.coulis (global)."""
    if _ARG_DIR["dir"]:
        return Path(os.path.expanduser(_ARG_DIR["dir"]))
    env = os.environ.get("COULIS_PROFILE_DIR") or os.environ.get("SAUCE_PROFILE_DIR") or os.environ.get("TASTEE_PROFILE_DIR")
    if env:
        return Path(env)
    here = Path(os.getcwd())
    if (here / "TASTE.md").exists() or (here / "claims.md").exists():
        return here
    home = home_dir()
    return home if (home / "TASTE.md").exists() or (home / "claims.md").exists() else here


def home_dir():
    """~/.coulis, or ~/.sauce / ~/.tastee for installs made before the renames."""
    new = Path.home() / ".coulis"
    olds = [Path.home() / ".sauce", Path.home() / ".tastee"]
    has = lambda d: (d / "TASTE.md").exists() or (d / "claims.md").exists()
    for d in [new] + olds:
        if has(d):
            return d
    if new.is_dir():
        return new
    return next((d for d in olds if d.is_dir()), new)


def profile():
    return profile_from_folder(profile_dir())


def learned_recently(prof, days=7):
    """How many rules were learned from edits in the last `days` days (the loop, made visible)."""
    import datetime as _dt
    today = _dt.date.today()
    n = 0
    for r in prof.rules:
        if r.source == "learned" and r.added:
            try:
                if (today - _dt.date.fromisoformat(r.added)).days <= days:
                    n += 1
            except ValueError:
                pass
    return n


CLAIMS_TEMPLATE = """# claims.md

Legacy notes only. Numeric approvals require complete records in claims.json.

owner:
product:

## Approved facts

## Needs confirm

## Banned phrases

## Story checks
"""


def add_entry(kind, text, reason=""):
    """Append one approved fact or banned phrase to claims.md, keeping the file hand-editable."""
    import re
    text = " ".join(text.split())
    if not text:
        raise ValueError("text is empty")
    path = profile_dir() / "claims.md"
    md = path.read_text() if path.exists() else CLAIMS_TEMPLATE
    if kind == "approved_fact":
        heading, line = "## Approved facts", f"- {text}"
    else:
        heading, line = "## Banned phrases", f"- {reason or 'Banned by the user'} :: " + r"\b" + re.escape(text.lower()) + r"\b"
    if line in md:
        return {"added": False, "note": "Already in claims.md", "file": str(path)}
    if heading not in md:
        md = md.rstrip() + f"\n\n{heading}\n"
    i = md.index(heading) + len(heading)
    nxt = md.find("\n## ", i)
    block_end = len(md) if nxt < 0 else nxt
    md = md[:block_end].rstrip() + f"\n{line}\n" + ("\n" + md[block_end:].lstrip("\n") if nxt >= 0 else "")
    path.write_text(md)
    return {"added": True, "kind": kind, "line": line, "file": str(path)}


def log_use(name, args, out):
    """Usage log next to the profile (coulis-log.jsonl): what was used, when, and the outcome.
    Off by default. COULIS_LOG=1 enables local counts and outcomes, without draft previews."""
    if (os.environ.get("COULIS_LOG") or os.environ.get("TASTEE_LOG", "0")) == "0" or name == "coulis_profile":
        return
    import datetime
    text = args.get("text") or args.get("draft") or ""
    entry = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "tool": name,
             "words": len(text.split())}
    if isinstance(out, dict):
        for k in ("verdict", "mode", "added"):
            if k in out:
                entry[k] = out[k]
        if "proposed_rules" in out:
            entry["rules_proposed"] = len(out["proposed_rules"])
    if name == "coulis_skip":
        entry.update({"reason": args.get("reason", ""), "kind": args.get("kind", "")})
    try:
        home = home_dir()  # one log for every profile, so the record isn't split
        path = (home if home.is_dir() else profile_dir()) / "coulis-log.jsonl"
        if _ARG_DIR["dir"]:
            entry["profile"] = _ARG_DIR["dir"]
        with path.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never break a check


def call_tool(name, args):
    _ARG_DIR["dir"] = args.pop("profile_dir", None)
    try:
        out = _call_tool(name, args)
        log_use(name, args, out)
        return out
    finally:
        _ARG_DIR["dir"] = None


def _call_tool(name, args):
    if name == "coulis_check":
        out = check(args["text"], profile(), args.get("surface", "linkedin"), max_sameness=args.get("max_sameness"), context=args.get("context"))
        d = profile_dir()
        if not ((d / "TASTE.md").exists() or (d / "claims.md").exists()):
            out["profile_status"] = ("default: no profile yet, so every number is unapproved and only the house "
                                     "tells are checked. Say 'add <fact> as a fact' to start claims.md, or run "
                                     "/coulis:setup (or `coulis setup --linkedin export.zip`) to build your voice file.")
        return out
    if name == "coulis_critique":
        prof, surface = profile(), args.get("surface", "linkedin")
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            # No key (the normal plug-in case): hand the rubric to the model already in the chat.
            from coulis_core.critique import SYSTEM, SCHEMA, build_prompt
            return {"mode": "host_model",
                    "instructions": SYSTEM + "\n\nScore the draft below now, in this chat, and reply with JSON "
                                    "matching `output_schema`. Then show the user each axis and the rewrite.",
                    "task": build_prompt(args["text"], prof, surface, args.get("context")),
                    "output_schema": SCHEMA}
        return critique(args["text"], prof, surface, context=args.get("context"))
    if name == "coulis_learn":
        return learn(args["draft"], args["final"], profile(), {**args.get("context", {}), "surface": args.get("surface", "linkedin")})
    if name == "coulis_preference":
        from coulis_core.memory import update
        if bool(args.get("rule")) == bool(args.get("retire_id")):
            raise ValueError("Supply either rule or retire_id")
        return update(profile_dir(), args.get("rule"), args.get("retire_id"))
    if name == "coulis_approve_claim":
        from claims import validate
        from coulis_core.memory import save_json
        if args.get("approved") is not True:
            raise ValueError("Explicit human approval is required")
        record = validate(args["claim"])
        path = profile_dir() / 'claims.json'
        rows = json.loads(path.read_text()) if path.exists() else []
        if any(r['id'] == record['id'] and r != record for r in rows):
            raise ValueError("Use a new approval id for changed facts; do not overwrite history")
        if record not in rows:
            rows.append(record)
            save_json(path, rows)
        return {"saved": True, "file": str(path), "facts_verified": False}
    if name == "coulis_add":
        return add_entry(args["kind"], args["text"], args.get("reason", ""))
    if name == "coulis_skip":
        return {"logged": True, "reason": args["reason"]}
    if name == "coulis_pick":
        import datetime
        rec = {"t": datetime.datetime.now().isoformat(timespec="seconds"), "picked": args["picked"],
               "rejected": args.get("rejected", []), "surface": args.get("surface", "linkedin"),
               "context": args.get("context", "")}
        path = profile_dir() / "picks.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n = sum(1 for _ in path.open())
        return {"saved": True, "pairs_added": len(rec["rejected"]), "total_picks": n, "file": str(path)}
    if name == "coulis_doctor":
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        import doctor
        return doctor.run(profile_dir())
    if name == "coulis_profile":
        out = profile().to_dict()
        out["learned_this_week"] = learned_recently(profile(), 7)
        out["profile_dir"] = str(profile_dir())
        return out
    raise KeyError(name)


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        result = {"protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL),
                  "capabilities": {"tools": {}},
                  "serverInfo": {"name": "coulis", "version": __version__}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        p = msg.get("params", {})
        try:
            out = call_tool(p.get("name"), p.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(out, indent=2)}], "structuredContent": out}
        except KeyError as e:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"Unknown tool or missing argument: {e}"}}
        except Exception as e:  # tool errors go back to the model, not as protocol errors
            result = {"content": [{"type": "text", "text": f"Coulis error: {e}"}], "isError": True}
    elif method == "ping":
        result = {}
    elif mid is None:  # notifications (e.g. notifications/initialized) get no reply
        return None
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            reply = handle(json.loads(line))
        except Exception:
            traceback.print_exc(file=sys.stderr)
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
