# Security

coulis runs on your machine. The basic check (`coulis_check`, the gate) makes no network call. The critique sends the draft and a few of your sample posts to Claude under your own Claude subscription or API key; coulis stores nothing from that call. Your taste files (`TASTE.md`, `claims.md`) and the local log (`~/.coulis/coulis-log.jsonl`, verdicts only, never drafts) stay on your machine.

The optional REST API (`api/`) stores profiles encrypted at rest, keeps API keys only as hashes, never logs request bodies or drafts, and rate-limits per key. It is not hosted by us today; if you run it, set `COULIS_ENC_KEY`.

## Reporting a problem
Email 4goelbhavya@gmail.com with "coulis security" in the subject, or open a private security advisory on GitHub (Security tab → Report a vulnerability). Please include steps to reproduce. You will get a reply within 72 hours. Please do not open a public issue for a security problem.

## Scope
This repository, the published plug-in, and the landing page at bhavya-in-sf.github.io/coulis.
