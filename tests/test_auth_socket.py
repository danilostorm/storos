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

    def test_app_routes_disabled_by_default(self):
        token, csrf = self.login()
        headers = {"Authorization": "Bearer " + token, "X-StorOS-CSRF": csrf}
        self.assertEqual(self.req("POST", "/v1/apps/plan",
            {"slug":"nginx"}, headers=headers)[0], 403)
        self.assertEqual(self.req("POST", "/v1/apps/install",
            {"slug":"nginx","accepted_sha256":"0"*64}, headers=headers)[0], 403)
        self.assertEqual(self.req("GET", "/v1/apps/installed",
            headers={"Authorization": "Bearer " + token})[0], 403)

    def test_app_plan_and_install_admin_csrf_when_explicitly_enabled(self):
        from app_manager import plan
        class FakeManager:
            def __init__(self):
                self.calls=[]
            def list_installed(self):
                return [{"project":"storos-nginx","state":"configured","running":None}]
            def install(self, slug, accepted_sha256):
                self.calls.append((slug, accepted_sha256))
                return {"name":"storos-nginx","state":"deployed"}
        fake=FakeManager()
        self.server.app_manager=fake
        token, csrf=self.login()
        auth={"Authorization":"Bearer "+token}
        self.assertEqual(self.req("POST", "/v1/apps/plan",{"slug":"nginx"},headers=auth)[0],403)
        headers={**auth,"X-StorOS-CSRF":csrf}
        code, app, _ = self.req("POST", "/v1/apps/plan",{"slug":"nginx"},headers=headers)
        self.assertEqual(code,200)
        self.assertEqual(app["project"],"storos-nginx")
        self.assertEqual(app["sha256"],plan("nginx")["sha256"])
        self.assertEqual(self.req("POST","/v1/apps/install",{
            "slug":"nginx","accepted_sha256":app["sha256"]
        },headers=headers)[0],200)
        self.assertEqual(fake.calls,[("nginx",app["sha256"])])
        code, rows, _=self.req("GET","/v1/apps/installed",headers=auth)
        self.assertEqual(code,200)
        self.assertEqual(rows["items"][0]["project"],"storos-nginx")
        audit=(self.directory/"audit.jsonl").read_text()
        self.assertIn('"action":"apps.install"',audit)
        self.assertNotIn(token,audit)
        self.assertNotIn(csrf,audit)

    def test_lifecycle_control_requires_admin_csrf_and_explicit_enable(self):
        class FakeManager:
            def __init__(self):
                self.requests = []
            def control(self, slug, action, digest):
                self.requests.append((slug, action, digest))
                return {"slug": slug, "action": action, "state": "stopped"}
        token, csrf = self.login()
        auth = {"Authorization": "Bearer " + token}
        payload = {"slug": "nginx", "action": "stop",
                   "accepted_sha256": __import__("app_manager").plan("nginx")["sha256"]}
        self.assertEqual(self.req("POST", "/v1/apps/control", payload,
                                  headers={**auth, "X-StorOS-CSRF": csrf})[0], 403)
        fake = FakeManager()
        self.server.app_manager = fake
        self.assertEqual(self.req("POST", "/v1/apps/control", payload,
                                  headers=auth)[0], 403)
        self.assertEqual(self.req("POST", "/v1/apps/control", payload,
                                  headers={**auth, "X-StorOS-CSRF": "invalid"})[0], 403)
        self.assertEqual(fake.requests, [])
        ok, response, _ = self.req("POST", "/v1/apps/control", payload,
                                  headers={**auth, "X-StorOS-CSRF": csrf})
        self.assertEqual(ok, 200)
        self.assertEqual(response["action"], "stop")
        self.assertEqual(fake.requests, [("nginx", "stop", payload["accepted_sha256"])])
        audit = (self.directory / "audit.jsonl").read_text()
        self.assertIn('"action":"apps.stop"', audit)
        self.assertNotIn(token, audit)
        self.assertNotIn(csrf, audit)

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
