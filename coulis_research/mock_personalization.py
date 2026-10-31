"""Full synthetic exercise, not model evaluation: python -m coulis_research.mock_personalization --output private/mock-run"""
import argparse
import json
from pathlib import Path
import tempfile
from .personalization import prepare, blind, report, CONDITIONS, digest
from sdk.python.coulis_client import LocalClient


def dataset():
    data={'manifest':{'version':'mock-six-writers-v1','allowed_uses':['research_evaluation'],'synthetic':True},
          'samples':[],'preferences':[],'tasks':[]}
    for i in range(6):
        u=f'mock-writer-{i}';sid=f'{u}-history'
        reference=f'Private reference marker for fictional writer {i}, never a generation input.'
        data['samples'] += [
            {'id':sid,'user_id':u,'topic':'hiring','at':'2026-01-01T00:00:00Z','text':f'Writer {i}: building useful tools starts with listening. Our product launch follows customer questions.'},
            {'id':u+'-same-topic','user_id':u,'topic':'launch','at':'2026-01-02T00:00:00Z','text':f'Writer {i}: a launch is a promise to keep improving our tools for customers.'},
            {'id':u+'-future','user_id':u,'topic':'later','at':'2027-01-01T00:00:00Z','text':'FUTURE LEAK SENTINEL: build product launch'},
            {'id':u+'-duplicate','user_id':u,'topic':'old','at':'2026-01-02T00:00:00Z','text':reference}]
        def pref(suffix, **extra):
            return {'id':u+suffix,'user_id':u,'key':'punctuation','value':'avoid' if i%2==0 else 'allow',
                    'text':'Avoid em dashes.' if i%2==0 else 'Em dashes are welcome.',
                    'scope':{'surface':'linkedin'},'approved':True,'approved_at':'2026-01-03T00:00:00Z',
                    'evidence_ids':[sid],**extra}
        data['preferences'] += [pref('-preference'),pref('-unapproved',approved=False),
            pref('-future-pref',approved_at='2027-01-01T00:00:00Z'),
            pref('-expired',expires_at='2026-01-15T00:00:00Z'),
            pref('-disabled',disabled_at='2026-01-15T00:00:00Z'),
            pref('-email',key='email_only',scope={'surface':'cold_email'},text='EMAIL ONLY SENTINEL')]
        if i==1:data['preferences'].append(pref('-conflict',value='avoid',text='Avoid em dashes.'))
        for j,topic in enumerate(('launch','support','pricing','research')):
            data['tasks'].append({'id':f'{u}-task-{j}','user_id':u,'topic':topic,'at':'2026-02-01T00:00:00Z',
                'task':f'Write a short {topic} update about building tools for customers.',
                'context':{'surface':'linkedin'},'approved_facts':['The pilot has 10 participants.'],'reference':reference})
    return data


