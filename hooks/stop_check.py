#!/usr/bin/env python3
"""Sauce Stop hook: make sure drafts get checked.

Runs when Claude finishes a reply. If the reply contains text the user is
likely to post or send (a quoted block or an unlabelled code block of prose)
and no Sauce tool ran during the turn, it asks Claude to check those drafts
with sauce_check, or record sauce_skip with a reason, before the user sees
the reply. It asks once per turn, never loops, and never blocks on errors.

Turn off with SAUCE_HOOK=0.
"""
import json
import os
import re
import sys

CODE_LANGS_OK = {"", "text", "txt", "markdown", "md"}
COMMANDY = re.compile(r"^\s*(/|\$|git |cd |claude |python3? |npm |bash |curl |ls |mkdir |hdiutil |export |echo )")


def is_real_user(msg):
    """A message the person typed (not a tool result)."""
    c = msg.get("message", {}).get("content")
    if isinstance(c, str):
        return True
    return isinstance(c, list) and any(b.get("type") == "text" for b in c) and \
        not any(b.get("type") == "tool_result" for b in c)


def last_turn(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    start = 0
    for i, r in enumerate(rows):
        if r.get("type") == "user" and is_real_user(r):
            start = i
    return [r for r in rows[start + 1:] if r.get("type") == "assistant"]


def drafts_in(text):
    found = []
    for lang, body in re.findall(r"```([^\n`]*)\n(.*?)```", text, re.S):
        lines = [l for l in body.strip().splitlines() if l.strip()]
        if lang.strip().lower() not in CODE_LANGS_OK or not lines:
            continue
        if sum(1 for l in lines if COMMANDY.match(l)) >= len(lines) / 2:
            continue  # shell commands, not a post
        if len(body.split()) >= 12:
            found.append(body.strip())
    for block in re.findall(r"(?:^>.*\n?)+", text, re.M):
        body = "\n".join(l[1:].strip() for l in block.strip().splitlines())
        if len(body.split()) >= 5:  # quoted one-liners are often post suggestions
            found.append(body)
    return found


def main():
    if (os.environ.get("SAUCE_HOOK") or os.environ.get("TASTEE_HOOK", "1")) == "0":
        return
    try:
        data = json.load(sys.stdin)
        if data.get("stop_hook_active"):
            return  # already asked once this turn
        turn = last_turn(data["transcript_path"])
    except Exception:
        return  # never get in the way on errors
    used_sauce, text = False, []
    for r in turn:
        for b in r.get("message", {}).get("content", []) or []:
            if b.get("type") == "tool_use" and "sauce_" in b.get("name", ""):
                used_sauce = True
            elif b.get("type") == "text":
                text.append(b.get("text", ""))
    drafts = drafts_in("\n".join(text))
    if drafts and not used_sauce:
        print(json.dumps({
            "decision": "block",
            "reason": (f"Sauce: this reply has {len(drafts)} draft(s) the user may post or send, and none were "
                       "checked. Run sauce_check on each draft (use profile_dir if it's written for a company "
                       "or client), fix any BLOCK issues, then give the reply again. If a block isn't something "
                       "the user will post or send, call sauce_skip with the reason instead."),
        }))


if __name__ == "__main__":
    main()
