"""Structured taste profile.

TASTE.md + claims.md (the plug-in's two plain files) become one JSON object
that can be stored, versioned and sent over an API, and turned back into
files. Nothing is invented: every field comes from the user's own files or
samples.
"""
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

SCHEMA_VERSION = "coulis.profile/v1"


def rhythm_fingerprint(samples):
    """Mean and spread of words per sentence, and lines per post, measured from the person's own samples.
    Deterministic; computed once per profile load. Empty dict when there are too few samples."""
    import statistics
    sents, lines = [], []
    for smp in samples:
        for sent in re.split(r"(?<=[.!?])\s+|\n+", smp):
            w = len(sent.split())
            if w >= 2:
                sents.append(w)
        lines.append(len([l for l in smp.splitlines() if l.strip()]))
    if len(sents) < 8 or len(lines) < 2:
        return {}
    return {"words_per_sentence": round(statistics.mean(sents), 1),
            "words_per_sentence_sd": round(statistics.pstdev(sents), 1),
            "lines_per_post": round(statistics.mean(lines), 1),
            "lines_per_post_sd": round(statistics.pstdev(lines), 1),
            "n_sentences": len(sents)}



@dataclass
class Rule:
    text: str
    source: str = "user"          # user | learned
    approved: bool = True
    added: str = ""               # YYYY-MM-DD when known
    id: str = ""
    scope: dict = field(default_factory=dict)
    key: str = ""
    value: str = ""
    active: bool = True
    expires: str = ""
    evidence_ids: list = field(default_factory=list)



@dataclass
class Pattern:
    why: str
    regex: str


@dataclass
class Profile:
    owner: str = ""
    product: str = ""
    who_i_write_as: str = ""
    audience: str = ""
    goal: str = ""
    samples: list = field(default_factory=list)          # the user's own writing, verbatim
    rules: list = field(default_factory=list)            # list[Rule]
    approved_facts: list = field(default_factory=list)   # claims allowed in public
    needs_confirm: list = field(default_factory=list)
    banned: list = field(default_factory=list)           # list[Pattern]
    story_checks: list = field(default_factory=list)     # list[Pattern]
    schema: str = SCHEMA_VERSION

    def to_dict(self):
        return asdict(self)

    # The gate engine expects its original persona shape. Build it from the profile.
    def to_persona(self):
        norm = lambda s: re.sub(r"\s+", " ", s.lower().replace("’", "'")).strip()
        return {
            "approved_text": norm("\n".join(f"- {f}" for f in self.approved_facts)),
            "folder": None,
            "stories": [(p.why, p.regex) for p in self.story_checks],
            "banned": [(p.why, p.regex) for p in self.banned],
            "owner": norm(self.owner),
            "product": norm(self.product),
            "samples": list(self.samples),
            "rhythm": rhythm_fingerprint(self.samples),
        }

    def to_files(self):
        """Render back to the plug-in's TASTE.md and claims.md (round trip)."""
        taste = ["# TASTE.md", "", "## Who I write as",
                 f"- Name / role: {self.who_i_write_as}", f"- Who I write for: {self.audience}",
                 f"- What I want readers to do: {self.goal}", "", "## My voice in 3 samples"]
        for i, s in enumerate(self.samples, 1):
            taste += ["", f"### Sample {i}", s]
        taste += ["", "## My rules"] + [f"- {r.text}" for r in self.rules if r.source == "user" and not r.id]
        taste += ["", "## Learned from my edits"] + [
            f"- [{r.added}] {r.text}" for r in self.rules if r.source == "learned" and r.approved and not r.id]
        claims = [f"owner: {self.owner}", f"product: {self.product}", "", "## Approved facts"]
        claims += [f"- {f}" for f in self.approved_facts] + ["", "## Needs confirm"]
        claims += [f"- {f}" for f in self.needs_confirm] + ["", "## Banned phrases"]
        claims += [f"- {p.why} :: {p.regex}" for p in self.banned] + ["", "## Story checks"]
        claims += [f"- {p.why} :: {p.regex}" for p in self.story_checks]
        return {"TASTE.md": "\n".join(taste) + "\n", "claims.md": "\n".join(claims) + "\n"}


