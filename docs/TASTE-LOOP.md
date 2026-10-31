# Taste memory inside the product

One profile, one workflow database, all interfaces. The loop is **context → draft → human edit/choice → proposed preference → explicit approval → next draft**. No separate website.

| Interface | Entry point |
|---|---|
| MCP and Claude plugin | coulis_context, coulis_workflow, coulis_critique |
| CLI and OpenClaw | scripts/coulis.py context / workflow / call |
| Python local | LocalClient(profile_dir) |
| REST | POST /v1/context and /v1/workflow |
| Python remote | Client(base_url, api_key, profile_id) |
| TypeScript | new Coulis(baseUrl, apiKey, profileId) |

Every path reads the same profile folder, including TASTE.md, claims.md and coulis-research.db. REST selects the folder through a server-controlled mapping; remote users cannot choose filesystem paths. Different machines do not automatically synchronize folders. [API/SDK setup](API.md).

## Normal writing

Retrieve context for the task and known surface/audience/purpose. The host model uses the returned relevant examples and approved preferences; unresolved conflicts remain visible. Run the existing check and critique. Contextual preferences guide generation and critique, but arbitrary preferences are not all enforced by deterministic checks.

On a user-supplied edit, ask for retention permission if not already granted. Record it through `edit`, with category style/fact/task/other. Propose a rule only from an explicit style choice and approve only with per-rule authorization. No automatic weight updates, fabricated preferences or inferred approvals.

## Workflow actions

All use the same arguments in MCP, CLI and SDKs:

| Action | Arguments |
|---|---|
| prepare | task, context, method? — returns matched baseline/Coulis generation inputs, not drafts |
| create | task, candidates (2–8 distinct text/condition objects), context, consent:true |
| view | comparison_id — returns randomized positions; conditions hidden until decision |
| decide | comparison_id, choice (displayed integer position, tie, neither), category, reason?, final?, active_edit_seconds? |
| edit | task, draft, final, context, category, consent:true, reason? — records the actual supplied final |
| extract | comparison_id — conservative edit-feature proposals with before/after evidence; may abstain; confidence uncalibrated |
| propose | comparison_id, key, value, wording — style evidence required |
| approve | proposal_id, approved:true, supersedes? |
| revise | preference_id, value, wording — pending replacement until approved |
| reject | proposal_id |
| disable | preference_id |
| state | none — preferences, pending proposals, comparisons, descriptive summary |
| purge | approved:true — explicit deletion request required |

Context requires surface, optionally audience/purpose. A condition label describes how a draft was created; descriptive choice counts do not prove model quality. Before/after edits are observational, not blind experiments. Durations are optional client reports, not measured time savings.

```sh
python3 scripts/coulis.py context '{"text":"Launch post","surface":"linkedin","context":{"audience":"founders"}}' --profile private/my-profile
python3 scripts/coulis.py workflow state --profile private/my-profile
# JSON can be supplied on stdin with -:
python3 scripts/coulis.py workflow edit - --profile private/my-profile < permitted-edit.json
```

```python
from sdk.python.coulis_client import LocalClient
c = LocalClient('private/my-profile')
# Only after permission to retain these actual user-provided texts:
edit = c.workflow('edit', task='Launch post', draft=original, final=user_final,
                  context={'surface':'linkedin'}, category='style', consent=True)
p = c.workflow('propose', comparison_id=edit['id'], key='opener', value='example', wording='Open with an example')
# Only after the user approves this exact preference:
c.workflow('approve', proposal_id=p['id'], approved=True)
next_context = c.context('A different topic', surface='linkedin')
```

Approved memory is loaded automatically by profile/context/critique. DB-backed rules are not duplicated into Markdown. Legacy learn/pick capture remains compatible but does not itself approve contextual preferences. Purge affects workflow data only; legacy files and backups need separate deletion. This is contextual continual memory, not a trained taste model or evidence of performance gains.

## Personalization evaluation

Use the separate offline [personalization benchmark](PERSONALIZATION-EVAL.md) to compare no profile, samples only, and approved preferences on dated held-out tasks. Ordinary workflow summaries are not that experiment.
