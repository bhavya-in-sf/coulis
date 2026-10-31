"""Shared personalization context for the existing critic and research runner."""
from dataclasses import asdict
import datetime as dt

def select(rules, context=None):
    context = context or {}
    buckets = {}
    for rule in rules:
        if not rule.approved or not rule.active:
            continue
        if rule.expires and dt.date.fromisoformat(rule.expires) < dt.date.today():
            continue
        if any(context.get(k) != v for k, v in rule.scope.items()):
            continue
        buckets.setdefault(rule.key or rule.text, []).append(rule)
    chosen, conflicts = [], []
    for key, candidates in buckets.items():
        specificity = max(len(r.scope) for r in candidates)
        candidates = [r for r in candidates if len(r.scope) == specificity]
        values = {r.value or r.text for r in candidates}
        if len(values) > 1:
            conflicts.append(key)
        else:
            chosen.append(candidates[-1])
    return chosen, conflicts

from .retrieval import retrieve

def _tokens(text):
    """Cheap token estimate: about four characters per token for English prose."""
    return max(1, len(text) // 4)


def _mentioned(draft, fact):
    """A fact is relevant when any number in it appears in the draft."""
    import re
    low = draft.lower()
    for n in re.findall(r"\d[\d,.]*[kKmM%+]?", fact):
        n = n.rstrip('.').lower()
        if n and re.search(r"(?<![\d.,])" + re.escape(n) + r"(?![\d.,kKmM%])", low):
            return True
    return False


def build_context(text, profile, surface='linkedin', context=None, method='bm25', k=5, budget_tokens=None):
    """Everything the critic is allowed to see, inside a token budget.

    Order of filling: rules (most specific, then most recent) up to 35% of the budget; facts the draft
    mentions plus the ten most recent, up to 15%; samples by retrieval until the rest is spent. The bundle
    reports its own token estimate and what was dropped, so the doctor and the user can see it.
    """
    import os
    budget = budget_tokens or int(os.environ.get('COULIS_CONTEXT_TOKENS', '2400'))
    selected, conflicts = select(profile.rules, {**(context or {}), 'surface':surface})
    selected = sorted(selected, key=lambda r: (-len(r.scope), r.added or ''), reverse=False)
    selected = sorted(selected, key=lambda r: (len(r.scope), r.added or ''), reverse=True)
    dropped = {'rules': 0, 'facts': 0, 'samples': 0}
    rules, used = [], 0
    for r in selected:
        t = _tokens(r.text)
        if used + t > budget * 0.35:
            dropped['rules'] += 1
            continue
        rules.append(r); used += t
    facts_all = list(profile.approved_facts)
    mentioned = [f for f in facts_all if _mentioned(text, f)]
    recent = [f for f in reversed(facts_all) if f not in mentioned][:10]
    facts, fused = [], 0
    for f in mentioned + recent:
        t = _tokens(f)
        if fused + t > budget * 0.15:
            dropped['facts'] += 1
            continue
        facts.append(f); fused += t
    dropped['facts'] += max(0, len(facts_all) - len(mentioned) - len(recent))
    documents = [{'id':f'sample-{i+1}', 'text':s} for i,s in enumerate(profile.samples)]
    if method == 'original':
        ranked = [{'id':d['id'], 'text':d['text'], 'score':None} for d in documents]
    else:
        ranked = retrieve(text, documents, max(k, len(documents)), method)
        if not ranked:  # nothing overlapped: fall back to the first samples rather than judging with none
            ranked = [{'id':d['id'], 'text':d['text'], 'score':None} for d in documents]
    samples, sused, remaining = [], 0, budget - used - fused
    for smp in ranked:
        t = _tokens(smp['text'])
        if len(samples) >= k or sused + t > remaining:
            dropped['samples'] += 1
            continue
        samples.append(smp); sused += t
    return {'samples': samples, 'preferences':[asdict(r) for r in rules], 'facts': facts,
            'conflicts': conflicts, 'retrieval_method':method, 'facts_verified':False,
            'tokens': {'budget': budget, 'rules': used, 'facts': fused, 'samples': sused, 'total': used + fused + sused},
            'dropped': dropped}
