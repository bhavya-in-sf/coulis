# Evaluation status — no user outcome tests yet

No repeated-use, editing-time, or unseen-topic improvement study has been completed. Automated tests establish software behavior, not product effectiveness.

## Historical results are not current accuracy claims

Earlier material reported 16/24 and 41/44 held-out voice results, 46/47 team drafts, a 673-post pass rate, and an engagement association. The old scoring script combined a rule-pattern score with issue penalties. Approved facts and banned phrases could influence it; it did not validate the eight-axis model critique. The precise post-vs-comparison denominator, split provenance and historical result artifacts have not been established here. These numbers are withdrawn from current effectiveness claims, not silently reinterpreted or rerun against unavailable private data.

Private inputs cannot be reproduced from this public repository. Do not publish private writing or claim public reproducibility merely because the runner is public.

## Public rule diagnostic v1

Numbers are masked and factual and banned-phrase issues are excluded from scoring. Only explicit punctuation/filler/slang preferences contribute. This is intentionally a weak rule baseline. Ties are expected; this is not voice recognition.

From repository root:

```sh
python3 evals/benchmark.py voice --personas evals/fixtures/voice/a evals/fixtures/voice/b --heldout evals/fixtures/voice/heldout.jsonl --dataset-version synthetic-v1 --split-description 'Handwritten synthetic samples and distinct held-out sentences; no human study' --public-inputs --output evals/results/synthetic-v1.json
```

The committed artifact records the exact command, dataset version, split description, input and code hashes, commit, row count, profile count, comparison count, wins/ties/losses and per-row outcomes. With N posts and K profiles there are N*(K-1) comparisons if every post is eligible. These are dependent comparisons, not independent people. Unknown authors and exact sample leakage fail rather than disappear from the denominator. The fixture proves the runner works; it says nothing about customer outcomes.

## Human evaluation protocol (prepared, not run)

Recruit 10 consenting writers across 3–5 agencies. Each contributes five real briefs and a separate setup sample set. Reserve later topics/time periods for held-out evaluation. Keep all client data isolated; get separate permission for any shared evaluation or publication.

Compare three conditions using the same model/version, generation budget, facts and briefs:
1. Normal writing prompt.
2. Carefully configured style profile with the same samples and facts.
3. That profile plus Coulis critique and approved preference memory.

Randomize and blind labels per brief. Save prompt/model versions, temperature, seed where supported, profile version, assignment seed and actual outputs privately. Have the actual writer choose or tie, then edit to acceptable quality. Log active editing seconds (exclude breaks), first-draft acceptance, edit distance, unsupported claims introduced/missed, rejected preferences, and the rate a previous correction recurs on an unseen topic. Score quality separately from resemblance. Report eight-axis critic reliability against human ratings separately; do not claim deterministic-rule results validate it.

Track week-1 through week-4 use by writer and agency; include dropouts and setup time. Analyse paired differences and bootstrap by writer/agency, not by output comparison. Report denominators, uncertainty, negative outcomes and ties. No savings claim until real results exist. Pre-register the protocol and decision thresholds before looking at outcomes.

See [PILOT.md](PILOT.md) for the ready-to-use pilot workflow and data template.

## Taste-LLM extension (planned)

The current runner is a deterministic diagnostic, not evaluation of a trained Coulis model. When a candidate exists, add it as a separate condition alongside its equally informed base model, profile/retrieval and current Coulis memory baselines. Keep generation, ranking, critique and continual-learning results separate. Record model checkpoint, training-data version, license, training configuration and held-out splits. See RESEARCH.md. No model-performance result is claimed today.
