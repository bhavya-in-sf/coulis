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
    """0 to 100: how much this draft reads like the statistical average AI post. Built only from
    quoted, reproducible tells; it is a style score, not a detector of who wrote it."""
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
    label = ("sounds like a person" if score <= 20 else "some AI tells" if score <= 50 else
             "reads as AI" if score <= 80 else "pure slop")
    return {"score": score, "label": label, "hits": hits[:8]}


def norm(s):
    return re.sub(r"\s+", " ", s.lower().replace("’", "'")).strip()


def load_persona(folder):
    folder = Path(folder)
    claims = (folder / "claims.md").read_text()
    approved = claims.split("## Needs", 1)[0]
    stories = []
    if "## Story checks" in claims:
        for line in claims.split("## Story checks", 1)[1].split("\n## ", 1)[0].splitlines():
            if line.startswith("- ") and "::" in line:
                desc, rx = line[2:].split("::", 1)
                stories.append((desc.strip(), rx.strip()))
    banned = []
    if "## Banned phrases" in claims:
        for line in claims.split("## Banned phrases", 1)[1].split("\n## ", 1)[0].splitlines():
            if line.startswith("- ") and "::" in line:
                desc, rx = line[2:].split("::", 1)
                banned.append((desc.strip(), rx.strip()))

    def field(name):
        m = re.search(r"^" + name + r":\s*(.+)$", claims, re.M)
        return norm(m.group(1)) if m else ""
    return {"approved_text": norm(approved), "folder": folder, "stories": stories, "banned": banned,
            "owner": field("owner"), "product": field("product")}


EXAMPLE_CUES = ("words like", "opening with", "openers like", "things like", "like saying", "for example", "e.g.", "such as")


def is_example(t, start):
    return any(c in t[max(0, start - 60):start] for c in EXAMPLE_CUES)


def money_claims(t):
    """Revenue/money and business-count claims, with the number normalised."""
    out = []
    for m in re.finditer(r"\$\s?(\d[\d,.]*)\s?(k|m)?\+?\s*(arr|mrr|in revenue|revenue|a month|/month|per month)?", t):
        num = (m.group(1).replace(",", "") + (m.group(2) or "")).rstrip(".")
        if not is_example(t, m.start()):
            out.append((m.group(0).strip(), num, "money"))
    for m in re.finditer(r"\b(\d[\d,.]*)\s?(k)?\+?\s*(?:" + CLAIM_NOUNS + r")\b", t):
        num = m.group(1).replace(",", "") + (m.group(2) or "")
        if t[max(0, m.start() - 3):m.start()] == "in " or is_example(t, m.start()):
            continue  # "1 in 6 leads" is a ratio, not a claim
        out.append((m.group(0).strip(), num, "count"))
    for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s?%", t):
        if not is_example(t, m.start()):
            out.append((m.group(0), m.group(1), "percent"))
    # multipliers: "10x reach", "3x more leads", "2.5x faster" (not "24x7", "2x2", "4x4")
    for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s?x(?![\w\d])", t):
        if not is_example(t, m.start()):
            out.append((m.group(0), m.group(1) + "x", "percent"))
    for m in re.finditer(r"\b(\d+)\s?(?:->|→|to)\s?(\d+)\s+meetings", t):
        out.append((m.group(0), m.group(1) + "->" + m.group(2), "count"))
    return out


def approved_number(num, approved_text):
    if "->" in num:
        x, y = num.split("->")
        return bool(re.search(re.escape(x) + r"\s?(->|→|to)\s?" + re.escape(y), approved_text))
    base = num.lower()
    forms = {base}
    if base.endswith("k"):
        n = base[:-1]
        forms |= {n + ",000", n + "000", n + "k"}
    elif base.isdigit() and len(base) >= 4:
        forms |= {f"{int(base):,}", base[:-3] + "k" if base.endswith("000") else base}
    return any(re.search(r"(?<![\d,])" + re.escape(f) + r"(?![\d])", approved_text) for f in forms)


FIRST_PERSON = re.compile(r"\b(i|i'm|i've|i'd|me|my|we|we're|we've|our|us|client|clients|customer|customers|"
                          r"user|users|team|teams)\b")
STAT_CUES = re.compile(r"\b(of (people|founders|leaders|users|marketers|buyers|readers|posts|companies|women|men)|"
                       r"most|average|typically|studies|research|survey)\b")


