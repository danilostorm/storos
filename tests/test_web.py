import contextlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from http.server import ThreadingHTTPServer

from storos_cli import main as cli_main
from storos_config import apply_settings, basic_auth_value, ensure_admin_token, init_config, read_config
from storos_tasks import create_dry_run_task, list_tasks
from storos_vm import plan_vm
from storos_vm_store import apply_vm_intent, intent_preconditions, read_vm_intent
from storos_web import make_handler


class WebPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config_root = self.root / 'config'
        self.intent_root = self.root / 'vm-intents'
        self.task_root = self.root / 'tasks'
        init_config(self.config_root)
        self.token = ensure_admin_token(self.root / 'admin.token')
        self.snapshot = self.root / 'status.json'
        self.snapshot_document = {
            'schema_version': 1,
            'host': {'logical_cpus': 8},
            'libvirt': {'status': 'ok', 'discovered_count': 0, 'vms': []},
        }
        self.snapshot.write_text(json.dumps(self.snapshot_document))
        self.vm_uuid = '11111111-1111-4111-8111-111111111111'
        self.intent = {
            'schema_version': 1,
            'uuid': self.vm_uuid,
            'name': 'web-test',
            'desired_state': 'running',
            'resources': {'vcpus': 2, 'memory_mib': 2048},
        }
        self.intent_record = apply_vm_intent(
            self.intent,
            self.intent_root,
            expected_generation=0,
            reason='web-test',
        )
        self.plan = plan_vm(self.intent, self.snapshot_document)
        self.task = create_dry_run_task(
            self.plan,
            {
                **intent_preconditions(self.intent_record),
                'snapshot_sha256': self.plan['snapshot_sha256'],
            },
            self.task_root,
        )
        handler = make_handler(
            self.config_root,
            self.snapshot,
            self.token,
            self.intent_root,
            self.task_root,
        )
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def _request(self, path, auth=True, method='GET'):
        headers = {'Authorization': basic_auth_value(self.token)} if auth else {}
        return urlopen(Request(self.base + path, headers=headers, method=method), timeout=2)

    def test_health_is_public_but_api_requires_auth(self):
        with self._request('/healthz', auth=False) as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as raised:
            self._request('/api/status', auth=False)
        self.assertEqual(raised.exception.code, 401)
        with self.assertRaises(HTTPError) as raised:
            self._request('/api/vms/intents', auth=False)
        self.assertEqual(raised.exception.code, 401)

    def test_status_and_config_are_readable_when_authenticated(self):
        with self._request('/api/status') as response:
            self.assertEqual(json.load(response)['host']['logical_cpus'], 8)
        with self._request('/api/config') as response:
            self.assertEqual(json.load(response)['generation'], 1)

    def test_intent_and_plan_endpoints_are_read_only_views(self):
        with self._request('/api/vms/intents') as response:
            body = json.load(response)
        self.assertEqual(body['count'], 1)
        self.assertEqual(body['items'][0]['vm_uuid'], self.vm_uuid)

        with self._request(f'/api/vms/intents/{self.vm_uuid}') as response:
            record = json.load(response)
        self.assertEqual(record['generation'], 1)
        self.assertEqual(record['intent']['name'], 'web-test')

        with self._request(f'/api/vms/intents/{self.vm_uuid}/plan') as response:
            planned = json.load(response)
        self.assertEqual(planned['intent_generation'], 1)
        self.assertEqual(planned['intent_sha256'], record['intent_sha256'])
        self.assertEqual(planned['plan']['mode'], 'dry_run')
        self.assertFalse(planned['plan']['can_apply'])
        self.assertTrue(planned['plan']['actions'])
        self.assertTrue(all(action['executable'] is False for action in planned['plan']['actions']))

    def test_task_endpoints_expose_only_non_executable_records(self):
        with self._request('/api/tasks') as response:
            body = json.load(response)
        self.assertEqual(body['count'], 1)
        self.assertFalse(body['items'][0]['executable'])

        with self._request(f'/api/tasks/{self.task["task_id"]}') as response:
            task = json.load(response)
        self.assertEqual(task['task_id'], self.task['task_id'])
        self.assertEqual(task['mode'], 'dry_run')
        self.assertFalse(task['executable'])
        self.assertFalse(task['plan']['can_apply'])

    def test_mutation_is_rejected_without_store_side_effects(self):
        before_intent = read_vm_intent(self.vm_uuid, self.intent_root)
        before_tasks = list_tasks(self.task_root)
        with self.assertRaises(HTTPError) as raised:
            self._request(f'/api/vms/intents/{self.vm_uuid}', method='POST')
        self.assertEqual(raised.exception.code, 405)
        after_intent = read_vm_intent(self.vm_uuid, self.intent_root)
        after_tasks = list_tasks(self.task_root)
        self.assertEqual(after_intent['generation'], before_intent['generation'])
        self.assertEqual(
            [item['task_id'] for item in after_tasks],
            [item['task_id'] for item in before_tasks],
        )

    def test_plan_requires_available_observed_snapshot(self):
        self.snapshot.unlink()
        with self.assertRaises(HTTPError) as raised:
            self._request(f'/api/vms/intents/{self.vm_uuid}/plan')
        self.assertEqual(raised.exception.code, 503)

    def test_root_page_summarizes_read_only_vm_state(self):
        with self._request('/') as response:
            page = response.read().decode('utf-8')
        self.assertIn('Intenções persistidas', page)
        self.assertIn('Tarefas dry-run', page)
        self.assertIn('web-test', page)
        self.assertIn('Escrita em VMs</dt><dd>bloqueada', page)

    def test_mutation_is_rejected(self):
        with self.assertRaises(HTTPError) as raised:
            self._request('/api/config', method='POST')
        self.assertEqual(raised.exception.code, 405)

    def test_web_marker_authenticates_without_revealing_token(self):
        settings = read_config(self.config_root)['settings']
        settings['web']['port'] = self.server.server_port
        document = apply_settings(settings, self.config_root, expected_generation=1, reason='marker-test')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli_main([
                'web-marker',
                '--config-root', str(self.config_root),
                '--token-file', str(self.root / 'admin.token'),
                '--wait', '2',
            ])
        marker = output.getvalue().strip()
        self.assertEqual(code, 0)
        self.assertNotIn(self.token, marker)
        self.assertIn(f'config_generation={document["generation"]}', marker)
        self.assertRegex(marker, r'config_sha256=[0-9a-f]{64}')
        self.assertRegex(marker, r'token_sha256=[0-9a-f]{64}')
        self.assertIn('STOROS_WEB_READY auth=ok', marker)


if __name__ == '__main__':
    unittest.main()
