"""Integration tests: browser gateway -> private Unix auth, no host write routes."""
import base64
import http.client
import importlib.util
import ipaddress
import json
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "tools"))

from auth_socket import create_server
from security_core import AccountStore
from native_auth_bridge import AuthBridge, AuthBridgeError, cookie_token

spec = importlib.util.spec_from_file_location("auth_test_gateway", ROOT / "tools/lan_gateway.py")
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


class NativeWebIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.private = tempfile.TemporaryDirectory()
        self.addCleanup(self.private.cleanup)
        self.path = Path(self.private.name) / "secret"
        self.path.mkdir(mode=0o700)
        self.password = "private local web login test password"
        AccountStore(self.path / "accounts.json").bootstrap_admin("storadmin", self.password)
        self.auth = create_server(self.path)
        self.auth_thread = threading.Thread(target=self.auth.serve_forever, daemon=True)
        self.auth_thread.start()
        self.addCleanup(self.close_auth)
        self.gateway = ThreadingHTTPServer(("127.0.0.1", 0), gateway.Gateway)
        self.gateway.user_password = "storos:lab-protected-credential-123"
        self.gateway.native_auth_bridge = AuthBridge(self.path / "auth.sock")
        self.gateway.upstream_port = 1
        self.web_thread = threading.Thread(target=self.gateway.serve_forever, daemon=True)
        self.web_thread.start()
        self.addCleanup(self.close_web)
        self.lan = mock.patch.object(gateway, "LAN", ipaddress.ip_network("127.0.0.0/8"))
        self.lan.start()
        self.addCleanup(self.lan.stop)
        self.basic = "Basic " + base64.b64encode(
            self.gateway.user_password.encode()).decode()
        self.origin = "https://192.168.30.10:" + str(self.gateway.server_port)
        self.host = "192.168.30.10:" + str(self.gateway.server_port)

    def close_auth(self):
        self.auth.shutdown()
        self.auth.server_close()
        self.auth_thread.join(timeout=4)
        (self.path / "auth.sock").unlink(missing_ok=True)

    def close_web(self):
        self.gateway.shutdown()
        self.gateway.server_close()
        self.web_thread.join(timeout=4)

    def request(self, method, path, payload=None, authorized=True, origin=True, extra=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.gateway.server_port, timeout=5)
        headers = {"Host": self.host}
        if authorized:
            headers["Authorization"] = self.basic
        if origin and method == "POST":
            headers["Origin"] = self.origin
        headers.update(extra or {})
        body = None
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        elif method == "POST":
            body = ""
        conn.request(method, path, body=body, headers=headers)
        res = conn.getresponse()
        raw = res.read()
        code = res.status
        fields = dict(res.getheaders())
        conn.close()
        try:
            decoded = json.loads(raw) if raw else {}
        except ValueError:
            decoded = {}
        return code, decoded, fields

    def login(self):
        status, value, headers = self.request("POST", "/api/native/login", {
            "username": "storadmin", "password": self.password,
        })
        self.assertEqual(status, 200)
        self.assertNotIn("session_token", value)
        self.assertNotIn("password", json.dumps(value))
        self.assertIn("HttpOnly", headers.get("Set-Cookie", ""))
        self.assertIn("Secure", headers.get("Set-Cookie", ""))
        return headers["Set-Cookie"].split(";", 1)[0], value["csrf_token"]

    def test_basic_auth_still_required(self):
        status, _, _ = self.request("GET", "/api/native/status", authorized=False)
        self.assertEqual(status, 401)
        status, _, _ = self.request("POST", "/api/native/login",
            {"username":"storadmin","password":self.password}, authorized=False)
        self.assertEqual(status, 401)

    def test_native_login_me_logout(self):
        status, value, _ = self.request("GET", "/api/native/status")
        self.assertEqual(status, 200)
        self.assertTrue(value["enabled"])
        self.assertFalse(value["host_mutations"])
        cookie, csrf = self.login()
        status, value, _ = self.request("GET", "/api/native/me", extra={"Cookie":cookie})
        self.assertEqual(status, 200)
        self.assertEqual(value["name"], "storadmin")
        self.assertFalse(value["host_mutations"])
        status, _, _ = self.request("POST", "/api/native/logout",
                                    extra={"Cookie":cookie,"X-StorOS-CSRF":"bad"})
        self.assertEqual(status, 403)  # malformed CSRF denied at gateway
        status, value, headers = self.request("POST", "/api/native/logout",
                                    extra={"Cookie":cookie,"X-StorOS-CSRF":csrf})
        self.assertEqual(status, 200)
        self.assertTrue(value["signed_out"])
        self.assertIn("Max-Age=0", headers["Set-Cookie"])
        self.assertEqual(self.request("GET", "/api/native/me",extra={"Cookie":cookie})[0],401)
        audit=(self.path/"audit.jsonl").read_text()
        self.assertNotIn(self.password,audit)
        self.assertNotIn(csrf,audit)

    def test_native_login_rejects_cross_origin(self):
        status, _, _ = self.request("POST", "/api/native/login",{
            "username":"storadmin","password":self.password}, origin=False)
        self.assertEqual(status, 403)
        status, _, _ = self.request("POST", "/api/native/login",{
            "username":"storadmin","password":self.password},
            extra={"Origin":"https://malicious.invalid"})
        self.assertEqual(status, 403)

    def test_login_disabled_by_default_and_no_mutations(self):
        self.gateway.native_auth_bridge = None
        status, value, _ = self.request("GET", "/api/native/status")
        self.assertEqual(status, 200)
        self.assertFalse(value["enabled"])
        status, _, _=self.request("POST","/api/native/login",{
            "username":"storadmin","password":self.password})
        self.assertEqual(status,403)
        for path in ("/api/native/apps/install", "/api/docker/install", "/api/format"):
            self.assertEqual(self.request("POST",path)[0],405)

    def test_private_socket_permission_and_cookie_checks(self):
        self.assertIsNone(cookie_token("__Host-storos_session=short"))
        self.assertIsNone(cookie_token("bad=foo"))
        self.assertIsNone(cookie_token("".join(["x"]*5000)))
        with self.assertRaises(AuthBridgeError):
            self.gateway.native_auth_bridge.request("POST", "/v1/apps/install")
        self.path.chmod(0o755)
        with self.assertRaises(AuthBridgeError):
            self.gateway.native_auth_bridge.request("GET", "/v1/me")


if __name__=="__main__":
    unittest.main()
