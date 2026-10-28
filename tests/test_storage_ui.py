import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class StorageUITests(unittest.TestCase):
    def test_assets_and_allowlist(self):
        html=(ROOT/'web/index.html').read_text()
        gateway=(ROOT/'tools/lan_gateway.py').read_text()
        server=(ROOT/'backend/server.py').read_text()
        for asset in ("/storage.js","/storage.css"):
            self.assertIn(asset,html)
            self.assertIn('"' + asset + '"',gateway)
        self.assertIn('"/api/storage"',gateway)
        self.assertIn('"/api/storage"',server)

    def test_no_destructive_actions_or_fictitious_smart(self):
        js=(ROOT/'web/storage.js').read_text()
        for forbidden in ("fetch(", "docker.sock", "mkfs", "mount(", "innerHTML", "formatDisk"):
            self.assertNotIn(forbidden,js)
        self.assertIn("SMART",js)
        self.assertIn("Indisponível",js)

    def test_existing_navigation_retained(self):
        html=(ROOT/'web/index.html').read_text()
        self.assertIn('data-target="storage"',html)
        self.assertIn('data-target="shares"',html)
        self.assertIn("Ver discos",html)

if __name__=="__main__":
    unittest.main()
