# Coulis Research

**A frontier research lab building AI taste infrastructure.**

Our goal is to make individual and collective judgment representable, learnable and usable by AI systems. Writing is the first domain because people can supply explicit preferences and observable edits. The local plug-in is an experimental interface for the research, not the boundary of the company.

This is our research direction. We do not claim a frontier-trained model, validated preference predictor or demonstrated cross-domain generalization today.

## The research question

How can an AI system learn what a particular person considers good, apply it in the right context, and improve from feedback without flattening their preferences into a population average?

Taste is not just stylistic similarity. It includes what to say, what to omit, specificity, novelty, appropriateness, risk and the intended audience. Factual validity and permission constraints are distinct from subjective preference. A model should not trade a factual violation for a higher taste score.

## Research program

1. **Represent judgment.** Study a user-conditioned preference representation over person, audience, purpose and surface. Compare explicit rules, retrieved exemplars, embeddings and learned representations. A portable state should preserve provenance, uncertainty, permissions and change history.
2. **Learn continuously.** Start with approved edit events and pairwise choices. Study whether new evidence improves held-out preference prediction without forgetting older preferences or leaking across clients. Compare retrieval-only memory, a learned reranker/reward model, and parameter-efficient adaptation. Do not call memory updates weight training.
3. **Evaluate taste.** Measure agreement with the actual person's held-out choices, editing effort and context appropriateness. Include ties and disagreement. Separate voice resemblance from quality and preference from factual correctness. Compare against models with equally good profiles and samples.
4. **Transfer judgment.** Test whether a preference transfers across topics, models and eventually modalities, and where it should not transfer. New domains require new evidence; writing results cannot establish visual-design taste.
5. **Serve infrastructure.** Expose versioned taste state, preference updates, contextual retrieval and critique to AI applications. Local Python and MCP are the prototype interfaces. Hosted APIs, trained models and enterprise governance remain planned/waitlist only.

## Staged experiments and decision gates

- **Now:** deterministic correctness, scoped retrieval and approval lifecycle tests. Synthetic fixtures only demonstrate implementation behavior.
- **First human study:** the blinded, same-context baseline in BENCHMARK.md, using consented writers and separate held-out topics. Zero completed user outcome tests at this stage.
- **Preference-model study:** only after obtaining purpose-specific research/training rights, train a small user-conditioned pairwise predictor. Split by time/topic within user, plus a separate unseen-user test. Include native-model, rule-only, retrieval-only and generic reward-model baselines. Report per-user results, calibration/abstention, context transfer and forgetting. No training run has been performed.
- **Continual-learning study:** introduce preferences in chronological batches; measure new-preference adaptation and regression on previous tasks. Include preference reversals and context collisions. Preserve a frozen evaluation set.
- **Infrastructure pilot:** integrate with 1–2 AI writing/agent products. Measure downstream user benefit, integration effort, latency/cost, isolation and consented data flows. Paid hosted access is not live.

## Commercial direction

The first paying customer should be an AI product team building writing or communication agents and needing a persistent taste layer. Select small teams with real users, repeated editing workflows and willingness to integrate. Agencies and professional writers are high-signal design/evaluation partners, not the company's category. Avoid letting bespoke brand-strategy services become the product roadmap.

The long-term asset could be a better learned representation and predictor of contextual taste, supported by specifically permissioned data and independent evaluation. Open-source glue, MCP support and a folder of customer posts are not, by themselves, that asset.
