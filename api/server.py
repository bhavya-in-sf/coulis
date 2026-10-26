#!/usr/bin/env python3
"""Taste API (REST, v1). Standard library HTTP server; put it behind a TLS proxy
in production.

    SAUCE_ENC_KEY=$(python3 api/admin.py new-enc-key) python3 api/server.py --port 8787

Endpoints (all JSON, all need `Authorization: Bearer <key>` except /v1/health):
    GET    /v1/health
    POST   /v1/profiles                 build a profile from samples (or upload a full profile)
    GET    /v1/profiles/{id}
    DELETE /v1/profiles/{id}
    POST   /v1/check                    the gate: no model call, deterministic
    POST   /v1/critique                 8 axes, never one overall score (one model call)
    POST   /v1/learn                    proposes rules from draft vs final; saves them as pending
    POST   /v1/rules/{id}/approve       a human approves one pending rule; it joins the profile
    POST   /v1/rules/{id}/reject
    GET    /v1/usage                    your metered calls and tokens
"""
import argparse
import json
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sauce_core import __version__, check, critique, learn, profile_from_dict, profile_from_samples  # noqa: E402
from sauce_core.profile import Rule  # noqa: E402
from api.store import Store  # noqa: E402

MAX_BODY = 200_000  # bytes
MAX_TEXT = 20_000   # characters per draft


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def need(body, *fields):
    for f in fields:
        v = body.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ApiError(400, "missing_field", f"'{f}' is required.")
        if isinstance(v, str) and len(v) > MAX_TEXT:
            raise ApiError(413, "too_long", f"'{f}' is over {MAX_TEXT} characters.")


