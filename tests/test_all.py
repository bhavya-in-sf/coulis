"""Tastee test suite. No network, no model calls (the critic is faked).

    python3 -m unittest discover -s tests -v
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tastee_core import AXES, check, learn, profile_from_dict, profile_from_folder  # noqa: E402
from tastee_core.profile import parse_files  # noqa: E402
from api.server import Api  # noqa: E402
from api.store import Cipher, Store  # noqa: E402
from evals.run_eval import regression  # noqa: E402

EXAMPLE = ROOT / "personas" / "example"


def fake_critic(text, profile, surface="linkedin"):
    axes = {a: {"score": 5, "why": "fake", "quote": text[:20]} for a in AXES}
    return {"axes": axes, "slop_found": [], "weakest_axis": "proof",
            "rewrite": {"before": text[:20], "after": "x"}, "missing_proof": "",
            "usage": {"input_tokens": 100, "output_tokens": 50}}


class Core(unittest.TestCase):
    def test_profile_round_trip(self):
        p = profile_from_folder(EXAMPLE)
        self.assertEqual(p.product, "Notely")
        self.assertIn("1,200 users", p.approved_facts)
        files = p.to_files()
        p2 = parse_files(files["TASTE.md"], files["claims.md"])
        self.assertEqual(p.approved_facts, p2.approved_facts)
        self.assertEqual([b.regex for b in p.banned], [b.regex for b in p2.banned])
        self.assertEqual(profile_from_dict(p.to_dict()).to_dict(), p.to_dict())

    def test_check_is_deterministic(self):
        p = profile_from_folder(EXAMPLE)
        text = "Notely is the first app to hit $20k MRR"
        a, b = check(text, p, "x"), check(text, p, "x")
        self.assertEqual(a, b)
        self.assertEqual(a["verdict"], "BLOCK")
        self.assertEqual(check("We hit 1,200 users", p)["verdict"], "PASS")

    def test_learn_proposes_not_applies(self):
        p = profile_from_folder(EXAMPLE)
        out = learn("We leverage AI. It is great.", "It is great.", p)
        self.assertTrue(out["proposed_rules"])
        self.assertTrue(all(r["approved"] is False for r in out["proposed_rules"]))

    def test_regression_golden(self):
        r = regression(EXAMPLE, ROOT / "evals" / "golden" / "example.json")
        self.assertTrue(r["pass"], r["drift"])


class ApiFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))
        self.store = Store(os.path.join(self.tmp, "t.db"), Cipher(Cipher.new_key()))
        self.api = Api(self.store, critic=fake_critic)
        self.key = self.store.create_key("test", rate_per_min=1000)

    def tearDown(self):
        self.store.db.close()

    def call(self, method, path, body=None, key=True):
        h = {"authorization": f"Bearer {self.key}"} if key else {}
        return self.api.dispatch(method, path, h, json.dumps(body or {}).encode())

    def test_full_flow(self):
        prof = profile_from_folder(EXAMPLE).to_dict()
        s, out = self.call("POST", "/v1/profiles", {"profile": prof})
        self.assertEqual(s, 200)
        pid = out["id"]
        s, out = self.call("POST", "/v1/check", {"profile_id": pid, "text": "Notely is the first, $20k MRR"})
        self.assertEqual((s, out["verdict"]), (200, "BLOCK"))
        s, out = self.call("POST", "/v1/critique", {"profile_id": pid, "text": "We hit 1,200 users"})
        self.assertEqual(s, 200)
        self.assertNotIn("overall", json.dumps(out).lower())
        self.assertEqual(set(out["axes"]), set(AXES))
        s, out = self.call("POST", "/v1/learn", {"profile_id": pid, "draft": "We leverage AI. Great.", "final": "Great."})
        rid = out["proposed_rules"][0]["id"]
        n_before = len(self.call("GET", f"/v1/profiles/{pid}")[1]["profile"]["rules"])
        s, out = self.call("POST", f"/v1/rules/{rid}/approve")
        self.assertTrue(out["approved"])
        n_after = len(self.call("GET", f"/v1/profiles/{pid}")[1]["profile"]["rules"])
        self.assertEqual(n_after, n_before + 1)
        self.assertEqual(self.call("POST", f"/v1/rules/{rid}/approve")[0], 404)  # single use
        usage = {u["endpoint"]: u for u in self.call("GET", "/v1/usage")[1]["usage"]}
        self.assertEqual(usage["/v1/critique"]["input_tokens"], 100)
        self.assertEqual(self.call("DELETE", f"/v1/profiles/{pid}")[0], 200)
        self.assertEqual(self.call("GET", f"/v1/profiles/{pid}")[0], 404)

    def test_profile_from_samples(self):
        s, out = self.call("POST", "/v1/profiles", {"samples": ["One real post.", "Another."], "who": "Sam"})
        self.assertEqual(s, 200)
        self.assertEqual(out["profile"]["rules"], [])  # nothing invented

    def test_auth_and_isolation(self):
        self.assertEqual(self.call("POST", "/v1/check", {"text": "x"}, key=False)[0], 401)
        pid = self.call("POST", "/v1/profiles", {"samples": ["hi there"]})[1]["id"]
        other = self.store.create_key("other")
        s, _ = self.api.dispatch("GET", f"/v1/profiles/{pid}", {"authorization": f"Bearer {other}"}, b"")
        self.assertEqual(s, 404)  # one key cannot read another key's profile

    def test_encrypted_at_rest(self):
        pid = self.call("POST", "/v1/profiles", {"samples": ["secret revenue 999999"]})[1]["id"]
        raw = self.store.db.execute("SELECT blob FROM profiles WHERE id=?", (pid,)).fetchone()[0]
        self.assertTrue(raw.startswith(b"F1"))
        self.assertNotIn(b"999999", raw)

    def test_rate_limit(self):
        slow = self.store.create_key("slow", rate_per_min=2)
        codes = [self.api.dispatch("GET", "/v1/usage", {"authorization": f"Bearer {slow}"}, b"")[0] for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_errors_are_clean(self):
        self.assertEqual(self.call("POST", "/v1/check", {"profile_id": "prf_00", "text": "x"})[0], 404)
        self.assertEqual(self.call("POST", "/v1/check", {"profile_id": "prf_00"})[0], 400)
        s, out = self.api.dispatch("POST", "/v1/check", {"authorization": f"Bearer {self.key}"}, b"{not json")
        self.assertEqual((s, out["error"]["code"]), (400, "bad_json"))


class PythonSdk(unittest.TestCase):
    """Runs the real SDK against the real API handler, with urlopen routed in-process."""

    def test_sdk_against_api(self):
        import io
        import urllib.error
        import urllib.request
        sys.path.insert(0, str(ROOT / "sdk" / "python"))
        import tastee_client
        tmp = tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))
        store = Store(os.path.join(tmp, "s.db"), Cipher(Cipher.new_key()))
        api = Api(store, critic=fake_critic)
        key = store.create_key("sdk", 1000)

        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): pass

        def fake_urlopen(req, timeout=None):
            path = req.full_url.split("localhost:8787", 1)[1]
            status, out = api.dispatch(req.get_method(), path, {k.lower(): v for k, v in req.header_items()},
                                       req.data or b"")
            body = json.dumps(out).encode()
            if status >= 400:
                raise urllib.error.HTTPError(req.full_url, status, "err", {}, io.BytesIO(body))
            return Resp(body)

        real = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen
        try:
            t = tastee_client.Tastee(key, "http://localhost:8787")
            p = t.create_profile(samples=["We launched in March."], approved_facts=["1,200 users"])
            self.assertEqual(t.check(p["id"], "We have 1,200 users.")["verdict"], "PASS")
            self.assertEqual(t.check(p["id"], "We hit $20k MRR")["verdict"], "BLOCK")
            self.assertEqual(set(t.critique(p["id"], "hello")["axes"]), set(AXES))
            r = t.learn(p["id"], "We leverage AI. Great.", "Great.")
            self.assertTrue(t.approve_rule(r["proposed_rules"][0]["id"])["approved"])
            with self.assertRaises(tastee_client.TasteeError) as e:
                tastee_client.Tastee("tst_bad", "http://localhost:8787").usage()
            self.assertEqual(e.exception.status, 401)
        finally:
            urllib.request.urlopen = real
            store.db.close()


if __name__ == "__main__":
    unittest.main()
