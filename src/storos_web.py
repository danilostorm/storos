"""Minimal authenticated read-only web panel for StorOS."""
from __future__ import annotations

import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import html
import json
from pathlib import Path
import socket

from storos_config import CONFIG_ROOT, TOKEN_FILE, ensure_admin_token, init_config, read_config

SNAPSHOT = Path('/run/storos/status.json')


def _authorized(header, token):
    if not header or not header.startswith('Basic '):
        return False
    try:
        decoded = base64.b64decode(header[6:], validate=True).decode('utf-8')
        username, password = decoded.split(':', 1)
    except (ValueError, UnicodeError):
        return False
    return hmac.compare_digest(username, 'admin') and hmac.compare_digest(password, token)


def make_handler(config_root, snapshot_path, token):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'StorOSPanel/0.1'

        def log_message(self, fmt, *args):
            return

        def _headers(self, status, content_type='application/json; charset=utf-8'):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()

        def _json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=True).encode('utf-8')
            self._headers(status)
            self.wfile.write(body)

        def _auth(self):
            if _authorized(self.headers.get('Authorization'), token):
                return True
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="StorOS", charset="UTF-8"')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            return False

        def do_GET(self):
            if self.path == '/healthz':
                self._json(200, {'status': 'ok', 'product': 'StorOS'})
                return
            if not self._auth():
                return
            if self.path == '/api/config':
                self._json(200, read_config(config_root))
                return
            if self.path == '/api/status':
                try:
                    data = json.loads(Path(snapshot_path).read_text())
                    self._json(200, data)
                except (OSError, ValueError, json.JSONDecodeError):
                    self._json(503, {'status': 'unavailable', 'message': 'Inventário StorOS indisponível.'})
                return
            if self.path == '/':
                try:
                    status = json.loads(Path(snapshot_path).read_text())
                    libvirt = status.get('libvirt', {})
                    host = status.get('host', {})
                    vm_count = libvirt.get('discovered_count')
                    health = libvirt.get('status', 'unknown')
                except (OSError, ValueError, json.JSONDecodeError):
                    vm_count, health, host = '—', 'unavailable', {}
                config = read_config(config_root)
                page = f'''<!doctype html><html><head><meta charset="utf-8"><title>StorOS</title></head>
<body><h1>StorOS</h1><p>Painel autenticado — modo somente leitura.</p>
<dl><dt>Config generation</dt><dd>{config['generation']}</dd>
<dt>Libvirt</dt><dd>{html.escape(str(health))}</dd><dt>VMs descobertas</dt><dd>{html.escape(str(vm_count))}</dd>
<dt>CPUs lógicas</dt><dd>{html.escape(str(host.get('logical_cpus', '—')))}</dd>
<dt>Escrita em VMs</dt><dd>bloqueada</dd></dl>
<p>APIs: /api/status e /api/config</p></body></html>'''.encode('utf-8')
                self._headers(200, 'text/html; charset=utf-8')
                self.wfile.write(page)
                return
            self._json(404, {'error': 'not_found'})

        def do_POST(self):
            if not self._auth():
                return
            self._json(405, {'error': 'read_only_panel'})

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description='Painel web StorOS autenticado, somente leitura.')
    parser.add_argument('--config-root', default=str(CONFIG_ROOT))
    parser.add_argument('--snapshot', default=str(SNAPSHOT))
    parser.add_argument('--token-file', default=str(TOKEN_FILE))
    args = parser.parse_args(argv)
    config = init_config(args.config_root)
    token = ensure_admin_token(args.token_file)
    web = config['settings']['web']
    server_class = ThreadingHTTPServer
    if ':' in web['listen_host']:
        class IPv6ThreadingHTTPServer(ThreadingHTTPServer):
            address_family = socket.AF_INET6
        server_class = IPv6ThreadingHTTPServer
    server = server_class((web['listen_host'], web['port']), make_handler(args.config_root, args.snapshot, token))
    server.serve_forever()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
