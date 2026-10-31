#!/usr/bin/env python3
"""coulis doctor: health check of a taste profile folder (TASTE.md + claims.md).

    python3 scripts/doctor.py [profile_dir]
"""
import json
import sys
import time
from pathlib import Path


def run(folder):
    d = Path(folder).expanduser()
    problems, ok = [], []
    taste, claims = d / "TASTE.md", d / "claims.md"
    if not taste.exists():
        problems.append({"issue": "No TASTE.md", "fix": "Run /coulis:extract or /coulis:setup to build your voice file."})
    else:
        t = taste.read_text(encoding="utf-8", errors="ignore")
        ok.append("TASTE.md found")
        if len(t.split()) < 80:
            problems.append({"issue": "TASTE.md is very short", "fix": "Add 3 to 5 of your best posts as samples, or run /coulis:extract."})
        age = (time.time() - taste.stat().st_mtime) / 86400
        if age > 30:
            problems.append({"issue": f"TASTE.md not updated in {int(age)} days", "fix": "Run /coulis:learn on a recent post you edited."})
    if not claims.exists():
        problems.append({"issue": "No claims.md", "fix": "Say 'add <fact> as a fact' so the gate knows your real numbers."})
    else:
        c = claims.read_text(encoding="utf-8", errors="ignore")
        ok.append("claims.md found")
        facts = [l for l in c.split("## Banned")[0].splitlines() if l.strip().startswith("- ")]
        if len(facts) < 3:
            problems.append({"issue": f"Only {len(facts)} approved facts", "fix": "Add your key numbers (followers, users, revenue) so they stop getting flagged."})
        if "## Banned phrases" not in c:
            problems.append({"issue": "No banned phrases section", "fix": "Add phrases you always cut, e.g. 'game-changer'."})
    try:
        import sys as _s; _s.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from coulis_core import profile_from_folder
        from coulis_core.context import build_context, _tokens
        prof = profile_from_folder(d)
        raw = sum(_tokens(x) for x in prof.samples) + sum(_tokens(r.text) for r in prof.rules) + sum(_tokens(f) for f in prof.approved_facts)
        b = build_context("a draft about what you usually write", prof, "linkedin")
        ok.append(f"profile is about {raw} tokens; the critic sees about {b['tokens']['total']} of a {b['tokens']['budget']} budget "
                  f"({len(b['samples'])} of {len(prof.samples)} samples, {len(b['preferences'])} of {len(prof.rules)} rules, {len(b['facts'])} of {len(prof.approved_facts)} facts)")
        if raw > b['tokens']['budget'] * 3:
            problems.append({"issue": f"Profile is {raw} tokens, well over the {b['tokens']['budget']} the critic reads per call",
                             "fix": "That is fine for retrieval, but prune rules you no longer want; the finder only shows the matching samples."})
    except Exception as e:  # doctor never fails because of a size estimate
        ok.append(f"token size not measured ({str(e)[:60]})")
    picks = d / "picks.jsonl"
    if picks.exists():
        ok.append(f"{sum(1 for _ in picks.open())} variant picks saved")
    return {"profile_dir": str(d), "healthy": not problems, "ok": ok, "problems": problems}


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "~/.coulis"), indent=2))
