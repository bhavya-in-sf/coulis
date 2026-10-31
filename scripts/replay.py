#!/usr/bin/env python3
"""Shadow-mode replay: run an agent's past drafts through Coulis in time order,
as if Coulis had been checking each draft live. Read-only: it never posts anywhere.

    python3 replay.py --persona ../personas/example --out report.md
"""
import argparse
import collections
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gate import backtest  # noqa: E402


def question(issue):
    q = issue["quote"]
    if issue["check"] == "unapproved_claim":
        return f'Your draft says "{q}". Is that true? Reply with the real number, or "never use".'
    if issue["check"] == "unconfirmed_story":
        return f'A draft tells this story: "{q}". Did it happen? yes / no'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = backtest(a.persona)
    counts = collections.Counter(r["verdict"] for r in rows)
    checks = collections.Counter(i["check"] for r in rows for i in r["issues"])
    asks = collections.OrderedDict()
    for r in rows:
        for i in r["issues"]:
            q = question(i)
            if q:
                asks.setdefault(i["quote"].lower(), (q, []))[1].append(r["id"])

    L = [f"# Shadow replay: {Path(a.persona).name}", "",
         f"Read-only replay of {len(rows)} drafts in time order. Nothing was posted or sent.", "",
         "## Headline", "",
         f"- Would have stopped **{counts['BLOCK']}** drafts before anyone saw them (BLOCK).",
         f"- Would have sent **{counts['FIX']}** back for a quick fix, and passed **{counts['PASS']}**.",
         "- Issues found: " + ", ".join(f"{k} {v}" for k, v in checks.most_common()), "",
         "## Questions the owner would have been asked (plain English, once each)", ""]
    money = {k: v for k, v in asks.items() if k.startswith("$")}
    if len(money) > 1:
        ids = sorted({i for _, v in money.values() for i in v})
        L.append(f'- Your drafts use {len(money)} different money figures: {", ".join(money)}. '
                 f'Which one is true? Reply with the real number, or "never use revenue". (in {", ".join(ids)})')
        asks = {k: v for k, v in asks.items() if k not in money}
    L += [f"- {q} (in {', '.join(ids)})" for q, ids in asks.values()] or (["- None."] if len(money) <= 1 else [])
    L += ["", "## Timeline", "", "| Draft | Date | Surface | Verdict | What shadow mode does |", "|---|---|---|---|---|"]
    for r in rows:
        act = "Sends to owner" if r["verdict"] == "PASS" else "; ".join(
            sorted({f"{i['level']} {i['check']}" for i in r["issues"]}))
        L.append(f"| {r['id']} {r['title'][:45]} | {r['date']} | {r['surface']} | {r['verdict']} | {act} |")
    L += ["", "## Weekly digest the owner would have received", ""]
    weeks = collections.defaultdict(list)
    for r in rows:
        y, w, _ = dt.date.fromisoformat(r["date"]).isocalendar()
        weeks[f"{y}-W{w:02d}"].append(r)
    for wk, rs in sorted(weeks.items()):
        c = collections.Counter(i["check"] for r in rs for i in r["issues"])
        top = ", ".join(f"{k} x{v}" for k, v in c.most_common(3)) or "nothing"
        L.append(f"- **{wk}:** {len(rs)} drafts. Caught: {top}. "
                 f"Passed: {', '.join(r['id'] for r in rs if r['verdict'] == 'PASS') or 'none'}.")
    L += ["", "## Learning from edits", "",
          "This replay has drafts only, no matching final versions, so no rules were learned. "
          "In live shadow mode each draft is saved next to the version actually posted, and learn.py proposes rules from the difference."]
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"{counts['BLOCK']} BLOCK / {counts['FIX']} FIX / {counts['PASS']} PASS -> {a.out}")


if __name__ == "__main__":
    main()
