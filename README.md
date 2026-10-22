# Tastee

**The taste layer for AI. It learns what good looks like to you, and checks every draft before you see it.**

A free, open-source plug-in for Claude, Claude Desktop and Cursor. It starts with founder writing: launch posts, LinkedIn and X posts, cold emails, bios, investor updates.

## What it does, on a real draft
A typical AI draft, checked against a real founder's profile ([personas/bhavya](personas/bhavya)):

```
In today's fast-paced world, every founder needs a game-changer — and AI is it.
We've helped 300+ founders grow, and our clients see 10x reach in 30 days.
Want to know how? Comment below!
```

What Tastee sends back, in under a second, with no model call:

```
BLOCK
  BLOCK em_dash: '—' Em dash or double hyphen (house rule).
  FIX unapproved_claim: '300+ founders' Number not in claims.md. Add it to claims.md or cut it.
  BLOCK banned_phrase: "in today's fast-paced world" Generic AI filler she cuts from every draft
  BLOCK banned_phrase: 'game-changer' Generic AI filler she cuts from every draft
```

And a post in her own voice, with only approved numbers:

```
100 investors who back women building AI.
Every week the same question lands in my inbox: who writes the checks?
So here they are. Angels and funds, pre-seed through growth.
Comment "INVESTORS" and I'll send you the list.
```

```
PASS
```

Then `/tastee:critique` scores the draft on 8 separate axes against her own samples, and rewrites only the weakest line.

**Tested on a real team.** On 47 messages a startup's team drafted for its creator program, Tastee flagged the pay terms 32 times, because two versions of the terms were in circulation. Once the team confirmed one version, 46 of 47 passed, and the gate still caught the one unsupported number.

## Try it in 60 seconds (no setup)
Check any draft against the real founder profile that ships with the repo:

```bash
git clone https://github.com/bhavya-in-sf/tastee && cd tastee
echo "We just hit \$50k MRR — a total game-changer." | python3 scripts/gate.py --persona personas/bhavya -
```

Python 3.10+ only, nothing to install. Then make it yours with `/tastee:setup`.

## Why
AI writing sounds like everyone else. Memory tools help the AI know who you are, but nothing checks the finished draft against your taste. Tastee adds that check, the critic step, and learns from what you actually change.

## Install
**Claude Code** (plug-in: commands plus the MCP tools):
```
/plugin marketplace add bhavya-in-sf/tastee
/plugin install tastee@tastee
```
**Claude Desktop, Cursor and other MCP apps:** see [docs/INSTALL.md](docs/INSTALL.md). No API key needed.

## Three commands
| Command | What it does |
|---|---|
| `/tastee:setup` | 5 questions and 3 samples of your writing become `TASTE.md`, your taste in one file |
| `/tastee:critique` | The critic step. Scores a draft on 8 separate axes and rewrites only the weakest part |
| `/tastee:learn` | Paste the AI's draft and what you actually posted. It proposes up to 3 rules; you approve each one |

Everything stays in a plain `TASTE.md` in your folder. No account, no server, no data leaves your machine beyond your normal Claude session.

## The 8 axes
**Checkable** (firm for everyone): Clarity, Proof, Why you, Ask.
**Taste** (yours, from TASTE.md): Hook, Voice, Boldness, Rhythm.

There's no single overall score, on purpose. See [reference/axes.md](reference/axes.md).

## How it compares
| | Taste Skill | Impeccable | Tastee |
|---|---|---|---|
| Domain | Frontend design | Frontend design | **Writing** (founders first) |
| Whose taste | The author's rules | The author's rules | **Yours**, seeded with expert defaults |
| Learns from your edits | No | No | **Yes** (`/learn`, you approve each rule) |
| Critic step | Look-and-fix loop on screenshots | `critique`, `audit` commands | `critique` on 8 separate axes |
| Profile file | 3 dials | PRODUCT.md, DESIGN.md | TASTE.md, scoped per folder |
| Sources for its rules | Study of 247 curated sites | Grew from Anthropic's frontend-design skill | Public [evidence ledger](EVIDENCE.md) |
| License | MIT | Apache-2.0 | MIT |

Use them together: Taste Skill or Impeccable for your landing page, Tastee for the words on it.

## Evidence
Every rule maps to research or labeled practitioner experience in [EVIDENCE.md](EVIDENCE.md), including what each source does *not* prove.

## For developers (preview)
- `tastee_core/`: the taste layer as a library. JSON in, JSON out.
- `mcp/server.py`: MCP server with `tastee_check`, `tastee_critique` (works without an API key), `tastee_learn`, `tastee_add` and `tastee_profile`. Ships inside the plug-in.
- `api/`: the Taste API (REST): profiles, check, critique, learn, rule approval, usage. See [docs/API.md](docs/API.md).
- `sdk/`: Python and TypeScript clients. `examples/writing_app.py` shows a writing app gating every draft.
- `personas/bhavya/`: a real founder's profile, published with her permission: TASTE.md built from 673 public LinkedIn posts, an approved-facts list, and 553 posts to test against. Point Tastee at it to see a real taste profile in action: `TASTEE_PROFILE_DIR=personas/bhavya`.
- `evals/`: a regression suite (same input, same verdict) and an edit-pairs suite. Run `python3 -m unittest discover -s tests`.

## Roadmap
- v0.1: founder writing, local `TASTE.md`
- v0.2: core library, MCP server, Taste API preview, SDKs, evals
- v0.3: gate calibrated on real posts; MCP works with no API key; `tastee_add`
- v0.4: a real founder's profile and 553-post regression set (this release)
- Next: hosted API, pitches and decks

## License
MIT. Built by Bhavya Goel.
