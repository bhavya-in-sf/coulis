# Writing corpus permissions and data handling

Product policy, effective for this implementation. This does not retrospectively establish rights in an existing corpus or replace a signed customer agreement.

## Default: service use only

A writer must own the material or have authority from the relevant rights holder to process it. Agency access to a client's work does not automatically grant permission for model training or publication. Local import requires an explicit rights confirmation and records a local permissions.json receipt. It does not upload the corpus. Use separate client folders. Do not mix client samples or profiles.

- Local profile building: permitted only on the user's instruction with appropriate rights.
- Model critique: the requested draft, relevant profile and samples are sent to the user's selected model provider. Its account terms and retention settings apply. Local storage does not mean inference is local.
- Shared training, cross-client reuse, shared research and public benchmark release: off by default. No importer enables these uses.
- Public posts are not automatically licensed for training or republication.
- The user retains rights in writing and profiles. The code's MIT license must not be treated as a grant of rights in third-party writing.

## Separate permission for future research or training

Before any such use, obtain a recorded, purpose-specific authorization identifying: rights holder and authority; files/record ids; allowed purpose (evaluation, publication, training each separately); recipients/providers; duration; retention; withdrawal contact and limits; whether identifiable quotations may be published; and whether a resulting model may be distributed. Do not make service access conditional on optional training permission. Redaction alone is not proof of anonymity or ownership.

Suggested service permission wording:
“I confirm I own this writing or have permission to use it to build and operate this client's Coulis profile. I understand a requested model critique shares the selected draft and profile context with my model provider. This does not authorize shared training, cross-client reuse, or publication.”

Optional future permissions must be separate, unchecked choices with an actual operational retention/deletion process before collection. They are not implemented collection paths today.

## Existing corpus: audit required

The historical 2,437-post/38-voice corpus has no complete rights manifest established by this change. Do not designate it proprietary training data or use it for shared learning until reviewed. The existing founder sample remains a demonstration under the repository's stated permission; that statement does not establish broader training rights. For each source record ownership, customer authorization, permitted uses, expiry and evidence reference. Unknown records are excluded from shared evaluation/training/publication.

## Retention and deletion

Local files persist until the user removes them. Delete a profile folder to remove its samples, preferences, approvals and optional pick logs; inspect backups such as TASTE.md.bak as well. No remote deletion guarantee is implied. Model-provider requests and waitlist submissions have separate recipients. Local usage logging is off by default; COULIS_LOG=1 records counts and outcomes without draft previews. Explicit variant picks store text locally in picks.jsonl.

The waitlist sends its displayed fields to FormSubmit and the configured recipient. Do not submit private drafts. Reply to a response email to request removal; a hosted deletion service is not live.

## Basis for this policy

We deliberately separate service delivery, evaluation, publication and training. See the [ICO guidance on purpose limitation in generative AI](https://ico.org.uk/about-the-ico/what-we-do/our-work-on-artificial-intelligence/generative-ai-second-call-for-evidence/) and the [US Copyright Office's AI materials](https://www.copyright.gov/ai/). Applicable obligations depend on the data and jurisdiction; this product policy does not declare the historical corpus legally cleared.
