# Coulis API and SDK contract

Self-hosted preview, source SDKs, no hosted endpoint or published package. The API invokes the existing MCP tool dispatcher and the same profile-local workflow store. It adds no frontend or generation service.

## Run

From the repository root, set a strong `COULIS_API_KEY` secret in your environment, then:

```sh
python3 -m api.server --profile /absolute/path/to/your/profile
```

Default bind: 127.0.0.1:8787. The `default` profile points to that exact folder. Existing CLI, MCP and LocalClient must use that same folder to share memory. API keys stay server-side; do not embed them in browser code. Remote deployment needs TLS, rate limits, secret management, backups and access controls. This is not an enterprise hosting implementation.

`Api({secret: {profile_id: Path(...)}})` supports server-configured accounts and profile mappings. A key can access only its mapping. Request paths cannot select filesystem folders. Different keys should map to separate folders unless sharing is intentional. There are no public signup/provisioning/key-rotation endpoints.

## Requests

`GET /v1/health` is public. All other endpoints require `Authorization: Bearer <key>` and use POST:

```json
{"profile_id":"default","arguments":{"action":"state","arguments":{}}}
```

Send this to `/v1/workflow`. Other endpoints use the same envelope and the existing tool arguments:

| Endpoint | Arguments |
|---|---|
| /v1/context | text, surface?, context?, method? |
| /v1/check | text, surface?, max_sameness? |
| /v1/critique | text, surface?, context? |
| /v1/workflow | action, arguments (see TASTE-LOOP.md) |
| /v1/profile | none |
| /v1/learn | draft, final, surface? — legacy edit capture |
| /v1/pick | picked, rejected?, surface?, context?, why? — legacy choice capture |
| /v1/feedback | event fields and approved:true; see MCP schema |
| /v1/add | kind, text, reason? — explicit approved fact/banned phrase |
| /v1/skip | reason, kind? |
| /v1/doctor | none |

The exact schemas are in `mcp/server.py`. Unknown fields and client-supplied profile_dir are rejected. 401 = unauthorized; 404 = unknown profile/operation; 400 = invalid request/state; 413 = body over 200 KB; 500 = internal failure. Errors do not echo private content. Mutations are not automatically retried by SDKs; after an ambiguous network failure inspect state before retrying.

Critique uses the existing configured Anthropic credentials when present; otherwise it returns host-model instructions. Workflow prepare never calls a model. Check remains deterministic and does not enforce every natural-language taste preference.

## Python

```python
from sdk.python.coulis_client import Client, LocalClient
local = LocalClient('/absolute/path/to/profile')
remote = Client('http://127.0.0.1:8787', api_key, profile_id='default')
bundle = remote.context('Write a launch post', context={'audience':'founders'})
inputs = local.workflow('prepare', task='Write a launch post', context={'surface':'linkedin'})
```

Both clients expose workflow, context, check, critique, learn and `call(operation, **arguments)` for every other tool. Import from the source checkout; no PyPI release is claimed.

## TypeScript

```ts
import {Coulis} from './sdk/typescript/src/index.ts';
const coulis = new Coulis('http://127.0.0.1:8787', process.env.COULIS_API_KEY!);
const context = await coulis.context('Write a launch post', 'linkedin', {context:{audience:'founders'}});
const state = await coulis.workflow('state');
```

Server-side runtimes with fetch and AbortSignal.timeout. `npm install && npm run build` in sdk/typescript builds the source package; it is private/unpublished. Use workflow for every memory action or call for the remaining tools. SDK HTTP errors expose status and payload.

## Data handling

The API is a transport over the local product: profiles and workflow drafts are plaintext Markdown/SQLite on the server's filesystem, protected by the deployment's disk/access controls. Keys are supplied in memory/environment, not stored in a user database. HTTP access logs are disabled. Explicit learn/pick/workflow operations retain text as documented; existing product metadata logs remain. Do not confuse 'no HTTP request logging' with 'no retained drafts'. Workflow purge removes workflow rows, not Markdown, legacy capture files or backups. Retention consent does not grant research/training rights.
