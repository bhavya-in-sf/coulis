# "Sounds like you" benchmark (v0, open)

A public test AI writing apps can run to see whether their output sounds like the person it was written for.

**Task 1, held-out voice.** Posts by known authors that the system never saw. Does the author's own profile score the post as more "them" than a stranger's profile? First results: own profile higher in 16 of 24 held-out posts (6 voices; 6 ties, 2 lower), then 41 of 44 (11 voices). Small samples: a pattern, not an accuracy rate.

**Task 2, pairwise picks.** Every time someone picks one of three variants with `/coulis:variants`, coulis saves "picked beats rejected" pairs (`picks.jsonl`). The benchmark reports how often the score ranks the human's pick higher. Apps can submit pairs of (their output, the human's pick).

Run it:

    python3 evals/benchmark.py picks --persona <profile dir> --picks <profile dir>/picks.jsonl
    python3 evals/benchmark.py voice --personas personas/a personas/b --heldout heldout.jsonl

Rules: no model call; same input, same score; every published number comes with its n and reruns from this repo. Private client writing is never published; only anonymised counts.
