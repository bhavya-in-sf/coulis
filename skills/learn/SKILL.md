---
name: learn
description: Learn the user's taste from their edits. Compare an AI draft with the version the user actually published, propose taste rules from the differences, and add the ones the user approves to TASTE.md. Use when the user says "learn from this", "here's what I actually posted", "update my taste", or runs /coulis:learn.
---

# Coulis: learn

Goal: taste learned from what the user does, not just what they say. Every rule needs the user's approval.

## Steps
1. Ask for two things if not given: the draft (what the AI wrote) and the final (what the user actually posted or sent).
2. Compare them. List each meaningful change: cut, added, reworded, reordered. Ignore typo fixes.
3. Propose at most 3 rules that explain the changes. Each rule:
   - is written as an instruction ("Lead the hook with the number")
   - cites the evidence: "draft said X" → "you posted Y"
   - names the axis it belongs to (from `reference/axes.md` in this plugin's root, two levels up)
4. Read the current `TASTE.md`. If a proposed rule repeats or contradicts an existing one, say so and propose merging or replacing it instead of adding a duplicate.
5. Ask the user to approve, edit or reject each rule, numbered. Write only the approved ones to the "Learned from my edits" section, with today's date and the evidence.
6. If "Learned from my edits" has more than 30 rules, suggest which ones to merge or retire, and wait for a yes.

## Rules
- Never write to TASTE.md without explicit approval of each rule. Memory created without the user's say is a known failure (EVIDENCE.md, E5).
- Only learn from this folder's TASTE.md scope. Don't carry rules across brands or clients.
- Don't infer personal facts about the user. Learn writing choices only.
