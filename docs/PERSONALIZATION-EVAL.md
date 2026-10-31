# Does personal memory improve writing on new tasks?

This benchmark compares the **same model/settings** in three conditions:

1. `no_profile`: task, context and supplied facts; no writing samples or preferences.
2. `samples_only`: the same inputs plus retrieved writing samples.
3. `samples_preferences`: the same samples plus eligible approved preferences.

This is separate from the legacy `evals/benchmark.py` checker-score diagnostic. Neither deterministic violation counts nor public memory-dataset retrieval scores measure whether a person prefers Coulis's writing.

## Current status

The runner, leakage filters, blind review packet and report are implemented and tested. The committed fixture is synthetic. No live model comparison or real human-choice result is claimed. There are no user preference win rates or measured editing-time savings yet.

The founder corpus can supply permitted examples, but published posts alone are not preference comparisons. The current checkout does not contain a complete dated, topic-labeled task/evidence dataset with human ballots. Do not guess dates, fabricate edit histories or infer rejection labels from publication.

## Dataset contract

Use a private JSON object following `evals/fixtures/personalization/synthetic.json`:

- `manifest`: version, allowed_uses including research_evaluation, and synthetic true/false. This is an operator assertion of permission, not a license validator. Research permission is separate from shared-model training.
- `samples`: id, user_id, topic, at (timezone-aware timestamp), text. These are writing examples or final edit evidence. Use only permitted text. Keep before/after evidence in the product store and map its comparison ID to the corresponding evidence record when preparing an export.
- `preferences`: id, user_id, key, value, text, scope, approved, approved_at, evidence_ids. Optional supersedes, expires_at and disabled_at. Evidence IDs must refer to sample records. A historical evaluation requires the actual approval/retirement dates, not today's reconstructed profile.
- `tasks`: id, user_id, topic, at, task, context (surface and optional audience/purpose), approved_facts, optional reference. Task facts must be those available at the task date; the operator must verify their provenance. References are used only for duplicate filtering and never included in generation inputs.

The `future` split includes only earlier samples and earlier approvals from the same person. The `unseen_topic` split additionally excludes evidence with the task's topic label. All preference evidence must survive the split filters. Exact/near duplicate references or task text are excluded using normalized four-word-shingle Jaccard overlap >=0.8. This is a lexical safeguard, not semantic duplicate detection. Topic/date correctness is the operator's responsibility. It tests new topics for known writers, not unseen people.

Preparation freezes sample/preference selection; zero-overlap BM25 retrieval may return no examples. Coverage is reported. A case with no applicable preference provides no preference-treatment contrast—do not present it as evidence that memory helped. Conflicts stay explicit; do not silently resolve them for the experiment.

## Run

Run from the repository root; keep private datasets, generations, reviewer packets and condition keys under ignored `private/`.

```sh
python3 -m coulis_research.personalization prepare \
  --dataset private/personalization.json --split unseen_topic \
  --output private/eval-unseen/bundle.json
```

Generate each condition **in separate model contexts**, with the same model version, system instructions, tools, decoding settings, token limits and retry policy. Use only the corresponding prepared input; do not give one condition another condition's profile or output. The runner makes no model calls. Record an array in outputs.json:

```json
[{"case_id":"task-id","condition":"no_profile","input_hash":"hash from bundle","text":"actual model output","model":"actual model version","settings":{"temperature":0,"max_tokens":500,"system_prompt_hash":"actual hash"}}]
```

Supply all three outputs per case. Input hashes and matching model/settings are checked; the runner cannot independently verify that the caller actually used those inputs/settings. Do not label hand-written examples as model generations.

```sh
python3 -m coulis_research.personalization blind \
  --bundle private/eval-unseen/bundle.json --outputs private/eval-unseen/outputs.json \
  --packet private/eval-unseen/reviewer.json --key private/eval-unseen/conditions-private.json
```

Each case produces all three pairwise comparisons, with random order and opaque trial IDs. Give the reviewer only reviewer.json. Keep the key and outputs separate until judgments are complete. The intended writer judges voice; factual reviews may require a reviewer with the underlying evidence. Do not show experimental condition labels in candidate text.

