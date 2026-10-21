---
name: critique
description: The critic step. Score a piece of writing (post, launch announcement, cold email, bio, investor update) on 8 separate taste axes against the user's TASTE.md, then rewrite only the weakest part. Use when the user says "critique this", "does this sound like me", "taste check", "make this less generic", or runs /tastee:critique.
---

# Tastee: critique (the critic step)

Goal: check a draft against what good looks like for this user, and send it back if it's off.

## Before scoring
1. Read `TASTE.md` in the current folder. If there is none, say so and offer `/tastee:setup`. You can still critique using the seed defaults, but say that you are.
2. Read `reference/axes.md` and `reference/seed-taste.md` in this plugin's root folder (two levels up from this skill). TASTE.md wins over the seed whenever they disagree.

## Output format
Keep it tight. Exactly this shape:

**Checkable** (firm)
| Axis | Score /10 | Why, quoting the draft |
|---|---|---|
| Clarity | | |
| Proof | | |
| Why you | | |
| Ask | | |

**Taste** (yours, from TASTE.md)
| Axis | Score /10 | Why, quoting the draft |
|---|---|---|
| Hook | | |
| Voice | | |
| Boldness | | |
| Rhythm | | |

**Slop found:** list each phrase from the seed slop list or the user's rules, quoted. "None" if none.

**Weakest axis:** name it, then rewrite only the part of the draft that fixes it. Show before and after.

**Missing proof:** if Proof scored under 6, ask for the specific number, name or result. Never make one up.

## Rules
- Never give one overall score. Report every axis separately (see EVIDENCE.md, E2 and E3).
- Every score cites words from the draft. No vague feedback.
- Rewrite only the weakest part, not the whole draft, unless the user asks. The user stays the author.
- Do not invent facts, numbers, stories or experience.
- This step runs only when called, so normal drafting stays fast.
- Offer at the end, in one line: "After you post, run /tastee:learn with this draft and your final version so I learn what you changed."
