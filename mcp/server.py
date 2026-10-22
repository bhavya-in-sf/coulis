#!/usr/bin/env python3
"""Tastee MCP server (stdio). The universal taste layer for Claude, Cursor and
any MCP client. Zero dependencies beyond the standard library; tastee_critique
also needs the anthropic SDK and a credential.

Profile: the folder in TASTEE_PROFILE_DIR (default: the current folder), i.e.
the same TASTE.md + claims.md the Claude plug-in uses.

    claude mcp add tastee -- python3 /path/to/tastee/mcp/server.py
"""
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tastee_core import __version__, check, critique, learn, profile_from_folder  # noqa: E402

PROTOCOL = "2025-06-18"
SURFACE = {"type": "string", "enum": ["linkedin", "x", "reddit", "instagram", "youtube"], "default": "linkedin"}

TOOLS = [
    {"name": "tastee_check",
     "description": "The gate. Check a draft against the user's approved facts, banned phrases and house rules before it is shown or posted. Deterministic, no model call. Returns BLOCK, FIX or PASS with each issue quoted.",
     "inputSchema": {"type": "object", "required": ["text"], "additionalProperties": False,
                     "properties": {"text": {"type": "string"}, "surface": SURFACE}}},
    {"name": "tastee_critique",
     "description": "The critic step. Score a draft on 8 separate axes (clarity, proof, why_you, ask, hook, voice, boldness, rhythm) against the user's taste profile, and rewrite only the weakest part. Never one overall score. With ANTHROPIC_API_KEY set it scores via the API; otherwise it returns the rubric and profile (mode: host_model) for you to score in this chat.",
     "inputSchema": {"type": "object", "required": ["text"], "additionalProperties": False,
                     "properties": {"text": {"type": "string"}, "surface": SURFACE}}},
    {"name": "tastee_learn",
     "description": "Propose taste rules from the difference between an AI draft and what the user actually posted. Rules are proposals only; the user must approve each one before it is saved.",
     "inputSchema": {"type": "object", "required": ["draft", "final"], "additionalProperties": False,
                     "properties": {"draft": {"type": "string"}, "final": {"type": "string"}}}},
    {"name": "tastee_add",
     "description": "Add one entry to the user's claims.md (created if missing): an approved fact the gate should allow (e.g. '1,200 users'), or a banned phrase with a reason. Only call this after the user explicitly says to add it.",
     "inputSchema": {"type": "object", "required": ["kind", "text"], "additionalProperties": False,
                     "properties": {"kind": {"type": "string", "enum": ["approved_fact", "banned_phrase"]},
                                    "text": {"type": "string", "description": "The fact, or the phrase to ban"},
                                    "reason": {"type": "string", "description": "Why it's banned (banned_phrase only)"}}}},
    {"name": "tastee_skip",
     "description": "Record that Tastee was considered for a piece of writing but didn't make sense to use, and why (e.g. 'internal Slack reply, no public claims', 'code comment'). Call this whenever you decide not to run the gate or critique on writing the user will send or post.",
     "inputSchema": {"type": "object", "required": ["reason"], "additionalProperties": False,
                     "properties": {"reason": {"type": "string"},
                                    "kind": {"type": "string", "description": "What the writing was, e.g. 'Slack reply', 'email', 'LinkedIn post'"}}}},
    {"name": "tastee_profile",
     "description": "Return the user's taste profile (TASTE.md + claims.md) as structured JSON.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
]


def profile_dir():
    """TASTEE_PROFILE_DIR if set; else the current folder if it has a profile; else ~/.tastee (global)."""
    if os.environ.get("TASTEE_PROFILE_DIR"):
        return Path(os.environ["TASTEE_PROFILE_DIR"])
    here = Path(os.getcwd())
    if (here / "TASTE.md").exists() or (here / "claims.md").exists():
        return here
    home = Path.home() / ".tastee"
    return home if (home / "TASTE.md").exists() or (home / "claims.md").exists() else here


def profile():
    return profile_from_folder(profile_dir())


CLAIMS_TEMPLATE = """# claims.md

The gate allows only the numbers and claims listed under Approved facts.

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
    """Usage log next to the profile (tastee-log.jsonl): what was used, when, and the outcome.
    Stores a short preview of the text, never the whole draft. Turn off with TASTEE_LOG=0."""
    if os.environ.get("TASTEE_LOG", "1") == "0" or name == "tastee_profile":
        return
    import datetime
    text = args.get("text") or args.get("draft") or ""
    entry = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "tool": name,
             "words": len(text.split()), "preview": " ".join(text.split()[:10])}
    if isinstance(out, dict):
        for k in ("verdict", "mode", "added"):
            if k in out:
                entry[k] = out[k]
        if "proposed_rules" in out:
            entry["rules_proposed"] = len(out["proposed_rules"])
    if name == "tastee_skip":
        entry.update({"reason": args.get("reason", ""), "kind": args.get("kind", "")})
    try:
        path = profile_dir() / "tastee-log.jsonl"
        with path.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never break a check


def call_tool(name, args):
    out = _call_tool(name, args)
    log_use(name, args, out)
    return out


def _call_tool(name, args):
    if name == "tastee_check":
        return check(args["text"], profile(), args.get("surface", "linkedin"))
    if name == "tastee_critique":
        prof, surface = profile(), args.get("surface", "linkedin")
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            # No key (the normal plug-in case): hand the rubric to the model already in the chat.
            from tastee_core.critique import SYSTEM, SCHEMA, build_prompt
            return {"mode": "host_model",
                    "instructions": SYSTEM + "\n\nScore the draft below now, in this chat, and reply with JSON "
                                    "matching `output_schema`. Then show the user each axis and the rewrite.",
                    "task": build_prompt(args["text"], prof, surface),
                    "output_schema": SCHEMA}
        return critique(args["text"], prof, surface)
    if name == "tastee_learn":
        return learn(args["draft"], args["final"], profile())
    if name == "tastee_add":
        return add_entry(args["kind"], args["text"], args.get("reason", ""))
    if name == "tastee_skip":
        return {"logged": True, "reason": args["reason"]}
    if name == "tastee_profile":
        return profile().to_dict()
    raise KeyError(name)


def handle(msg):
    method, mid = msg.get("method"), msg.get("id")
    if method == "initialize":
        result = {"protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL),
                  "capabilities": {"tools": {}},
                  "serverInfo": {"name": "tastee", "version": __version__}}
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
            result = {"content": [{"type": "text", "text": f"Tastee error: {e}"}], "isError": True}
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
