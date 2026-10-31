# Research agenda

coulis is a product today and a research question underneath it. This page states the question, the hypothesis, what has been measured, and how the rest will be tested. Everything here is labelled as measured, in progress, or planned.

## The question
Can taste be measured and learned? Specifically: can a person's own editorial decisions (what they keep, change and reject) be turned into rules that improve how much a future draft, on a topic they have never written about, sounds like them?

## The hypothesis
Contextual editorial decisions, captured with permission and applied by audience and format, improve personalisation on unseen topics beyond what a strong general model achieves with the same samples in its prompt.

## What has been measured (reruns from the repo)
1. Her archive: 673 published LinkedIn posts through the check. 2 in 3 pass untouched; the rest carry the tells that read as AI.
2. One voice, many hands: 47 drafts a startup team wrote as its founder. One approved fact fixed 46 of 47; the one unsupported number was still caught.
3. Voice match: 24 held-out posts from 6 founder voices, then 44 posts from 11 voices, each scored once with the author's profile and once with a stranger's. Own profile scored higher in 16 of 24 (6 ties, 2 lower), then 41 of 44.
4. Reach: 211 posts with their real engagement. Posts the check would have held earned about 15% less (median 371 vs 434). Association, not cause.

What these do not show: that users prefer the drafts, edit less, or come back; that learned rules transfer to unseen topics; that a trained model beats prompting.

## How the rest will be tested
| Test | Question | Method | Status |
|---|---|---|---|
| Blind taste test | Does the critique agree with human readers more than chance? | 20 raters, pairs of drafts, critique verdict hidden; agreement vs chance and vs inter-rater agreement (Zheng et al. 2023 framing). | Planned, Dec 2026 |
| Unseen-topic transfer | Do learned rules help on a new topic? | For each writer: hold out topics, learn rules from the rest, generate with and without rules, score with their profile and with raters. | Planned |
| Edit-pair benchmark | Which rules are learnable from real edits? | Build the edit-pair set from the archive (original, revision, context), with permission; measure how often the proposed rule matches the editor's stated reason. | In progress: archive organised; from v0.9 every learn call captures a live pair locally (edit-pairs.jsonl) |
| Prompting vs retrieval vs training | Does training add value? | Same examples and context for each condition; a trained taste model is the last condition, run only if the first two leave headroom. | Research direction, no model yet |
| User outcomes | Better drafts, less editing, return visits? | Writing pilot: edit distance per draft, drafts per week, retention, against a no-coulis baseline. | Planned with the writing pilot |

## The data
2,437 real posts across 38 voices, 2022 to 2026: 673 of the founder's own published posts; 380 posts ghostwritten for founder clients; 1,384 posts from 29 client content sheets covering 28 brand and founder voices; a 211-post engagement export; 47 team drafts. Only the founder's own posts are public (personas/bhavya). Everything else stays private and is used under the permissions in DATA-PERMISSIONS.md. The archive's size is a starting advantage, not a model advantage; the useful asset will be the edit pairs and what they teach.

## Papers we stand on
Zheng et al. 2023 (LLM as judge), Padmakumar and He 2024 (co-writing reduces diversity), Doshi and Hauser 2024 (Science Advances), Chakrabarty et al. 2025 (8,000 edits of AI text), Salemi et al. 2024 (LaMP), Kobak et al. 2024 (excess vocabulary), Min et al. 2023 (FActScore), Kirk et al. 2024 (RLHF reduces output diversity, ICLR). Links and what each does and does not prove: EVIDENCE.md.