Ballots are an array of actual reviewer responses:

```json
[{"id":"trial-id","choice":"tie","human_confirmed":true,"observations":[{"position":0,"factual_error":false,"final":"actual edited version","active_edit_seconds":30}]}]
```

Choice is displayed position 0/1, tie, or neither. Observations are optional and must be real: no factual-error value means unreviewed, not correct. Timings are client-reported. Human confirmation is an attestation, not identity verification. Do not treat a model judge as a human ballot.

```sh
python3 -m coulis_research.personalization report \
  --key private/eval-unseen/conditions-private.json --ballots private/eval-unseen/ballots.json \
  --output private/eval-unseen/report.json
```

Repeat preparation with `--split future` into a new directory for the temporal evaluation. Keep the two results distinct. Output files refuse overwrites to preserve artifacts.

## Read the report

- Pairwise wins, ties, neither and missing ballots are reported separately. Win share uses **all received ballots for that condition pair**, including ties/neither. The denominator is not posts or people.
- Equal-person macro win shares prevent prolific writers from dominating. With at least two people, a seeded 2,000-draw person bootstrap produces descriptive 95% intervals. Very small or selected samples remain inconclusive.
- Human-reviewed factual error rates include only explicit true/false reviews.
- Correction effort is word-level Levenshtein edits divided by original word count. It can exceed 1 and is not automatically time saved.
- Editing seconds are optional self-reports, with a separate denominator. Repeated candidate appearances across pairs count as repeated observations, not unique drafts.
- Dataset/version, bundle/output/ballot hashes and source hashes support provenance. Private inputs remain necessary for reproduction. Share only an appropriately reviewed aggregate report.

Predeclare the primary comparison (samples_preferences vs samples_only), task selection, factual-regression tolerance and success criteria before collecting judgments. A small positive result is a pilot signal, not evidence of a frontier model.

## Preference extraction in the existing product

After recording an actual style edit with `workflow edit`, call `workflow extract` with its comparison_id. It proposes up to three structural preferences, scoped to the edit's context, with full before/after evidence and observed feature counts.

```python
suggestions = client.workflow('extract', comparison_id=edit['id'])
# Display proposals. Only after approval of a specific rule:
client.workflow('approve', proposal_id=approved_id, approved=True)
```

The same action works through REST, MCP, CLI, Python and TypeScript. Repeated/concurrent extraction does not duplicate proposals. Resolved proposals are not reactivated.

Version 1 conservatively handles em-dash addition/removal, lowercase, paragraph breaks and sentence shortening when lexical content is unchanged. Numeric changes, non-style decisions, variant-only choices and unsupported semantic edits abstain. Confidence is explicitly null/uncalibrated with a tentative-single-edit label; there is no invented probability. Semantic preferences can still be supplied by a human/host model through `propose` and reviewed normally.

This is approved contextual memory. It does not train weights. Candidate ranking and a trained taste scorer remain later work, dependent on actual labeled comparisons.

## Run the full mock exercise

```sh
python3 -m coulis_research.mock_personalization --output private/mock-run
```

Use a new output directory. This runs real local workflow calls on disposable profiles, then both benchmark splits on six fictional writers and 24 tasks per split. It writes all bundles, scripted output fixtures, blinded packets, condition keys, simulated ballots, reports and a summary. It deliberately includes conflicts, future evidence, duplicate references, unapproved/expired/disabled preferences, factual regressions, ties, neither, and missing judgments/reviews. It makes zero model calls and collects zero human judgments.

The mock runner uses `report(..., simulated=True)`. The equivalent CLI flag is `report --simulated`. This requires a synthetic dataset and ballots with `simulated:true` and no true human confirmation. The default human-review report rejects simulated ballots. Simulation reports are labeled `evaluation_mode: simulation` and `effectiveness_measured: false`. Scripted preference shares, edit times and factual-error rates are not product measurements. Randomized presentation and opaque trial IDs vary per run; retain that run's key and packet together.

The first run passed 199 software checks. The committed summary is `research/results/mock-personalization-v1.json`; software tests rerun the complete exercise in CI.
