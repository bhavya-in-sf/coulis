---
name: sauce
description: Check a draft against the owner's approved facts and voice before the agent posts, emails or messages as them. Returns BLOCK, FIX or PASS with each problem quoted. Deterministic, runs locally, no model call. Use before any post(), send() or reply() that goes out under the owner's name.
version: 0.6.2
homepage: https://github.com/bhavya-in-sf/sauce
license: MIT
---

# sauce: the check an agent runs before it speaks as its owner

## When to use
Before anything goes out under the owner's name: a LinkedIn or X post, a launch announcement, a cold email, an investor update, a Slack message to a team, a reply in a group chat. Not for research notes, code, or messages the owner only reads.

## Setup (once)
```
git clone https://github.com/bhavya-in-sf/sauce ~/.openclaw/skills/sauce/repo
python3 ~/.openclaw/skills/sauce/repo/scripts/sauce.py setup --linkedin <LinkedIn export.zip>
```
Setup writes two files to `~/.sauce/`: `TASTE.md` (how the owner writes, their rules, banned words) and `claims.md` (facts they have approved). If there is no export, copy `templates/TASTE.md` and have the owner fill in five sample posts and five approved facts. Keep both files on the owner's machine.

## Check a draft
```
python3 ~/.openclaw/skills/sauce/repo/scripts/sauce.py check - --surface linkedin <<'DRAFT'
<the draft>
DRAFT
```
Surfaces: `linkedin`, `x`, `reddit`, `instagram`, `youtube` (use `linkedin` for email and Slack). Add `--profile <folder>` to check as a client or company instead of the owner.

Exit code 2 = BLOCK, 1 = FIX, 0 = PASS. For JSON, run `scripts/gate.py --persona ~/.sauce --surface linkedin --json -`.

## What to do with the verdict
- **BLOCK**: do not send. Fix every BLOCK line (quoted in the output), then check again. Never fix an unapproved number by inventing a supported one: cut it, or ask the owner to approve it.
- **FIX**: fix the FIX lines if you can without changing the owner's meaning, then send. Mention what you changed.
- **PASS**: send.

## Approve a fact (only after the owner says yes)
```
python3 ~/.openclaw/skills/sauce/repo/scripts/sauce.py add approved_fact "1,200 users"
```

## Learn from the owner's edit
When the owner edits your draft before sending, run
```
python3 ~/.openclaw/skills/sauce/repo/scripts/sauce.py learn draft.txt final.txt
```
It proposes rules from the difference. Add a rule only when the owner approves it.

## Rules
- Never skip the check to save time. If the check cannot run, say so and do not send.
- Never add facts or rules without the owner's explicit yes.
- Every check and skip is logged to `~/.sauce/sauce-log.jsonl` on the owner's machine. Nothing is uploaded.
