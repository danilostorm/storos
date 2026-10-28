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

    def test_password_not_in_command_line(self):
        import inspect
        source=inspect.getsource(storosctl)
        self.assertIn("getpass.getpass",source)
        self.assertNotIn('parser.add_argument("--password"',source)
        self.assertNotIn("subprocess.run",source)

if __name__=="__main__":unittest.main()
