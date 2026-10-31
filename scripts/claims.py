"""Conservative, local approval matching. Never independently verifies a source.

Only a complete approved sentence (or explicitly approved paraphrase) matches.
Unknown wording is unresolved, rather than guessed equivalent. Numeric-free
claims are outside this detector's coverage and are always disclosed as such.
"""
import datetime as dt
import re
from decimal import Decimal

FIELDS = ('id', 'entity', 'metric', 'value', 'unit', 'time_period', 'source',
          'approved_at', 'valid_until', 'statement')


def canonical(text):
    text = re.sub(r'\s+', ' ', text.casefold().replace('’', "'")).strip().rstrip('.!?')
    def number(m):
        n = Decimal(m[1].replace(',', '')) * {'k': 1000, 'm': 1000000, '': 1}[m[2] or '']
        return format(n.normalize(), 'f')
    return re.sub(r'(?<![\w])([0-9][0-9,]*(?:\.[0-9]+)?)(?:\s*([km]))?\b', number, text)


def clauses(text):
    # Keep decimal points; split sentences and semicolon-separated claims.
    return [s.strip() for s in re.split(r'(?<=[.!?;])\s+|\n+', text) if s.strip()]


def validate(record):
    if not isinstance(record, dict):
        raise ValueError('A structured claim must be an object')
    missing = [k for k in FIELDS if not str(record.get(k, '')).strip()]
    if missing:
        raise ValueError('Missing claim fields: ' + ', '.join(missing))
    start, end = (dt.date.fromisoformat(record[k]) for k in ('approved_at', 'valid_until'))
    if end < start:
        raise ValueError('valid_until precedes approved_at')
    Decimal(str(record['value']))
    aliases = record.get('paraphrases', [])
    if not isinstance(aliases, list) or any(not isinstance(x, str) or not x.strip() for x in aliases):
        raise ValueError('paraphrases must be a list of explicitly approved complete sentences')
    return record


def assess(text, records=(), today=None):
    today = today or dt.date.today()
    valid, invalid = [], []
    for r in records:
        try:
            validate(r)
            valid.append(r)
        except (ValueError, TypeError, KeyError):
            invalid.append(r.get('id', 'unknown') if isinstance(r, dict) else 'unknown')
    results = []
    for sentence in clauses(text):
        if not re.search(r'\d|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion)\b', sentence, re.I):
            continue
        matching = [r for r in valid if canonical(sentence) in
                    {canonical(s) for s in [r['statement']] + r.get('paraphrases', [])}]
        active = [r for r in matching if dt.date.fromisoformat(r['approved_at']) <= today <= dt.date.fromisoformat(r['valid_until'])]
        status = 'unresolved'
        reason = 'No complete approved wording matched. Review entity, metric, value, unit, period and source.'
        if matching and not active:
            reason = 'Matching approval is expired or not yet effective.'
        if active:
            conflicts = []
            for r in active:
                conflicts += [x for x in valid if all(canonical(str(x[k])) == canonical(str(r[k])) for k in ('entity', 'metric', 'unit', 'time_period'))
                              and dt.date.fromisoformat(x['approved_at']) <= today <= dt.date.fromisoformat(x['valid_until'])
                              and Decimal(str(x['value'])) != Decimal(str(r['value']))]
            if conflicts:
                reason = 'Conflicting active approvals for the same entity, metric, unit and period.'
            else:
                status = 'matched_approval'
                reason = 'Matched user-approved wording; the source has not been independently verified.'
        results.append({'quote': sentence, 'status': status, 'reason': reason,
                        'approval_ids': [r['id'] for r in active]})
    return {'status': 'unresolved' if any(r['status'] == 'unresolved' for r in results) or invalid else 'no_unresolved_detected',
            'facts_verified': False, 'coverage': 'numeric sentences only; qualitative claims and unrecognized wording require human review',
            'invalid_approvals': invalid, 'claims': results}
