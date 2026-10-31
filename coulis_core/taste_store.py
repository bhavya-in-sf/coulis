"""Local SQLite research store. Tenant arguments are isolation filters, NOT authentication."""
from contextlib import nullcontext
import datetime as dt
import json
import sqlite3
import uuid

SCOPES = {'surface', 'audience', 'purpose'}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamps require a timezone')
    return parsed.astimezone(dt.timezone.utc)

class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS preferences (tenant TEXT, person TEXT, id TEXT, payload TEXT, PRIMARY KEY(tenant, person, id))')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, tenant TEXT, person TEXT, payload TEXT)')
        self.db.commit()

    def close(self):
        self.db.close()

    def event(self, tenant, person, kind, payload):
        if not tenant or not person:
            raise ValueError('Tenant and person required')
        self.db.execute('INSERT INTO events(tenant,person,payload) VALUES(?,?,?)',
                        (tenant, person, json.dumps({'at': now(), 'kind': kind, 'payload': payload})))

    def add(self, tenant, person, preference):
        p = dict(preference)
        if not tenant or not person:
            raise ValueError('Tenant and person required')
        for key in ('key', 'value', 'text'):
            if not isinstance(p.get(key), str) or not p[key].strip():
                raise ValueError(f'Preference requires {key}')
        p.setdefault('id', str(uuid.uuid4()))
        p.setdefault('scope', {})
        p.setdefault('approved', False)
        p.setdefault('evidence_ids', [])
        p.setdefault('confidence', None)
        p.setdefault('effective_at', now())
        if type(p['approved']) is not bool:
            raise ValueError('approved must be a boolean')
        if not isinstance(p['scope'], dict) or set(p['scope']) - SCOPES or any(not isinstance(v,str) or not v for v in p['scope'].values()):
            raise ValueError('Invalid context scope')
        if not isinstance(p['evidence_ids'], list) or not all(isinstance(x,str) for x in p['evidence_ids']):
            raise ValueError('Evidence ids must be a string list')
        if p['confidence'] is not None and (type(p['confidence']) not in (int,float) or not 0 <= p['confidence'] <= 1):
            raise ValueError('Confidence must be in [0,1]')
        timestamp(p['effective_at'])
        if p.get('expires_at') and timestamp(p['expires_at']) <= timestamp(p['effective_at']):
            raise ValueError('Expiry must follow effective date')
        if p.get('supersedes'):
            old = self.db.execute('SELECT payload FROM preferences WHERE tenant=? AND person=? AND id=?', (tenant,person,p['supersedes'])).fetchone()
            if not old:
                raise ValueError('Unknown superseded preference in this tenant/person')
            old = json.loads(old[0])
            if old['key'] != p['key'] or old['scope'] != p['scope']:
                raise ValueError('Supersession must use the same key and scope')
            if timestamp(p['effective_at']) < timestamp(old['effective_at']):
                raise ValueError('Supersession cannot predate the original')
        with (nullcontext() if self.db.in_transaction else self.db):
            self.db.execute('INSERT INTO preferences VALUES(?,?,?,?)', (tenant, person, p['id'], json.dumps(p)))
            # Audit metadata only: deleted preference text is not retained here.
            self.event(tenant, person, 'preference_added', {'id': p['id'], 'approved':p['approved']})
        return p

    def active(self, tenant, person, at=None):
        instant = timestamp(at or now())
        rows = [json.loads(x[0]) for x in self.db.execute('SELECT payload FROM preferences WHERE tenant=? AND person=? ORDER BY id', (tenant, person))]
        effective = [p for p in rows if p['approved'] and timestamp(p['effective_at']) <= instant]
        retired = {p['supersedes'] for p in effective if p.get('supersedes')}
        for (payload,) in self.db.execute('SELECT payload FROM events WHERE tenant=? AND person=?', (tenant,person)):
            event = json.loads(payload)
            if event['kind'] == 'preference_disabled' and timestamp(event['at']) <= instant:
                retired.add(event['payload']['id'])
        active = [p for p in effective if p['id'] not in retired and
                  (not p.get('expires_at') or timestamp(p['expires_at']) > instant)]
        return active

    def select(self, tenant, person, context=None, at=None):
        context = context or {}
        active = [p for p in self.active(tenant,person,at) if all(context.get(k) == v for k,v in p['scope'].items())]
        selected, conflicts = [], []
        for key in sorted({p['key'] for p in active}):
            candidates = [p for p in active if p['key'] == key]
            maximum = max(len(p['scope']) for p in candidates)
            candidates = [p for p in candidates if len(p['scope']) == maximum]
            if len({p['value'] for p in candidates}) > 1:
                conflicts.append({'key':key, 'preference_ids':[p['id'] for p in candidates]})
            else:
                selected.append(max(candidates, key=lambda p:(timestamp(p['effective_at']),p['id'])))
        return {'selected':selected, 'conflicts':conflicts}

    def list_preferences(self, tenant, person):
        rows = [json.loads(x[0]) for x in self.db.execute('SELECT payload FROM preferences WHERE tenant=? AND person=? ORDER BY rowid', (tenant,person))]
        active_ids = {p['id'] for p in self.active(tenant,person)}
        return [{**p, 'active':p['id'] in active_ids} for p in rows]

    def disable(self, tenant, person, preference_id):
        if not self.db.execute('SELECT 1 FROM preferences WHERE tenant=? AND person=? AND id=?',(tenant,person,preference_id)).fetchone():
            raise ValueError('Unknown preference')
        with self.db:
            self.event(tenant,person,'preference_disabled',{'id':preference_id})

    def delete_person(self, tenant, person):
        # Full local purge, including feedback; unlike soft retirement this is irreversible.
        with self.db:
            self.db.execute('DELETE FROM preferences WHERE tenant=? AND person=?', (tenant, person))
            self.db.execute('DELETE FROM events WHERE tenant=? AND person=?', (tenant, person))
            if (tenant,person)==('local','profile'):
                tables={r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                for table in ('comparisons','proposals'):
                    if table in tables:self.db.execute('DELETE FROM '+table)

    def feedback(self, tenant, person, payload):
        if payload.get('action') not in ('accepted','edited','removed','not_selected','explicit_preference'):
            raise ValueError('Invalid feedback action')
        if not payload.get('example_id'):
            raise ValueError('Feedback requires example_id')
        with self.db:
            self.event(tenant, person, 'feedback', payload)
