#!/usr/bin/env python3
"""coulis taste card: one shareable page that shows how you write, from your own profile.

    python3 scripts/taste_card.py --profile ~/.coulis --out card.html

Reads TASTE.md and claims.md, measures the samples (sentence length, opener style, dash habit,
average length), and renders a white card with red bubbles. Nothing is invented: every line on the
card is a measurement of the samples or a rule the person wrote. Approved facts are listed as
"numbers I stand behind". The card never shows private data: Needs-confirm items are skipped.
"""
import argparse
import html
import os
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coulis_core.profile import profile_from_folder  # noqa: E402


def measure(samples):
    if not samples:
        return {}
    lens, openers_q, dashes, words = [], 0, 0, []
    for s in samples:
        sents = [x for x in re.split(r"(?<=[.!?])\s+", s.replace("\n", " ")) if len(x.split()) >= 3]
        lens += [len(x.split()) for x in sents]
        first = (sents[0] if sents else s).strip()
        openers_q += first.endswith("?")
        dashes += ("—" in s or "–" in s)
        words.append(len(s.split()))
    return {"sentence": round(statistics.median(lens)) if lens else 0, "post": round(statistics.mean(words)),
            "question_openers": openers_q, "n": len(samples), "dashes": dashes}


def card(prof, m):
    name = html.escape(prof.who_i_write_as or "me")
    rules = [r.text for r in prof.rules][:6]
    facts = prof.approved_facts[:6]
    bubble = lambda t: f'<span class="b">{html.escape(t)}</span>'
    rows = []
    if m:
        rows.append(f"Sentences run about {bubble(str(m['sentence']) + ' words')}.")
        rows.append(f"A post is about {bubble(str(m['post']) + ' words')}.")
        rows.append(("Opens with a question in " + bubble(f"{m['question_openers']} of {m['n']}") + " samples.") if m["question_openers"] else "Opens with a claim, " + bubble("not a question") + ".")
        rows.append(("Uses the em dash." if m["dashes"] else "No em dashes. " + bubble("None.")))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>taste card: {name}</title>
<style>
body{{margin:0;background:#fff;color:#111;font:17px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;padding:40px 20px}}
.card{{max-width:640px;margin:0 auto;border:1px solid #ececec;border-radius:20px;padding:36px}}
h1{{font-size:34px;letter-spacing:-.035em;line-height:1.05;margin:0 0 6px}}
.sub{{color:#6b6b6b;margin:0 0 26px}}
.b{{display:inline-block;background:#e3261c;color:#fff;border-radius:999px;padding:.05em .5em .12em;line-height:1.15;transform:rotate(-1.5deg)}}
ul{{padding-left:0;list-style:none;margin:0;display:grid;gap:12px}}
h2{{font-size:13px;letter-spacing:.02em;color:#6b6b6b;margin:28px 0 10px;font-weight:600}}
.rules li{{padding-left:18px;position:relative;color:#333}}
.rules li::before{{content:"";position:absolute;left:0;top:.55em;width:9px;height:9px;border-radius:50%;background:#e3261c}}
.foot{{margin-top:30px;font-size:13px;color:#6b6b6b;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}
.mark{{font-weight:600;color:#111}}
</style></head><body><div class="card">
<h1>How {name} writes</h1>
<p class="sub">Measured from {m.get('n', 0)} of their own posts by coulis. Nothing here is a guess.</p>
<ul>{''.join(f'<li>{r}</li>' for r in rows)}</ul>
{('<h2>Rules they wrote</h2><ul class="rules">' + ''.join(f'<li>{html.escape(r)}</li>' for r in rules) + '</ul>') if rules else ''}
{('<h2>Numbers they stand behind</h2><ul class="rules">' + ''.join(f'<li>{html.escape(f)}</li>' for f in facts) + '</ul>') if facts else ''}
<div class="foot"><span class="mark">coulis</span><span>An editor for AI drafts, not a detector · github.com/bhavya-in-sf/coulis</span></div>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=os.path.expanduser("~/.coulis"))
    ap.add_argument("--out", default="taste-card.html")
    a = ap.parse_args()
    prof = Path(a.profile)
    if not (prof / "TASTE.md").exists():
        prof = Path(os.path.expanduser("~/.tastee"))
    p = profile_from_folder(prof)
    Path(a.out).write_text(card(p, measure(p.samples)))
    print(a.out)


if __name__ == "__main__":
    main()
