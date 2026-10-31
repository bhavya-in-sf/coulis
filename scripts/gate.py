#!/usr/bin/env python3
"""Coulis post gate: the checkable half.

Checks a draft against a persona folder (TASTE.md + claims.md) before it posts.
No AI calls, no network. Same input always gives the same answer, so an agent
can call it as a hard gate and a human can trust it.

    python3 gate.py --persona ../personas/example --surface linkedin draft.txt
    echo "text" | python3 gate.py --persona ../personas/example --surface x -
    python3 gate.py --persona ../personas/example --backtest   # runs on corpus/posts.md

Verdict: Hold (must fix before posting), Revise (should fix), Send.
The taste half (hook, voice, boldness, rhythm) is judged by the critique skill,
not here, because it needs judgment.
"""
import claims as claim_checker
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

FILLER = ["streamline", "leverage", "unlock", "seamless", "empower", "game-changer", "game changer",
          "hope this finds you well", "in today's fast-paced", "delve", "elevate your"]
SLANG = ["lol", "tbh", "ngl", "lmao", "bro", "ik "]
CLAIM_NOUNS = (r"(companies|cos|customers|clients|leads|meetings|messages|founders|signups|followers|subscribers|"
               r"readers|members|downloads|installs|stars|views|impressions|posts|"
               r"requests|users|people\s+served|launches|pivots|vas|replies)")
SKELETONS = {
    "arr_guide": r"\$\s?\d+\s?k\+?\s?(arr|mrr)",
    "how_to_guide": r"\b(guide|here'?s how|here'?s \d+|\d+ things|\d+ lessons|\d+ checks)\b",
    "scale_with_own_product": r"(using|use) (my|our) (own )?(scaling )?product to scale",
}


# patterns that mark a draft as "the average AI post" (from the humanizer / tell-linter clusters and
# Kobak et al. 2024). Each hit is a reason, quoted, never a guess about who wrote it.
TELLS = [
    ("not_x_but_y", r"\b(it'?s|this is|that'?s) not (just |only |about )?[^.?!]{3,60}?,? (it'?s|this is|but) ", "The \"it's not X, it's Y\" frame."),
    ("question_opener", r"^\s*[^.!?\n]{8,120}\?\s*(\n|$)", "Opens with a question. The default AI hook."),
    ("comment_cta", r"\b(comment|drop) (below|a |\"|\')[^.\n]{0,40}", "Ends with the stock \"comment below\" ask."),
    ("tricolon", r"\b(\w+), (\w+),? and (\w+)\b[^.]{0,3}\.", "Three-item list cadence, three times the usual rate in AI text."),
    ("emoji_pile", r"([\U0001F300-\U0001FAFF\u2600-\u27BF]\s*){3,}", "Three or more emoji in a row."),
    ("one_line_paras", r"(?:^[^\n]{10,90}\n\n){4,}", "Four or more one-line paragraphs in a row."),
]


def sameness(text, issues):
    """Legacy 0–100 pattern diagnostic, not a validated voice/quality score or authorship detector."""
    score, hits = 0, []
    for i in issues:
        if i["check"] == "em_dash": score += 20; hits.append("em dash")
        elif i["check"] == "banned_phrase": score += 15; hits.append(i["quote"])
        elif i["check"] == "filler": score += 10; hits.append(i["quote"])
    low = text.lower().replace("’", "'")
    for name, rx, why in TELLS:
        if re.search(rx, low if name != "emoji_pile" else text, re.M | re.S):
            score += 12; hits.append(name.replace("_", " "))
    score = min(100, score)
    label = ("few pattern matches" if score <= 20 else "some pattern matches" if score <= 50 else "many pattern matches")
    return {"score": score, "label": label, "hits": hits[:8]}


def norm(s):
    return re.sub(r"\s+", " ", s.lower().replace("’", "'")).strip()


def load_persona(folder, context=None):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from coulis_core.profile import profile_from_folder
    persona = profile_from_folder(folder).to_persona(context)
    persona["folder"] = Path(folder)
    return persona


