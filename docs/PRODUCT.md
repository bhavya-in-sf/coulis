# Coulis: capability and ownership status

Coulis is being built as a frontier research lab for AI taste infrastructure. Writing is the first domain, and the plug-in is the current experimental interface. [Research agenda](RESEARCH.md).

Install the local layer to check drafts and carry approved editorial preferences into the next critique. Stop repeating the same corrections is the goal; savings and unseen-topic gains have not been measured.

## Available in this implementation

- Local Python checking and MCP tools for Claude-compatible clients; no hosted account required.
- Numeric-sentence approval matching, with entity, metric, value, unit, period, source and validity metadata. Unknown wording, stale approvals and conflicting active values remain unresolved.
- Eight-axis critique via the host model or the user's model-provider credentials.
- Human-approved, context-scoped preference memory stored locally in preferences.json. No model-weight training.
- Separate profile folders per client. This is local isolation by user-selected folder, not enterprise authentication or permission enforcement.

## Enterprise: waitlist only

Hosted REST API, hosted SDK service, organization accounts, role-based permissions, SSO, shared approval history, ERP/CRM integrations, custom models and managed enterprise security are not live. Local Python/MCP code is not a hosted enterprise service. Joining the waitlist does not provision access or buy a product. [Join the enterprise waitlist](waitlist.html?door=enterprise).

## What is proprietary today?

The repository code is MIT-licensed. The prompts, rules, schemas and public benchmark runner are inspectable, not an exclusive technical moat. A customer retains rights in its writing and profiles; those are not Coulis-owned training assets. No proprietary trained model or exclusive licensed corpus is established here. Founder editorial expertise and workflow knowledge are an advantage, not proof of defensibility. A future permissioned dataset of contextual edits and measured preference prediction could become an advantage; it does not exist merely because posts have been collected.

## Continual preference learning

The local loop is draft → human edit → scoped proposal → explicit approval → persistence → retrieval in a later critique. It records evidence hashes rather than storing the whole edit pair by default. Sent text is evidence, not infallible preference truth. Single observations remain proposals. Repeated approved evidence can be accumulated; it never silently approves a rule.

Call coulis_learn with surface and optional audience/purpose. Review each proposal and edit its key/value when it represents a conflicting choice (for example key `em_dash`, value `allow` or `avoid`). Call coulis_preference only after approval. A rule's scope matches only when every supplied dimension matches. More specific rules override broader rules with the same key. Equal-specificity disagreements remain unresolved. Missing context never activates a narrower preference. Use retire_id to retire a rule; reapprove the same unchanged record to restore it. Changes need a new id. Optional expires dates retire stale preferences from retrieval.

Free-text semantic contradictions cannot be reliably detected by this deterministic selector. Give mutually exclusive preferences the same key; the critic must ask about other conflicts. Rules influence later critiques; only supported machine-readable preferences affect the deterministic gate. Human-reviewed generalization to unseen topics remains untested.

## Structured claims

Store a list of records in claims.json or use coulis_approve_claim after explicit approval. Example is synthetic:

```json
{
  "id": "example-followers-oct26",
  "entity": "Example founder",
  "metric": "followers",
  "value": "62000",
  "unit": "people",
  "time_period": "2026-10",
  "source": "Owner-reviewed account export dated 2026-10-31 (synthetic example)",
  "approved_at": "2026-10-31",
  "valid_until": "2026-11-30",
  "statement": "I have 62K followers.",
  "paraphrases": ["My audience includes 62,000 followers."]
}
```

The user approves the complete wording and any paraphrases. The engine normalizes capitalization, whitespace and equivalent numeric notation, not meaning. It does not approve unseen paraphrases by guessing. A source reference is provenance, not verification that the source is true. Expired/future/incomplete/conflicting records stay unresolved. Legacy claims.md notes no longer authorize numbers: migrate deliberately rather than inventing metadata. Qualitative claims and undetected numeric wording still need human review. `Send` is retained for compatibility and means only “No configured rule violations found”; it is never permission to publish or a statement that facts are verified.

## Why this differs from LLMs that write well

A better writing model improves general generation. Coulis aims to carry an individual's approved, context-specific judgment across models and sessions. The model can write; Coulis supplies memory, checks constraints, and structures review. Native models can also personalize and critique. The incremental value of this layer over a well-configured model is a hypothesis to test, not an assumed moat.
