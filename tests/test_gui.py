import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class GuiConfigurationTests(unittest.TestCase):
    def test_kiosk_local_only(self):
        session=(ROOT/'gui/storos-gui-session').read_text()
        self.assertIn('http://127.0.0.1:8765/', session)
        self.assertIn('--kiosk', session)
        self.assertNotIn('0.0.0.0:', session)

    def test_headless_and_gui_separate(self):
        gui=(ROOT/'installer/Containerfile.gui').read_text()
        base=(ROOT/'installer/Containerfile').read_text()
        self.assertIn('graphical.target', gui)
        self.assertNotIn('graphical.target', base)
        self.assertIn('/usr/etc/lightdm/lightdm.conf.d/', gui)

    def test_unprivileged_kiosk_user(self):
        u=(ROOT/'gui/storos-gui.sysusers').read_text()
        self.assertIn('storos-gui', u)
        self.assertNotIn('wheel', u)
        self.assertNotIn('sudo', u)
