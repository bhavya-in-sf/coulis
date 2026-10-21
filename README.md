# Tastee

**The taste layer for AI. It learns what good looks like to you, and checks every draft before you see it.**

A free, open-source Claude plug-in. v0.1 starts with founder writing: launch posts, LinkedIn and X posts, cold emails, bios, investor updates.

## Why
AI writing sounds like everyone else. Memory tools help the AI know who you are, but nothing checks the finished draft against your taste. Tastee adds that check, the critic step, and learns from what you actually change.

## Install (Claude Code)
```
/plugin marketplace add bhavya-in-sf/tastee
/plugin install tastee@tastee
```

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

## Roadmap
- v0.1: founder writing, local `TASTE.md` (this release)
- Next: a universal taste MCP for Claude, ChatGPT and Cursor
- Later: pitches and decks, then a Taste API for AI writing apps

## License
MIT. Built by Bhavya Goel.
