import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class USBV05ReleaseTests(unittest.TestCase):
    def test_preview_is_versioned_and_still_read_only(self):
        page = (ROOT/"web/index.html").read_text()
        self.assertIn("v0.5", page)
        docker = (ROOT/"installer/Containerfile.ui-v05").read_text()
        self.assertIn("FROM localhost/storos:usb-preview", docker)
        self.assertIn("COPY web/", docker)
        self.assertIn("COPY backend/", docker)
        self.assertNotIn("passwd", docker)
        self.assertNotIn("ssh-key", docker)
    def test_build_script_rejects_wrong_environment(self):
        source = (ROOT/"installer/build-ui-v05.sh").read_text()
        self.assertIn("systemd-detect-virt --vm", source)
        self.assertIn("image-builder build", source)
        self.assertIn("test ! -e", source)
        self.assertNotIn("dd if=", source)
        self.assertNotIn("of=/dev/", source)
    def test_documentation_does_not_misstate_release(self):
        content = (ROOT/"docs/USB_V05_BUILD_STATUS.md").read_text()
        self.assertIn("No v0.5 RAW/IMG", content)
        self.assertIn("Legacy", content)
        self.assertIn("UEFI", content)

if __name__ == "__main__":
    unittest.main()
