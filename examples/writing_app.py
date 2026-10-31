#!/usr/bin/env python3
"""Example: an AI writing app that runs every draft through the Taste API
before the user sees it.

Claude writes a draft, Coulis's gate checks it (no model call), and if the
gate blocks it, Claude gets the quoted issues back for one revision. The user
only ever sees a draft that passed, or the issues that still need a human.

    export ANTHROPIC_API_KEY=...  COULIS_API_KEY=tst_...  COULIS_PROFILE_ID=prf_...
    python3 examples/writing_app.py "Announce that we passed 1,200 users"
"""
import os
import sys
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdk" / "python"))
from coulis_client import Coulis  # noqa: E402

MODEL = "claude-opus-5-5"


def draft(client, brief, feedback=None):
    content = f"Write one LinkedIn post. Brief: {brief}"
    if feedback:
        content += "\n\nA reviewer blocked the last draft for these issues. Fix only these:\n" + feedback
    r = client.messages.create(model=MODEL, max_tokens=2048, output_config={"effort": "low"},
                               messages=[{"role": "user", "content": content}])
    return next(b.text for b in r.content if b.type == "text").strip()


def main():
    brief = " ".join(sys.argv[1:]) or "Announce our launch"
    claude, coulis = anthropic.Anthropic(), Coulis()
    profile_id = os.environ["COULIS_PROFILE_ID"]

    text = draft(claude, brief)
    result = coulis.check(profile_id, text)
    if result["verdict"] == "Hold":
        issues = "\n".join(f"- {i['check']}: \"{i['quote']}\" ({i['detail']})" for i in result["issues"])
        text = draft(claude, brief, issues)
        result = coulis.check(profile_id, text)

    print(text, "\n")
    print(f"Coulis verdict: {result['verdict']}")
    for i in result["issues"]:
        print(f"  {i['level']} {i['check']}: {i['quote']!r}  {i['detail']}")
    if result["verdict"] != "Send":
        print("\nNeeds a human before posting.")


if __name__ == "__main__":
    main()
