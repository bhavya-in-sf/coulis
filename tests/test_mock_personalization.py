import json
from pathlib import Path
import tempfile
import unittest
from coulis_research.mock_personalization import run
from coulis_research.personalization import report

class MockRunTests(unittest.TestCase):
    def test_full_mock_run_and_simulation_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'run'
            summary=run(root)
            self.assertEqual(summary['checks_passed'],199)
            self.assertFalse(summary['effectiveness_measured'])
            self.assertEqual(summary['model_calls'],0)
            for split in summary['splits']:
                self.assertEqual(split['pairwise_trials'],72)
                self.assertEqual(split['simulated_ballots'],66)
            key=json.loads((root/'future/conditions-private.json').read_text())
            ballots=json.loads((root/'future/simulated-ballots.json').read_text())
            key['synthetic']=False
            with self.assertRaises(ValueError):report(key,ballots,simulated=True)
            key['synthetic']=True;ballots[0]['human_confirmed']=True
            with self.assertRaises(ValueError):report(key,ballots,simulated=True)
            with self.assertRaises(ValueError):run(root)
