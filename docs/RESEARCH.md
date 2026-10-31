# Coulis Research: a taste LLM

**A frontier research lab building a taste LLM and taste infrastructure for AI.**

We aim to build a language model that can generate, critique and choose according to individual judgment in context. Writing is the first domain. The current open-source plug-in is an experimental interface and non-trained baseline, not the proposed taste LLM.

## Hypothesis

Training on specifically authorized editorial choices, revisions and contextual preference comparisons may yield better person-conditioned judgment than prompting a general model with the same samples. We have not tested or established that result.

A useful taste LLM must learn what to say, emphasize, omit and select—not just imitate vocabulary. Preferences vary by person, audience, purpose and time. Factual validity and data-use permissions remain constraints, not taste scores to trade away.

## Proposed model and system

1. **Generative model:** start with an appropriately licensed pretrained language model and evaluate supervised editorial adaptation followed by preference optimization. Base-model choice, scale, licenses, compute budget and training recipe remain undecided. No training run is claimed.
2. **Personal conditioning:** compare explicit profiles, retrieved examples, compact learned taste representations and optional user-specific adapters. Test a new user with limited examples separately from a user represented during training.
3. **Judgment capability:** evaluate pairwise ranking, critique and uncertainty in addition to generation. Compare one multitask model against a separate evaluator; do not assume the generator can reliably judge itself.
4. **Taste state:** retain approved preferences, provenance, scope and explicit changes outside weights where this improves control. Inspectable memory and learned representations should be complementary experimental conditions.
5. **Delivery:** offer the successful model and state through an API or other licensed deployment. Local Python/MCP tools exist; hosted inference and enterprise capabilities are waitlist only.

Training a taste LLM does not necessarily mean pretraining a foundation model from scratch. A post-trained open-weight model can be the first research candidate if its license permits the planned uses. Frontier is the research ambition; state-of-the-art performance requires evidence.

## Continual learning: two distinct loops

**Implemented loop:** edits → scoped proposals → human approval → persistent memory → contextual retrieval. No model weights change. Automatic inference of every context and free-text contradiction is not implemented.

**Proposed model loop:** purpose-specific training permission → reviewed examples/choices → versioned training batches → adaptation → held-out evaluations → promotion or rollback. Never automatically train on everything someone sends. Measure forgetting, reversals, contextual spillover and cross-user leakage. Personal memory permission does not authorize shared model training.

## Dataset design

Each research example should carry an authorized pseudonymous writer/client id, context, original draft, edited or preferred text, rejected alternatives where available, explanation if supplied, event time, permission record, and split assignment. Store identifying mappings separately. Use the minimum necessary data; retain and delete according to the actual agreement.

Reserve future topics and time periods per writer. Maintain a separate unseen-writer split and a held-out external evaluation group. Deduplicate near-identical passages; exact-match checks alone are insufficient. Do not let approved numbers or named entities act as shortcuts for voice identification. No cleared training corpus is established by the existing post count.

## Evaluation program

Compare the same licensed base model under: ordinary prompting; a strong profile and retrieval baseline; current Coulis memory/critique; and a trained candidate when one exists. Match relevant context and generation budgets. Evaluate with blinded choices by the actual writer and independent quality review.

Measure preference wins/ties/losses, active editing time, factual regressions, context appropriateness, calibration/abstention, diversity, forgetting, new-user adaptation and inference cost/latency. Report per-writer results and uncertainty clustered by writer. Study whether a user's distinctive choices are preserved rather than merely maximizing a population-average preference score.

Use separate tests for generation, ranking, critique and continual adaptation. Writing results do not establish multimodal taste. Publish failures and limits alongside gains.

## Milestones and current status

| Milestone | Status | Evidence needed to advance |
|---|---|---|
| Local constraints and approved contextual memory | Implemented prototype | Regression and workflow tests |
| Human baseline study | Prepared, not run | Blinded comparisons and permissioned outcomes |
| Rights-cleared training dataset | Not established | Auditable purpose-specific permissions and split manifest |
| First taste-LLM candidate | Research plan only | Base-model/license choice, technical owner, compute budget, reproducible training run |
| Continual model adaptation | Research plan only | Gains on new preferences without unacceptable forgetting or leakage |
| Hosted model/API pilot | Waitlist only | Measured benefit, operational reliability and willing integrators |

The next step is the human baseline and data-rights work, followed by a bounded model experiment. The prototype, agency partnerships and first integrations serve that research program.

## Commercial and funding strategy

**B2B2C. VC-first. Paid from the first commercial engagement.** AI product companies are the buyers; their end users receive personalized taste capabilities. Raise venture capital for the model research and infrastructure while selling scoped integrations/evaluations of the existing prototype. These paid pilots are distinct from future hosted taste-LLM/API access, which remains waitlist only. No revenue or funding amount is claimed without verification. See [business model and initial paid offer](BUSINESS.md).