def about_us(text, quote, persona):
    """Is this number a claim about the owner or their business?

    Calibrated on 673 founder posts (Oct 2026). Numbers inside quotation marks
    are examples. Numbers in a sentence that names someone else (a capitalised
    name that is not the owner or product) and has no first-person words are
    about that third party. Everything else stays a claim to check.
    """
    flat = text.replace("’", "'").replace("\n", " ")
    low = flat.lower()
    k = low.find(quote)
    if k < 0:
        return True
    start = max(low.rfind(c, 0, k) for c in ".!?:•→↳\"“") + 1
    ends = [low.find(c, k + len(quote)) for c in ".!?\n•"]
    end = min([e for e in ends if e > 0] or [len(low)])
    sent, sent_low = flat[start:end], low[start:end]
    before = low[:k]
    if before.count("“") > before.count("”") or before.count('"') % 2 == 1:
        return False  # inside a quotation: an example, not a claim
    if FIRST_PERSON.search(sent_low):
        return True
    own = {persona.get("owner", ""), persona.get("product", "")}
    starters = {"the", "a", "an", "this", "that", "these", "it", "its", "they", "their", "he", "she", "his", "her",
                "you", "your", "if", "when", "now", "here", "there", "every", "most", "almost", "around", "about",
                "over", "only", "just", "then", "so", "and", "but", "one", "in", "on", "at", "for", "with", "by"}
    words = re.findall(r"[A-Za-z&][\w&']*", sent)
    names = [w for i, w in enumerate(words) if w[0].isupper() and w.lower() not in own
             and (i > 0 or w.lower() not in starters)]
    if names:
        return False  # names a third party, no first person: their number, not ours
    if STAT_CUES.search(sent_low):
        return True  # a general stat: still needs a source in claims.md
    return True


def ngrams(t, n=3):
    w = re.findall(r"[a-z0-9']+", t)
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


# Modes: each surface has its own length limit, target score and extra rules.
MODES = {
    "linkedin":        { "target_score": 70, "label": "LinkedIn post"},
    "x":               {  "target_score": 70, "label": "X post"},
    "reddit":          { "target_score": 70, "label": "Reddit post"},
    "instagram":       { "target_score": 70, "label": "Instagram caption"},
    "youtube":         {"target_score": 70, "label": "YouTube description"},
    "cold_email":      {"max_words": 125, "target_score": 80, "label": "Cold email",
                        "ask": r"\?|reply|worth a|open to|15 min|call"},
    "investor_update": {"max_words": 400, "target_score": 85, "label": "Investor update",
                        "needs_number": True},
    "bio":             {"max_words": 80,  "target_score": 80, "label": "Bio"},
}


def check(text, persona, surface="reddit", history=()):
    t = norm(text)
    issues = []

    def add(level, check_name, detail, quote=""):
        issues.append({"level": level, "check": check_name, "detail": detail, "quote": quote})

    # 1. dashes
    for d in ("—", "–", "--"):
        if d in text:
            add("Hold", "em_dash", "Em dash or double hyphen (house rule).", d)

    # 2. claims vs claims.md
    seen = set()
    for quote, num, kind in money_claims(t):
        if (quote, num) in seen:
            continue
        seen.add((quote, num))
        if approved_number(num, persona["approved_text"]):
            continue
        if not about_us(text, quote, persona):
            continue  # a number about someone else, or a quoted example: not our claim
        level ="Hold" if kind == "money" or "arr" in quote or "mrr" in quote else "Revise"
        add(level, "unapproved_claim", "Number not in claims.md. Add it to claims.md or cut it.", quote)

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
    for f in FILLER:
        for m in re.finditer(re.escape(f), t):
            if not is_example(t, m.start()):
                add("Revise", "filler", "Corporate filler word.", f)
                break

    # 5. slang overuse (voice rule: at most once)
    slang_hits = [s.strip() for s in SLANG if re.search(r"\b" + re.escape(s.strip()) + r"\b", t)]
    total = sum(len(re.findall(r"\b" + re.escape(s) + r"\b", t)) for s in slang_hits)
    if total > 2:
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
    return {"verdict": verdict, "issues": issues, "skeleton": sorted(skel), "sameness": sameness(text, issues)}


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
        r = check(p["text"], persona, p["surface"], recent)
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
    r = check(text, load_persona(a.persona), a.surface)
    print(json.dumps(r, indent=2) if a.json else f"{r['verdict']}\n" + "\n".join(
        f"  {i['level']} {i['check']}: {i['quote']!r} {i['detail']}" for i in r["issues"]))
    sys.exit(2 if r["verdict"] == "Hold" else 0)


if __name__ == "__main__":
    main()
