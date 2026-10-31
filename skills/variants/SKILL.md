---
name: variants
description: Offer alternative hooks or drafts using shared contextual taste memory, capture a real choice with permission, and propose preferences for explicit approval.
---

# Coulis: variants

Follow `reference/workflow.md` in the plugin root (two levels up).

1. Call `coulis_context` for the task, surface and known audience/purpose, then generate three distinct alternatives using approved facts and applicable taste preferences.
2. Check each with `coulis_check`. Fix Hold issues without inventing facts.
3. If the user permits retaining the alternatives, use `coulis_workflow` action `create` with task, candidates `[{text,condition}]`, context, consent:true. Use descriptive condition labels; do not label all candidates as an experiment against a baseline. Display returned positions as A/B/C, mapping A to position 0. Conditions are hidden until a decision.
4. Capture their actual choice with `decide`, including the category and reason if known. Allow tie/neither. Do not assume an unchosen candidate was judged bad. Without retention permission, show options normally and do not persist them.
5. Provide the chosen wording in the draft. When a style preference is worth retaining, propose it with its evidence through the shared workflow and ask for per-rule approval. A pick alone does not update the profile or prove quality.
