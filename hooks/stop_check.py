#!/usr/bin/env python3
"""Coulis Stop hook: make sure drafts get checked.

Runs when Claude finishes a reply. If the reply contains text the user is
likely to post or send (a quoted block or an unlabelled code block of prose)
and no Coulis tool ran during the turn, it asks Claude to check those drafts
with coulis_check, or record coulis_skip with a reason, before the user sees
the reply. It asks once per turn, never loops, and never blocks on errors.

Turn off with COULIS_HOOK=0.
"""
import json
import os
import re
import sys
import time
from pathlib import Path


def debug(event, **kw):
    """One line per run in ~/.coulis/hook-log.jsonl so you can see the hook fired (COULIS_HOOK_LOG=0 to turn off)."""
    if os.environ.get("COULIS_HOOK_LOG", "1") == "0":
        return
    try:
        d = Path.home() / ".coulis"
        d.mkdir(exist_ok=True)
        with (d / "hook-log.jsonl").open("a") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **kw}) + "\n")
    except OSError:
        pass

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


def edited_pair(checked, drafts, min_change=0.15, max_change=0.8):
    """The checked draft and the final draft, when they are the same piece edited (not a different post)."""
    def toks(t):
        return re.findall(r"[a-z0-9']+", t.lower())
    for final in drafts:
        f = toks(final)
        if len(f) < 12:
            continue
        for c in checked:
            cs = toks(c)
            if not cs or abs(len(cs) - len(f)) > max(len(cs), len(f)) * 0.5:
                continue
            same = len(set(cs) & set(f)) / max(len(set(cs) | set(f)), 1)
            change = 1 - same
            if min_change <= change <= max_change:
                return c, final
    return None


def main():
    if (os.environ.get("COULIS_HOOK") or os.environ.get("TASTEE_HOOK", "1")) == "0":
        return
    try:
        data = json.load(sys.stdin)
        if data.get("stop_hook_active"):
            debug("skip_already_asked")
            return  # already asked once this turn
        # The desktop app can fire Stop before the last reply is written to the transcript: wait for it briefly.
        turn = []
        for _ in range(6):
            turn = last_turn(data["transcript_path"])
            if any(b.get("type") == "text" for r in turn for b in (r.get("message", {}).get("content") or [])
                   if isinstance(b, dict)):
                break
            time.sleep(0.25)
        extra = data.get("last_assistant_message")
        if isinstance(extra, str) and extra.strip():
            turn = turn + [{"type": "assistant", "message": {"content": [{"type": "text", "text": extra}]}}]
    except Exception as e:
        debug("error", error=str(e)[:200])
        return  # never get in the way on errors
    used_coulis, learned, checked, text = False, False, [], []
    for r in turn:
        for b in r.get("message", {}).get("content", []) or []:
            if b.get("type") == "tool_use" and "coulis_" in b.get("name", ""):
                used_coulis = True
                if b["name"].endswith("coulis_learn"):
                    learned = True
                if b["name"].endswith("coulis_check"):
                    checked.append(str((b.get("input") or {}).get("text", "")))
            elif b.get("type") == "text":
                text.append(b.get("text", ""))
    drafts = drafts_in("\n".join(text))
    debug("ran", drafts=len(drafts), used_coulis=used_coulis, turn_rows=len(turn))
    pair = edited_pair(checked, drafts) if (checked and drafts and not learned) else None
    if pair:
        # the draft that was checked is not the draft that went out: that difference is taste. Learn from it, once.
        print(json.dumps({
            "decision": "block",
            "reason": ("Coulis: the final draft in this reply differs from the version that was checked. Call coulis_learn "
                       "with draft = the checked version and final = the version in the reply (same profile_dir as the check), "
                       "then give the reply again with the proposed rules listed in one short line each, for the user to approve or reject. "
                       "Do not save any rule without their yes."),
        }))
        return
    if drafts and not used_coulis:
        print(json.dumps({
            "decision": "block",
            "reason": (f"Coulis: this reply has {len(drafts)} draft(s) the user may post or send, and none were "
                       "checked. Run coulis_check on each draft (use profile_dir if it's written for a company "
                       "or client), fix any BLOCK issues, then give the reply again. If a block isn't something "
                       "the user will post or send, call coulis_skip with the reason instead."),
        }))


if __name__ == "__main__":
    main()
