---
name: variants
description: Variants that teach. Show 3 alternative hooks (or openings, subject lines, closing asks) for a draft, let the user pick one, and save the pick as taste data with sauce_pick. Use when the user says "give me options", "3 hooks", "alternatives", "which opener", or runs /sauce:variants.
---

# Sauce: variants (every pick teaches the profile)

1. Take the draft and what to vary (default: the hook / first line). Read TASTE.md via sauce_profile.
2. Write 3 alternatives that are genuinely different in approach (e.g. a number-led line, a short story line, a contrarian line), all in the user's voice, using only facts in the draft or claims.md.
3. Run sauce_check on each (same surface). Drop or fix any that come back Hold.
4. Show them numbered A, B, C with the check verdict on each, and ask: "Which one? (A, B, C, or none)".
5. When the user picks, call sauce_pick with picked = the chosen line, rejected = the other two, context = what they were for. If they pick none, ask what was wrong and offer one more round.
6. Then give the full draft with the chosen line in place. Picks are pairwise taste data: they build the profile and the "sounds like you" benchmark.
