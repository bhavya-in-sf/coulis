# coulis

**A frontier research lab building AI taste infrastructure.**

Your judgment, available to the models you use. [Research agenda](docs/RESEARCH.md).

Coulis is a reusable local layer for approved facts, contextual editorial preferences, critique and learning from edits. An AI application can call it rather than maintain its own disconnected user profile. Writing is the first domain; infrastructure is the product direction.

Install today to check a draft, review preference proposals, and carry approved context into the next critique. Better writing, reduced editing time and improvement on unseen topics have **not been validated in user tests**.

## Availability

| Available in this branch | Waitlist only / not live |
|---|---|
| Local Python library and MCP tools | Hosted REST API and hosted SDK service |
| Claude Code plug-in; MCP connection to compatible clients | Enterprise accounts, SSO and role-based permissions |
| Local scoped preferences and numeric approval checks | Shared team governance and review history |
| Model-based critique through the host or your provider account | Custom models, ERP/CRM and managed integrations |

[Enterprise waitlist](https://bhavya-in-sf.github.io/coulis/waitlist.html?door=enterprise). A local library is not a hosted enterprise service.

## Install

Python 3.10+ for the deterministic tools. Claude Code:

```
/plugin marketplace add bhavya-in-sf/coulis
/plugin install coulis@coulis
```

For Desktop, Cursor and compatible MCP clients, see [INSTALL.md](docs/INSTALL.md). Onboard with three authorized writing samples using `/coulis:setup`; a full export is optional. Your model provider processes the context you send it.

```python
from coulis_core import check, profile_from_folder
profile = profile_from_folder("./my-profile")
result = check("We have 63K paying customers.", profile, surface="linkedin",
               context={"audience": "founders", "purpose": "launch"})
print(result["verdict"], result["fact_check"], result["summary"])
```

`Send` is retained for compatibility: it means no configured violations were found, **not** that facts are verified or publication is authorized. Unresolved numeric claims, expired approvals and conflicting active values remain visible. Matching is conservative: a complete approved statement or explicitly approved paraphrase must match. Qualitative claims remain outside this detector's coverage.

## The infrastructure loop

- **Check:** local constraint checking with structured approval provenance.
- **Critique:** model judgment across eight axes, using the applicable approved preferences. These ratings are not objective accuracy scores.
- **Learn:** edits produce scoped proposals, never automatic permanent rules. Human approval persists them for later retrieval.
- **Resolve context:** pass surface, audience and purpose. More specific rules with the same key override broader ones. Equal-specificity conflicts ask for review; missing context does not activate narrow rules.

This is continual preference memory, not model-weight training. Native models can also personalize; the extra value of Coulis must be measured against a strong baseline.

Each client has a separate profile folder. TASTE.md stores samples and broad instructions; claims.json stores structured approvals; preferences.json stores versionable, scoped preference records. Local folder selection is not enterprise access control.

## Tools

- `coulis_check`, `coulis_critique`, `coulis_learn`: accept surface and optional audience/purpose context.
- `coulis_preference`: save one explicitly approved rule, or retire it by id. Same-key conflicts are exposed; free-text semantic contradictions need human review.
- `coulis_approve_claim`: save a complete approval only after human confirmation.
- `coulis_add`: legacy fact notes or personal phrase bans; a fact note alone no longer clears numbers.
- `coulis_pick`, `coulis_profile`, `coulis_doctor`: local picks, profile inspection and health checks.

See [PRODUCT.md](docs/PRODUCT.md) for schemas, precedence, retirement, limitations and current ownership.

## Migration

Existing claims.md notes remain readable but no longer authorize numeric claims by matching a bare number. Review and migrate to claims.json with source, validity and complete wording; no metadata is invented. Punctuation/filler preferences are opt-in. Old golden verdicts and published benchmark claims do not apply to this behavior.

`/coulis:learn` should use the scoped tools. The standalone `scripts/learn.py` requires `--surface`; `--apply` means the human has approved the displayed proposals. Do not use it to bypass review.

## Evidence and evaluation

No repeated-use, editing-time or held-out human preference study has been completed. The historical rule results do not validate the eight-axis critique. The public synthetic fixture demonstrates the diagnostic runner, not quality improvement. See [BENCHMARK.md](docs/BENCHMARK.md), [PILOT.md](docs/PILOT.md) and [EVIDENCE.md](EVIDENCE.md).

```
python3 -m unittest discover -s tests -v
node tests/test_claims.js
```

## Ownership and permissions

The code is MIT-licensed. No exclusive trained model or cleared proprietary training corpus is claimed. Users retain their writing and profile rights. The potential advantage is permissioned contextual preference data and demonstrated prediction quality; it remains to be earned.

Local import requires confirmation of ownership or authorization:

```
python3 scripts/coulis.py setup --linkedin Shares.csv --out ./my-profile --confirm-rights
```

Shared training, public benchmark reuse and cross-client reuse are off by default. Existing corpus rights require an audit; this change does not retroactively clear them. [Data permissions](docs/DATA-PERMISSIONS.md).

## Privacy

Local checks make no network call. Critique sends selected drafts and profile context to your chosen model provider. Local usage logging is off by default; `COULIS_LOG=1` enables counts/outcomes without draft previews. Explicit variant choices store text locally in picks.jsonl. Files and backups remain until the user removes them. The waitlist uses FormSubmit; it is not a writing-data collection or training opt-in.

## Direction

The product is taste infrastructure. The initial domain is writing. Candidate first paying customers are small AI writing/agent product teams that need to maintain their users' judgment across sessions and models. Agencies managing several voices are design partners and evaluation environments, not a limit on the product's ambition. Hosted paid access remains waitlist only.

Formerly sauce/Tastee; legacy profile-directory discovery remains supported. MIT. Built by Bhavya Goel.
