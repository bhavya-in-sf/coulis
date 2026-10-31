# Evidence ledger

Every rule in Coulis traces back to one of two kinds of source, always labeled:

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

### E7. AI help makes each writer better and everyone more alike
- Source: [Doshi & Hauser 2024, Science Advances](https://www.science.org/doi/pdf/10.1126/sciadv.adn5290) (doi 10.1126/sciadv.adn5290)
- Finding: in a pre-registered experiment with 293 writers, access to AI story ideas raised ratings of creativity and writing quality, most for less creative writers, but AI-assisted stories were more similar to each other.
- Used for: why coulis protects individual voice instead of chasing a generic "better".
- Does NOT prove: anything about professional or founder writing (short stories, online participants).

### E8. LLM help homogenizes ideas across people
- Source: [Anderson, Shah & Kreminski 2024](https://arxiv.org/abs/2402.01536) (C&C '24, arXiv 2402.01536)
- Finding: 36 participants; ChatGPT users produced less semantically distinct ideas across users than with an alternative tool, and felt less responsible for their ideas. The effect is at the group level.
- Used for: the "everyone's AI orders the same thing" problem.
- Does NOT prove: large-scale effects (small study, ideation task).

### E9. Writing style is getting less varied at scale
- Sources: [Sourati et al. 2026, Nature Human Behaviour](https://www.nature.com/articles/s41562-026-02549-7); [Sourati, Ziabari & Dehghani 2026, Trends in Cognitive Sciences](https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613(26)00003-3) (preprint arXiv 2508.01491)
- Finding: across 880,000 texts, writing became less varied as AI use spread after ChatGPT; LLM rewrites kept meaning but compressed style and blurred author traits (classifiers lost accuracy for age and gender). The review argues LLM styles reproduce dominant norms and erode minority voices.
- Used for: the "why now" slide and the core pain point (sounds like everyone).
- Does NOT prove: that a taste layer reverses the trend. That's what coulis has to show.

### E10. AI edits pull writing away from the writer's voice
- Source: [How LLMs Distort Our Written Language](https://arxiv.org/html/2603.18161v2) (arXiv 2603.18161)
- Finding: LLM revisions produce larger semantic shifts that point in a common direction, unlike human revisions; in a randomized trial heavy LLM users said their essays were less creative and not in their voice.
- Used for: learn from the writer's own edits (draft vs posted), not from generic rewrites.
- Does NOT prove: the effect for short social posts specifically.

### E11. Alignment for one style suppresses diverse views
- Sources: [PERSPECTRA, ICLR 2026](https://arxiv.org/pdf/2602.08716) (arXiv 2602.08716); [Evaluating Pluralism in LLMs](https://arxiv.org/pdf/2606.13254) (arXiv 2606.13254)
- Finding: preference training (RLHF) optimizes for a single response style and suppresses heterogeneity; the literature names this "artificial hivemind" and "generative monoculture".
- Used for: steerable taste axes instead of one house style.
- Does NOT prove: anything about personal writing profiles (benchmarks of perspectives and opinions).

### E12. Human content is a scarce, restricted input for AI
- Sources: [Consent in Crisis, Longpre et al. 2024](https://arxiv.org/abs/2407.14933) (NeurIPS 2024); [Market Design for AI](https://arxiv.org/html/2606.12260v2) (arXiv 2606.12260); [The Economics of AI Training Data](https://arxiv.org/html/2510.24990) (arXiv 2510.24990)
- Finding: in one year new restrictions closed off 28%+ of the most critical sources in C4 (45% counting terms of service); a formal model shows synthetic data can't make up for scarce original human content; of 24 major data deals only 7 pay the original creators.
- Used for: positioning human taste and edits as valuable infrastructure; why users own their TASTE.md.
- Does NOT prove: that personal taste profiles have market value. Theory and deal analysis only.

### E13. Half the new web is AI-written, but humans win attention
- Source: [Graphite, May 2026](https://graphite.io/five-percent/research/ai-now-writes-as-many-online-articles-as-humans-do) (covered by [Axios](https://www.axios.com/2026/05/15/human-vs-ai-written-articles))
- Finding: primarily AI-written articles reached about 50% of new English web articles and plateaued since Q1 2025; 86% of articles in top Google results are human-written. Pew (Aug 2026) finds about 10% of all pages show AI authorship, using a different measure.
- Used for: "why now" (the flood is here, and human voice still wins).
- Does NOT prove: causation between human writing and ranking. Graphite is an SEO company; detector-based estimates vary.

### P1. Practitioner: 5 years of founder and personal-brand editing
- Source: Bhavya Goel's editing practice: 5 years, 50+ brands, 62K LinkedIn followers built from zero.
- Used for: the seed slop list and the default directions for the taste axes (`reference/seed-taste.md`).
- Label: experience, not research. Your TASTE.md overrides all of it.
