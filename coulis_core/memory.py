"""Local, approval-based preference memory. No weight updates or cross-client pooling."""
import datetime as dt
import hashlib
import json
import os
import tempfile
from pathlib import Path

DIMENSIONS = {'surface', 'audience', 'purpose'}


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


def propose(draft, final, profile, context=None):
    from .engine import _learn
    scope = dict(context or {})
    if not scope or not scope.get('surface'):
        raise ValueError('Learning requires a surface; add audience and purpose when relevant')
    if set(scope) - DIMENSIONS or any(not isinstance(v, str) or not v for v in scope.values()):
        raise ValueError('Scope supports nonempty surface, audience and purpose strings')
    evidence = hashlib.sha256((draft + '\0' + final).encode()).hexdigest()
    result = []
    for text in _learn.propose(draft, final, profile.to_persona(scope))[:3]:
        rid = hashlib.sha256((text + json.dumps(scope, sort_keys=True)).encode()).hexdigest()[:16]
        result.append({'id': rid, 'text': text, 'source': 'learned', 'approved': False,
                       'scope': scope, 'key': '', 'value': '', 'active': True,
                       'added': dt.date.today().isoformat(), 'expires': '', 'evidence_ids': [evidence]})
    return {'proposed_rules': result, 'learning_type': 'approved preference memory, not model training',
            'generalization_validated': False}


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.coulis-', text=True)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.write('\n')
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def update(folder, rule=None, retire_id=None):
    """Persist one explicitly approved rule, or retire it. Caller must obtain approval.

    Single local writer. Retired records remain for audit/undo; this is not a team service.
    """
    from .profile import Rule
    path = Path(folder) / 'preferences.json'
    rows = json.loads(path.read_text()) if path.exists() else []
    if retire_id:
        found = False
        for row in rows:
            if row.get('id') == retire_id:
                row['active'] = False
                found = True
        if not found:
            raise ValueError('Unknown preference id')
    else:
        rule = dict(rule or {})
        if rule.get('approved') is not True or not rule.get('id') or not rule.get('text'):
            raise ValueError('An id, text and explicit approval are required')
        if set(rule.get('scope', {})) - DIMENSIONS:
            raise ValueError('Unsupported scope dimension')
        if any(not isinstance(v, str) or not v.strip() for v in rule.get('scope', {}).values()):
            raise ValueError('Scope values must be nonempty strings')
        if rule.get('expires'):
            dt.date.fromisoformat(rule['expires'])
        Rule(**rule)  # validate shape before writing
        existing = next((r for r in rows if r.get('id') == rule['id']), None)
        if existing:
            if any(existing.get(k) != rule.get(k) for k in ('text', 'scope', 'key', 'value')):
                raise ValueError('Retire the old rule and use a new id for a changed preference')
            rule['evidence_ids'] = sorted(set(existing.get('evidence_ids', []) + rule.get('evidence_ids', [])))
        rows = [r for r in rows if r.get('id') != rule['id']] + [rule]
    save_json(path, rows)
    return {'saved': True, 'file': str(path), 'rules': len(rows)}
