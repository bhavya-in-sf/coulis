# coulis

> **Formerly sauce, and before that Tastee.** Renamed to coulis 31 Oct 2026; `~/.sauce` profiles keep working.
> **Tastee rename:** Renamed 26 Oct 2026. The old repo URL redirects here. If you installed `tastee@tastee`, run `/plugin uninstall tastee@tastee`, then the two install lines below. Your profile in `~/.tastee` keeps working; `~/.coulis` is also read.

**The taste layer for AI. It learns what good looks like to you, and checks every draft before you see it.**

A free, open-source check that runs inside Claude Code, Claude Desktop and Cursor today, and behind an API for everything else. It starts with founder writing: launch posts, LinkedIn and X posts, cold emails, bios, investor updates.

## What it does, on a real draft
A typical AI draft, checked against a real founder's profile ([personas/bhavya](personas/bhavya)):

```
In today's fast-paced world, every founder needs a game-changer — and AI is it.
We've helped 300+ founders grow, and our clients see 10x reach in 30 days.
Want to know how? Comment below!
```

What coulis sends back, in under a second, with no model call:

```
Hold
  Hold em_dash: '—' Em dash or double hyphen (house rule).
  Revise unapproved_claim: '300+ founders' Number not in claims.md. Add it to claims.md or cut it.
  Revise unapproved_claim: '10x' Number not in claims.md. Add it to claims.md or cut it.
  Hold banned_phrase: "in today's fast-paced world" Generic AI filler she cuts from every draft
  Hold banned_phrase: 'game-changer' Generic AI filler she cuts from every draft
```

And a post in her own voice, with only approved numbers:

```
100 investors who back women building AI.
Every week the same question lands in my inbox: who writes the checks?
So here they are. Angels and funds, pre-seed through growth.
Comment "INVESTORS" and I'll send you the list.
```

```
Send
```

Then `/coulis:critique` scores the draft on 8 separate axes against her own samples, and rewrites only the weakest line.

**Tested on a real team.** On 47 messages a startup's team drafted for its creator program, Coulis flagged the pay terms 32 times, because two versions of the terms were in circulation. Once the team confirmed one version, 46 of 47 passed, and the gate still caught the one unsupported number.


## New in 0.7
- **Directions, with approval:** `/coulis:bolder`, `/coulis:quieter`, `/coulis:shorter`, `/coulis:clearer`. One rewrite, checked, and nothing changes until you say yes.
- **Variants that teach:** `/coulis:variants` shows 3 hooks; your pick is saved as taste data (`coulis_pick`).
- **Modes by surface:** `linkedin`, `x`, `cold_email`, `investor_update`, `bio` (plus reddit, instagram, youtube), each with its own rules and target score.
- **`/coulis:extract`:** turn your past posts or LinkedIn export into a starter TASTE.md and claims.md. To get the export: LinkedIn > Me > Settings & Privacy > Data privacy > Get a copy of your data > tick Posts > Request archive. The zip arrives by email in about 10 minutes.
- **`/coulis:doctor`:** checks your profile is complete and up to date.
- **Always on:** the Stop hook now waits for the last reply before checking, and logs each run to `~/.coulis/hook-log.jsonl`.
- **Benchmark:** a public "sounds like you" test for AI writing apps. See [docs/BENCHMARK.md](docs/BENCHMARK.md).

## Try it in 60 seconds (no setup)
Check any draft against the real founder profile that ships with the repo:

```bash
git clone https://github.com/bhavya-in-sf/coulis && cd coulis
echo "We just hit \$50k MRR — a total game-changer." | python3 scripts/gate.py --persona personas/bhavya -
```

Python 3.10+ only, nothing to install. Then make it yours: `/coulis:extract` with your LinkedIn export (Me > Settings & Privacy > Data privacy > Get a copy of your data > Posts; about 10 minutes), or `/coulis:setup` to answer 5 questions and paste 3 posts.

## Why
AI writing sounds like everyone else. Memory tools help the AI know who you are, but nothing checks the finished draft against your taste. Coulis adds that check, the critic step, and learns from what you actually change.

## Install
**Claude Code** (plug-in: commands plus the MCP tools):
```
/plugin marketplace add bhavya-in-sf/coulis
/plugin install coulis@coulis
```
In Claude Code, the plug-in also adds a small check at the end of each reply: if Claude wrote a draft you might post and didn't run Coulis on it, it sends Claude back once to check it. Turn it off with `COULIS_HOOK=0`.

**Claude Desktop, Cursor and other MCP apps:** see [docs/INSTALL.md](docs/INSTALL.md). No API key needed.

## Three commands
| Command | What it does |
|---|---|
| `/coulis:setup` | 5 questions and 3 samples of your writing become `TASTE.md`, your taste in one file |
| `/coulis:critique` | The critic step. Scores a draft on 8 separate axes and rewrites only the weakest part |
| `/coulis:learn` | Paste the AI's draft and what you actually posted. It proposes up to 3 rules; you approve each one |

Everything stays in a plain `TASTE.md` in your folder. No account, no server, no data leaves your machine beyond your normal Claude session.

