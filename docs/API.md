# Taste API (v1, developer preview)

The taste layer as an API: a gate that blocks off-brand or unapproved claims, a critic that scores 8 separate axes, and rules learned from what humans actually change.

Status: developer preview. Runs locally. Not a hosted service yet, and nothing here is for sale.

## Run it
```
python3 api/admin.py new-enc-key                     # save as SAUCE_ENC_KEY in a secret manager
export SAUCE_ENC_KEY=...  SAUCE_DB=sauce.db
python3 api/admin.py create-key --owner you --rate 60 # prints a key once
python3 api/server.py --port 8787
```
No dependencies beyond Python 3.10+, except `cryptography` (encryption) and `anthropic` (only for `/v1/critique`).

## Auth
Every call except `/v1/health` needs `Authorization: Bearer tst_...`. Keys are stored only as SHA-256 hashes. One key can never read another key's profiles.

## Endpoints

| Method | Path | What it does | Model call? |
|---|---|---|---|
| GET | `/v1/health` | Liveness and version | No |
| POST | `/v1/profiles` | Create a profile from `samples` (your own writing) or upload a full `profile` | No |
| GET | `/v1/profiles/{id}` | Read a profile | No |
| DELETE | `/v1/profiles/{id}` | Delete a profile and its pending rules | No |
| POST | `/v1/check` | The gate. `BLOCK`, `FIX` or `PASS`, every issue quoted | **No**, deterministic |
| POST | `/v1/critique` | 8 axes scored separately, weakest part rewritten. **No overall score** | Yes, one |
| POST | `/v1/learn` | Proposes rules from `draft` vs `final`. Saved as pending, not applied | No |
| POST | `/v1/rules/{id}/approve` | A human approves one rule; it joins the profile | No |
| POST | `/v1/rules/{id}/reject` | Discard a proposed rule | No |
| GET | `/v1/usage` | Your calls and tokens per endpoint per day | No |

### Example: the gate
```
curl -X POST localhost:8787/v1/check -H "Authorization: Bearer $KEY" \
  -d '{"profile_id":"prf_...","text":"Notely is the first app to hit $20k MRR","surface":"x"}'
```
```json
{"verdict": "BLOCK",
 "issues": [{"level": "BLOCK", "check": "unapproved_claim", "quote": "$20k mrr",
             "detail": "Number not in claims.md. Add it to claims.md or cut it."}],
 "counts": {"BLOCK": 2, "FIX": 0}}
```

### Critique response shape
`axes` has exactly 8 keys: `clarity`, `proof`, `why_you`, `ask` (checkable) and `hook`, `voice`, `boldness`, `rhythm` (taste). Each is `{score 1-10, why, quote}`. Plus `slop_found`, `weakest_axis`, `rewrite {before, after}`, `missing_proof`, and two more checks answered in a sentence or left empty: `bias` (who is missing from the story, or shown only as a stereotype) and `private_data` (a client, company or personal detail that may not belong in public).
Model: `SAUCE_MODEL` (default `claude-opus-5-5`), effort `SAUCE_EFFORT` (default `low`, because it runs on every draft).

## Profile format (`sauce.profile/v1`)
The same data as the plug-in's `TASTE.md` + `claims.md`, as JSON: `owner`, `product`, `who_i_write_as`, `audience`, `goal`, `samples[]`, `rules[] {text, source: user|learned, approved, added}`, `approved_facts[]`, `needs_confirm[]`, `banned[] {why, regex}`, `story_checks[] {why, regex}`. Converts both ways (`Profile.to_files()`).

## Privacy defaults
- Profiles and pending rules are **encrypted at rest** (Fernet). Without `SAUCE_ENC_KEY` the server warns and runs in dev mode.
- **No request logging.** The server logs no paths, bodies or IPs.
- **Drafts are never stored.** Metering records counts and token totals only.
- **No training on customer data.** Nothing sent to the API is used to train any model.
- Rate limit per key (token bucket, default 60/min). Bodies over 200 KB and drafts over 20,000 characters are rejected.

## Errors
`{"error": {"code": "...", "message": "..."}}` with status 400 (`missing_field`, `bad_json`, `invalid`), 401 `unauthorized`, 404 `not_found`, 413 `too_long`/`too_large`, 429 `rate_limited`, 500 `internal` (never echoes your draft).

## Clients
- Python: `sdk/python/sauce_client.py` (standard library only)
- TypeScript: `sdk/typescript` (zero dependencies, global `fetch`)
- MCP: `mcp/server.py` (Claude, Cursor, any MCP client). Ships inside the Claude plug-in from v0.2.
- Example app: `examples/writing_app.py` (Claude drafts, Sauce gates, one revision if blocked)

## Evals
```
python3 evals/run_eval.py regression --persona personas/example --golden evals/golden/example.json
python3 evals/run_eval.py edits --persona personas/example --pairs evals/edit_pairs/example.jsonl
python3 -m unittest discover -s tests
```
The regression suite fails on any verdict drift. The edits suite measures how often the gate flags what humans actually remove (`gate_agreement`); `--critique` adds a paid model call per pair to measure whether the critic targets what humans changed.


## Sameness score and team gates (v0.6)
Every `/v1/check` response carries `sameness`: `{score 0..100, label, hits}`, built only from quoted tells (em dash, banned phrase, filler, "it's not X, it's Y", question opener, "comment below", tricolon, emoji pile, one-line paragraphs). It is a style score, not a detector of who wrote the text.
Pass `max_sameness` (0 to 100) in the body to turn it into a gate: the verdict becomes BLOCK with a `sameness_gate` issue when the score is above the limit. Teams set one number ("nothing ships above 50") and CI can fail on it.
