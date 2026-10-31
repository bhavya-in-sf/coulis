// SDK contract test with a stubbed fetch (no server needed): node sdk/typescript/test.mts
import assert from "node:assert/strict";
import { Coulis, CoulisError } from "./src/index.ts";

const calls: Array<{ url: string; init: any }> = [];
(globalThis as any).fetch = async (url: string, init: any) => {
  calls.push({ url, init });
  if (init.headers.Authorization === "Bearer bad") {
    return new Response(JSON.stringify({ error: { code: "unauthorized", message: "no" } }), { status: 401 });
  }
  if (url.endsWith("/v1/check")) {
    return new Response(JSON.stringify({ verdict: "Hold", issues: [], skeleton: [], counts: { Hold: 1, Revise: 0 } }));
  }
  return new Response(JSON.stringify({ id: "prf_1", profile: {} }));
};

const t = new Coulis({ apiKey: "tst_x", baseUrl: "https://api.example.com/" });
const p = await t.createProfile({ samples: ["one post"] });
assert.equal(p.id, "prf_1");
const r = await t.check("prf_1", "We hit $20k MRR", "x");
assert.equal(r.verdict, "Hold");
const sent = JSON.parse(calls[1].init.body);
assert.deepEqual(sent, { profile_id: "prf_1", text: "We hit $20k MRR", surface: "x" });
assert.equal(calls[1].url, "https://api.example.com/v1/check");
await assert.rejects(new Coulis({ apiKey: "bad" }).usage(), (e: CoulisError) => e.status === 401 && e.code === "unauthorized");
console.log("ts sdk: all assertions passed");
