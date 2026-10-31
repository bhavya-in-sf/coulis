# The Coulis taste loop

Compare two drafts → record a human choice/edit → propose a contextual preference → explicitly approve → use on a new topic.

This extends the existing Python/MCP product. It does not train model weights. The GitHub Pages checker remains a browser checker; the new workflow runs locally with your profile.

## Open the local workspace

From the repository root:

```sh
python3 scripts/taste_loop.py --profile /absolute/path/to/your/profile
```

Open http://127.0.0.1:8767. No new packages or credentials are needed for this workspace. It binds only to loopback and requires a per-process token for API calls. The single local profile folder is the authority boundary; this is not a hosted multi-user service.

For an empty sandbox profile:

```sh
python3 scripts/taste_loop.py --profile private/my-profile
```

Use the same folder in your MCP configuration (`COULIS_PROFILE_DIR`) or tool `profile_dir` argument. Update and restart the MCP server to discover `coulis_workflow`.

## First session

1. Paste two candidate drafts for the same task. Identify their conditions, such as `baseline` and `coulis`, and supply surface/audience/purpose. Confirm local storage.
2. The workspace shuffles A/B and hides condition labels until a decision. A person who supplied the text may recognize it; this is not a fully blind study.
3. Choose A, B, tie, or neither. Optionally edit the selected draft. Classify the main reason as style, fact, task, or other.
4. Only a selected **style** choice can support a reusable preference proposal. Write the proposed preference, category and value. These structured fields allow contradictory preferences in the same category to be detected.
5. Review and explicitly approve. Fact/task edits are preserved as observations but are not automatically generalized into style preferences.
6. Give a new task with the appropriate context. The workspace prepares matched baseline/Coulis inputs with identical writing samples. Only the Coulis input includes applicable approved preferences.
7. Ask the model in your MCP host to produce one draft for each condition, then compare those outputs. No model is invoked by the local HTTP page. For a controlled experiment, use separate generation calls with the same model/settings and avoid showing either response to the other condition.

## MCP usage

`coulis_workflow` takes `action` and `arguments` (plus optional `profile_dir`).

Prepare a new task:

```json
{"action":"prepare","arguments":{"task":"Write a post about a customer interview","context":{"surface":"linkedin","audience":"founders","purpose":"share a lesson"}}}
```

The result includes matched generation inputs, selected preferences, evidence IDs and conflicts. The host model should generate the two candidates. Conflicts require resolution, not a silent choice. It must not claim a preference outcome until the user chooses.

Create a comparison from those outputs:

```json
{"action":"create","arguments":{"task":"Write a post about a customer interview","context":{"surface":"linkedin","audience":"founders","purpose":"share a lesson"},"consent":true,"candidates":[{"condition":"baseline","text":"FIRST ACTUAL OUTPUT"},{"condition":"coulis","text":"SECOND ACTUAL OUTPUT"}]}}
```

Remaining actions:

- `view(comparison_id)`: retrieve randomized candidates; source conditions stay hidden until the decision.
- `decide(comparison_id, choice, category, reason?, final?)`: user choice is 0, 1, `tie` or `neither`. Saved decisions cannot be overwritten.
- `propose(comparison_id, key, value, wording)`: reviewable wording supplied by a human or host model, not an automatically established preference.
- `approve(proposal_id, approved:true, supersedes?)`: save only after human approval.
- `revise(preference_id, value, wording)`: create a new pending revision; the original remains active until approved.
- `reject(proposal_id)`: dismiss a pending proposal.
- `disable(preference_id)`: remove it from future context without deleting its history.
- `state()`: inspect active/inactive preferences, pending proposals, comparisons and counts.
- `purge(approved:true)`: after an explicit deletion request, remove local workflow drafts, decisions, proposals, preferences and events. Legacy Markdown and backups are not deleted; logical deletion is not a secure-erasure guarantee.

## One store shared with the product

`coulis_core.taste_store` is the canonical implementation. `coulis_research.store` is a compatibility import, not another database. New preferences and feedback use the existing `coulis-research.db` beside the profile.

`profile_from_folder` loads effective approved preferences from that store alongside legacy Markdown rules. Both `coulis_context` and `coulis_critique` see them. Database-backed rules are not copied into TASTE.md during export, avoiding duplicate stale rules. Keep the database with the profile when transferring it. Existing `coulis_learn` remains available and is not changed to silently approve or migrate old rules.

Scope matches exactly. Preferences for LinkedIn/founders do not apply to email/customers. Same-key, equally specific contradictory values are surfaced as conflicts. Supersession and disabling take effect in subsequent profile loads. Legacy free-text rules without a shared structured key cannot have arbitrary semantic contradictions automatically detected.

## What results mean

The summary groups decisions by the actual pair of condition labels and reports wins, ties and neither. It does not infer preference from clicks, generate rejected examples, calculate a universal taste score, or claim causal improvement. No ranker or model training is added. Active editing time is optional client-reported metadata; the UI does not present it as a verified savings metric.

A research study still needs independent participants, model/configuration provenance, fixed held-out tasks, leakage control and uncertainty estimates. Agent-generated UI checks use a disposable synthetic profile and are not human research evidence.

## Tests

```sh
COULIS_LOG=0 python3 -m unittest discover -s tests -v
node --check docs/taste-loop.js
```

Tests cover approval boundaries, fact/tie exclusions, scope matching, revisions, disabling, conflicts, profile isolation, MCP integration, deletion, and local HTTP token/origin checks.
