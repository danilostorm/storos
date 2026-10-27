import unittest
import importlib.util
import ipaddress
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("storos_gateway", ROOT / "tools" / "lan_gateway.py")
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)

class GatewaySafetyTests(unittest.TestCase):
    def test_read_only_allowlist(self):
        self.assertIn("/api/status", gw.ALLOWED)
        self.assertIn("/", gw.ALLOWED)
        self.assertNotIn("/api/shutdown", gw.ALLOWED)
        self.assertNotIn("/etc/passwd", gw.ALLOWED)

    def test_lan_boundary(self):
        self.assertIn(ipaddress.ip_address("192.168.30.10"), gw.LAN)
        self.assertNotIn(ipaddress.ip_address("100.99.136.79"), gw.LAN)
        self.assertNotIn(ipaddress.ip_address("8.8.8.8"), gw.LAN)
