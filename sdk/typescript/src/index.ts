/** Source SDK for the self-hosted Coulis API. Uses the platform fetch implementation. */
export type Arguments = Record<string, unknown>;
export type Context = {surface: string; audience?: string; purpose?: string};
export type WorkflowAction = 'state' | 'extract' | 'edit' | 'create' | 'view' | 'decide' | 'propose' | 'approve' | 'prepare' | 'revise' | 'reject' | 'disable' | 'purge';
export class CoulisError extends Error {
  status: number;
  payload: any;
  constructor(status: number, payload: any) {
    super(payload?.error?.message ?? 'Coulis request failed');
    this.status = status; this.payload = payload;
  }
}
export class Coulis {
  private baseUrl: string;
  private apiKey: string;
  private profileId: string;
  constructor(baseUrl: string, apiKey: string, profileId = 'default') {
    this.baseUrl = baseUrl; this.apiKey = apiKey; this.profileId = profileId;
  }
  async call<T = Record<string, any>>(operation: string, args: Arguments = {}): Promise<T> {
    if (!/^[a-z_]+$/.test(operation)) throw new Error('Invalid operation');
    const response = await fetch(`${this.baseUrl.replace(/\/$/, '')}/v1/${operation}`, {
      method: 'POST',
      headers: {'Authorization': `Bearer ${this.apiKey}`, 'Content-Type': 'application/json'},
      body: JSON.stringify({profile_id: this.profileId, arguments: args}),
      signal: AbortSignal.timeout(30000),
    });
    const payload = await response.json();
    if (!response.ok) throw new CoulisError(response.status, payload);
    return payload as T;
  }
  workflow(action: WorkflowAction, args: Arguments = {}) { return this.call('workflow', {action, arguments: args}); }
  context(text: string, surface = 'linkedin', options: Arguments = {}) { return this.call('context', {...options, text, surface}); }
  check(text: string, surface = 'linkedin', options: Arguments = {}) { return this.call('check', {...options, text, surface}); }
  critique(text: string, surface = 'linkedin', options: Arguments = {}) { return this.call('critique', {...options, text, surface}); }
  learn(draft: string, final: string, surface = 'linkedin') { return this.call('learn', {draft, final, surface}); }
}
