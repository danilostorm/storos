import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"backend"))
import storosctl
from auth_socket import create_server
from security_core import AccountStore

class LocalOperatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)/"admin"
        self.folder.mkdir(mode=0o700)
        AccountStore(self.folder/"accounts.json").bootstrap_admin(
            "storadmin","private test password for CLI")
        self.server=create_server(self.folder)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        (self.folder/"auth.sock").unlink(missing_ok=True)

    def test_status_cli_uses_only_private_socket(self):
        self.assertEqual(storosctl.main(["--socket",str(self.folder/"auth.sock"),"status"]),0)

    def test_plan_cli_logs_in_and_revokes_session(self):
        with patch("builtins.input",return_value="storadmin"):
            with patch.object(storosctl.getpass,"getpass",
                              return_value="private test password for CLI"):
                # manager is disabled: request is properly denied
                with self.assertRaises(storosctl.OperatorError):
                    storosctl.main(["--socket",str(self.folder/"auth.sock"),"plan","nginx"])

    def test_lifecycle_cli_requires_typed_name_and_uses_csrf(self):
        from app_manager import plan
        calls = []
        approved = plan("nginx")
        def fake_request(sock, method, endpoint, payload=None, token=None, csrf=None):
            calls.append((endpoint, payload, token, csrf))
            if endpoint == "/v1/login":
                return {"role":"admin", "session_token":"token-test", "csrf_token":"csrf-test"}
            if endpoint == "/v1/apps/plan":
                return approved
            if endpoint == "/v1/apps/control":
                return {"project":"storos-nginx","action":"stop","state":"stopped"}
            if endpoint == "/v1/logout":
                return {"signed_out": True}
            raise AssertionError(endpoint)
        with patch.object(storosctl, "request", side_effect=fake_request):
            with patch("builtins.input", side_effect=["storadmin", "nginx"]):
                with patch.object(storosctl.getpass, "getpass",
                                  return_value="test password not shared"):
                    result = storosctl.main(["--socket", "/tmp/test-auth.sock", "stop", "nginx"])
        self.assertEqual(result, 0)
        control = next(item for item in calls if item[0] == "/v1/apps/control")
        self.assertEqual(control[1]["action"], "stop")
        self.assertEqual(control[1]["accepted_sha256"], approved["sha256"])
        self.assertEqual(control[2:], ("token-test", "csrf-test"))
        self.assertEqual(calls[-1][0], "/v1/logout")

    def test_lifecycle_cli_wrong_confirmation_never_controls(self):
        from app_manager import plan
        calls = []
        def fake_request(sock, method, endpoint, payload=None, token=None, csrf=None):
            calls.append(endpoint)
            return ({"role":"admin", "session_token":"t", "csrf_token":"c"}
                    if endpoint == "/v1/login" else plan("nginx")
                    if endpoint == "/v1/apps/plan" else {"signed_out":True})
        with patch.object(storosctl, "request", side_effect=fake_request):
            with patch("builtins.input", side_effect=["storadmin", "wrong-name"]):
                with patch.object(storosctl.getpass, "getpass", return_value="dummy"):
                    with self.assertRaises(storosctl.OperatorError):
                        storosctl.main(["--socket", "/tmp/test-auth.sock", "restart", "nginx"])
        self.assertNotIn("/v1/apps/control", calls)
        self.assertEqual(calls[-1], "/v1/logout")

    def test_password_not_in_command_line(self):
        import inspect
        source=inspect.getsource(storosctl)
        self.assertIn("getpass.getpass",source)
        self.assertNotIn('parser.add_argument("--password"',source)
        self.assertNotIn("subprocess.run",source)

if __name__=="__main__":unittest.main()
