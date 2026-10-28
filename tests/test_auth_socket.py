import http.client
import json
import socket
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from auth_socket import create_server
from security_core import AccountStore, IdentityError


class SocketHTTP(http.client.HTTPConnection):
    def __init__(self, path):
        self.path = str(path)
        super().__init__("localhost", timeout=4)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


class PrivateAuthIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / "secret"
        self.directory.mkdir(mode=0o700)
        self.password = "test-only unique local password"
        AccountStore(self.directory / "accounts.json").bootstrap_admin("storadmin", self.password)
        self.server = create_server(self.directory)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        (self.directory / "auth.sock").unlink(missing_ok=True)

    def req(self, method, path, data=None, headers=None):
        conn = SocketHTTP(self.directory / "auth.sock")
        headers = dict(headers or {})
        body = None if data is None else json.dumps(data).encode()
        if data is not None:
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        status, resp_headers = response.status, dict(response.getheaders())
        payload = json.loads(response.read())
        conn.close()
        return status, payload, resp_headers

    def login(self):
        code, body, _ = self.req("POST", "/v1/login", {
            "username": "storadmin", "password": self.password})
        self.assertEqual(code, 200)
        return body["session_token"], body["csrf_token"]

    def test_socket_permissions_and_health(self):
        path = self.directory / "auth.sock"
        self.assertTrue(stat.S_ISSOCK(path.stat().st_mode))
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertFalse(hasattr(self.server, "server_port"))
        code, body, _ = self.req("GET", "/v1/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["transport"], "unix-socket")
        self.assertFalse(body["web_login_exposed"])
        self.assertFalse(body["host_mutations"])

    def test_login_me_csrf_logout_and_audit(self):
        self.assertEqual(self.req("GET", "/v1/me")[0], 401)
        token, csrf = self.login()
        code, body, headers = self.req("GET", "/v1/me",
            headers={"Authorization": "Bearer " + token})
        self.assertEqual(code, 200)
        self.assertEqual(body["role"], "admin")
        self.assertFalse(body["host_mutations"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertNotIn("Set-Cookie", headers)
        self.assertEqual(self.req("POST", "/v1/logout", headers={
            "Authorization": "Bearer " + token, "X-StorOS-CSRF": "wrong"})[0], 403)
        self.assertEqual(self.req("POST", "/v1/logout", headers={
            "Authorization": "Bearer " + token, "X-StorOS-CSRF": csrf})[0], 200)
        self.assertEqual(self.req("GET", "/v1/me", headers={
            "Authorization": "Bearer " + token})[0], 401)
        audit = (self.directory / "audit.jsonl").read_text()
        for action in ('"action":"auth.login"', '"action":"auth.logout"'):
            self.assertIn(action, audit)
        for secret in (token, csrf, self.password):
            self.assertNotIn(secret, audit)
        self.assertEqual(stat.S_IMODE((self.directory / "audit.jsonl").stat().st_mode), 0o600)

    def test_failed_login_throttled(self):
        for _ in range(5):
            self.assertEqual(self.req("POST", "/v1/login", {
                "username": "storadmin", "password": "some incorrect passphrase"})[0], 401)
        self.assertEqual(self.req("POST", "/v1/login", {
            "username": "storadmin", "password": self.password})[0], 429)

    def test_host_mutations_never_reachable(self):
        token, csrf = self.login()
        headers = {"Authorization": "Bearer " + token, "X-StorOS-CSRF": csrf}
        for method, path in (("POST", "/v1/storage/format"), ("POST", "/v1/docker/compose"),
                             ("DELETE", "/v1/me"), ("PUT", "/v1/me"), ("PATCH", "/v1/me")):
            self.assertIn(self.req(method, path, headers=headers)[0], (404, 405))
        self.assertEqual(self.req("POST", "/v1/health")[0], 405)

    def test_invalid_input_and_private_directory(self):
        self.assertEqual(self.req("POST", "/v1/login", {
            "username": "storadmin", "password": self.password, "role": "admin"})[0], 400)
        self.assertEqual(self.req("POST", "/v1/login", {
            "username": "storadmin", "password": "x" * 2200})[0], 400)
        with self.assertRaises(IdentityError):
            create_server(self.directory)
        self.directory.chmod(0o755)
        with self.assertRaises(IdentityError):
            create_server(self.directory)


if __name__ == "__main__":
    unittest.main()
