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
from urllib.parse import urlsplit

from storos_config import CONFIG_ROOT, TOKEN_FILE, ensure_admin_token, init_config, read_config
from storos_tasks import TASK_ROOT, list_tasks, read_task
from storos_vm import plan_vm
from storos_vm_store import VM_INTENT_ROOT, list_vm_intents, read_vm_intent

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


def make_handler(
    config_root,
    snapshot_path,
    token,
    vm_intent_root=VM_INTENT_ROOT,
    task_root=TASK_ROOT,
):
    config_root = Path(config_root)
    snapshot_path = Path(snapshot_path)
    vm_intent_root = Path(vm_intent_root)
    task_root = Path(task_root)

    class Handler(BaseHTTPRequestHandler):
        server_version = 'StorOSPanel/0.2'

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

        def _snapshot(self):
            try:
                return json.loads(snapshot_path.read_text())
            except (OSError, ValueError, json.JSONDecodeError):
                return None

        def _intent_list(self):
            try:
                return list_vm_intents(vm_intent_root)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return None

        def _task_list(self):
            try:
                return list_tasks(task_root)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                return None

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/healthz':
                self._json(200, {'status': 'ok', 'product': 'StorOS'})
                return
            if not self._auth():
                return

            if path == '/api/config':
                self._json(200, read_config(config_root))
                return

            if path == '/api/status':
                data = self._snapshot()
                if data is None:
                    self._json(503, {'status': 'unavailable', 'message': 'Inventário StorOS indisponível.'})
                else:
                    self._json(200, data)
                return

            if path == '/api/vms/intents':
                intents = self._intent_list()
                if intents is None:
                    self._json(503, {'status': 'unavailable', 'message': 'Store de intenções indisponível.'})
                else:
                    self._json(200, {'count': len(intents), 'items': intents})
                return

            if path == '/api/tasks':
                tasks = self._task_list()
                if tasks is None:
                    self._json(503, {'status': 'unavailable', 'message': 'Ledger de tarefas indisponível.'})
                else:
                    self._json(200, {'count': len(tasks), 'items': tasks})
                return

            parts = [part for part in path.strip('/').split('/') if part]
            if len(parts) in (4, 5) and parts[:3] == ['api', 'vms', 'intents']:
                vm_uuid = parts[3]
                try:
                    record = read_vm_intent(vm_uuid, vm_intent_root)
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    self._json(404, {'error': 'vm_intent_not_found'})
                    return
                if len(parts) == 4:
                    self._json(200, record)
                    return
                if parts[4] != 'plan':
                    self._json(404, {'error': 'not_found'})
                    return
                snapshot = self._snapshot()
                if snapshot is None:
                    self._json(503, {'status': 'unavailable', 'message': 'Inventário StorOS indisponível para planejar.'})
                    return
                try:
                    plan = plan_vm(record['intent'], snapshot)
                except (ValueError, TypeError):
                    self._json(503, {'status': 'unavailable', 'message': 'Inventário StorOS inválido para planejar.'})
                    return
                self._json(200, {
                    'vm_uuid': record['vm_uuid'],
                    'intent_generation': record['generation'],
                    'intent_sha256': record['intent_sha256'],
                    'plan': plan,
                })
                return

            if len(parts) == 3 and parts[:2] == ['api', 'tasks']:
                task_id = parts[2]
                try:
                    task = read_task(task_id, task_root)
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    self._json(404, {'error': 'task_not_found'})
                    return
                self._json(200, task)
                return

            if path == '/':
                status = self._snapshot()
                if status is None:
                    vm_count, health, host = '—', 'unavailable', {}
                else:
                    libvirt = status.get('libvirt', {})
                    host = status.get('host', {})
                    vm_count = libvirt.get('discovered_count', '—')
                    health = libvirt.get('status', 'unknown')
                config = read_config(config_root)
                intents = self._intent_list()
                tasks = self._task_list()
                intent_count = 'indisponível' if intents is None else len(intents)
                task_count = 'indisponível' if tasks is None else len(tasks)
                rows = ''
                if intents:
                    for record in intents:
                        intent = record['intent']
                        rows += (
                            '<tr><td>' + html.escape(intent['name']) + '</td>'
                            '<td>' + html.escape(intent['desired_state']) + '</td>'
                            '<td>' + html.escape(str(intent['resources']['vcpus'])) + '</td>'
                            '<td>' + html.escape(str(intent['resources']['memory_mib'])) + ' MiB</td>'
                            '<td>' + html.escape(str(record['generation'])) + '</td></tr>'
                        )
                if not rows:
                    rows = '<tr><td colspan="5">Nenhuma intenção persistida disponível.</td></tr>'
                page = f'''<!doctype html><html><head><meta charset="utf-8"><title>StorOS</title></head>
<body><h1>StorOS</h1><p>Painel autenticado — modo somente leitura.</p>
<dl><dt>Config generation</dt><dd>{config['generation']}</dd>
<dt>Libvirt</dt><dd>{html.escape(str(health))}</dd><dt>VMs descobertas</dt><dd>{html.escape(str(vm_count))}</dd>
<dt>CPUs lógicas</dt><dd>{html.escape(str(host.get('logical_cpus', '—')))}</dd>
<dt>Intenções persistidas</dt><dd>{html.escape(str(intent_count))}</dd>
<dt>Tarefas dry-run</dt><dd>{html.escape(str(task_count))}</dd>
<dt>Escrita em VMs</dt><dd>bloqueada</dd></dl>
<h2>Intenções de VM</h2><table><thead><tr><th>Nome</th><th>Desejado</th><th>vCPU</th><th>RAM</th><th>Geração</th></tr></thead>
<tbody>{rows}</tbody></table>
<p>APIs somente leitura: /api/status, /api/config, /api/vms/intents e /api/tasks.</p></body></html>'''.encode('utf-8')
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
    parser.add_argument('--vm-intent-root', default=str(VM_INTENT_ROOT))
    parser.add_argument('--task-root', default=str(TASK_ROOT))
    args = parser.parse_args(argv)
    config = init_config(args.config_root)
    token = ensure_admin_token(args.token_file)
    web = config['settings']['web']
    server_class = ThreadingHTTPServer
    if ':' in web['listen_host']:
        class IPv6ThreadingHTTPServer(ThreadingHTTPServer):
            address_family = socket.AF_INET6
        server_class = IPv6ThreadingHTTPServer
    server = server_class((
        web['listen_host'],
        web['port'],
    ), make_handler(
        args.config_root,
        args.snapshot,
        token,
        args.vm_intent_root,
        args.task_root,
    ))
    server.serve_forever()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
