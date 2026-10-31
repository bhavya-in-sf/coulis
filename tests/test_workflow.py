import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from http.server import HTTPServer
from coulis_core.workflow import Workflow
from coulis_core.profile import profile_from_folder
from coulis_core.critique import build_prompt
from coulis_core.context import build_context

ROOT=Path(__file__).resolve().parents[1]
class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.w=Workflow(self.tmp.name)
    def tearDown(self): self.w.close();self.tmp.cleanup()
    def comparison(self,category='style'):
        c=self.w.create('Launch post',[{'text':'Excited to share our launch.','condition':'base'},{'text':'A customer asked. We built it.','condition':'coulis'}],{'surface':'linkedin','audience':'founders'},True)
        self.assertNotIn('condition',c['candidates'][0]);self.assertNotIn('conditions',c)
        self.w.decide(c['id'],0,category,'More direct')
        return c
    def approved(self):
        c=self.comparison();p=self.w.propose(c['id'],'opener','example','Lead with an example')
        self.assertEqual(profile_from_folder(self.tmp.name).rules,[])
        return self.w.approve(p['id'],True)
    def test_full_loop_context_and_reload(self):
        p=self.approved()
        result=self.w.prepare('A new topic',{'surface':'linkedin','audience':'founders'})
        self.assertIn(p['id'],result['applied_preference_ids'])
        self.assertEqual(result['baseline']['preferences'],[])
        self.assertEqual(result['baseline']['samples'],result['coulis']['samples'])
        self.assertFalse(result['generated'])
        self.assertEqual(self.w.prepare('Other',{'surface':'cold_email'})['applied_preference_ids'],[])
        profile=profile_from_folder(self.tmp.name)
        self.assertIn('Lead with an example',build_prompt('A new topic',profile,'linkedin',{'audience':'founders'}))
        self.assertNotIn('Lead with an example',profile.to_files()['TASTE.md'])
    def test_no_implicit_consent_or_approval(self):
        with self.assertRaises(ValueError):self.w.create('Task',[],{'surface':'x'})
        c=self.comparison();p=self.w.propose(c['id'],'opener','example','Example first')
        with self.assertRaises(ValueError):self.w.approve(p['id'],False)
        self.assertEqual(profile_from_folder(self.tmp.name).rules,[])
    def test_facts_ties_and_duplicate_decisions(self):
        c=self.comparison('fact')
        with self.assertRaises(ValueError):self.w.propose(c['id'],'tone','warm','Be warm')
        with self.assertRaises(ValueError):self.w.decide(c['id'],1,'style')
        c=self.w.create('Task',[{'text':'a','condition':'base'},{'text':'b','condition':'coulis'}],{'surface':'x'},True)
        self.w.decide(c['id'],'tie','style')
        with self.assertRaises(ValueError):self.w.propose(c['id'],'tone','warm','Be warm')
        self.assertEqual(sum(g['ties'] for g in self.w.summary()['groups']),1)
    def test_revision_and_disable_reach_product(self):
        p=self.approved();pending=self.w.revise(p['id'],'question','Open with a question')
        self.assertEqual(profile_from_folder(self.tmp.name).rules[0].text,p['text'])
        new=self.w.approve(pending['id'],True)
        self.assertEqual([r.text for r in profile_from_folder(self.tmp.name).rules],['Open with a question'])
        self.w.dispatch('disable',{'preference_id':new['id']})
        self.assertEqual(profile_from_folder(self.tmp.name).rules,[])
    def test_conflicts_visible_and_other_profile_isolated(self):
        self.approved();c=self.comparison();p=self.w.propose(c['id'],'opener','question','Open with a question');self.w.approve(p['id'],True)
        result=self.w.prepare('Task',{'surface':'linkedin','audience':'founders'})
        self.assertEqual(result['coulis']['conflicts'],['opener'])
        self.assertEqual(result['applied_preference_ids'],[])
        with tempfile.TemporaryDirectory() as other:self.assertEqual(profile_from_folder(other).rules,[])
    def test_editing_does_not_invent_training_pairs(self):
        c=self.w.create('Task',[{'text':'a','condition':'base'},{'text':'b','condition':'coulis'}],{'surface':'x'},True)
        out=self.w.decide(c['id'],1,'task',final='A new version')
        self.assertEqual(out['decision']['final'],'A new version')
        self.assertEqual(self.w.state()['proposals'],[])

    def test_full_workflow_purge(self):
        self.approved()
        with self.assertRaises(ValueError):self.w.dispatch('purge',{'approved':False})
        self.w.dispatch('purge',{'approved':True})
        state=self.w.state()
        self.assertEqual(state['preferences'],[])
        self.assertEqual(state['comparisons'],[])
        self.assertEqual(state['proposals'],[])

    def test_mcp_profile_and_workflow_share_memory(self):
        p=self.approved()
        spec=importlib.util.spec_from_file_location('workflow_mcp',ROOT/'mcp/server.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        result=m.call_tool('coulis_context',{'profile_dir':self.tmp.name,'text':'New task','surface':'linkedin','context':{'audience':'founders'}})
        self.assertEqual(result['preferences'][0]['id'],p['id'])
        state=m.call_tool('coulis_workflow',{'profile_dir':self.tmp.name,'action':'state'})
        self.assertEqual(state['preferences'][0]['id'],p['id'])

class LocalServerTests(unittest.TestCase):
    def test_token_origin_and_workflow(self):
        spec=importlib.util.spec_from_file_location('loop_server',ROOT/'scripts/taste_loop.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        with tempfile.TemporaryDirectory() as folder:
            server=HTTPServer(('127.0.0.1',0),m.make_handler(folder,'test-secret'));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            url=f'http://127.0.0.1:{server.server_port}'
            try:
                with urllib.request.urlopen(url) as r:self.assertIn(b'test-secret',r.read())
                for headers in ({},{'X-Coulis-Token':'test-secret','Origin':'https://evil.example'}):
                    req=urllib.request.Request(url+'/api',data=b'{"action":"state"}',headers=headers)
                    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(req)
                    self.assertEqual(e.exception.code,403)
                    e.exception.close()
                req=urllib.request.Request(url+'/api',data=b'{"action":"state"}',headers={'X-Coulis-Token':'test-secret'})
                with urllib.request.urlopen(req) as r:self.assertEqual(json.load(r)['preferences'],[])
            finally:server.shutdown();server.server_close();thread.join()
