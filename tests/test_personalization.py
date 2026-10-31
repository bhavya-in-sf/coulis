import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from coulis_core.workflow import Workflow
from coulis_research.personalization import prepare, blind, report, CONDITIONS, digest
from sdk.python.coulis_client import LocalClient

FIXTURE=Path(__file__).resolve().parents[1]/'evals/fixtures/personalization/synthetic.json'

class PersonalizationTests(unittest.TestCase):
    def setUp(self):self.data=json.loads(FIXTURE.read_text())
    def outputs(self,bundle):
        return [{'case_id':c['id'],'condition':k,'text':'Synthetic fixture output '+k,'input_hash':c['input_hashes'][k],'model':'fixture-not-a-model','settings':{'temperature':0}} for c in bundle['cases'] for k in CONDITIONS]
    def test_ablation_and_reference_exclusion(self):
        b=prepare(self.data);c=b['cases'][0];inputs=c['inputs']
        self.assertEqual(inputs['no_profile']['samples'],[])
        self.assertEqual(inputs['samples_only']['preferences'],[])
        self.assertEqual(inputs['samples_only']['samples'],inputs['samples_preferences']['samples'])
        self.assertEqual(inputs['samples_preferences']['preferences'][0]['id'],'p1')
        self.assertEqual(c['coverage']['eligible_samples'],1)
        self.assertNotIn('held-out reference',json.dumps(b))
        self.assertEqual(b,prepare(self.data))
    def test_future_and_wrong_person_evidence_excluded(self):
        for change in ({'at':'2027-01-01T00:00:00Z'},{'user_id':'other'},{'topic':'launch'}):
            data=copy.deepcopy(self.data);data['samples'][0].update(change)
            c=prepare(data)['cases'][0]
            self.assertEqual(c['coverage']['eligible_preferences'],0)
        self.assertEqual(prepare(self.data,'future')['cases'][0]['coverage']['eligible_samples'],2)
    def test_duplicate_reference_and_future_preference_excluded(self):
        self.data['samples'][0]['text']=self.data['tasks'][0]['reference']
        self.assertEqual(prepare(self.data)['cases'][0]['coverage']['eligible_preferences'],0)
        self.data=json.loads(FIXTURE.read_text());self.data['preferences'][0]['approved_at']='2027-01-01T00:00:00Z'
        self.assertEqual(prepare(self.data)['cases'][0]['coverage']['eligible_preferences'],0)
    def test_permissions_and_ids(self):
        self.data['manifest']['allowed_uses']=[]
        with self.assertRaises(ValueError):prepare(self.data)
        self.data=json.loads(FIXTURE.read_text());self.data['samples'].append(self.data['samples'][0])
        with self.assertRaises(ValueError):prepare(self.data)
    def test_blinding_and_output_contract(self):
        b=prepare(self.data);outputs=self.outputs(b);packet,key=blind(b,outputs)
        self.assertEqual(len(packet['trials']),3)
        for trial in packet['trials']:
            self.assertNotIn('conditions',trial);self.assertNotIn('case_id',trial)
        self.assertEqual(key['packet_sha256'],digest(packet))
        for mutation in ({'model':'different'},{'input_hash':'wrong'}):
            changed=copy.deepcopy(outputs);changed[0].update(mutation)
            with self.assertRaises(ValueError):blind(b,changed)
        with self.assertRaises(ValueError):blind(b,outputs[:-1])
    def test_report_ties_missing_and_observation_denominators(self):
        b=prepare(self.data);packet,key=blind(b,self.outputs(b));t=packet['trials'][0]
        ballots=[{'id':t['id'],'choice':'tie','human_confirmed':True,'observations':[{'position':0,'factual_error':False,'final':t['candidates'][0]['text'],'active_edit_seconds':12}]}]
        r=report(key,ballots)
        self.assertEqual(r['missing_pairwise_ballots'],2)
        self.assertEqual(r['comparisons'][0]['ties'],1)
        self.assertEqual(sum(r['comparisons'][0]['win_share_all_ballots'].values()),0)
        self.assertIsNone(r['comparisons'][0]['person_bootstrap_95_interval'])
        self.assertEqual(sum(x['fact_review_count'] for x in r['observations'].values()),1)
        self.assertEqual(sum(x['edited_output_observations'] for x in r['observations'].values()),1)
        self.assertNotIn('Synthetic fixture output',json.dumps(r))
        with self.assertRaises(ValueError):report(key,ballots+ballots)
        ballots[0]['human_confirmed']=False
        with self.assertRaises(ValueError):report(key,ballots)
    def test_person_weighting_and_bootstrap(self):
        b=prepare(self.data);_,key=blind(b,self.outputs(b))
        first=key['trials'][0]
        second={**first,'id':'second-person','user_id':'other-writer'}
        key['trials'].append(second)
        ballots=[{'id':first['id'],'choice':0,'human_confirmed':True},
                 {'id':second['id'],'choice':1,'human_confirmed':True}]
        r=report(key,ballots)['comparisons'][0]
        self.assertEqual(r['people'],2)
        self.assertEqual(list(r['person_macro_win_share'].values()),[.5,.5])
        self.assertIsNotNone(r['person_bootstrap_95_interval'])

    def test_zero_labels_is_not_zero_performance(self):
        b=prepare(self.data);_,key=blind(b,self.outputs(b));r=report(key,[])
        self.assertEqual(r['comparisons'],[])
        self.assertTrue(all(x['factual_error_rate'] is None for x in r['observations'].values()))

