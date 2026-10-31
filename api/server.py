"""Self-hosted JSON transport for the existing Coulis tools. No web UI.

COULIS_API_KEY=<secret> python3 -m api.server --profile /path/to/profile
Local default; use TLS and deployment-level rate limits before remote exposure.
"""
import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from coulis_core.service import call, OPERATIONS

MAX_BODY = 200_000


class Api:
    def __init__(self, accounts):
        # Server-controlled key -> {profile_id: folder}. Never accept filesystem paths over HTTP.
        if not accounts or any(not key for key in accounts):
            raise ValueError('Configure nonempty API keys')
        self.accounts = accounts

    def dispatch(self, method, path, headers, raw):
        def error(status, message):
            return status, {'error': {'message': message}}
        if method == 'GET' and path == '/v1/health':
            return 200, {'ok': True}
        auth = headers.get('authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else ''
        profiles = next((profiles for key, profiles in self.accounts.items()
                         if hmac.compare_digest(key.encode(), token.encode())), None)
        if profiles is None: return error(401, 'Invalid API key')
        if method != 'POST' or not path.startswith('/v1/') or path[4:] not in OPERATIONS:
            return error(404, 'Unknown operation')
        if len(raw) > MAX_BODY: return error(413, 'Request too large')
        try:
            body = json.loads(raw)
            if not isinstance(body, dict) or set(body) - {'profile_id', 'arguments'}:
                return error(400, 'Expected profile_id and arguments')
            pid = body.get('profile_id', 'default')
            if not isinstance(pid, str) or pid not in profiles:
                return error(404, 'Unknown profile')
            args = body.get('arguments', {})
            if not isinstance(args, dict): return error(400, 'Arguments must be an object')
            return 200, call(profiles[pid], path[4:], args)
        except (ValueError, KeyError, TypeError):
            return error(400, 'Invalid request or workflow state; check the operation contract')
        except Exception:
            # Never return private text, credentials or filesystem paths in errors.
            return error(500, 'Internal error')


def make_handler(api):
    class Handler(BaseHTTPRequestHandler):
        def handle_request(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 <= size <= MAX_BODY: raise ValueError()
            except ValueError:
                self.send_error(413); self.close_connection = True; return
            self.connection.settimeout(15)
            raw = self.rfile.read(size)
            status, result = api.dispatch(self.command, self.path,
                {k.lower(): v for k, v in self.headers.items()}, raw)
            encoded = json.dumps(result).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        do_POST = do_GET = handle_request
        def log_message(self, *args): pass
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8787)
    args = parser.parse_args()
    key = os.environ.get('COULIS_API_KEY')
    if not key: parser.error('Set COULIS_API_KEY to a strong secret')
    api = Api({key: {'default': Path(args.profile).resolve()}})
    print(f'Coulis JSON API listening on {args.host}:{args.port}', flush=True)
    ThreadingHTTPServer((args.host, args.port), make_handler(api)).serve_forever()


if __name__ == '__main__': main()
