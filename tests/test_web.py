import base64
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from storos_config import basic_auth_value, ensure_admin_token, init_config
from storos_web import make_handler
from http.server import ThreadingHTTPServer


class WebPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        init_config(self.root / 'config')
        self.token = ensure_admin_token(self.root / 'admin.token')
        self.snapshot = self.root / 'status.json'
        self.snapshot.write_text(json.dumps({'schema_version': 1, 'host': {'logical_cpus': 8}, 'libvirt': {'status': 'ok', 'discovered_count': 0}}))
        handler = make_handler(self.root / 'config', self.snapshot, self.token)
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

    def test_status_and_config_are_readable_when_authenticated(self):
        with self._request('/api/status') as response:
            self.assertEqual(json.load(response)['host']['logical_cpus'], 8)
        with self._request('/api/config') as response:
            self.assertEqual(json.load(response)['generation'], 1)

    def test_mutation_is_rejected(self):
        with self.assertRaises(HTTPError) as raised:
            self._request('/api/config', method='POST')
        self.assertEqual(raised.exception.code, 405)


if __name__ == '__main__':
    unittest.main()