def run(output):
    root=Path(output)
    if root.exists():raise ValueError('Use a new output directory')
    root.mkdir(parents=True)
    def save(name,value):
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+'\n')
    checks=[]
    def check(name,passed):
        checks.append({'check':name,'passed':bool(passed)})
        if not passed:raise AssertionError(name)
    # Real product calls on disposable profiles, with fictional content only.
    with tempfile.TemporaryDirectory() as tmp:
        clients=[LocalClient(Path(tmp)/str(i)) for i in range(6)]
        for i,c in enumerate(clients):
            comma='We build useful tools, we learn from the people who use them.'
            dash='We build useful tools — we learn from the people who use them.'
            before,after=(dash,comma) if i%2==0 else (comma,dash)
            edit=c.workflow('edit',task='Mock post',draft=before,final=after,context={'surface':'linkedin'},category='style',consent=True)
            proposals=c.workflow('extract',comparison_id=edit['id'])['proposals']
            check(f'writer_{i}_pending_has_no_effect',not c.context('New topic')['preferences'])
            p=proposals[0];c.workflow('approve',proposal_id=p['id'],approved=True)
            check(f'writer_{i}_approval_applies',c.context('New topic')['preferences'][0]['value']==('avoid' if i%2==0 else 'allow'))
            check(f'writer_{i}_surface_isolation',not c.context('New topic','cold_email')['preferences'])
            check(f'writer_{i}_resolved_not_reproposed',not c.workflow('extract',comparison_id=edit['id'])['proposals'])
        c=clients[0];p=c.workflow('state')['preferences'][0]
        revision=c.workflow('revise',preference_id=p['id'],value='allow',wording='Em dashes are welcome.')
        c.workflow('approve',proposal_id=revision['id'],approved=True)
        check('revision_retires_old_preference',len(c.context('New topic')['preferences'])==1 and c.context('New topic')['preferences'][0]['value']=='allow')
        c.workflow('disable',preference_id=revision['id'])
        check('disable_removes_preference',not c.context('New topic')['preferences'])
        check('other_writer_unaffected',len(clients[1].context('New topic')['preferences'])==1)
        correction=c.workflow('edit',task='Mock facts',draft='The pilot has 10 participants who use the product every day.',final='The pilot has 20 participants who use the product every day.',context={'surface':'linkedin'},category='style',consent=True)
        check('numeric_change_abstains',c.workflow('extract',comparison_id=correction['id'])['abstained'])
        c.workflow('purge',approved=True)
        check('purge_clears_workflow',not c.workflow('state')['comparisons'])
    data=dataset();save('dataset.json',data);summaries=[]
    for split in ('unseen_topic','future'):
        b=prepare(data,split);save(f'{split}/bundle.json',b)
        for case in b['cases']:
            inputs=case['inputs'];personal=inputs['samples_preferences']
            check(f"{split}:{case['id']}:no_future_or_reference_leak",'FUTURE LEAK' not in json.dumps(inputs) and 'Private reference marker' not in json.dumps(inputs))
            check(f"{split}:{case['id']}:no_cross_writer_samples",all(s['id'].startswith(case['user_id']+'-') for s in personal['samples']))
            check(f"{split}:{case['id']}:context_and_status_filter",all(p['id']==case['user_id']+'-preference' for p in personal['preferences']))
            if case['user_id']=='mock-writer-1':check(f"{split}:{case['id']}:conflict_visible",personal['conflicts']==['punctuation'] and personal['preferences']==[])
            if split=='unseen_topic' and case['topic']=='launch':check(f"{split}:{case['id']}:topic_holdout",all(not s['id'].endswith('same-topic') for s in personal['samples']))
        outputs=[]
        for n,case in enumerate(b['cases']):
            for k,condition in enumerate(CONDITIONS):
                # Deliberately scripted outputs: condition differences are not learned behavior.
                prefix=['We have news.','A customer asked us to build this.','We built this after a customer asked.'][k]
                participants=999 if (n*3+k)%17==0 else 10 # injected regression to exercise review accounting
                outputs.append({'case_id':case['id'],'condition':condition,'input_hash':case['input_hashes'][condition],
                    'text':f'{prefix} The pilot has {participants} participants.',
                    'model':'mock-template-v1-not-an-LLM','settings':{'fixture':True,'seed':0}})
        save(f'{split}/outputs.json',outputs)
        packet,key=blind(b,outputs);save(f'{split}/reviewer.json',packet);save(f'{split}/conditions-private.json',key)
        check(f'{split}:condition_labels_hidden',all('conditions' not in t and 'case_id' not in t for t in packet['trials']))
        ballots=[]
        # Use stable case/pair order despite random left/right presentation.
        for n,t in enumerate(key['trials']):
            if n%13==0:continue # intentionally absent judgments
            choice=(0,1,'tie','neither')[n%4]
            obs=[]
            for pos,body in enumerate(t['texts']):
                o={'position':pos}
                if n%3!=0:o.update(factual_error='999' in body,final=body.replace('999','10'))
                if n%4!=0:o['active_edit_seconds']=20+n%7
                if len(o)>1:obs.append(o)
            ballots.append({'id':t['id'],'choice':choice,'simulated':True,'human_confirmed':False,'observations':obs})
        save(f'{split}/simulated-ballots.json',ballots)
        r=report(key,ballots,simulated=True);save(f'{split}/report.json',r)
        check(f'{split}:missing_ballots_preserved',r['missing_pairwise_ballots']==6)
        check(f'{split}:ties_and_neither_preserved',sum(g['ties'] for g in r['comparisons'])>0 and sum(g['neither'] for g in r['comparisons'])>0)
        check(f'{split}:simulated_factual_regressions_visible',any((m['factual_error_rate'] or 0)>0 for m in r['observations'].values()))
        check(f'{split}:unknown_fact_reviews_not_counted',sum(m['fact_review_count'] for m in r['observations'].values())<len(ballots)*2)
        try:report(key,ballots)
        except ValueError:rejected=True
        else:rejected=False
        check(f'{split}:simulation_cannot_be_human_results',rejected)
        summaries.append({'split':split,'tasks':len(b['cases']),'mock_outputs':len(outputs),'pairwise_trials':len(key['trials']),
                          'simulated_ballots':len(ballots),'intentionally_missing':r['missing_pairwise_ballots'],
                          'ties':sum(g['ties'] for g in r['comparisons']),'neither':sum(g['neither'] for g in r['comparisons'])})
    summary={'version':'mock-run-v1','synthetic':True,'model_calls':0,'human_judgments':0,'writers':6,
             'dataset_sha256':digest(data),'splits':summaries,'checks_passed':len(checks),'checks':checks,
             'effectiveness_measured':False,'conclusion':'Software exercise passed. Outputs, choices, editing times and fact reviews are scripted. No product-quality or time-saving claim follows.'}
    save('summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args()
    summary=run(a.output)
    print(json.dumps({k:v for k,v in summary.items() if k!='checks'},indent=2))

if __name__=='__main__':main()
