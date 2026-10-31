"""Coulis test suite. No network, no model calls (the critic is faked).

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

from coulis_core import AXES, check, learn, profile_from_dict, profile_from_folder  # noqa: E402
from coulis_core.profile import parse_files  # noqa: E402
from test_context_and_claims import claim
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

    def test_any_approved_heading_counts(self):
        # found testing the MCP on a real team's claims.md: headings like "## Approved (confirmed ...)"
        claims = ("owner: Sam\nproduct: Notely\n\n## Approved (confirmed by Sam, Oct 2026)\n- $100 a month plan\n\n"
                  "## Approved credential wording\n- 2 to 17 meetings in a month\n\n## Needs confirm\n- revenue\n\n"
                  "## Banned phrases\n- no firsts :: \\bthe first\\b\n")
        p = parse_files("", claims)
        self.assertEqual(p.approved_facts, ["$100 a month plan", "2 to 17 meetings in a month"])
        self.assertEqual(check("Our plan is $100 a month.", p)["verdict"], "Hold")
        p.claims = [claim(id='price', metric='plan price', value='100', unit='USD/month', statement='Our plan is $100 a month.')]
        self.assertEqual(check("Our plan is $100 a month.", p)["verdict"], "Send")

    def test_check_is_deterministic(self):
        p = profile_from_folder(EXAMPLE)
        text = "Notely is the first app to hit $20k MRR"
        a, b = check(text, p, "x"), check(text, p, "x")
        self.assertEqual(a, b)
        self.assertEqual(a["verdict"], "Hold")
        self.assertEqual(check("We hit 1,200 users", p)["verdict"], "Revise")  # legacy notes do not approve

    def test_numbers_about_others_require_review(self):
        # calibrated on real founder posts: third-party numbers and quoted examples are not our claims
        p = profile_from_folder(EXAMPLE)
        self.assertEqual(check("Capital F closed a $17M fund last month.", p)["verdict"], "Hold")
        self.assertEqual(check("RB2B scaled from $0 to $5M ARR in 12 months.", p)["verdict"], "Hold")
        self.assertEqual(check('Try an opener like “I lost $2M in 48 hours.”', p)["verdict"], "Hold")
        self.assertEqual(check("We hit $50k MRR last month.", p)["verdict"], "Hold")
        self.assertEqual(check("A coach we work with closed a $4,000 deal.", p)["verdict"], "Hold")

    def test_audience_claims(self):
        # found dogfooding: "673 of my posts" and follower counts slipped through
        p = profile_from_folder(EXAMPLE)
        self.assertEqual(check("I have 90K followers.", p)["verdict"], "Revise")
        self.assertEqual(check("We got 72,000 views in 30 days.", p)["verdict"], "Revise")
        self.assertEqual(check("We hit 1,200 users.", p)["verdict"], "Revise")  # approved

    def test_multiplier_claims(self):
        p = profile_from_folder(EXAMPLE)
        self.assertEqual(check("Our clients see 10x reach in 30 days.", p)["verdict"], "Revise")
        self.assertEqual(check("We got 2.5x more leads.", p)["verdict"], "Revise")
        for ok in ("Support is open 24x7.", "Use a 2x2 matrix.", "Notion grew 10x after launch."):
            self.assertEqual(check(ok, p)["verdict"], "Revise", ok)  # conservative numeric coverage

    def test_learn_proposes_not_applies(self):
        p = profile_from_folder(EXAMPLE)
        out = learn("We leverage AI. It is great.", "It is great.", p)
        self.assertTrue(out["proposed_rules"])
        self.assertTrue(all(r["approved"] is False for r in out["proposed_rules"]))

    def test_regression_golden(self):
        r = regression(EXAMPLE, ROOT / "evals" / "golden" / "example.json")
        self.assertFalse(r["pass"])  # historical baselines intentionally invalidate unsafe number matching
        self.assertTrue(any("E1:" in d for d in r["drift"]))

    def test_regression_real_founder(self):
        # 553 real public posts from a founder (personas/bhavya): any verdict drift fails
        r = regression(ROOT / "personas" / "bhavya", ROOT / "evals" / "golden" / "bhavya.json")
        self.assertEqual(r["cases"], 553)
        self.assertFalse(r["pass"])  # archived v0 behavior is not current quality evidence
        self.assertTrue(r["drift"])


class Mcp(unittest.TestCase):
    """The MCP server as a brand-new plug-in user would hit it: no API key, no claims.md yet."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))
        os.environ["COULIS_PROFILE_DIR"] = self.dir
        self.key = os.environ.pop("ANTHROPIC_API_KEY", None)
        sys.path.insert(0, str(ROOT / "mcp"))
        import server
        self.s = server

    def tearDown(self):
        os.environ.pop("COULIS_PROFILE_DIR", None)
        if self.key:
            os.environ["ANTHROPIC_API_KEY"] = self.key

    def call(self, name, args):
        r = self.s.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})
        return r["result"]["structuredContent"]

    def test_new_user_flow(self):
        text = "We now have 1,200 users."
        self.assertEqual(self.call("coulis_check", {"text": text})["verdict"], "Revise")
        self.assertTrue(self.call("coulis_add", {"kind": "approved_fact", "text": "1,200 users"})["added"])
        self.assertFalse(self.call("coulis_add", {"kind": "approved_fact", "text": "1,200 users"})["added"])
        self.assertEqual(self.call("coulis_check", {"text": text})["verdict"], "Revise")
        self.call("coulis_approve_claim", {"approved": True, "claim": claim(id='users', metric='users', value='1200', statement=text)})
        self.assertEqual(self.call("coulis_check", {"text": text})["verdict"], "Send")
        self.call("coulis_add", {"kind": "banned_phrase", "text": "game-changer", "reason": "generic"})
        self.assertEqual(self.call("coulis_check", {"text": "A game-changer."})["verdict"], "Hold")

    def test_critique_without_key_uses_host_model(self):
        out = self.call("coulis_critique", {"text": "We now have 1,200 users."})
        self.assertEqual(out["mode"], "host_model")
        self.assertIn("rhythm", json.dumps(out["output_schema"]))


