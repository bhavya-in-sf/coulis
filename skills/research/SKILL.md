---
name: research
description: The sauce researcher. Sweep for new research and data on taste, AI homogenization, pluralistic alignment, human content as AI infrastructure and the AI share of the web; verify every source by opening it; and propose new EVIDENCE.md entries with what each proves and does NOT prove. Use when the user says "research sweep", "what's new in taste research", "update the evidence", or runs /sauce:research.
---

# Sauce: research (the evidence sweep)

The researcher keeps sauce's claims honest. It finds new sources, opens them, and proposes ledger entries. It never writes a claim it has not read in the source.

## Topics (the seed library is EVIDENCE.md, E1 to E13)
1. Taste and personalization: personal vs population preference models, pluralistic alignment, steerable models.
2. Homogenization: AI effects on writing style, voice, ideas and diversity.
3. Human content as AI infrastructure: data consent, licensing, data markets, creator compensation, model collapse.
4. AI share of the web and of attention: AI-written content measurements, what ranks and what people read.
5. Founder and business writing: any dataset or study on posts, pitches, cold email or persuasion quality.

## Steps
1. Read EVIDENCE.md so you know what is already covered. Do not add duplicates.
2. Search the web for each topic, limited to the last 90 days unless the user asks otherwise. Prefer: arXiv, Nature family, Science, ACM/IEEE proceedings, Pew, peer-reviewed journals. Industry reports are allowed but labeled with who published them and their interest.
3. Open every candidate source (a search snippet is never a source). Quote numbers exactly as written, with sample size and date.
4. For each source worth keeping, draft an entry in the ledger format:
   ```
   ### E<next number>. <one-line finding>
   - Source: [title](url) (venue or arXiv id, year)
   - Finding: <numbers, sample, method, in plain words>
   - Used for: <which sauce rule, feature, or pitch claim it supports>
   - Does NOT prove: <limits, conflicts of interest, what it can't support>
   ```
5. Also list sources that contradict a current entry, under "Challenges".
6. Show the user the proposed entries. Write them into EVIDENCE.md only after the user approves each one.
7. Run the user's sauce check on the summary before showing it (no overclaiming, no em dashes).

## Output to the user
- New entries proposed (count, one line each)
- Challenges to existing entries
- One stat worth adding to the deck's "why now" slide, if any
- Sources searched but rejected, with the reason (paywalled and unread, no data, duplicate)

## Rules
- Never invent or round a number beyond what the source says.
- Self-reported or vendor numbers are labeled as such.
- Preprints are labeled preprint.
- If a source can't be opened (paywall), say so; the user can pull it through a library.
