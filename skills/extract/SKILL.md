---
name: extract
description: Build a starter taste profile from someone's past writing: a LinkedIn data export, a folder or file of posts, or pasted posts. Writes TASTE.md (voice, hooks, rhythm, words they use and avoid) and a starter claims.md (numbers that recur in their posts, for them to confirm). Use when the user says "extract my voice", "build my profile from my posts", "import my LinkedIn", or runs /sauce:extract.
---

# Sauce: extract (your past posts become your taste file)

1. Ask for the source if not given: a LinkedIn data export (.zip or its Shares csv), a file or folder of posts, or posts pasted in the chat.
   If they do not have the export yet, give them these exact steps and wait:
   "On LinkedIn: click Me > Settings & Privacy > Data privacy > Get a copy of your data. Choose 'Want something in particular?' and tick Posts (or Shares). Click Request archive. LinkedIn emails a download link in about 10 minutes. Download the zip and give me its path, or drag it into this chat."
   If they would rather not wait: ask them to paste 3 to 5 posts they are proud of, and go to step 3.
2. LinkedIn export: run from the plug-in root
   `python3 scripts/sauce.py setup --linkedin <export.zip or Shares.csv> --out <profile folder, default ~/.sauce> --name "<name, role>"`
   This writes TASTE.md and claims.md from the person's own posts, locally. Nothing is uploaded.
3. Pasted or other files: read the posts and write TASTE.md with sections: Who, Audience, Voice (5 to 8 observed traits with a quoted example each), Hooks that worked, Words they never use, Format habits. Write claims.md with "## Approved" left EMPTY and a "## Needs confirm" list of every number that recurs in their posts.
4. Never mark a number approved on your own. Show the "Needs confirm" list and ask the user to confirm each one (then use sauce_add).
5. Finish with sauce_doctor and show what is still missing.
