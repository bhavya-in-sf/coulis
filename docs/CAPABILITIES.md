# What coulis can do today, what is being tested, and what is planned

Updated 31 Oct 2026, v0.9.0. One table, kept honest. If a line moves between columns, the commit says why.

| Capability | Status | What it means in practice |
|---|---|---|
| Check: fixed rules, no model, about 4 ms | **Available** | Em dashes, banned phrases, filler, numbers not on your approved list, stock hooks, repeated hooks. Returns Send, Revise or Hold with each problem quoted. Same answer every time. |
| Opening-pattern check | **Available** | Line one is a pain, a punch or a promise. Question openers, "Excited to share", "In today's", "I'm thrilled", "ever wondered" and the not-X-but-Y frame get a Revise, with one of your own openers quoted as the alternative. |
| Rhythm fingerprint | **Available** | Words per sentence and lines per post measured from your TASTE.md samples at load. A draft more than two standard deviations away gets a Revise with the numbers. Makes part of the rhythm axis checkable, no model. |
| Repeated phrases across your last 20 posts | **Available** | Any exact six-word run already used in a post you sent (sent.jsonl) is quoted back. Hooks and skeletons were already checked; this catches closers and list bones. |
| Edit-pair capture | **Available** | When coulis_learn runs, the original, your revision, the surface and the proposed rules are written to edit-pairs.jsonl next to your profile. Local only. Research use needs the separate permission in DATA-PERMISSIONS.md. |
| Override log | **Available** | Flagged lines you kept, and passed drafts you changed anyway, go to overrides.jsonl. The calibration set for the critique. |
| Pick reasons | **Available** | coulis_pick takes a why tag: clearer, bolder, truer, more_me, shorter, other. Preference data per axis. |
| Sameness score 0 to 100 | **Available** | Counted from the tells the check found. It is not a detector and not a measure of your voice. |
| Critique: eight parts, never one number | **Available** | Clarity, proof, why you, the ask, hook, voice, boldness, rhythm, scored against your own samples by Claude. Rewrites only the weakest line. Needs a model call. |
| Learn from your edits | **Available** | Compares the draft with what you actually sent and proposes a rule. Nothing joins your taste file without your yes. |
| Approved facts and banned phrases | **Available** | claims.md on your machine. The check enforces it. |
| Learned rules enforced by the check | **Experimental** | A learned rule is shown to the critique today. Whether every learned rule is also enforced deterministically by the check is being verified; see the demo storyboard note. |
| Modes: linkedin, x, cold_email, investor_update, bio | **Available** | Word limit, the one thing the draft must contain, and a target score per surface. |
| One-command setup from a LinkedIn export | **Available** | `/coulis:extract` or `coulis setup --linkedin export.zip`. Builds TASTE.md and claims.md locally. |
| Stop hook (Claude is sent back if it skipped the check) | **Available** | Logs each run to ~/.coulis/hook-log.jsonl. |
| MCP server, Python and TypeScript SDKs | **Available** | Same tools, same profile, in Cursor and any MCP client. |
| Relevant-example retrieval for the critique | **Experimental** | Opt in with COULIS_RETRIEVAL=bm25 (or tfidf). Picks the samples from your own profile that match the draft instead of the first five. Lexical, not semantic. Off by default. |
| coulis_context and coulis_feedback tools | **Experimental** | Context returns the retrieved samples, approved preferences and conflicts for a draft, no model call. Feedback records accepted, edited, removed, not_selected or explicit_preference next to the profile. Records only; nothing trains. |
| Research runner on public datasets | **Experimental** | LongMemEval, LaMP, PRISM and CoAuthor adapters with licence manifests. First run: session retrieval on 500 LongMemEval queries, BM25 recall@3 0.86. Retrieval diagnostics, not taste or model scores. |
| REST API | **Experimental** | Code and tests exist (keys hashed, profiles encrypted, drafts never logged). Not hosted yet. |
| Team profiles and the team score gate | **Planned** | One taste file and one approved-facts list shared across a team; a sameness ceiling as a gate. |
| Blind taste test with human raters | **Planned** | Does the critique agree with people more often than chance? Not yet run. |
| A trained taste model | **Planned, research direction** | No coulis model exists. The hypothesis and the test are in RESEARCH-AGENDA.md. |
| Enterprise: custom taste model from a company's own data, integrated into its systems | **Planned** | The paid door. No pilot signed. |
| Slack and ChatGPT | **Planned** | Through the API once it is hosted. |

What the check does not do: it does not verify that an approved fact is true, and it does not measure how much a draft sounds like you. The critique's voice axis does the second part, against your samples, and is a model judgment, not a measurement.
