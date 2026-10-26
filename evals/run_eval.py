#!/usr/bin/env python3
"""Sauce eval set. Two suites.

1. Regression (deterministic, free): run the gate over a persona's corpus and
   compare every verdict to a saved golden file. Same input must give the same
   verdict. Any drift fails the run.

       python3 evals/run_eval.py regression --persona personas/example --golden evals/golden/example.json
       # private pilot (kept out of this public repo):
       python3 evals/run_eval.py regression --persona ~/Cowork/taste-layer/personas/pumpgtm \
           --golden ~/Cowork/taste-layer/personas/pumpgtm/backtest.json

2. Edit pairs: does Sauce predict what a human actually changes?
   Each pair is {id, draft, final}. Free metrics come from the gate and learn.
   --critique adds a model call per pair (costs money, opt-in): does the critic's
   weakest-axis rewrite touch a sentence the human really changed?

       python3 evals/run_eval.py edits --persona personas/example --pairs evals/edit_pairs/example.jsonl

Print a golden file:  python3 evals/run_eval.py snapshot --persona personas/example
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sauce_core import backtest, check, learn, profile_from_folder  # noqa: E402


def snapshot(persona):
    return [{"id": r["id"], "verdict": r["verdict"],
             "issues": sorted(f"{i['level']}:{i['check']}:{i['quote']}" for i in r["issues"])}
            for r in backtest(persona)]


def regression(persona, golden_path):
    golden = {g["id"]: g for g in json.loads(Path(golden_path).read_text())}
    rows = backtest(persona)
    drift = []
    for r in rows:
        g = golden.get(r["id"])
        if g is None:
            drift.append(f"{r['id']}: not in golden file")
        elif g["verdict"] != r["verdict"]:
            drift.append(f"{r['id']}: golden {g['verdict']} -> now {r['verdict']}")
    tally = lambda vs: {v: sum(1 for x in vs if x == v) for v in ("BLOCK", "FIX", "PASS")}
    report = {"suite": "regression", "cases": len(rows),
              "golden": tally([g["verdict"] for g in golden.values()]),
              "now": tally([r["verdict"] for r in rows]), "drift": drift, "pass": not drift}
    return report


def sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", t) if s.strip()]


def edits(persona, pairs_path, use_critique=False):
    profile = profile_from_folder(persona)
    pairs = [json.loads(l) for l in Path(pairs_path).read_text().splitlines() if l.strip()]
    flagged = fixed = learned = crit_hits = crit_runs = 0
    rows = []
    for p in pairs:
        d, f = check(p["draft"], profile), check(p["final"], profile)
        d_keys = {(i["check"], i["quote"]) for i in d["issues"]}
        f_keys = {(i["check"], i["quote"]) for i in f["issues"]}
        human_fixed = d_keys - f_keys
        flagged += len(d_keys)
        fixed += len(human_fixed)
        rules = learn(p["draft"], p["final"], profile)["proposed_rules"]
        learned += bool(rules)
        row = {"id": p["id"], "gate_flags": len(d_keys), "human_fixed": len(human_fixed), "rules": len(rules)}
        if use_critique:
            from sauce_core import critique
            c = critique(p["draft"], profile)
            changed = set(sentences(p["draft"])) - set(sentences(p["final"]))
            before = c["rewrite"]["before"].strip()
            hit = any(before and (before in s or s in before) for s in changed)
            crit_runs += 1
            crit_hits += hit
            row.update({"weakest_axis": c["weakest_axis"], "critic_touched_human_edit": hit})
        rows.append(row)
    return {"suite": "edits", "pairs": len(pairs),
            # share of gate flags the human also removed: high = the gate flags what people fix
            "gate_agreement": round(fixed / flagged, 3) if flagged else None,
            "pairs_with_learned_rule": learned,
            "critic_hit_rate": round(crit_hits / crit_runs, 3) if crit_runs else None,
            "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("suite", choices=["regression", "edits", "snapshot"])
    ap.add_argument("--persona", required=True)
    ap.add_argument("--golden")
    ap.add_argument("--pairs")
    ap.add_argument("--critique", action="store_true", help="adds a paid model call per pair")
    a = ap.parse_args()
    if a.suite == "snapshot":
        print(json.dumps(snapshot(a.persona), indent=2))
        return
    report = regression(a.persona, a.golden) if a.suite == "regression" else edits(a.persona, a.pairs, a.critique)
    print(json.dumps(report, indent=2))
    if a.suite == "regression" and not report["pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
