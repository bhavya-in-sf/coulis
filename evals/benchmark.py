#!/usr/bin/env python3
""""Sounds like you" benchmark (v0, open).

Two tasks, both scored without a model:

1. Held-out voice: for each held-out post by a known author, does that author's
   profile score it as more "them" than a stranger's profile? (own vs other)
2. Pairwise picks: for each pick a human made between variants (picks.jsonl from
   coulis_pick), does the score rank the picked line above the rejected ones?

An AI writing app can run its own outputs through task 2: give it pairs of
(your output, the human's pick) and report how often the human's pick wins.

    python3 evals/benchmark.py picks --persona <profile dir> --picks <profile dir>/picks.jsonl
    python3 evals/benchmark.py voice --personas personas/a personas/b --heldout heldout.jsonl

heldout.jsonl rows: {"author": "<persona folder name>", "text": "..."}
Score = 100 - sameness, minus 15 per Hold issue and 5 per Revise issue (floor 0).
Results are a pattern on small samples, not an accuracy rate. Publish n with every number.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coulis_core import check, profile_from_folder  # noqa: E402


def score(text, prof, surface="linkedin"):
    r = check(text, prof, surface if surface else "linkedin")
    s = 100 - r["sameness"]["score"] - 15 * r["counts"]["Hold"] - 5 * r["counts"]["Revise"]
    return max(0, s)


def picks(a):
    prof = profile_from_folder(a.persona)
    wins = ties = n = 0
    for line in open(a.picks, encoding="utf-8"):
        rec = json.loads(line)
        p = score(rec["picked"], prof, rec.get("surface"))
        for rej in rec.get("rejected", []):
            q = score(rej, prof, rec.get("surface"))
            n += 1
            wins += p > q
            ties += p == q
    print(json.dumps({"task": "pairwise_picks", "pairs": n, "picked_scored_higher": wins, "ties": ties,
                      "agreement": round(wins / n, 3) if n else None}, indent=2))


def voice(a):
    profs = {Path(p).name: profile_from_folder(p) for p in a.personas}
    own_higher = ties = n = 0
    for line in open(a.heldout, encoding="utf-8"):
        row = json.loads(line)
        if row["author"] not in profs:
            continue
        own = score(row["text"], profs[row["author"]])
        for name, prof in profs.items():
            if name == row["author"]:
                continue
            other = score(row["text"], prof)
            n += 1
            own_higher += own > other
            ties += own == other
    print(json.dumps({"task": "heldout_voice", "comparisons": n, "own_higher": own_higher, "ties": ties}, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("picks"); a1.add_argument("--persona", required=True); a1.add_argument("--picks", required=True)
    a2 = sub.add_parser("voice"); a2.add_argument("--personas", nargs="+", required=True); a2.add_argument("--heldout", required=True)
    a = ap.parse_args()
    picks(a) if a.cmd == "picks" else voice(a)
