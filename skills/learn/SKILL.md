---
name: learn
description: Learn from a user-supplied draft and final edit, propose contextual taste preferences, and save only rules the user explicitly approves through the shared Coulis workflow.
---

# Coulis: learn

Follow `reference/workflow.md` in the plugin root (two levels up). Use the same profile as the current writing task.

1. Obtain the actual original and final text, task, surface, and known audience/purpose. If unchanged, there is no preference evidence to record.
2. Explain the meaningful changes. Separate style from factual corrections and task changes. If mixed or unclear, ask which style change should become a preference; do not label the whole edit style without justification.
3. With permission to retain the pair, call `coulis_workflow` action `edit`, arguments `{task,draft,final,context,category,consent:true,reason}`. This records the supplied final, not an invented blind test.
4. Load `state` to check existing preferences. Propose at most three style rules using action `propose` with the returned comparison_id, key, value and wording. Cite the before/after evidence and scope. For an existing rule that needs replacing, use `revise` instead.
5. Show each pending rule for approval/edit/rejection. Use `approve` with `approved:true` only after explicit approval, or `reject` for rejected proposals. Do not write these rules into TASTE.md: the shared database is read by every interface.
6. Confirm what will apply next time and where. This updates contextual memory, not model weights. Never infer personal facts or carry rules across clients.