## The 8 axes
**Checkable** (firm for everyone): Clarity, Proof, Why you, Ask.
**Taste** (yours, from TASTE.md): Hook, Voice, Boldness, Rhythm.

There's no single overall score, on purpose. See [reference/axes.md](reference/axes.md).

## How it compares
| | Taste Skill | Impeccable | Coulis |
|---|---|---|---|
| Domain | Frontend design | Frontend design | **Writing** (founders first) |
| Whose taste | The author's rules | The author's rules | **Yours**, seeded with expert defaults |
| Learns from your edits | No | No | **Yes** (`/learn`, you approve each rule) |
| Critic step | Look-and-fix loop on screenshots | `critique`, `audit` commands | `critique` on 8 separate axes |
| Profile file | 3 dials | PRODUCT.md, DESIGN.md | TASTE.md, scoped per folder |
| Sources for its rules | Study of 247 curated sites | Grew from Anthropic's frontend-design skill | Public [evidence ledger](EVIDENCE.md) |
| License | MIT | Apache-2.0 | MIT |

Use them together: Taste Skill or Impeccable for your landing page, Coulis for the words on it.

## Evidence
Every rule maps to research or labeled practitioner experience in [EVIDENCE.md](EVIDENCE.md), including what each source does *not* prove.

## For agents (Remix, Wajo, OpenClaw, your own)
Personal agents now post, email and message as their owner. coulis is the check they run first. One call, deterministic, local, no model, about 4 ms.

```python
import sys; sys.path.insert(0, "path/to/coulis")
from coulis_core import check, profile_from_folder

profile = profile_from_folder("~/.coulis")              # the owner's TASTE.md + claims.md
r = check("We're leveraging AI to 10x your workflow. 300+ founders trust us.", profile, surface="linkedin")
r["verdict"]        # "Revise"
r["issues"][0]      # {"level": "Revise", "check": "unapproved_claim", "quote": "10x", "detail": "Number not in claims.md. Add it to claims.md or cut it."}
```

From a shell or any language:
```
python3 scripts/coulis.py check - --json <<'DRAFT'
the draft
DRAFT
```
Exit code 2 = Hold (do not send), 1 = Revise (fix the quoted lines, then send), 0 = Send. `--profile <folder>` checks as a client or a company instead of the owner.

Rules for an agent: never send on Hold; never invent a number to satisfy a claim check (cut it or ask the owner to approve it); add facts only after the owner says yes (`coulis.py add approved_fact "..."`); when the owner edits your draft, run `coulis.py learn draft.txt final.txt` and propose the rules it finds.

- OpenClaw skill: [`openclaw/`](openclaw/) (`clawhub install coulis`).
- Claude Code and Claude Desktop: the plug-in above (MCP tools `coulis_check`, `coulis_add`, `coulis_learn`).
- Over HTTP: for teams and agents, on the waitlist.
- Hosted API and per-check pricing for agent companies: not yet. Write to the address in the footer of the site.

## For developers
- `coulis_core/`: the taste layer as a library. JSON in, JSON out.
- `mcp/server.py`: MCP server with `coulis_check`, `coulis_critique` (works without an API key), `coulis_learn`, `coulis_add` and `coulis_profile`. Ships inside the plug-in.
- `examples/writing_app.py` shows a writing app gating every draft with the library.
- `personas/bhavya/`: a real founder's profile, published with her permission: TASTE.md built from 673 public LinkedIn posts, an approved-facts list, and 553 posts to test against. Point Coulis at it to see a real taste profile in action: `COULIS_PROFILE_DIR=personas/bhavya`.
- `evals/`: a regression suite (same input, same verdict) and an edit-pairs suite. Run `python3 -m unittest discover -s tests`.

## Roadmap
- v0.1: founder writing, local `TASTE.md`
- v0.2: core library, MCP server, Taste API preview, SDKs, evals
- v0.3: gate calibrated on real posts; MCP works with no API key; `coulis_add`
- v0.4: a real founder's profile and 553-post regression set (this release)
- Next: teams and agents. Join the waitlist at bhavya-in-sf.github.io/coulis/waitlist.html

## License
MIT. Built by Bhavya Goel.


## Also in the box
- `python3 scripts/deck_check.py deck.pdf` checks a deck slide by slide and flags the same noun with different numbers across slides ("300 customers" on slide 3, "350" on slide 9). Also .pptx and .md.
- `python3 scripts/taste_card.py --out card.html` renders a shareable one-page card of how you write, measured from your own samples. Nothing invented.
- `coulis setup --linkedin export.zip` builds your TASTE.md and claims.md from your own posts in one command (the export: LinkedIn > Me > Settings & Privacy > Data privacy > Get a copy of your data > Posts).
- `coulis check --max-sameness 50` turns the sameness score into a gate.

## Privacy
- The gate runs on your machine and makes no network call.
- The critique sends your draft and a few of your sample posts to Claude under your own account. coulis keeps nothing from that call.
- Your taste files and the local log stay in `~/.coulis/`. The log records verdicts and tool names, never your drafts.
- The landing page has no analytics or tracking. The waitlist form keeps a name, an email and your choice, nothing else.
- Security problems: see [SECURITY.md](SECURITY.md).
