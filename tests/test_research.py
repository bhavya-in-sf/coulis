import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from coulis_core.profile import Profile, Rule
from coulis_core.context import build_context
from coulis_core.critique import build_prompt
from coulis_core.retrieval import retrieve
from coulis_research.data import adapt, audit, user_split, manifest
from coulis_research.evaluate import evaluate
from coulis_research.store import Store

ROOT = Path(__file__).resolve().parents[1]

class RetrievalTests(unittest.TestCase):
    def test_selection_and_no_overlap_abstention(self):
        docs = [{'id':'a','text':'sourdough starter bread'},{'id':'b','text':'databases transactions indexes'}]
        for method in ('bm25','tfidf'):
            self.assertEqual(retrieve('sourdough bread',docs,1,method)[0]['id'],'a')
            self.assertEqual(retrieve('waterfall',docs,1,method),[])
        self.assertEqual(retrieve('bread',docs,1,'none'),[])

    def test_existing_critic_uses_shared_context(self):
        p = Profile(samples=['six cats','bread starter'],rules=[Rule(text='Short posts',scope={'surface':'x'})])
        b = build_context('bread',p,'x',method='bm25',k=1)
        self.assertEqual(b['samples'][0]['text'],'bread starter')
        self.assertEqual(b['preferences'][0]['text'],'Short posts')
        prompt = build_prompt('bread',p,'x',retrieval_method='bm25')
        self.assertIn('bread starter',prompt)
        self.assertNotIn('six cats',prompt)
        self.assertIn('six cats',build_prompt('bread',p,'x',retrieval_method='original'))

    def test_evaluation_does_not_score_missing_labels(self):
        row = {'id':'a','user_id':'u','source':'lamp','task':'personalized_generation','query':'bread','documents':[], 'relevant_ids':None}
        result = evaluate([row])
        self.assertIsNone(result['mean_recall_at_k'])
        self.assertEqual(result['scored_queries'],0)

