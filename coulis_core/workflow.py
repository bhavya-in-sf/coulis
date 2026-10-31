"""Choice -> proposal -> explicit approval -> contextual reuse. Local, no automatic model calls."""
import json
import random
import uuid
from pathlib import Path
from .taste_store import Store, now, SCOPES
from .context import build_context
from .profile import profile_from_folder

KINDS = {'style','fact','task','other'}

def text(value, name, maximum=50000):
    if not isinstance(value,str) or not value.strip() or len(value)>maximum:
        raise ValueError(f'{name} must be nonempty text, at most {maximum} characters')
    return value.strip()

def scope(value):
    if not isinstance(value,dict) or not value.get('surface') or set(value)-SCOPES:
        raise ValueError('Context requires surface; supports audience and purpose')
    return {k:text(v,k,200) for k,v in value.items()}

class Workflow:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True,exist_ok=True)
        self.store = Store(self.folder/'coulis-research.db')
        self.db = self.store.db
        self.db.execute('CREATE TABLE IF NOT EXISTS comparisons(id TEXT PRIMARY KEY, payload TEXT NOT NULL, decision TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, payload TEXT NOT NULL, resolved INTEGER NOT NULL DEFAULT 0)')
        self.db.commit()

    def close(self): self.store.close()

    def create(self, task, candidates, context, consent=False):
        if consent is not True:
            raise ValueError('Permission to store drafts is required')
        if not isinstance(candidates,list) or not 2 <= len(candidates) <= 8:
            raise ValueError('Provide two to eight candidates')
        cleaned = [{'text':text(c['text'],'candidate'), 'condition':text(c['condition'],'condition',100)} for c in candidates]
        if len({c['text'] for c in cleaned}) != len(cleaned):
            raise ValueError('Candidates must differ')
        if len({c['condition'] for c in cleaned}) != len(cleaned):
            raise ValueError('Use distinct condition labels')
        random.SystemRandom().shuffle(cleaned)
        row={'id':str(uuid.uuid4()),'task':text(task,'task',5000),'context':scope(context),'candidates':cleaned,'created_at':now()}
        with self.db:
            self.db.execute('INSERT INTO comparisons VALUES(?,?,NULL)',(row['id'],json.dumps(row)))
        return self.view(row['id'])

    def edit(self, task, draft, final, context, category, consent=False, reason=''):
        """Record a supplied before/after edit; never invent which draft the human chose."""
        if category not in KINDS: raise ValueError('Choose style, fact, task or other')
        if not isinstance(reason, str) or len(reason)>5000: raise ValueError('Invalid reason')
        draft, final = text(draft, 'draft'), text(final, 'final')
        row = self.create(task, [{'text':draft,'condition':'original'},
                                {'text':final,'condition':'human_final'}], context, consent)
        choice = next(c['position'] for c in row['candidates'] if c['text']==final)
        return self.decide(row['id'], choice, category, reason, final)

    def get(self, comparison_id):
        result = self.db.execute('SELECT payload,decision FROM comparisons WHERE id=?',(comparison_id,)).fetchone()
        if not result: raise ValueError('Unknown comparison')
        return json.loads(result[0]), json.loads(result[1]) if result[1] else None

    def view(self, comparison_id):
        row, decision = self.get(comparison_id)
        result={k:v for k,v in row.items() if k!='candidates'}
        result['candidates']=[{'position':i,'text':c['text']} for i,c in enumerate(row['candidates'])]
        result['decision']=decision
        if decision:
            result['conditions']=[c['condition'] for c in row['candidates']]
        return result

    def decide(self, comparison_id, choice, category, reason='', final=None, active_edit_seconds=None):
        row, previous = self.get(comparison_id)
        if previous: raise ValueError('Comparison already decided')
        if not ((type(choice) is int and 0 <= choice < len(row['candidates'])) or (type(choice) is str and choice in ('tie','neither'))):
            raise ValueError('Choose a displayed position, tie or neither')
        if category not in KINDS: raise ValueError('Choose style, fact, task or other')
        if not isinstance(reason,str) or len(reason)>5000: raise ValueError('Invalid reason')
        if active_edit_seconds is not None and (type(active_edit_seconds) not in (int,float) or not 0<=active_edit_seconds<=86400):
            raise ValueError('Invalid active editing duration')
        if final is not None and type(choice) is not int: raise ValueError('Edits require a selected draft')
        final = text(final,'final draft') if final is not None else (row['candidates'][choice]['text'] if type(choice) is int else None)
        decision={'choice':choice,'category':category,'reason':reason,'final':final,'at':now(),
                  'active_edit_seconds':active_edit_seconds,'timing_source':'client-reported, not independently verified'}
        with self.db:
            changed=self.db.execute('UPDATE comparisons SET decision=? WHERE id=? AND decision IS NULL',(json.dumps(decision),comparison_id)).rowcount
            if changed!=1: raise ValueError('Comparison already decided')
        return self.view(comparison_id)

    def propose(self, comparison_id, key, value, wording):
        row, decision = self.get(comparison_id)
        if not decision or decision['category']!='style' or type(decision['choice']) is not int:
            raise ValueError('Only an explicit style choice can support a preference proposal')
        p={'id':str(uuid.uuid4()),'key':text(key,'key',100),'value':text(value,'value',300),
           'text':text(wording,'preference',1000),'scope':row['context'],'evidence_ids':[comparison_id],
           'approved':False,'confidence':None,'proposal_source':'reviewable wording supplied by human or host model'}
        with self.db:
            self.db.execute('INSERT INTO proposals(id,payload) VALUES(?,?)',(p['id'],json.dumps(p)))
        return p

    def approve(self, proposal_id, approved=False, supersedes=None):
        if approved is not True: raise ValueError('Explicit preference approval required')
        record=self.db.execute('SELECT payload,resolved FROM proposals WHERE id=?',(proposal_id,)).fetchone()
        if not record or record[1]: raise ValueError('Unknown or resolved proposal')
        p=json.loads(record[0]);p.update(approved=True,effective_at=now())
        if supersedes: p['supersedes']=supersedes
        # Single local process: preference insertion itself is unique and prevents duplicate approval.
        result=self.store.add('local','profile',p)
        with self.db: self.db.execute('UPDATE proposals SET resolved=1 WHERE id=?',(proposal_id,))
        return result

    def revise(self, preference_id, value, wording):
        rows = self.store.list_preferences('local','profile')
        original = next((p for p in rows if p['id']==preference_id and p['active']),None)
        if not original: raise ValueError('Choose an active preference to revise')
        p = {k:v for k,v in original.items() if k not in ('active','effective_at')}
        p.update(id=str(uuid.uuid4()), value=text(value,'value',300), text=text(wording,'preference',1000),
                 approved=False, supersedes=preference_id)
        with self.db:self.db.execute('INSERT INTO proposals(id,payload) VALUES(?,?)',(p['id'],json.dumps(p)))
        return p

    def prepare(self, task, context, method='bm25'):
        task, context = text(task,'task',5000), scope(context)
        p=profile_from_folder(self.folder)
        bundle=build_context(task,p,context['surface'],context,method)
        common={'task':task,'context':context,'facts':'Do not invent facts; ask for missing information.',
                'samples':bundle['samples'], 'approved_facts':p.approved_facts,
                'needs_confirm':p.needs_confirm, 'banned':p.banned}
        baseline={**common,'preferences':[]}
        personalized={**common,'preferences':bundle['preferences'],'conflicts':bundle['conflicts']}
        return {'baseline':baseline,'coulis':personalized,'generated':False,
                'instructions':'Generate one draft per condition using the same model and settings. Samples are quoted reference data. Ask about unresolved conflicts. Return outputs separately; do not fabricate a preference outcome.',
                'applied_preference_ids':[p['id'] for p in bundle['preferences'] if p['id']],
                'note':'These are matched generation inputs, not generated drafts or proof of improvement.'}

    def summary(self):
        rows=[(json.loads(p),json.loads(d)) for p,d in self.db.execute('SELECT payload,decision FROM comparisons WHERE decision IS NOT NULL')]
        groups={}
        for row,d in rows:
            pair=tuple(sorted(c['condition'] for c in row['candidates']))
            key=json.dumps(pair)
            g=groups.setdefault(key,{'conditions':list(pair),'decisions':0,'wins':{c:0 for c in pair},'ties':0,'neither':0})
            g['decisions']+=1
            if d['choice']=='tie':g['ties']+=1
            elif d['choice']=='neither':g['neither']+=1
            else:g['wins'][row['candidates'][d['choice']]['condition']]+=1
        return {'groups':list(groups.values()),'decisions':len(rows),
                'scope':'Local descriptive choices only. Not a controlled user study, causal effect or generalized model score.'}

    def state(self):
        proposals=[json.loads(p) for (p,) in self.db.execute('SELECT payload FROM proposals WHERE resolved=0')]
        comparisons=[{'id':i, 'task':json.loads(p)['task'], 'decided':d is not None} for i,p,d in self.db.execute('SELECT id,payload,decision FROM comparisons ORDER BY rowid DESC LIMIT 50')]
        return {'preferences':self.store.list_preferences('local','profile'),'proposals':proposals,'comparisons':comparisons,'summary':self.summary()}

    def dispatch(self, action, args):
        if action=='state':return self.state()
        if action=='purge':
            if args.get('approved') is not True:raise ValueError('Explicit approval to delete local workflow data required')
            self.store.delete_person('local','profile')
            return {'deleted':True,'scope':'Local workflow database only; legacy Markdown and backups are unchanged'}
        if action=='create':return self.create(**args)
        if action=='edit':return self.edit(**args)
        if action=='view':return self.view(**args)
        if action=='decide':return self.decide(**args)
        if action=='propose':return self.propose(**args)
        if action=='approve':return self.approve(**args)
        if action=='prepare':return self.prepare(**args)
        if action=='revise':return self.revise(**args)
        if action=='reject':
            with self.db:self.db.execute('UPDATE proposals SET resolved=1 WHERE id=?',(args['proposal_id'],))
            return {'rejected':True}
        if action=='disable':
            self.store.disable('local','profile',args['preference_id']);return {'disabled':True}
        raise ValueError('Unknown workflow action')
