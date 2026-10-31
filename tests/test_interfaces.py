"""Cross-interface tests: persistent preferences, auth boundary, concurrency and SDK transport."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from api.server import Api, make_handler
from coulis_core import service
from sdk.python.coulis_client import Client, LocalClient, CoulisError

ROOT = Path(__file__).resolve().parents[1]

class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.a, self.b = Path(self.temp.name)/'a', Path(self.temp.name)/'b'
        self.local = LocalClient(self.a)
        self.api = Api({'key-a': {'default': self.a}, 'key-b': {'default': self.b}})
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.api))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.client = Client(self.url, 'key-a')
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(); self.temp.cleanup()
    def approve(self):
        row = self.local.workflow('edit', task='Launch', draft='Excited to announce', final='A customer asked us',
                                  context={'surface':'linkedin','audience':'founders'}, category='style', consent=True)
        proposal = self.client.workflow('propose', comparison_id=row['id'], key='opener', value='example', wording='Lead with an example')
        self.assertEqual(self.client.context('Launch')['preferences'], [])
        return self.client.workflow('approve', proposal_id=proposal['id'], approved=True)
    def test_full_loop_across_local_rest_cli_mcp(self):
        pref = self.approve()
        args = {'text':'Unseen topic','surface':'linkedin','context':{'audience':'founders'}}
        remote = self.client.call('context', **args)
        self.assertEqual(remote['preferences'][0]['id'], pref['id'])
        self.assertEqual(remote, self.local.call('context', **args))
        self.assertEqual(remote, service._dispatch.call_tool('coulis_context', {**args,'profile_dir':str(self.a)}))
        proc = subprocess.run([sys.executable, 'scripts/coulis.py', 'context', json.dumps(args), '--profile', str(self.a)], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(remote, json.loads(proc.stdout))
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY':'','ANTHROPIC_AUTH_TOKEN':''}):
            critique = self.client.critique('Unseen topic', context={'audience':'founders'})
        self.assertIn('Lead with an example', critique['task'])
        self.assertEqual(self.client.context('Other', surface='x')['preferences'], [])
        self.client.workflow('disable', preference_id=pref['id'])
        self.assertEqual(self.local.call('context', **args)['preferences'], [])
    def test_authorization_and_no_path_override(self):
        self.approve()
        self.assertEqual(Client(self.url, 'key-b').workflow('state')['preferences'], [])
        for client, operation, args, status in [
            (Client(self.url, 'wrong'),'profile',{},401),
            (Client(self.url,'key-b','../a'),'profile',{},404),
            (self.client,'profile',{'profile_dir':str(self.b)},400),
            (self.client,'workflow',{'action':'purge','arguments':{}},400),
        ]:
            with self.assertRaises(CoulisError) as error: client.call(operation, **args)
            self.assertEqual(error.exception.status, status)
        status, _ = self.api.dispatch('POST','/v1/profile',{'authorization':'Bearer key-a'},b'[]')
        self.assertEqual(status,400)
    def test_concurrent_profile_overrides_are_request_local(self):
        barrier = threading.Barrier(2)
        def probe(name, args):
            barrier.wait(timeout=3)
            return str(service._dispatch.profile_dir())
        with patch.object(service._dispatch, '_call_tool', probe):
            with ThreadPoolExecutor(2) as pool:
                results = list(pool.map(lambda folder: LocalClient(folder).call('profile'), [self.a,self.b]))
        self.assertEqual(results,[str(self.a.resolve()),str(self.b.resolve())])
    def test_variants_and_fact_edits(self):
        row = self.client.workflow('create', task='Hook', candidates=[{'text':str(i),'condition':str(i)} for i in range(3)], context={'surface':'x'}, consent=True)
        self.assertNotIn('conditions',row)
        self.client.workflow('decide',comparison_id=row['id'],choice=2,category='style')
        self.assertEqual(self.local.workflow('view',comparison_id=row['id'])['decision']['choice'],2)
        row = self.client.workflow('edit', task='Fix fact', draft='10 customers', final='20 customers', context={'surface':'x'},category='fact',consent=True)
        with self.assertRaises(CoulisError):
            self.client.workflow('propose',comparison_id=row['id'],key='numbers',value='larger',wording='Use larger numbers')
    def test_concurrent_approval_is_atomic(self):
        row = self.local.workflow('edit',task='Task',draft='a',final='b',context={'surface':'x'},category='style',consent=True)
        p = self.local.workflow('propose',comparison_id=row['id'],key='tone',value='direct',wording='Be direct')
        def approve(_):
            try:
                self.client.workflow('approve',proposal_id=p['id'],approved=True)
                return 200
            except CoulisError as e: return e.status
        with ThreadPoolExecutor(2) as pool: results = list(pool.map(approve, range(2)))
        self.assertEqual(sorted(results),[200,400])
        state = self.local.workflow('state')
        self.assertEqual(len(state['preferences']),1)
        self.assertEqual(state['proposals'],[])

    def test_concurrent_extraction_does_not_duplicate_proposals(self):
        row=self.client.workflow('edit',task='Post',draft='We build tools — we learn from the people who use them.',final='We build tools, we learn from the people who use them.',context={'surface':'x'},category='style',consent=True)
        with ThreadPoolExecutor(2) as pool:
            results=list(pool.map(lambda _:self.client.workflow('extract',comparison_id=row['id']),range(2)))
        self.assertEqual(results[0]['proposals'][0]['id'],results[1]['proposals'][0]['id'])
        self.assertEqual(len(self.local.workflow('state')['proposals']),1)

    def test_typescript_against_real_http_server(self):
        node = os.environ.get('COULIS_TEST_NODE')
        if not node: self.skipTest('Set COULIS_TEST_NODE to run TypeScript against the real HTTP API')
        result = subprocess.run([node,'--experimental-strip-types','sdk/typescript/test.mts', self.url],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
