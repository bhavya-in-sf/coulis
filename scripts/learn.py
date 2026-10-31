#!/usr/bin/env python3
"""Coulis learn: turn an edit into a rule.

Compares what was drafted with what actually went out (or what a human
changed after a HALT) and proposes TASTE.md rules from the difference.
Proposals are printed for a human to approve; --apply appends them.

    python3 learn.py --persona ../personas/example draft.txt final.txt
    python3 learn.py --persona ../personas/example draft.txt final.txt --apply
"""
import argparse
import datetime as dt
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gate  # noqa: E402


def sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]


def propose(draft, final, persona):
    rules = []
    d_check = gate.check(draft, persona)
    f_check = gate.check(final, persona)
    fixed = {(i["check"], i["quote"]) for i in d_check["issues"]} - {(i["check"], i["quote"]) for i in f_check["issues"]}
    for check, quote in sorted(fixed):
        if not quote:
            continue
        rules.append(f"Human removed {check.replace('_', ' ')} \"{quote}\". Keep flagging it.")

    d_s, f_s = sentences(draft), sentences(final)
    sm = difflib.SequenceMatcher(None, d_s, f_s)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "delete":
            for s in d_s[i1:i2]:
                rules.append(f"Cut lines like: \"{s[:90]}\"")
        elif op == "replace" and i2 - i1 == 1 and j2 - j1 == 1:
            rules.append(f"Prefer \"{f_s[j1][:80]}\" over \"{d_s[i1][:80]}\"")

    d_first, f_first = (d_s[:1] or [""])[0], (f_s[:1] or [""])[0]
    if d_first and f_first and d_first != f_first:
        rules.append(f"Hook changed. New opener style: \"{f_first[:90]}\"")

    d_len = sum(len(s.split()) for s in d_s) / max(1, len(d_s))
    f_len = sum(len(s.split()) for s in f_s) / max(1, len(f_s))
    if f_len < d_len * 0.8:
        rules.append(f"Shorter sentences: about {round(f_len)} words, not {round(d_len)}.")
    if draft.lower() != draft and final.lower() == final:
        rules.append("All lowercase on this surface.")
    return rules


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", required=True)
    ap.add_argument("draft")
    ap.add_argument("final")
    ap.add_argument("--apply", action="store_true", help="Approve and save the displayed proposals")
    ap.add_argument("--surface", required=True, choices=list(gate.MODES))
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from coulis_core import profile_from_folder, learn
    from coulis_core.memory import update
    import json
    rules = learn(Path(a.draft).read_text(), Path(a.final).read_text(), profile_from_folder(a.persona),
                  {"surface": a.surface})["proposed_rules"]
    print(json.dumps(rules, indent=2))
    if a.apply:
        for rule in rules:
            rule["approved"] = True
            update(a.persona, rule=rule)
        print(f"Saved {len(rules)} approved scoped rules to preferences.json")


if __name__ == "__main__":
    main()
