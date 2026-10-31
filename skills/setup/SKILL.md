---
name: setup
description: Build the user's TASTE.md, their personal taste profile for writing. Use when the user says "set up taste", "create my TASTE.md", "learn my voice", or runs /coulis:setup, or when /coulis:critique finds no TASTE.md.
---

# Coulis: setup

Goal: create a `TASTE.md` in the user's current folder, so they never have to re-explain their style.

## Steps
1. Check whether `TASTE.md` already exists in the current folder. If it does, show it and ask whether to update it or start fresh. Never overwrite without a yes.
2. Offer the fast route first: "If you have your LinkedIn data export, run /coulis:extract and I will build this from your real posts. To get it: Me > Settings & Privacy > Data privacy > Get a copy of your data > tick Posts > Request archive (about 10 minutes by email)." If they want to continue without it, ask these 5 questions, one message, numbered. Keep it short.
   1. Who are you and what do you do, in one line?
   2. Who do you write for?
   3. What do you want readers to do after reading?
   4. Paste 3 things you've written that you're proud of (posts, emails, anything).
   5. Anything you always or never do? (Optional.)
3. From the 3 samples, write 3 to 6 observations under "My rules", in the user's terms (for example "Short paragraphs, 1 to 2 lines", "Uses numbers in the first line"). Only describe what is actually in the samples. Do not invent traits.
4. Fill the template at `templates/TASTE.md` (in this plugin's root folder, two levels up from this skill) with their answers and samples. Leave "Learned from my edits" empty.
5. Show the finished file and ask: "Save this as TASTE.md here?" Write it only after a yes.
6. Facts the gate should allow. Ask: "List the numbers and claims you're happy to post publicly (users, revenue, customers, credentials). Anything not on this list gets flagged." Show them as a list and, after a yes, save each one with the `coulis_add` tool (kind `approved_fact`). If the tool isn't available, write them under "## Approved facts" in a `claims.md` next to TASTE.md. If they skip, create `claims.md` anyway and tell them the gate will flag every number until they add facts.
7. Tell them the next step: run `/coulis:critique` on any draft, or `/coulis:gate` before posting.

## Rules
- The user's own words go in the file. Don't polish their samples.
- One TASTE.md per folder. If they write for several brands, suggest one folder each, so styles don't bleed.
