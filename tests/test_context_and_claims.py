import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from coulis_core import check, learn, profile_from_folder
from coulis_core.profile import Profile, Rule
from coulis_core.memory import select, update
from coulis_core.critique import build_prompt
from coulis_core.importers import setup_from_linkedin
from claims import assess

TODAY = dt.date.today().isoformat()


def claim(**changes):
    result = dict(id='followers', entity='Example person', metric='followers', value='62000', unit='people',
                  time_period='October 2026', source='Synthetic test fixture', approved_at='2020-01-01',
                  valid_until='2099-12-31', statement='I have 62K followers.',
                  paraphrases=['My audience includes 62,000 followers.'])
    return {**result, **changes}


class ClaimTests(unittest.TestCase):
    def setUp(self):
        self.p = Profile(claims=[claim()])

    def test_exact_and_explicit_paraphrase(self):
        for text in ('I have 62K followers.', 'I have 62,000 followers.', 'My audience includes 62,000 followers.'):
            r = check(text, self.p)
            self.assertEqual(r['verdict'], 'Send')
            self.assertFalse(r['fact_check']['facts_verified'])
            self.assertIn('not independently verified', r['summary'])

    def test_no_metric_entity_period_or_modifier_transfer(self):
        for text in ('We have 62K founders.', 'We have 63K paying customers.', 'I have 62K paying followers.',
                     'Another company has 62K followers.', 'I had 62K followers last year.',
                     'I have 62K followers and 100 customers.', 'I have sixty thousand followers.'):
            self.assertNotEqual(check(text, self.p)['verdict'], 'Send', text)

    def test_new_paraphrase_unresolved(self):
        self.assertEqual(check('62,000 people follow me.', self.p)['fact_check']['status'], 'unresolved')

    def test_expiry_future_conflicts_and_invalid(self):
        for records in ([claim(valid_until='2020-02-01')], [claim(approved_at='2099-01-01')],
                        [claim(), claim(id='conflict', value='63000')], [{'id': 'incomplete'}]):
            self.assertEqual(assess('I have 62K followers.', records)['status'], 'unresolved')

    def test_legacy_number_alone_never_approves(self):
        self.assertEqual(check('We have 62K paying customers.', Profile(approved_facts=['62K followers']))['verdict'], 'Revise')

    def test_non_numeric_coverage_disclosed(self):
        result = check('We are the largest company.', Profile())
        self.assertFalse(result['fact_check']['facts_verified'])
        self.assertIn('qualitative', result['fact_check']['coverage'])

    def test_quotes_and_third_party_not_implicitly_cleared(self):
        for text in ('Someone said "we have 63K customers".', 'ExampleCorp has $10M ARR.'):
            self.assertNotEqual(check(text, self.p)['verdict'], 'Send')


class MemoryTests(unittest.TestCase):
    def test_punctuation_is_personal_and_contextual(self):
        p = Profile(rules=[Rule(text='Avoid dashes', key='em_dash', value='avoid'),
                           Rule(text='Use dashes', key='em_dash', value='allow', scope={'surface':'linkedin'})])
        self.assertEqual(check('A pause — then a thought.', Profile())['verdict'], 'Send')
        self.assertEqual(check('A pause — then a thought.', p, 'linkedin')['verdict'], 'Send')
        self.assertEqual(check('A pause — then a thought.', p, 'x')['verdict'], 'Hold')

    def test_conflict_is_not_silent_override(self):
        p = Profile(rules=[Rule(text='Avoid dashes', key='em_dash', value='avoid'),
                           Rule(text='Use dashes', key='em_dash', value='allow')])
        self.assertEqual(check('A pause — then a thought.', p)['verdict'], 'Revise')
        self.assertIn('UNRESOLVED preference conflict', build_prompt('Hi', p, 'linkedin'))

    def test_missing_context_and_inactive_expired_unapproved(self):
        rules = [Rule(text='Scoped', scope={'audience':'investors'}), Rule(text='Retired', active=False),
                 Rule(text='Old', expires='2020-01-01'), Rule(text='Not approved', approved=False)]
        self.assertEqual(select(rules)[0], [])
        self.assertEqual([r.text for r in select(rules, {'audience':'investors'})[0]], ['Scoped'])

    def test_learning_persists_after_approval_and_retrieves_new_topic(self):
        p = Profile()
        out = learn('We built a feature. It helps.', 'we built a feature. it helps.', p,
                    {'surface':'x', 'purpose':'launch'})
        self.assertTrue(out['proposed_rules'])
        self.assertFalse(out['generalization_validated'])
        rule = out['proposed_rules'][0]
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                update(folder, rule)
            rule['approved'] = True
            update(folder, rule)
            loaded = profile_from_folder(folder)
            self.assertIn(rule['text'], build_prompt('An unrelated launch topic.', loaded, 'x', {'purpose':'launch'}))
            self.assertNotIn(rule['text'], build_prompt('An investor letter.', loaded, 'investor_update'))
            update(folder, retire_id=rule['id'])
            self.assertNotIn(rule['text'], build_prompt('Next launch.', profile_from_folder(folder), 'x', {'purpose':'launch'}))
            update(folder, rule)
            self.assertIn(rule['text'], build_prompt('Next launch.', profile_from_folder(folder), 'x', {'purpose':'launch'}))

    def test_profile_files_preserve_scopes_without_global_leak(self):
        p = Profile(rules=[Rule(id='a', text='Short', scope={'surface':'x'}, key='length', value='short')], claims=[claim()])
        with tempfile.TemporaryDirectory() as folder:
            for name, text in p.to_files().items():
                (Path(folder)/name).write_text(text)
            restored = profile_from_folder(folder)
            self.assertEqual(restored.to_dict(), p.to_dict())
            self.assertNotIn('Short', (Path(folder)/'TASTE.md').read_text())

    def test_import_requires_rights(self):
        with self.assertRaisesRegex(ValueError, 'permission'):
            setup_from_linkedin('missing.csv', 'unused')

class BenchmarkTests(unittest.TestCase):
    def test_counts_and_ties_are_not_posts_or_quality(self):
        from evals.benchmark import run
        from types import SimpleNamespace
        result = run(SimpleNamespace(cmd='voice', personas=['evals/fixtures/voice/a','evals/fixtures/voice/b'],
                                    heldout='evals/fixtures/voice/heldout.jsonl', dataset_version='synthetic-v1',
                                    split_description='synthetic', public_inputs=True))
        self.assertEqual(result['rows'], 2)
        self.assertEqual(result['comparisons'], 2)
        self.assertEqual(result['ties'], 2)
        self.assertEqual(result['wins'], 0)
        self.assertIn('eight-axis critique', result['not_validated'])

    def test_facts_do_not_change_voice_diagnostic(self):
        from evals.benchmark import score
        a, b = Profile(claims=[claim()]), Profile()
        self.assertEqual(score('I have 62K followers.', a), score('I have 62K followers.', b))
