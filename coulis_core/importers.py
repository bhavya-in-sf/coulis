"""Build a starting profile from what the user already wrote.

`setup_from_linkedin(path, out_dir)` reads a LinkedIn data export (the zip LinkedIn emails you, or its
Shares_*.csv) and writes TASTE.md + claims.md into out_dir:
- the 6 strongest recent posts (60 to 400 words, most recent year preferred) become the voice samples;
- plain observations about how the person writes go under "My rules" (sentence length, openers,
  em-dash habit), each marked as observed so the user can delete it;
- claims.md starts empty on purpose: facts are approved one by one, never invented.
Nothing is uploaded. Nothing is stored beyond the two files.
"""
import csv
import io
import re
import statistics
import zipfile
from pathlib import Path

MIN_W, MAX_W, N_SAMPLES = 60, 400, 6


def _rows_from(path):
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if re.search(r"(^|/)Shares[^/]*\.csv$", n)]
            if not names:
                raise ValueError("No Shares csv in this zip. Is it the full LinkedIn data export?")
            data = z.read(names[0]).decode("utf-8", "ignore")
    else:
        data = path.read_text(encoding="utf-8", errors="ignore")
    return list(csv.DictReader(io.StringIO(data)))


def _posts(rows):
    out = []
    for r in rows:
        t = (r.get("ShareCommentary") or "").replace("\r", "").strip()
        if not t:
            continue
        w = len(t.split())
        if MIN_W <= w <= MAX_W:
            out.append({"date": (r.get("Date") or "")[:10], "text": t, "words": w})
    out.sort(key=lambda p: p["date"], reverse=True)
    return out


def _observe(posts):
    obs = []
    if not posts:
        return obs
    sent_lens = []
    openers_q = dashes = 0
    for p in posts:
        sents = [s for s in re.split(r"(?<=[.!?])\s+", p["text"].replace("\n", " ")) if len(s.split()) >= 3]
        sent_lens += [len(s.split()) for s in sents]
        if sents and sents[0].strip().endswith("?"):
            openers_q += 1
        if "—" in p["text"] or "–" in p["text"]:
            dashes += 1
    n = len(posts)
    med = statistics.median(sent_lens) if sent_lens else 0
    obs.append(f"Observed: sentences run about {round(med)} words. Keep them there.")
    if openers_q / n > 0.4:
        obs.append(f"Observed: {openers_q} of {n} recent posts open with a question. Decide if that is a habit or a tell.")
    else:
        obs.append("Observed: posts open with a claim, not a question. Keep it that way.")
    if dashes / n > 0.3:
        obs.append(f"Observed: {dashes} of {n} recent posts use an em dash. this is an observation, not a ban.")
    else:
        obs.append("Observed: almost no em dashes. Decide whether this should be a preference.")
    short = sum(1 for p in posts if p["words"] < 120)
    obs.append(f"Observed: {short} of {n} recent posts are under 120 words.")
    return obs


def setup_from_linkedin(path, out_dir, name="", rights_confirmed=False):
    if rights_confirmed is not True:
        raise ValueError("Confirm you own or have permission to process this writing for a local personal profile. Use --confirm-rights. No training or public reuse is granted.")
    if not path:
        raise ValueError("Pass --linkedin <export.zip or Shares.csv>")
    posts = _posts(_rows_from(path))
    if not posts:
        raise ValueError("No posts between 60 and 400 words found in the export.")
    recent = [p for p in posts if p["date"] >= posts[0]["date"][:4]] or posts
    samples = sorted(recent[:40], key=lambda p: -p["words"])[:N_SAMPLES]
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    taste = ["# TASTE.md", "", "Built by `coulis setup` from your LinkedIn export. Edit anything; delete what is wrong.", "",
             "## Who I write as", f"- Name / role: {name}", "- Who I write for:", "- What I want readers to do:", "",
             "## My voice in samples"]
    for i, p in enumerate(samples, 1):
        taste += ["", f"### Sample {i}", f"<!-- {p['date']}, {p['words']} words -->", p["text"]]
    taste += ["", "## Observations awaiting approval"] + [f"- {o}" for o in _observe(posts[:40])]
    taste += ["", "## Learned from my edits", "<!-- Added by coulis learn, only after you approve each one. -->", ""]
    claims = ["# claims.md", f"owner: {name}", "product:", "",
              "## Approved facts", "<!-- Legacy notes only. Use structured approvals in claims.json; nothing is approved by import. -->", "",
              "## Needs confirm", "", "## Banned phrases",
              "", "## Story checks", ""]
    tpath, cpath = out / "TASTE.md", out / "claims.md"
    if tpath.exists():
        tpath.rename(out / "TASTE.md.bak")
    if cpath.exists():
        cpath.rename(out / "claims.md.bak")
    from .memory import save_json
    import datetime
    save_json(out / 'permissions.json', {"local_profile": True, "confirmed_at": datetime.date.today().isoformat(),
        "authority": "user attests ownership or permission", "model_processing": "only when user requests critique under their provider account",
        "shared_training": False, "public_benchmark": False, "cross_client_reuse": False})
    tpath.write_text("\n".join(taste))
    cpath.write_text("\n".join(claims))
    return {"profile_dir": str(out), "posts_read": len(posts), "samples": len(samples),
            "observations": _observe(posts[:40]), "backed_up": [str(p) for p in out.glob("*.bak")]}
