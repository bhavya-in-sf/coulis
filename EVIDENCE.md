# Evidence ledger

Every rule in Sauce traces back to one of two kinds of source, always labeled:

- **Research (E):** a paper or dataset, linked, with what it proves and what it doesn't.
- **Practitioner (P):** real editing experience, labeled as experience, not research.

No rule ships without one. If you find a claim here that's wrong or overstated, open an issue.

---

### E1. PAM∃LA: personal taste beats the average
- Source: [Personalizing Text-to-Image Generation to Individual Taste](https://arxiv.org/html/2604.07427v1) (arXiv 2604.07427, preprint)
- Finding: most existing datasets "treat user variation as noise, averaging away subjective preference." About 200 people rated 5,077 images, 15 people per image. A model of each person's taste predicted that person better than the best population model (per-user SROCC 0.45 vs 0.40 for HPSv3).
- Used for: TASTE.md is personal, and learned per user.
- Does NOT prove: that this works for writing (images only). The gain is modest, and the user study had 6 people.

### E2. Human Creativity Benchmark: experts agree on some things, split on others
- Source: [The Human Creativity Benchmark](https://arxiv.org/abs/2606.30561) (Hopkins et al., Contra Labs, 2026)
- Finding: professional creatives converge on checkable dimensions (prompt adherence, visual hierarchy) and diverge on taste-driven ones (aesthetic direction, conceptual risk). The authors argue collapsing these into one quality score discards the most actionable information.
- Used for: two groups of axes (checkable vs taste), and no single overall score.
- Does NOT prove: anything about writing specifically (visual and product domains). Contra Labs sells human creative data, so it has a commercial interest in this conclusion.

### E3. The big taste scorers collapse separate judgments into one number
- Sources: [ImageReward](https://arxiv.org/html/2304.05977v4) (arXiv 2304.05977), [HPSv3](https://arxiv.org/html/2508.03789) (arXiv 2508.03789), [Pick-a-Pic](https://arxiv.org/html/2305.01569v2) (arXiv 2305.01569)
- Finding: ImageReward collected three separate 7-point scores (overall, alignment, fidelity) and trained a single scalar. HPSv3 trained only on pairs with at least 95% annotator agreement, discarding contested pairs, and its limitations name "a unified scoring metric." Pick-a-Pic asked only "which do you prefer."
- Used for: report each axis separately; treat disagreement as taste, not noise.
- Does NOT prove: that separate axes produce better writing. That's what this project tests.

### E4. No public taste dataset for founder writing (that we found)
- Searched (20 Oct 2026, 6 searches, not exhaustive): LinkedIn post datasets, LinkedIn's own papers, [WritingPreferenceBench](https://arxiv.org/html/2510.14616), [LitBench](https://arxiv.org/abs/2507.00769), [Persuasive-Pairs](https://arxiv.org/html/2406.17753v2), [PersuasionBench](https://arxiv.org/html/2410.02653v1), VCBench, PHBench.
- Finding: nearest datasets label stories, news, debate or tweets, or use likes and upvotes as the label. None has expert, multi-axis labels for founder posts or pitches.
- Used for: why the seed taste is practitioner-based (P1) for now, and why /learn saves edit pairs.
- Does NOT prove: that no such dataset exists privately.

### E5. Memory created without the user's say goes wrong
- Source: [arXiv 2602.01450](https://arxiv.org/pdf/2602.01450v2): of 2,050 memory entries from 80 users, 96% were created by the system unilaterally.
- Used for: /learn writes a rule to TASTE.md only after the user approves it.
- Does NOT prove: that system-created memories are usually wrong (the same study found 84% were grounded in user context). The issue is the user's lack of say.

### E6. People want taste add-ons for their AI
- Sources: [Taste Skill](https://github.com/Leonxlnx/taste-skill), 626,072 installs as of 17 Oct 2026 ([Skillselion](https://skillselion.com/skills/leonxlnx/taste-skill/design-taste-frontend)); [Impeccable](https://github.com/pbakaus/impeccable), 343,194 installs as of 19 Oct 2026 ([Skillselion](https://skillselion.com/skills/pbakaus/impeccable)).
- Used for: shipping as a plug-in inside Claude, not a separate app.
- Does NOT prove: demand for writing taste (both are design tools). Installs are not active users, and both counts come from one catalog.

---

### P1. Practitioner: 5 years of founder and personal-brand editing
- Source: Bhavya Goel's editing practice: 5 years, 50+ brands, 62K LinkedIn followers built from zero.
- Used for: the seed slop list and the default directions for the taste axes (`reference/seed-taste.md`).
- Label: experience, not research. Your TASTE.md overrides all of it.
