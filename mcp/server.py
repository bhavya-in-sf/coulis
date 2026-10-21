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
     "description": "The critic step. Score a draft on 8 separate axes (clarity, proof, why_you, ask, hook, voice, boldness, rhythm) against the user's taste profile, and rewrite only the weakest part. Never one overall score. Makes one model call.",
     "inputSchema": {"type": "object", "required": ["text"], "additionalProperties": False,
                     "properties": {"text": {"type": "string"}, "surface": SURFACE}}},
    {"name": "tastee_learn",
     "description": "Propose taste rules from the difference between an AI draft and what the user actually posted. Rules are proposals only; the user must approve each one before it is saved.",
     "inputSchema": {"type": "object", "required": ["draft", "final"], "additionalProperties": False,
                     "properties": {"draft": {"type": "string"}, "final": {"type": "string"}}}},
    {"name": "tastee_profile",
     "description": "Return the user's taste profile (TASTE.md + claims.md) as structured JSON.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
]


def profile():
    return profile_from_folder(os.environ.get("TASTEE_PROFILE_DIR", os.getcwd()))


def call_tool(name, args):
    if name == "tastee_check":
        return check(args["text"], profile(), args.get("surface", "linkedin"))
    if name == "tastee_critique":
        return critique(args["text"], profile(), args.get("surface", "linkedin"))
    if name == "tastee_learn":
        return learn(args["draft"], args["final"], profile())
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
