import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class UsbPreviewSafety(unittest.TestCase):
    def test_no_blueprint_or_injected_credential(self):
        script = (ROOT / "installer/build-usb-preview.sh").read_text()
        self.assertNotIn("--blueprint", script)
        self.assertNotIn("authorized_keys", script)
        self.assertIn("requires a VM", script)

    def test_ssh_server_masked(self):
        file = (ROOT / "installer/Containerfile.usb-preview").read_text()
        self.assertIn("/dev/null /usr/lib/systemd/system/sshd.service", file)
        self.assertIn("COPY web/", file)
        self.assertIn("FROM localhost/storos:v0.3.0", file)

    def test_raw_test_only_virtual_backing(self):
        script = (ROOT / "tools/test-boot-raw.sh").read_text()
        self.assertIn("qemu-img create -f qcow2 -F raw -b", script)
        self.assertIn("source network=", script)
        self.assertIn("virsh autostart --disable", script)
        self.assertIn("listen='127.0.0.1'", script)
