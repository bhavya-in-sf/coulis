# Coulis research, inside the existing product

This is an experimental extension of Coulis, not a second product. The existing gate, preference files, critic and MCP entrypoint remain the product. No website or deck deployment is part of this change.

## Use it now

No new Python dependencies, keys, paid calls or GPU are required.

```sh
python3 -m unittest discover -s tests -v
# Opt the existing critic into relevant-example retrieval:
COULIS_RETRIEVAL=bm25 python3 mcp/server.py
```

`COULIS_RETRIEVAL=original` (the default) retains first-five-example selection. `bm25` and `tfidf` are opt-in baselines. TF-IDF is lexical, not semantic embeddings. No-overlap retrieval abstains instead of selecting irrelevant examples. Only the active profile's samples are candidates; the research corpus is never automatically inserted into customer prompts.

New tools on the **existing MCP server**:

- `coulis_context`: text, surface, context, optional method and profile_dir. Returns retrieved samples, approved preferences, conflicts, and sample IDs. No model call.
- `coulis_feedback`: approved=true, example_id, action, optional reason and profile_dir. Records explicit feedback next to that profile in coulis-research.db. Actions: accepted, edited, removed, not_selected, explicit_preference. This does not train, infer rejection labels, or approve a rule.

Example arguments:

```json
{"text":"A post about database transactions","surface":"linkedin","context":{"audience":"engineers"},"method":"bm25"}
```

Existing `coulis_learn` retains its current workflow. This update preserves the latest main branch, including its opening-pattern, rhythm and sent-history features. The new SQLite versioned preference store is an **experimental research component**, not a replacement for the existing profile files. It supports scope, conflicts, timestamped supersession, evidence IDs, pending proposals and full person deletion. It is not yet wired into the product's preference-write flow. Do not maintain parallel production preference stores. Structured scope fields are supported in in-memory/JSON profiles, but the existing Markdown profile writer does not persist this additional scope metadata.

## Real-data evaluation

The publisher's cleaned LongMemEval card declares MIT. Only research evaluation is enabled in our manifests. Downloaded corpora, normalized data and per-query reports stay under ignored `private/research/`.

```sh
mkdir -p private/research
curl -fL https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json -o private/research/longmemeval_s_cleaned.json
python3 -m coulis_research evaluate --input private/research/longmemeval_s_cleaned.json --manifest research/longmemeval-s.manifest.json --output private/research/s-report.json --k 3
python3 -m coulis_research import --input private/research/longmemeval_s_cleaned.json --manifest research/longmemeval-s.manifest.json --output private/research/s-normalized.jsonl
```

The runner compares no retrieval, BM25 and TF-IDF. It reports session recall@k and reciprocal rank only on records with relevance labels. Missing or empty labels are unscored, never treated as success. Answers and `has_answer` flags never enter document text. Reports include input/manifest/code SHA256, git revision and dirty state, Python version, per-query results and observed local latency. Latency is not expected to reproduce exactly.

**Not official LongMemEval scores:** these runs evaluate session retrieval, not answer generation. Query IDs stand in for independent synthetic histories; macro-user metrics are not measured human-user outcomes. Oracle input contains evidence sessions only and is not a meaningful full-history retrieval test. Do not market its scores as model performance. Existing deterministic checker results remain separate.

## Adapter coverage

| Source | Implemented | Limits |
|---|---|---|
| LongMemEval | Official question/history JSON; strips answer indicators from retrieval text | Real oracle and S data exercised; no model-based answer evaluator |
| LaMP / LongLaMP | Question/profile arrays, explicit whitelist of text fields | Contract-tested synthetic shapes; not validated across every upstream task/version; separate gold-file join not implemented |
| PRISM | Conversation observations preserving conversation_history and feedback | No conversion of rating scales to pairwise preferences; no trained ranker |
| CoAuthor | Envelope of session_id, writer_id, raw events | Observation ingestion only; no keystroke replay or final-text reconstruction |

Only source names in the registry are accepted. A manifest must identify source, version, URL, license and explicitly permit research_evaluation. A manifest is a recorded operator assertion, not an automated legal determination. Do not set permissions merely because data is downloadable.

Imports assign stable source/user hash splits. LaMP records without explicit user IDs remain query-scoped, so this is not evidence of unseen-person generalization. The duplicate audit reports exact normalized text overlaps across identity groups. Near-duplicate clustering, temporal splitting and train/test promotion gates remain to implement before training. Keep source datasets separate.

## Research sources and how they are used

- [LaMP](https://lamp-benchmark.github.io/): personalization and retrieval baselines; Avocado requires separate access.
- [LongLaMP](https://longlamp-benchmark.github.io/): long-form personalization tasks.
- [CoAuthor](https://coauthor.stanford.edu/): interaction event design; not-selected is not automatically rejected.
- [PRISM](https://github.com/HannahKirk/prism-alignment): person-linked feedback; retain observational meaning.
- [LongMemEval](https://github.com/xiaowu0162/LongMemEval): memory retrieval evaluation and update/abstention tests.
- [Personalized Judge](https://aclanthology.org/2024.findings-emnlp.592/): next-stage evaluator comparison.
- [DPO](https://arxiv.org/abs/2305.18290) and [LoRA](https://arxiv.org/abs/2106.09685): future bounded adaptation experiments, not implemented training.
- USF ACM, Inspec, Scopus, O'Reilly and PsycInfo: reading/discovery resources only; no subscription content copied into a training corpus.

## Next stages, not claimed as built

1. Validate remaining adapters on pinned, permitted upstream samples; add near-duplicate and time-split audits.
2. Collect approved contextual comparisons in the existing writing flow. Add a human-choice evaluation runner with tie handling and uncertainty by person.
3. Compare a personalized ranker with a population evaluator; fit only on eligible training data.
4. Add semantic retrieval and measure its gain over BM25/TF-IDF.
5. Run supervised LoRA and then DPO only if data coverage and baseline results justify them.
6. Add authenticated HTTP service, PostgreSQL/pgvector, remote deployment and monitoring when integrations need them. Current transport is local stdio MCP; the caller's profile directory is trusted, not a hosted authorization boundary.

## Local data handling

Feedback is opt-in and local. Do not include unnecessary private text in the optional reason. Research store deletion removes that person's preferences and events from the logical database; it does not remove backups or guarantee physical erasure. No automatic uploads, background training, auto-downloads, or telemetry were added.

## First measured run (2026-10-31)

500 queries from LongMemEval S cleaned, session retrieval at k=3:

| Method | Mean session recall@3 | Mean reciprocal rank |
|---|---:|---:|
| No retrieval | 0 | 0 |
| BM25 | 0.8618 | 0.8987 |
| TF-IDF | 0.7234 | 0.7723 |

These are local retrieval diagnostics, not QA accuracy or taste scores. No generation calls were made. The no-retrieval condition is a harness control, not a competitive language-model baseline. The current query is matched against the supplied history; no temporal cutoff is applied. Thirteen repeated session-ID occurrences with identical text were collapsed; alternate dates were retained. Some histories recur across query groups; do not use hash splits for training without resolving the duplicate audit. Summary and exact command: `results/longmemeval-s-retrieval-v01.json`. Full private report retains individual outcomes.