class Api:
    def __init__(self, store, critic=critique):
        self.store, self.critic = store, critic

    def _profile(self, key, body):
        pid = body.get("profile_id")
        if not pid:
            raise ApiError(400, "missing_field", "'profile_id' is required.")
        d = self.store.load_profile(key["key_hash"], pid)
        if d is None:
            raise ApiError(404, "not_found", "No such profile for this key.")
        return pid, profile_from_dict(d)

    def dispatch(self, method, path, headers, raw):
        """Pure request handler: (status, json). Used by the HTTP server and by tests."""
        try:
            if method == "GET" and path == "/v1/health":
                return 200, {"ok": True, "version": __version__}
            auth = headers.get("authorization", "")
            key = self.store.auth(auth[7:].strip() if auth.lower().startswith("bearer ") else headers.get("x-api-key"))
            if not key:
                raise ApiError(401, "unauthorized", "Missing or invalid API key.")
            if not self.store.allow(key["key_hash"], key["rate_per_min"]):
                raise ApiError(429, "rate_limited", "Too many requests. Slow down and retry.")
            if len(raw) > MAX_BODY:
                raise ApiError(413, "too_large", "Request body too large.")
            try:
                body = json.loads(raw or b"{}")
            except ValueError:
                raise ApiError(400, "bad_json", "Body must be JSON.")
            out, tokens = self.route(method, path, key, body)
            self.store.meter(key["key_hash"], re.sub(r"/(prf|rul)_[a-f0-9]+", "/{id}", path), *tokens)
            return 200, out
        except ApiError as e:
            return e.status, {"error": {"code": e.code, "message": e.message}}
        except ValueError as e:
            return 400, {"error": {"code": "invalid", "message": str(e)}}
        except Exception as e:  # never echo drafts or stack traces to the client
            print(f"[sauce] internal error: {type(e).__name__}", file=sys.stderr)
            return 500, {"error": {"code": "internal", "message": "Internal error."}}

    def route(self, method, path, key, body):
        kh = key["key_hash"]
        if method == "POST" and path == "/v1/profiles":
            if "profile" in body:
                prof = profile_from_dict(body["profile"])
            else:
                if not body.get("samples"):
                    raise ApiError(400, "missing_field", "'samples' (list of your own writing) is required.")
                prof = profile_from_samples(body["samples"], body.get("who", ""), body.get("audience", ""),
                                            body.get("goal", ""), body.get("owner", ""), body.get("product", ""),
                                            body.get("approved_facts", []))
            pid = self.store.save_profile(kh, prof.to_dict())
            return {"id": pid, "profile": prof.to_dict()}, (0, 0)
        m = re.fullmatch(r"/v1/profiles/(prf_[a-f0-9]+)", path)
        if m and method == "GET":
            d = self.store.load_profile(kh, m.group(1))
            if d is None:
                raise ApiError(404, "not_found", "No such profile for this key.")
            return {"id": m.group(1), "profile": d}, (0, 0)
        if m and method == "DELETE":
            if not self.store.delete_profile(kh, m.group(1)):
                raise ApiError(404, "not_found", "No such profile for this key.")
            return {"deleted": True}, (0, 0)
        if method == "POST" and path == "/v1/check":
            need(body, "text")
            _, prof = self._profile(key, body)
            return check(body["text"], prof, body.get("surface", "linkedin"), body.get("history", [])), (0, 0)
        if method == "POST" and path == "/v1/critique":
            need(body, "text")
            _, prof = self._profile(key, body)
            r = self.critic(body["text"], prof, body.get("surface", "linkedin"))
            u = r.get("usage", {})
            return r, (u.get("input_tokens", 0), u.get("output_tokens", 0))
        if method == "POST" and path == "/v1/learn":
            need(body, "draft", "final")
            pid, prof = self._profile(key, body)
            rules = learn(body["draft"], body["final"], prof)["proposed_rules"]
            for r in rules:
                r["id"] = self.store.add_pending(kh, pid, r["text"])
            return {"profile_id": pid, "proposed_rules": rules,
                    "note": "Nothing is saved until a human approves each rule."}, (0, 0)
        m = re.fullmatch(r"/v1/rules/(rul_[a-f0-9]+)/(approve|reject)", path)
        if m and method == "POST":
            popped = self.store.pop_pending(kh, m.group(1))
            if not popped:
                raise ApiError(404, "not_found", "No such pending rule for this key.")
            pid, text = popped
            if m.group(2) == "reject":
                return {"rejected": True, "rule": text}, (0, 0)
            d = self.store.load_profile(kh, pid)
            if d is None:
                raise ApiError(404, "not_found", "The profile for this rule was deleted.")
            prof = profile_from_dict(d)
            prof.rules.append(Rule(text=text, source="learned", approved=True, added=time.strftime("%Y-%m-%d")))
            self.store.save_profile(kh, prof.to_dict(), pid)
            return {"approved": True, "rule": text, "profile_id": pid}, (0, 0)
        if method == "GET" and path == "/v1/usage":
            return {"usage": self.store.usage(kh)}, (0, 0)
        raise ApiError(404, "not_found", f"No route for {method} {path}.")


def make_handler(api):
    class Handler(BaseHTTPRequestHandler):
        server_version = "Sauce/" + __version__

        def _go(self):
            n = int(self.headers.get("content-length") or 0)
            raw = self.rfile.read(min(n, MAX_BODY + 1)) if n else b""
            status, out = api.dispatch(self.command, self.path.split("?")[0],
                                       {k.lower(): v for k, v in self.headers.items()}, raw)
            data = json.dumps(out).encode()
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = do_DELETE = _go

        def log_message(self, *args):  # logging off by default: no paths, bodies or IPs
            pass

    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args()
    api = Api(Store())
    if not api.store.cipher.enabled:
        print("[sauce] WARNING: SAUCE_ENC_KEY not set, profiles stored unencrypted (dev only).", file=sys.stderr)
    print(f"Taste API v{__version__} on http://{a.host}:{a.port}", file=sys.stderr)
    ThreadingHTTPServer((a.host, a.port), make_handler(api)).serve_forever()


if __name__ == "__main__":
    main()