class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.c=LocalClient(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def edit(self,draft,final,category='style'):
        return self.c.workflow('edit',task='Post',draft=draft,final=final,category=category,context={'surface':'linkedin'},consent=True)
    def test_evidence_pending_approval_and_idempotence(self):
        edit=self.edit('We build tools — we learn from the people who use them.', 'We build tools, we learn from the people who use them.')
        result=self.c.workflow('extract',comparison_id=edit['id']);p=result['proposals'][0]
        self.assertIsNone(p['confidence']);self.assertFalse(p['approved'])
        self.assertEqual(p['evidence_quotes']['after'],'We build tools, we learn from the people who use them.')
        self.assertEqual(self.c.context('Post')['preferences'],[])
        self.assertEqual(self.c.workflow('extract',comparison_id=edit['id'])['proposals'][0]['id'],p['id'])
        self.c.workflow('approve',proposal_id=p['id'],approved=True)
        self.assertEqual(self.c.context('Post')['preferences'][0]['value'],'avoid')
        self.assertEqual(self.c.context('Post','x')['preferences'],[])
        self.assertEqual(self.c.workflow('extract',comparison_id=edit['id'])['proposals'],[])
    def test_user_can_prefer_em_dashes(self):
        edit=self.edit('We build tools, we learn from the people who use them.', 'We build tools — we learn from the people who use them.')
        p=self.c.workflow('extract',comparison_id=edit['id'])['proposals'][0]
        self.assertEqual(p['value'],'allow')
    def test_facts_numbers_and_semantics_abstain(self):
        for before,after,category in [
            ('There are 10 people who use the product every day.','There are 20 people who use the product every day.','style'),
            ('We write in a very complicated way about the product.','The product makes life easy for all of our customers.','style'),
            ('We build tools — we learn from the people who use them.','We build tools, we learn from the people who use them.','fact')]:
            edit=self.edit(before,after,category)
            self.assertTrue(self.c.workflow('extract',comparison_id=edit['id'])['abstained'])
    def test_variant_pick_is_not_an_edit(self):
        c=self.c.workflow('create',task='Post',candidates=[{'text':'a','condition':'one'},{'text':'b','condition':'two'}],context={'surface':'x'},consent=True)
        self.c.workflow('decide',comparison_id=c['id'],choice=0,category='style')
        self.assertTrue(self.c.workflow('extract',comparison_id=c['id'])['abstained'])