class AdapterTests(unittest.TestCase):
    def test_longmemeval_labels_never_leak(self):
        row = dict(question_id='q',question_type='update',question='What?',answer='SECRET GOLD',question_date='date',
                   haystack_session_ids=['s'],haystack_dates=['date'],answer_session_ids=['s'],
                   haystack_sessions=[[{'role':'user','content':'hello','has_answer':True}]])
        result = adapt([row],{'source':'longmemeval','version':'1'})[0]
        self.assertEqual(result['documents'][0]['text'],'user: hello')
        self.assertNotIn('SECRET',json.dumps(result['documents']))
        self.assertNotIn('has_answer',json.dumps(result['documents']))
        row['haystack_session_ids'] *= 2
        row['haystack_dates'] *= 2
        row['haystack_sessions'] *= 2
        dedup = adapt([row],{'source':'longmemeval','version':'1'})[0]
        self.assertEqual(len(dedup['documents']),1)
        self.assertEqual(dedup['metadata']['duplicate_sessions_collapsed'],1)
        row['haystack_dates']=[]
        with self.assertRaises(ValueError): adapt([row],{'source':'longmemeval','version':'1'})

    def test_lamp_profile_and_no_invented_user(self):
        rows = [{'id':'q','input':'write','profile':[{'id':'p','text':'sample'}]}]
        x = adapt(rows,{'source':'lamp','version':'1'})[0]
        self.assertEqual(x['user_id'],'q')
        self.assertIsNone(x['reference'])
        with self.assertRaises(ValueError): adapt(rows+rows,{'source':'lamp','version':'1'})

    def test_observations_do_not_become_preference_pairs(self):
        prism = adapt([{'conversation_id':'c','user_id':'u','opening_prompt':'hi','conversation_history':[]}],{'source':'prism','version':'1'})[0]
        self.assertEqual(prism['task'],'interaction_observation')
        self.assertNotIn('rejected',prism)
        co = adapt([{'session_id':'s','writer_id':'u','events':[{'type':'dismiss'}]}],{'source':'coauthor','version':'1'})[0]
        self.assertEqual(co['metadata']['events'],[{'type':'dismiss'}])
        self.assertEqual(evaluate([prism,co])['queries'],0)

    def test_split_and_duplicates(self):
        self.assertEqual(user_split('lamp','u'),user_split('lamp','u'))
        rows = [{'source':'lamp','user_id':u,'documents':[{'text':'SAME  text'}]} for u in ('a','b')]
        self.assertEqual(len(audit(rows)['duplicate_cross_group_documents']),1)

    def test_manifest_requires_declared_use(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.json';p.write_text(json.dumps({'source':'lamp','version':'v','url':'u','license':'unknown','allowed_uses':['training']}))
            with self.assertRaises(ValueError): manifest(p)

class StoreTests(unittest.TestCase):
    def setUp(self): self.s=Store(':memory:')
    def tearDown(self): self.s.close()
    def add(self, **kw):
        return self.s.add('t','u',dict(key='tone',value='direct',text='Be direct',approved=True,effective_at='2026-01-01T00:00:00Z',**kw))

    def test_tenant_and_person_isolation(self):
        self.add(id='a')
        self.assertEqual(len(self.s.select('t','u')['selected']),1)
        self.assertEqual(self.s.select('other','u')['selected'],[])
        self.assertEqual(self.s.select('t','other')['selected'],[])

    def test_pending_future_expired_not_selected(self):
        for ident,fields in [('pending',{'approved':False}),('future',{'effective_at':'2099-01-01T00:00:00Z'}),('expired',{'expires_at':'2026-01-02T00:00:00Z'})]:
            p=dict(id=ident,key='tone',value='direct',text='Direct',approved=True,effective_at='2026-01-01T00:00:00Z');p.update(fields)
            self.s.add('t','u',p)
        self.assertEqual(self.s.select('t','u',at='2026-10-31T00:00:00Z')['selected'],[])

    def test_scope_conflict_and_supersession(self):
        self.add(id='a')
        self.s.add('t','u',dict(id='b',key='tone',value='warm',text='Warm',approved=True,scope={},effective_at='2026-02-01T00:00:00Z'))
        self.assertEqual(len(self.s.select('t','u')['conflicts']),1)
        self.s.add('t','u',dict(id='c',key='tone',value='direct',text='Direct',approved=True,scope={},supersedes='b',effective_at='2026-03-01T00:00:00Z'))
        self.assertEqual(self.s.select('t','u')['conflicts'],[])
        self.add(id='specific',scope={'surface':'x'})
        self.assertEqual(self.s.select('t','u',{'surface':'x'})['selected'][0]['id'],'specific')
        with self.assertRaises(ValueError): self.add(id='bad',supersedes='specific')

    def test_purge_and_feedback_no_implicit_learning(self):
        self.add(id='a')
        self.s.feedback('t','u',{'example_id':'e','action':'not_selected'})
        self.assertEqual(len(self.s.select('t','u')['selected']),1)
        self.s.delete_person('t','u')
        self.assertEqual(self.s.select('t','u')['selected'],[])
        self.assertEqual(self.s.db.execute('SELECT COUNT(*) FROM events').fetchone()[0],0)

    def test_mcp_existing_entrypoint(self):
        spec=importlib.util.spec_from_file_location('research_mcp',ROOT/'mcp/server.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as d:
            Path(d,'TASTE.md').write_text('# Taste\n## My voice in 3 samples\n### Sample 1\nbread starter\n')
            out=m.call_tool('coulis_context',{'profile_dir':d,'text':'bread'})
            self.assertEqual(out['samples'][0]['id'],'sample-1')
            with self.assertRaises(ValueError): m.call_tool('coulis_feedback',{'profile_dir':d,'approved':False,'example_id':'e','action':'accepted'})
            out=m.call_tool('coulis_feedback',{'profile_dir':d,'approved':True,'example_id':'e','action':'accepted'})
            self.assertTrue(out['saved'])
            self.assertFalse(out['model_trained'])
