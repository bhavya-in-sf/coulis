---
name: coulis
description: Check a draft against the owner's approved facts and voice before the agent posts, emails or messages as them. Returns Hold, Revise or Send with each problem quoted. Deterministic, runs locally, no model call. Use before any post(), send() or reply() that goes out under the owner's name.
version: 0.10.0
homepage: https://github.com/bhavya-in-sf/coulis
license: MIT
---

# coulis: the check an agent runs before it speaks as its owner

## When to use
Before anything goes out under the owner's name: a LinkedIn or X post, a launch announcement, a cold email, an investor update, a Slack message to a team, a reply in a group chat. Not for research notes, code, or messages the owner only reads.

## Setup (once)
```
git clone https://github.com/bhavya-in-sf/coulis ~/.openclaw/skills/coulis/repo
python3 ~/.openclaw/skills/coulis/repo/scripts/coulis.py setup --linkedin <LinkedIn export.zip>
```
Setup writes two files to `~/.coulis/`: `TASTE.md` (how the owner writes, their rules, banned words) and `claims.md` (facts they have approved). If there is no export, copy `templates/TASTE.md` and have the owner fill in five sample posts and five approved facts. Keep both files on the owner's machine.

## Check a draft
```
python3 ~/.openclaw/skills/coulis/repo/scripts/coulis.py check - --surface linkedin <<'DRAFT'
<the draft>
DRAFT
```
Surfaces: `linkedin`, `x`, `reddit`, `instagram`, `youtube` plus `cold_email`, `investor_update`, `bio`. Add `--profile <folder>` to check as a client or company instead of the owner.

Exit code 2 = Hold, 1 = Revise, 0 = Send. For JSON, add `--json` to the same CLI check command.

## What to do with the verdict
- **Hold**: do not send. Fix every Hold line (quoted in the output), then check again. Never fix an unapproved number by inventing a supported one: cut it, or ask the owner to approve it.
- **Revise**: fix the Revise lines if you can without changing the owner's meaning, then check again. Mention what you changed.
- **Send**: the check passed; send only if the user has authorized sending.

## Approve a fact (only after the owner says yes)
```
python3 ~/.openclaw/skills/coulis/repo/scripts/coulis.py add approved_fact "1,200 users"
```

## Learn from the owner's edit
Use workflow `edit`, `propose` and `approve` as described below. Record only the actual supplied final and only with retention permission. Approve each preference explicitly.

## Rules
- Never skip the check to save time. If the check cannot run, say so and do not send.
- Never add facts or rules without the owner's explicit yes.
- Every check and skip is logged to `~/.coulis/coulis-log.jsonl` on the owner's machine. Nothing is uploaded.


## Shared taste memory integration

Before generating or editing, run `python3 scripts/coulis.py context '<JSON>' --profile <folder>` with JSON containing text, surface, and context (audience/purpose when known). Apply the returned preferences and expose conflicts. This loads both the legacy profile and approved preference database.

For a real user edit, use `python3 scripts/coulis.py workflow edit - --profile <folder>` with JSON on stdin: task, draft, final, context, category and consent:true (only with retention permission). After a style edit, run workflow extract with comparison_id for conservative evidence-backed proposals. Abstention is valid. For choices use workflow create/decide. Use propose and explicit approve for each new taste rule; revise/disable for changing preferences. Never duplicate workflow rules in Markdown. See docs/TASTE-LOOP.md for all actions.

The gate returns Send/Revise/Hold. Send means no blocking configured issue was found, not factual verification or permission to publish. Follow the user's sending authorization. Legacy learn/pick capture is not automatic preference approval or model training.