EXAMPLE_CUES = ("words like", "opening with", "openers like", "things like", "like saying", "for example", "e.g.", "such as")


def is_example(t, start):
    return any(c in t[max(0, start - 60):start] for c in EXAMPLE_CUES)


def ngrams(t, n=3):
    w = re.findall(r"[a-z0-9']+", t)
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


# Modes: each surface has its own length limit and extra rules.
MODES = {
    "linkedin":        { "label": "LinkedIn post"},
    "x":               {  "label": "X post"},
    "reddit":          { "label": "Reddit post"},
    "instagram":       { "label": "Instagram caption"},
    "youtube":         {"label": "YouTube description"},
    "cold_email":      {"max_words": 125, "label": "Cold email",
                        "ask": r"\?|reply|worth a|open to|15 min|call"},
    "investor_update": {"max_words": 400, "label": "Investor update",
                        "needs_number": True},
    "bio":             {"max_words": 80,  "label": "Bio"},
}


def check(text, persona, surface="reddit", history=()):
    t = norm(text)
    issues = []

    def add(level, check_name, detail, quote=""):
        issues.append({"level": level, "check": check_name, "detail": detail, "quote": quote})

    # Style preferences are opt-in and selected for the current context.
    preferences = persona.get("preferences", {})
    if preferences.get("em_dash") == "avoid":
        for d in ("—", "–", "--"):
            if d in text:
                add("Hold", "em_dash", "This profile prefers no dashes in this context.", d)

    facts = claim_checker.assess(text, persona.get("claims", []))
    for item in facts["claims"]:
        if item["status"] == "unresolved":
            add("Hold" if "$" in item["quote"] else "Revise", "unapproved_claim", item["reason"], item["quote"])
    for claim_id in facts["invalid_approvals"]:
        add("Revise", "invalid_approval", "Repair the incomplete structured approval before relying on it.", claim_id)
    for conflict in persona.get("preference_conflicts", []):
        add("Revise", "preference_conflict", "Conflicting preferences: select or retire one before applying it.", conflict)

    # 2b. personal stories the owner must confirm they happened
    for desc, rx in persona.get("stories", []):
        m = re.search(rx, t)
        if m:
            add("Revise", "unconfirmed_story", f"Story not confirmed by the owner: {desc}.", m.group(0))

    # 3. banned phrases from claims.md ("## Banned phrases": "- why :: regex")
    for desc, rx in persona.get("banned", []):
        for m in re.finditer(rx, t):
            add("Hold", "banned_phrase", desc, m.group(0))

    # 4. filler
    for f in (FILLER if preferences.get("filler") == "avoid" else []):
        for m in re.finditer(re.escape(f), t):
            if not is_example(t, m.start()):
                add("Revise", "filler", "Corporate filler word.", f)
                break

    # 5. slang overuse (voice rule: at most once)
    slang_hits = [s.strip() for s in SLANG if re.search(r"\b" + re.escape(s.strip()) + r"\b", t)]
    total = sum(len(re.findall(r"\b" + re.escape(s) + r"\b", t)) for s in slang_hits)
    if preferences.get("slang") == "limited" and total > 2:
        add("Revise", "slang", f"Slang used {total} times. Voice rule: once, maybe twice.", ", ".join(slang_hits))

    # 6. disclosure + self-promo honesty (reddit)
    prod, owner = persona.get("product"), persona.get("owner")
    names_product = bool(prod) and prod in t
    if surface == "reddit":
        disclosed = re.search(r"(i (run|founded|built|am building)|i'm building|founder of|my (startup|company|product))", t)
        if names_product and not disclosed and not (owner and owner in t):
            add("Revise", "disclosure", "Names the product without saying you built it.")
        if "i will not promote" in t and names_product:
            add("Hold", "promo_honesty", "Says 'I will not promote' but names the product.", "i will not promote")

    # 6b. mode rules (length, the ask, numbers) per surface
    mode = MODES.get(surface, {})
    words = len(text.split())
    if mode.get("max_words") and words > mode["max_words"]:
        add("Revise", "mode_length", f"{words} words. {mode['label']}: keep it under {mode['max_words']}.")
    if mode.get("ask") and not re.search(mode["ask"], t):
        add("Revise", "mode_ask", f"{mode['label']}: needs one clear ask.")
    if mode.get("needs_number") and not re.search(r"\d", t):
        add("Revise", "mode_numbers", f"{mode['label']}: carry at least one real number.")

    # 7. sameness vs recent posts on the same surface
    skel = {k for k, p in SKELETONS.items() if re.search(p, t)}
    grams = ngrams(t)
    for h in history:
        hskel = h["skeleton"] & skel
        overlap = len(grams & h["grams"]) / max(1, min(len(grams), len(h["grams"])))
        if hskel or overlap > 0.12:
            why = []
            if hskel:
                why.append("same skeleton: " + ", ".join(sorted(hskel)))
            if overlap > 0.12:
                why.append(f"{overlap:.0%} shared phrasing")
            add("Revise", "sameness", f"Too close to {h['id']} ({h['date']}): " + "; ".join(why), h["title"][:70])

    uniq, keys = [], set()
    for i in issues:
        k = (i["check"], i["quote"])
        if k not in keys:
            keys.add(k)
            uniq.append(i)
    issues = uniq
    verdict = "Hold" if any(i["level"] == "Hold" for i in issues) else "Revise" if issues else "Send"
    return {"verdict": verdict, "issues": issues, "skeleton": sorted(skel), "sameness": sameness(text, issues), "fact_check": facts,
            "summary": "No configured rule violations found; facts are not independently verified." if verdict == "Send" else "Review the unresolved issues; this is not publication clearance."}


