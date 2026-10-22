#!/usr/bin/env python3
"""Tastee from the command line: the same tools as the MCP server, logging included.

    python3 scripts/tastee.py check "your draft"            # or: echo "draft" | ... check -
    python3 scripts/tastee.py critique "your draft"
    python3 scripts/tastee.py skip "why it didn't fit" --kind "Slack reply"
    python3 scripts/tastee.py add approved_fact "1,200 users"
    python3 scripts/tastee.py log                            # summary of uses and skips
    add --profile DIR to use another profile (e.g. a company's)
"""
import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mcp"))
import server  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "critique", "skip", "add", "learn", "log"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--profile")
    ap.add_argument("--surface", default="linkedin")
    ap.add_argument("--kind", default="")
    a = ap.parse_args()
    read = lambda s: sys.stdin.read() if s == "-" else s
    extra = {"profile_dir": a.profile} if a.profile else {}
    if a.cmd == "log":
        path = server.profile_dir() / "tastee-log.jsonl"
        rows = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
        print(f"{len(rows)} entries in {path}")
        print("by tool:", dict(collections.Counter(r["tool"] for r in rows)))
        print("verdicts:", dict(collections.Counter(r.get("verdict") for r in rows if r.get("verdict"))))
        for r in rows:
            if r["tool"] == "tastee_skip":
                print(f"  skip {r['ts']}: {r.get('kind') or '?'}: {r['reason']}")
        return
    if a.cmd in ("check", "critique"):
        out = server.call_tool("tastee_" + a.cmd, {"text": read(a.args[0]), "surface": a.surface, **extra})
    elif a.cmd == "skip":
        out = server.call_tool("tastee_skip", {"reason": a.args[0], "kind": a.kind, **extra})
    elif a.cmd == "add":
        out = server.call_tool("tastee_add", {"kind": a.args[0], "text": a.args[1], **extra})
    else:
        out = server.call_tool("tastee_learn", {"draft": read(a.args[0]), "final": read(a.args[1]), **extra})
    if a.cmd == "check":
        print(out["verdict"])
        for i in out["issues"]:
            print(f"  {i['level']} {i['check']}: {i['quote']!r} {i['detail']}")
    elif a.cmd == "critique" and out.get("mode") == "host_model":
        print(out["task"])
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
