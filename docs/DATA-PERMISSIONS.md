# Data and permissions

Three different permissions, never bundled.

| Permission | What it covers | Default |
|---|---|---|
| **Process your writing** | Running the check and the critique on a draft. The check runs on your machine and calls no model. The critique sends the draft and your samples to Claude for one call; HTTP request logging is disabled; explicit learning/choice operations can retain drafts. | Granted by using the tool. |
| **Retain preferences** | Keeping your TASTE.md and claims.md, adding learned rules to them, approved contextual preferences and permitted draft comparisons in coulis-research.db, and the local capture files next to them: edit-pairs.jsonl, overrides.jsonl, sent.jsonl, picks.jsonl. | Files live on your machine. Nothing is added to the taste file without your yes on each rule. Delete the capture files any time. |
| **Train shared models** | Using your writing or edits to train or evaluate a model that other people would use. | **Not granted by anything above.** Joining the waitlist does not grant it. It is a separate, written, revocable opt-in, and it does not exist yet. |

## The research archive
- 673 of the founder's own published LinkedIn posts: public, in personas/bhavya, by her decision.
- 380 ghostwritten posts, 1,384 content-sheet posts (28 voices), 211 engagement rows and 47 team drafts: private. Permission to use them for research and evaluation is founder-confirmed from the agency and consultancy contracts that produced them; client names and identifying details are never published, and no client post appears in the repo. Training permission is not assumed from research permission.
- Takeout and other personal exports: not part of any dataset.

## What signup means
Joining the writing pilot or the integration waitlist records your name, email, role and what you asked for. It does not guarantee access, and it grants none of the three permissions above.

## Hosting
The self-hosted API preview accepts server-configured bearer keys and profile mappings. Keys are kept in memory/environment, and profile/workflow data is plaintext on the server filesystem. HTTP access logs are off; explicit edit/choice workflows retain drafts with permission. It is not a managed hosted service. See [API boundaries and deletion](API.md).