def _section(md, title):
    m = re.search(r"^##\s+" + re.escape(title) + r"[^\n]*\n(.*?)(?=^##\s|\Z)", md, re.M | re.S)
    return m.group(1) if m else ""


def _bullets(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- ") and len(line) > 2 and not line.startswith("<!--"):
            out.append(line[2:].strip())
    return [b for b in out if b]


def _patterns(text):
    return [Pattern(why=b.split("::", 1)[0].strip(), regex=b.split("::", 1)[1].strip())
            for b in _bullets(text) if "::" in b]


def _field(md, label):
    m = re.search(r"^-?\s*" + re.escape(label) + r":\s*(.*)$", md, re.M)
    return m.group(1).strip() if m else ""


def parse_files(taste_md="", claims_md=""):
    p = Profile()
    if claims_md:
        p.owner, p.product = _field(claims_md, "owner"), _field(claims_md, "product")
        # Same rule as the plug-in's gate: every bullet before "## Needs" is approved, under any
        # "## Approved..." heading, except banned phrases and story checks.
        head = claims_md.split("## Needs", 1)[0]
        head = re.sub(r"^##\s+(Banned phrases|Story checks)[^\n]*\n.*?(?=^##\s|\Z)", "", head, flags=re.M | re.S)
        p.approved_facts = [b for b in _bullets(head) if "::" not in b]
        p.needs_confirm = _bullets(_section(claims_md, "Needs confirm"))
        p.banned = _patterns(_section(claims_md, "Banned phrases"))
        p.story_checks = _patterns(_section(claims_md, "Story checks"))
    if taste_md:
        p.who_i_write_as = _field(taste_md, "Name / role")
        p.audience = _field(taste_md, "Who I write for")
        p.goal = _field(taste_md, "What I want readers to do")
        samples = re.findall(r"^###\s+Sample \d+\s*\n(.*?)(?=^###\s|^##\s|\Z)", taste_md, re.M | re.S)
        p.samples = [s.strip() for s in samples if s.strip() and not s.strip().startswith("<!--")]
        p.rules = [Rule(text=r) for r in _bullets(_section(taste_md, "My rules"))]
        for r in _bullets(_section(taste_md, "Learned from my edits")):
            m = re.match(r"[\[(](\d{4}-\d{2}-\d{2})[^\])]*[\])]\s*(.*)", r)
            p.rules.append(Rule(text=m.group(2) if m else r, source="learned", added=m.group(1) if m else ""))
    return p


def profile_from_folder(folder):
    folder = Path(folder)
    read = lambda n: (folder / n).read_text() if (folder / n).exists() else ""
    p = parse_files(read("TASTE.md"), read("claims.md"))
    database = folder / 'coulis-research.db'
    if database.exists():
        from .taste_store import Store
        store = Store(database)
        try:
            for row in store.active('local', 'profile'):
                p.rules.append(Rule(text=row['text'], source='learned', approved=True,
                                    id=row['id'], scope=row['scope'], key=row['key'], value=row['value'],
                                    added=row['effective_at'][:10], evidence_ids=row['evidence_ids']))
        finally:
            store.close()
    return p


def profile_from_dict(d):
    d = dict(d)
    if d.get("schema", SCHEMA_VERSION) != SCHEMA_VERSION:
        raise ValueError(f"Unsupported profile schema: {d.get('schema')}")
    d["rules"] = [r if isinstance(r, Rule) else Rule(**r) for r in d.get("rules", [])]
    for k in ("banned", "story_checks"):
        d[k] = [p if isinstance(p, Pattern) else Pattern(**p) for p in d.get(k, [])]
    known = Profile.__dataclass_fields__
    return Profile(**{k: v for k, v in d.items() if k in known})


def profile_from_samples(samples, who="", audience="", goal="", owner="", product="", approved_facts=()):
    """POST /profiles: build a starting profile from the user's own samples.

    Only stores what the user gave. Rules are left empty on purpose: the
    plug-in's setup skill (or a human) writes observations, and /learn adds
    rules the user approves. No traits are invented here.
    """
    if not samples:
        raise ValueError("Give at least one writing sample.")
    return Profile(owner=owner, product=product, who_i_write_as=who, audience=audience, goal=goal,
                   samples=[s.strip() for s in samples if s.strip()][:10],
                   approved_facts=list(approved_facts))
