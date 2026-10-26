// TypeScript client for the Taste API. Zero dependencies (uses global fetch).
//
//   import { Sauce } from "sauce";
//   const t = new Sauce({ apiKey: process.env.SAUCE_API_KEY! });
//   const { verdict, issues } = await t.check(profileId, "Notely hit $20k MRR");

export type Surface = "linkedin" | "x" | "reddit" | "instagram" | "youtube";
export type Verdict = "BLOCK" | "FIX" | "PASS";

export interface Issue { level: "BLOCK" | "FIX"; check: string; detail: string; quote: string }
export interface CheckResult { verdict: Verdict; issues: Issue[]; skeleton: string[]; counts: { BLOCK: number; FIX: number } }

export const CHECKABLE = ["clarity", "proof", "why_you", "ask"] as const;
export const TASTE = ["hook", "voice", "boldness", "rhythm"] as const;
export type Axis = (typeof CHECKABLE)[number] | (typeof TASTE)[number];

// Eight separate scores. There is deliberately no overall score.
export interface CritiqueResult {
  axes: Record<Axis, { score: number; why: string; quote: string }>;
  slop_found: string[];
  weakest_axis: Axis;
  rewrite: { before: string; after: string };
  missing_proof: string;
  model: string;
}

export interface ProposedRule { id: string; text: string; source: "learned"; approved: false }

export class SauceError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(`${status} ${code}: ${message}`);
    this.status = status;
    this.code = code;
  }
}

export interface SauceOptions { apiKey: string; baseUrl?: string }

export class Sauce {
  private apiKey: string;
  private baseUrl: string;

  constructor(opts: SauceOptions) {
    if (!opts.apiKey) throw new Error("apiKey is required");
    this.apiKey = opts.apiKey;
    this.baseUrl = (opts.baseUrl ?? "http://localhost:8787").replace(/\/$/, "");
  }

  private async req<T>(method: string, path: string, body?: unknown): Promise<T> {
    const res = await fetch(this.baseUrl + path, {
      method,
      headers: { Authorization: `Bearer ${this.apiKey}`, "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = (await res.json().catch(() => ({}))) as any;
    if (!res.ok) throw new SauceError(res.status, data?.error?.code ?? "http_error", data?.error?.message ?? res.statusText);
    return data as T;
  }

  createProfile(input: { samples: string[]; who?: string; audience?: string; goal?: string; owner?: string; product?: string; approved_facts?: string[] } | { profile: unknown }) {
    return this.req<{ id: string; profile: unknown }>("POST", "/v1/profiles", input);
  }
  getProfile(id: string) { return this.req<{ id: string; profile: unknown }>("GET", `/v1/profiles/${id}`); }
  deleteProfile(id: string) { return this.req<{ deleted: boolean }>("DELETE", `/v1/profiles/${id}`); }

  check(profileId: string, text: string, surface: Surface = "linkedin") {
    return this.req<CheckResult>("POST", "/v1/check", { profile_id: profileId, text, surface });
  }
  critique(profileId: string, text: string, surface: Surface = "linkedin") {
    return this.req<CritiqueResult>("POST", "/v1/critique", { profile_id: profileId, text, surface });
  }
  learn(profileId: string, draft: string, final: string) {
    return this.req<{ profile_id: string; proposed_rules: ProposedRule[] }>("POST", "/v1/learn", { profile_id: profileId, draft, final });
  }
  approveRule(ruleId: string) { return this.req<{ approved: boolean; rule: string }>("POST", `/v1/rules/${ruleId}/approve`, {}); }
  rejectRule(ruleId: string) { return this.req<{ rejected: boolean; rule: string }>("POST", `/v1/rules/${ruleId}/reject`, {}); }
  usage() { return this.req<{ usage: Array<{ endpoint: string; day: string; calls: number }> }>("GET", "/v1/usage"); }
}
