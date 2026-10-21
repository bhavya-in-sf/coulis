---
name: setup
description: Build the user's TASTE.md, their personal taste profile for writing. Use when the user says "set up taste", "create my TASTE.md", "learn my voice", or runs /tastee:setup, or when /tastee:critique finds no TASTE.md.
---

# Tastee: setup

Goal: create a `TASTE.md` in the user's current folder, so they never have to re-explain their style.

## Steps
1. Check whether `TASTE.md` already exists in the current folder. If it does, show it and ask whether to update it or start fresh. Never overwrite without a yes.
2. Ask these 5 questions, one message, numbered. Keep it short.
   1. Who are you and what do you do, in one line?
   2. Who do you write for?
   3. What do you want readers to do after reading?
   4. Paste 3 things you've written that you're proud of (posts, emails, anything).
   5. Anything you always or never do? (Optional.)
3. From the 3 samples, write 3 to 6 observations under "My rules", in the user's terms (for example "Short paragraphs, 1 to 2 lines", "Uses numbers in the first line"). Only describe what is actually in the samples. Do not invent traits.
4. Fill the template at `templates/TASTE.md` (in this plugin's root folder, two levels up from this skill) with their answers and samples. Leave "Learned from my edits" empty.
5. Show the finished file and ask: "Save this as TASTE.md here?" Write it only after a yes.
6. Tell them the next step: run `/tastee:critique` on any draft.

## Rules
- The user's own words go in the file. Don't polish their samples.
- One TASTE.md per folder. If they write for several brands, suggest one folder each, so styles don't bleed.
