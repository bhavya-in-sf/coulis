"""Deterministic half: check (the gate) and learn. No model calls, no network.

Wraps scripts/gate.py and scripts/learn.py so the plug-in and the API run the
exact same code. Same input, same verdict, every time.
"""
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import gate as _gate    # noqa: E402
import learn as _learn  # noqa: E402

SURFACES = tuple(_gate.MODES)


def check(text, profile, surface="linkedin", history=(), max_sameness=None):
    """Gate a draft. Returns {verdict: BLOCK|FIX|PASS, issues: [...], skeleton: [...]}.

    history: optional recent posts on the same surface, each {id, date, title, text},
    used for the sameness check.
    """
    if surface not in SURFACES:
        raise ValueError(f"surface must be one of {SURFACES}")
    hist = [{"id": h.get("id", "?"), "date": h.get("date", ""), "title": h.get("title", "")[:70],
             "skeleton": {k for k, p in _gate.SKELETONS.items() if _gate.re.search(p, _gate.norm(h["text"]))},
             "grams": _gate.ngrams(_gate.norm(h["text"]))} for h in history]
    r = _gate.check(text, profile.to_persona(), surface, hist)
    same = r.get("sameness", {"score": 0, "label": "", "hits": []})
    if max_sameness is not None and same["score"] > max_sameness:
        r["issues"].append({"level": "BLOCK", "check": "sameness_gate",
                            "detail": f"Sameness {same['score']} is over this profile's limit of {max_sameness}.",
                            "quote": ", ".join(same["hits"][:3])})
        r["verdict"] = "BLOCK"
    mode = _gate.MODES.get(surface, {})
    return {"verdict": r["verdict"], "issues": r["issues"], "skeleton": r["skeleton"], "sameness": same,
            "mode": surface, "target_score": mode.get("target_score", 70),
            "counts": {lvl: sum(1 for i in r["issues"] if i["level"] == lvl) for lvl in ("BLOCK", "FIX")}}


def learn(draft, final, profile):
    """Propose rules from what a human changed. Nothing is applied until approved."""
    rules = _learn.propose(draft, final, profile.to_persona())
    return {"proposed_rules": [{"text": r, "source": "learned", "approved": False} for r in rules]}


def backtest(persona_dir):
    """Run the gate over a persona folder's corpus/posts.md (used by the eval set)."""
    return _gate.backtest(persona_dir)
