"""Python client for the Taste API. Standard library only.

    from coulis_client import Coulis
    t = Coulis(api_key="tst_...", base_url="http://localhost:8787")
    prof = t.create_profile(samples=["a post I'm proud of", "another"], owner="Sam", approved_facts=["1,200 users"])
    result = t.check(prof["id"], "Notely hit $20k MRR")
    if result["verdict"] == "BLOCK": ...
"""
import json
import os
import urllib.error
import urllib.request


class CoulisError(Exception):
    def __init__(self, status, code, message):
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code, self.message = status, code, message


class Coulis:
    def __init__(self, api_key=None, base_url=None, timeout=60):
        self.api_key = api_key or os.environ.get("COULIS_API_KEY")
        self.base_url = (base_url or os.environ.get("COULIS_BASE_URL", "http://localhost:8787")).rstrip("/")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("Pass api_key or set COULIS_API_KEY.")

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method, headers={
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read())["error"]
            except Exception:
                err = {"code": "http_error", "message": str(e)}
            raise CoulisError(e.code, err.get("code"), err.get("message")) from None

    # profiles
    def create_profile(self, samples=None, profile=None, **fields):
        return self._req("POST", "/v1/profiles", {"profile": profile} if profile else {"samples": samples, **fields})

    def get_profile(self, profile_id):
        return self._req("GET", f"/v1/profiles/{profile_id}")

    def delete_profile(self, profile_id):
        return self._req("DELETE", f"/v1/profiles/{profile_id}")

    # the taste layer
    def check(self, profile_id, text, surface="linkedin", history=None):
        return self._req("POST", "/v1/check", {"profile_id": profile_id, "text": text, "surface": surface,
                                               "history": history or []})

    def critique(self, profile_id, text, surface="linkedin"):
        return self._req("POST", "/v1/critique", {"profile_id": profile_id, "text": text, "surface": surface})

    def learn(self, profile_id, draft, final):
        return self._req("POST", "/v1/learn", {"profile_id": profile_id, "draft": draft, "final": final})

    def approve_rule(self, rule_id):
        return self._req("POST", f"/v1/rules/{rule_id}/approve", {})

    def reject_rule(self, rule_id):
        return self._req("POST", f"/v1/rules/{rule_id}/reject", {})

    def usage(self):
        return self._req("GET", "/v1/usage")
