---
name: bolder
description: Make a draft bolder: a sharper claim, a stronger opinion, a more specific hook. Proposes ONE rewrite and waits for approval; never replaces the user's text without a yes. Use when the user says "make it bolder", "punchier", "stronger hook", or runs /coulis:bolder.
---

# Coulis: bolder (a direction, with approval)

1. Take the draft (from the message or the last draft in the chat) and the surface (linkedin, x, cold_email, investor_update, bio; default linkedin).
2. Write ONE rewrite in the user's voice (read TASTE.md via coulis_profile). Raise conviction: lead with the strongest specific claim, cut hedges ("I think", "maybe", "just"), turn a soft question opener into a statement.
3. Never add a number, name or claim that is not in the draft or in claims.md.
4. Run coulis_check on the rewrite with the same surface. If it is Hold (Hold), fix and check again.
5. Show: the rewrite, one line on what changed and why, the check verdict, and ask: "Use this? (yes / no / edit)".
6. Only after "yes": hand back the final text. If the user edits it, call coulis_learn with draft = your rewrite and final = their version, and list proposed rules for approval.
