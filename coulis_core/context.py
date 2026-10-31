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

def build_context(text, profile, surface='linkedin', context=None, method='bm25', k=5):
    selected, conflicts = select(profile.rules, {**(context or {}), 'surface':surface})
    documents = [{'id':f'sample-{i+1}', 'text':s} for i,s in enumerate(profile.samples)]
    if method == 'original':
        samples = [{'id':d['id'], 'text':d['text'], 'score':None} for d in documents[:k]]
    else:
        samples = retrieve(text, documents, k, method)
    return {'samples': samples, 'preferences':[asdict(r) for r in selected],
            'conflicts': conflicts, 'retrieval_method':method, 'facts_verified':False}
