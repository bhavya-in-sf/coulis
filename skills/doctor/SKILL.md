---
name: doctor
description: Health check of the user's taste profile. Checks that TASTE.md and claims.md exist, are complete and recent, counts approved facts, banned phrases and saved variant picks, and gives a one-line fix for each problem. Use when the user says "is my profile ok", "why is everything flagged", "sauce doctor", or runs /sauce:doctor.
---

# Sauce: doctor

1. Call sauce_doctor (pass profile_dir for a company or client profile).
2. Show "healthy" or the list of problems, each with its one-line fix, most important first.
3. Offer to run the fix (e.g. /sauce:extract, adding facts with sauce_add). Change nothing without a yes.
