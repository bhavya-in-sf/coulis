---
name: shorter
description: Make a draft shorter without losing its point or voice. Proposes ONE rewrite and waits for approval; never replaces the user's text without a yes. Use when the user says "shorter", "tighten this", "cut it down", or runs /coulis:shorter.
---

# Coulis: shorter (a direction, with approval)

1. Take the draft (from the message or the last draft in the chat) and the surface (linkedin, x, cold_email, investor_update, bio; default linkedin).
2. Write ONE rewrite in the user's voice (read TASTE.md via coulis_profile). Cut length by about a third: drop repeated ideas, filler and setup sentences; keep the hook, the proof and the ask.
3. Never add a number, name or claim that is not in the draft or in claims.md.
4. Run coulis_check on the rewrite with the same surface. If it is Hold (BLOCK), fix and check again.
5. Show: the rewrite, one line on what changed and why, the check verdict, and ask: "Use this? (yes / no / edit)".
6. Only after "yes": hand back the final text. If the user edits it, call coulis_learn with draft = your rewrite and final = their version, and list proposed rules for approval.