def parse_corpus(path):
    posts = []
    for block in Path(path).read_text().split("\n## ")[1:]:
        head, _, body = block.partition("\n")
        parts = [p.strip() for p in head.split("|")]
        pid, date, surface = parts[0], parts[1], parts[2]
        title = ""
        if body.startswith("title:"):
            title, _, body = body.partition("\n")
            title = title[6:].strip()
        posts.append({"id": pid, "date": date, "surface": surface.split()[0], "title": title,
                      "text": (title + "\n" + body).strip(), "drafter": parts[3].replace("drafter:", "").strip()})
    return posts


def backtest(persona_dir):
    persona = load_persona(persona_dir)
    posts = parse_corpus(Path(persona_dir) / "corpus" / "posts.md")
    rows, history = [], []
    for p in posts:
        d = dt.date.fromisoformat(p["date"])
        recent = [h for h in history if h["surface"] == p["surface"] and (d - h["d"]).days <= 7]
        r = check(p["text"], load_persona(persona_dir, {"surface": p["surface"]}), p["surface"], recent)
        rows.append({**p, **r})
        history.append({"id": p["id"], "date": p["date"], "d": d, "surface": p["surface"], "title": p["title"],
                        "skeleton": set(r["skeleton"]), "grams": ngrams(norm(p["text"]))})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--persona", required=True)
    ap.add_argument("--surface", default="reddit", choices=list(MODES))
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("file", nargs="?")
    a = ap.parse_args()
    if a.backtest:
        rows = backtest(a.persona)
        if a.json:
            print(json.dumps([{k: v for k, v in r.items() if k != "text"} for r in rows], indent=2))
        else:
            for r in rows:
                print(f"{r['id']} {r['date']} {r['surface']:7} {r['verdict']:5} {r['title'][:60]}")
                for i in r["issues"]:
                    print(f"    {i['level']:5} {i['check']:16} {i['quote'][:50]!r}  {i['detail']}")
        return
    text = sys.stdin.read() if a.file in (None, "-") else Path(a.file).read_text()
    r = check(text, load_persona(a.persona, {"surface": a.surface}), a.surface)
    print(json.dumps(r, indent=2) if a.json else f"{r['verdict']}\n" + "\n".join(
        f"  {i['level']} {i['check']}: {i['quote']!r} {i['detail']}" for i in r["issues"]))
    sys.exit(2 if r["verdict"] == "Hold" else 0)


if __name__ == "__main__":
    main()
