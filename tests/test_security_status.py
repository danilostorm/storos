import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import security_core
import server


class SecurityPageTests(unittest.TestCase):
    def test_status_explicitly_denies_any_write_controls(self):
        value = security_core.security_status()
        self.assertTrue(value["available"])
        self.assertFalse(value["login_enabled"])
        self.assertFalse(value["native_sessions_enabled"])
        self.assertFalse(value["privileged_service_enabled"])
        self.assertFalse(value["mutations_enabled"])
        self.assertNotIn("password_hashes", value)
        self.assertEqual(value["mode"], "foundation-only")

    def test_route_and_gateway_allowlist_present(self):
        gateway = (ROOT / "tools/lan_gateway.py").read_text()
        self.assertIn('"/api/security/status"', gateway)
        self.assertIn("/api/security/status", server.API)
        self.assertEqual(server.API["/api/security/status"]()["mutations_enabled"], False)
        self.assertIn("def do_POST(self):", gateway)

    def test_security_menu_and_renderer(self):
        html = (ROOT / "web/index.html").read_text()
        app = (ROOT / "web/app.js").read_text()
        modules = (ROOT / "web/modules.js").read_text()
        self.assertIn('data-target="security"', html)
        self.assertIn("security:'Segurança'", app)
        self.assertIn('view === "security"', modules)
        self.assertIn("Não habilitado", modules)
        self.assertLess(modules.index('if (view === "security")'), modules.index('if (!d)'))
        self.assertIn('["Operações de alteração"', modules)


if __name__ == "__main__":
    unittest.main()
