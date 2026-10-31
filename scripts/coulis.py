#!/usr/bin/env python3
"""Coulis from the command line: the same tools as the MCP server, logging included.

    python3 scripts/coulis.py check "your draft"            # or: echo "draft" | ... check -   (exit 2 Hold, 1 Revise, 0 Send; --json for agents)
    python3 scripts/coulis.py critique "your draft"
    python3 scripts/coulis.py skip "why it didn't fit" --kind "Slack reply"
    python3 scripts/coulis.py add approved_fact "1,200 users"
    python3 scripts/coulis.py log                            # summary of uses and skips
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
    ap.add_argument("cmd", choices=["check", "critique", "skip", "add", "learn", "log", "setup", "workflow", "context", "feedback", "call"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--profile")
    ap.add_argument("--surface", default="linkedin")
    ap.add_argument("--kind", default="")
    ap.add_argument("--linkedin", help="setup: a LinkedIn data export zip, or its Shares csv")
    ap.add_argument("--out", help="setup: folder to write TASTE.md and claims.md (default ~/.coulis)")
    ap.add_argument("--name", default="", help="setup: name / role line")
    ap.add_argument("--max-sameness", type=int, help="check: Hold when the sameness score is above this (team gate)")
    ap.add_argument("--json", action="store_true", help="check: print the verdict as JSON (for agents)")
    a = ap.parse_args()
    read = lambda s: sys.stdin.read() if s == "-" else s
    extra = {"profile_dir": a.profile} if a.profile else {}
    if a.cmd == "setup":
        from coulis_core.importers import setup_from_linkedin
        out = setup_from_linkedin(a.linkedin, a.out or str(server.home_dir()), name=a.name)
        print(json.dumps(out, indent=2))
        return
    if a.cmd == "log":
        path = server.home_dir() / ("coulis-log.jsonl" if (server.home_dir() / "coulis-log.jsonl").exists() or not (server.home_dir() / "tastee-log.jsonl").exists() else "tastee-log.jsonl")
        rows = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
        print(f"{len(rows)} entries in {path}")
        print("by tool:", dict(collections.Counter(r["tool"] for r in rows)))
        print("verdicts:", dict(collections.Counter(r.get("verdict") for r in rows if r.get("verdict"))))
        try:
            print("rules learned this week:", server.learned_recently(server.profile(), 7))
        except Exception:
            pass
        for r in rows:
            if r["tool"] == "coulis_skip":
                print(f"  skip {r['ts']}: {r.get('kind') or '?'}: {r['reason']}")
        return
    if a.cmd in ("workflow", "context", "feedback", "call"):
        from sdk.python.coulis_client import LocalClient
        client = LocalClient(a.profile or server.profile_dir())
        if a.cmd in ("workflow", "call"):
            if not a.args: ap.error("provide an action or operation, followed by JSON or - for stdin")
            payload = json.loads(read(a.args[1])) if len(a.args)>1 else {}
            out = client.workflow(a.args[0], **payload) if a.cmd == "workflow" else client.call(a.args[0], **payload)
        else:
            payload = json.loads(read(a.args[0])) if a.args else {}
            out = client.call(a.cmd, **payload)
    elif a.cmd in ("check", "critique"):
        gate_args = {"max_sameness": a.max_sameness} if (a.cmd == "check" and a.max_sameness is not None) else {}
        out = server.call_tool("coulis_" + a.cmd, {"text": read(a.args[0]), "surface": a.surface, **gate_args, **extra})
    elif a.cmd == "skip":
        out = server.call_tool("coulis_skip", {"reason": a.args[0], "kind": a.kind, **extra})
    elif a.cmd == "add":
        out = server.call_tool("coulis_add", {"kind": a.args[0], "text": a.args[1], **extra})
    else:
        out = server.call_tool("coulis_learn", {"draft": read(a.args[0]), "final": read(a.args[1]), **extra})
    if a.cmd == "check":
        if a.json:
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            sm = out.get("sameness", {})
            print(out["verdict"], f"(sameness {sm.get('score')}: {sm.get('label')})" if sm else "")
            for i in out["issues"]:
                print(f"  {i['level']} {i['check']}: {i['quote']!r} {i['detail']}")
        sys.exit({"Hold": 2, "Revise": 1}.get(out["verdict"], 0))  # agents branch on the exit code
    elif a.cmd == "critique" and out.get("mode") == "host_model":
        print(out["task"])
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