class StopHook(unittest.TestCase):
    """The plug-in's Stop hook sends unchecked drafts back once, and stays out of the way otherwise."""

    def run_hook(self, turn, active=False):
        import subprocess
        d = tempfile.mkdtemp(dir=os.environ.get("TMPDIR"))
        p = os.path.join(d, "t.jsonl")
        rows = [{"type": "user", "message": {"content": "write me a post"}}] + turn
        Path(p).write_text("\n".join(json.dumps(r) for r in rows))
        out = subprocess.run([sys.executable, str(ROOT / "hooks" / "stop_check.py")], capture_output=True, text=True,
                             input=json.dumps({"transcript_path": p, "stop_hook_active": active})).stdout
        return json.loads(out)["decision"] if out.strip() else "allow"

    def test_hook(self):
        A = lambda *b: {"type": "assistant", "message": {"content": list(b)}}
        t = lambda s: {"type": "text", "text": s}
        post = "```\nI built a free tool that knows how I write. It checks every draft before it goes out.\n```"
        self.assertEqual(self.run_hook([A(t(post))]), "block")
        self.assertEqual(self.run_hook([A(t(post))], active=True), "allow")  # never loops
        self.assertEqual(self.run_hook([A({"type": "tool_use", "name": "mcp__plugin_coulis_coulis__coulis_check"}),
                                        A(t(post))]), "allow")
        self.assertEqual(self.run_hook([A(t("> My LinkedIn just passed 62K followers."))]), "block")
        self.assertEqual(self.run_hook([A(t("```bash\ngit push origin HEAD\n```"))]), "allow")
        self.assertEqual(self.run_hook([A(t("Pushed. Everything is in sync."))]), "allow")


class Sameness(unittest.TestCase):
    def test_sameness_score_and_gate(self):
        from coulis_core import check, profile_from_samples
        prof = profile_from_samples(["A real post about something specific I did last week."])
        slop = "It's not about speed, it's about taste. Fast, cheap, and good. Comment below!"
        r = check(slop, prof, "linkedin")
        self.assertGreater(r["sameness"]["score"], 20)
        self.assertEqual(check(slop, prof, "linkedin", max_sameness=10)["verdict"], "Hold")
        clean = check("Three months ago we had no customers. Today we signed our 300th.", prof, "linkedin", max_sameness=100)
        self.assertNotIn("sameness_gate", [i["check"] for i in clean["issues"]])

    def test_linkedin_importer(self):
        import tempfile, csv, os
        from coulis_core.importers import setup_from_linkedin
        d = tempfile.mkdtemp()
        p = os.path.join(d, "Shares.csv")
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["Date", "ShareLink", "ShareCommentary", "SharedUrl", "MediaUrl", "Visibility"])
            w.writeheader()
            for i in range(8):
                w.writerow({"Date": f"2026-0{i+1}-01 10:00:00", "ShareLink": "", "ShareCommentary": ("Word " * 90).strip() + f" post {i}.", "SharedUrl": "", "MediaUrl": "", "Visibility": "MEMBER_NETWORK"})
        out = setup_from_linkedin(p, os.path.join(d, "prof"), name="Test", rights_confirmed=True)
        self.assertEqual(out["samples"], 6)
        self.assertTrue(os.path.exists(os.path.join(d, "prof", "TASTE.md")))


if __name__ == "__main__":
    unittest.main()
