---
name: gate
description: Pre-post gate. Before a post goes out, check it against the persona's claims and rules (hard checks) and its taste (critique), and return BLOCK, FIX or PASS with exact fixes. Use when the user or an agent says "gate this", "check before posting", "can this go out", or runs /coulis:gate.
---

# Coulis: gate (check before it posts)

Two halves, in this order.

## 1. Hard checks (rules, no judgment)
Run the checker from this plugin's root:

```
python3 scripts/gate.py --persona <persona folder> --surface <reddit|x|linkedin> --json <draft file or ->
```

The persona folder holds TASTE.md and claims.md (example: personas/example). Exit code 2 means BLOCK.
Report every BLOCK and FIX issue with its quote. Never "fix" a BLOCK by inventing a number: cut it, or ask the owner to add it to claims.md.

## 2. Taste check (judgment)
Run the critique skill on the same draft with the persona's TASTE.md. Report the axes as critique does.

## Output
```
Verdict: BLOCK | FIX | PASS
Must fix: (BLOCK issues, one line each, quoted)
Should fix: (FIX issues + weakest taste axis)
Suggested edit: (only the parts that change, before -> after)
```
If the draft is PASS on both halves, say so in one line and stop.

## After it posts
Offer: run `python3 scripts/learn.py --persona <folder> draft.txt final.txt` so edits become rules. Apply only with the owner's yes.
