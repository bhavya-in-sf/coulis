#!/usr/bin/env python3
"""Local-only UI for the same Coulis workflow exposed over MCP. No external dependencies."""
import argparse
import hmac
import json
import secrets
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from coulis_core.workflow import Workflow


def make_handler(profile, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass  # no drafts or tokens in request logs
        def send(self, status, data, content_type='application/json'):
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)
        def valid_host(self):
            return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
        def do_GET(self):
            if not self.valid_host():return self.send(403,b'{}')
            if self.path=='/':
                data=(ROOT/'docs/taste-loop.html').read_text().replace('__TOKEN__',token).encode()
                return self.send(200,data,'text/html; charset=utf-8')
            assets={'/taste-loop.js':('docs/taste-loop.js','text/javascript'),'/taste-loop.css':('docs/taste-loop.css','text/css')}
            for name in ('InstrumentSans-Regular.ttf','InstrumentSans-Bold.ttf','InstrumentSerif-Italic.ttf'):
                assets['/fonts/'+name]=('docs/fonts/'+name,'font/ttf')
            if self.path not in assets:return self.send(404,b'{}')
            file,mime=assets[self.path];self.send(200,(ROOT/file).read_bytes(),mime)
        def do_POST(self):
            if not self.valid_host() or self.path!='/api' or not hmac.compare_digest(self.headers.get('X-Coulis-Token',''),token):
                return self.send(403,b'{"error":"Unauthorized local request"}')
            if self.headers.get('Origin') not in (None,f'http://127.0.0.1:{self.server.server_port}'):
                return self.send(403,b'{}')
            workflow=None
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=250000:raise ValueError('Invalid request size')
                body=json.loads(self.rfile.read(length))
                workflow=Workflow(profile)
                result=workflow.dispatch(body['action'],body.get('arguments',{}))
                self.send(200,json.dumps(result,allow_nan=False).encode())
            except (ValueError,KeyError,TypeError) as error:
                self.send(400,json.dumps({'error':str(error)}).encode())
            except Exception:
                self.send(500,b'{"error":"Local operation failed; no result confirmed"}')
            finally:
                if workflow:workflow.close()
    return Handler

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--port',type=int,default=8767);a=p.parse_args()
    server=HTTPServer(('127.0.0.1',a.port),make_handler(a.profile,secrets.token_urlsafe(32)))
    print(f'Coulis taste loop: http://127.0.0.1:{server.server_port} — profile: {a.profile}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
