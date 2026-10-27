#!/usr/bin/env python3
"""Sauce from the command line: the same tools as the MCP server, logging included.

    python3 scripts/sauce.py check "your draft"            # or: echo "draft" | ... check -   (exit 2 BLOCK, 1 FIX, 0 PASS; --json for agents)
    python3 scripts/sauce.py critique "your draft"
    python3 scripts/sauce.py skip "why it didn't fit" --kind "Slack reply"
    python3 scripts/sauce.py add approved_fact "1,200 users"
    python3 scripts/sauce.py log                            # summary of uses and skips
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
    ap.add_argument("cmd", choices=["check", "critique", "skip", "add", "learn", "log", "setup"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--profile")
    ap.add_argument("--surface", default="linkedin")
    ap.add_argument("--kind", default="")
    ap.add_argument("--linkedin", help="setup: a LinkedIn data export zip, or its Shares csv")
    ap.add_argument("--out", help="setup: folder to write TASTE.md and claims.md (default ~/.sauce)")
    ap.add_argument("--name", default="", help="setup: name / role line")
    ap.add_argument("--max-sameness", type=int, help="check: BLOCK when the sameness score is above this (team gate)")
    ap.add_argument("--json", action="store_true", help="check: print the verdict as JSON (for agents)")
    a = ap.parse_args()
    read = lambda s: sys.stdin.read() if s == "-" else s
    extra = {"profile_dir": a.profile} if a.profile else {}
    if a.cmd == "setup":
        from sauce_core.importers import setup_from_linkedin
        out = setup_from_linkedin(a.linkedin, a.out or str(server.home_dir()), name=a.name)
        print(json.dumps(out, indent=2))
        return
    if a.cmd == "log":
        path = server.home_dir() / ("sauce-log.jsonl" if (server.home_dir() / "sauce-log.jsonl").exists() or not (server.home_dir() / "tastee-log.jsonl").exists() else "tastee-log.jsonl")
        rows = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
        print(f"{len(rows)} entries in {path}")
        print("by tool:", dict(collections.Counter(r["tool"] for r in rows)))
        print("verdicts:", dict(collections.Counter(r.get("verdict") for r in rows if r.get("verdict"))))
        try:
            print("rules learned this week:", server.learned_recently(server.profile(), 7))
        except Exception:
            pass
        for r in rows:
            if r["tool"] == "sauce_skip":
                print(f"  skip {r['ts']}: {r.get('kind') or '?'}: {r['reason']}")
        return
    if a.cmd in ("check", "critique"):
        gate_args = {"max_sameness": a.max_sameness} if (a.cmd == "check" and a.max_sameness is not None) else {}
        out = server.call_tool("sauce_" + a.cmd, {"text": read(a.args[0]), "surface": a.surface, **gate_args, **extra})
    elif a.cmd == "skip":
        out = server.call_tool("sauce_skip", {"reason": a.args[0], "kind": a.kind, **extra})
    elif a.cmd == "add":
        out = server.call_tool("sauce_add", {"kind": a.args[0], "text": a.args[1], **extra})
    else:
        out = server.call_tool("sauce_learn", {"draft": read(a.args[0]), "final": read(a.args[1]), **extra})
    if a.cmd == "check":
        if a.json:
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            sm = out.get("sameness", {})
            print(out["verdict"], f"(sameness {sm.get('score')}: {sm.get('label')})" if sm else "")
            for i in out["issues"]:
                print(f"  {i['level']} {i['check']}: {i['quote']!r} {i['detail']}")
        sys.exit({"BLOCK": 2, "FIX": 1}.get(out["verdict"], 0))  # agents branch on the exit code
    elif a.cmd == "critique" and out.get("mode") == "host_model":
        print(out["task"])
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
