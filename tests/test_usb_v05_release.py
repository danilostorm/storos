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
        self.assertIn("COPY tools/storosctl.py", docker)
        self.assertNotIn("passwd", docker)
        self.assertNotIn("ssh-key", docker)
    def test_build_script_rejects_wrong_environment(self):
        source = (ROOT/"installer/build-ui-v05.sh").read_text()
        self.assertIn("systemd-detect-virt --vm", source)
        self.assertIn("image-builder build", source)
        self.assertIn('[[ ! -e "$artifact"', source)
        self.assertIn("flock -n 9", source)
        self.assertIn('mktemp -d "$OUT/.build-staging.', source)
        self.assertIn('python3 tools/check_usb_image.py "$STAGE/$NAME"', source)
        self.assertIn('sha256sum "$NAME" > "$NAME.sha256"', source)
        self.assertIn('mv -- "$STAGE/$NAME" "$RAW"', source)
        self.assertIn('printf \'Structure and SHA-256 recorded.', source)
        self.assertLess(source.index("python3 tools/check_usb_image.py"),
                        source.index('mv -- "$STAGE/$NAME"'))
        self.assertLess(source.index('mv -- "$STAGE/$NAME.structure.json"'),
                        source.index("STOROS_V05_RAW_STRUCTURE_VERIFIED"))
        self.assertNotIn("dd if=", source)
        self.assertNotIn("of=/dev/", source)
    def test_seabios_smoke_is_non_destructive(self):
        source = (ROOT/"tools/test-boot-raw-bios.sh").read_text()
        self.assertIn('qemu-img create -f qcow2 -F raw -b "$RAW"', source)
        self.assertIn('test ! -L "$RAW"', source)
        self.assertIn('test ! -e "$file"', source)
        self.assertIn("virsh -c qemu:///system start", source)
        self.assertIn("listen='127.0.0.1'", source)
        for forbidden in ("<interface", "<hostdev", "<loader", "<nvram",
                          "dd if=", "of=/dev/", "mkfs.", "virsh destroy",
                          "virsh undefine", "rm -rf"):
            self.assertNotIn(forbidden, source)

    def test_notebook_guide_identifies_legacy_firmware_and_limitations(self):
        guide = (ROOT / "docs/USB_V05_NOTEBOOK_GUIDE_PTBR.md").read_text(encoding="utf-8")
        for value in ("BIOS Legacy", "balenaEtcher", "SHA-256",
                      "de2ac025105f9b82e9fed350ba7664c9b46a3c19d905186cf93bbce59270d004",
                      "não foi testado", "não instala automaticamente"):
            self.assertIn(value.casefold(), guide.casefold())
        self.assertIn("USB_V05_NOTEBOOK_GUIDE_PTBR.md",
                      (ROOT/"docs/USB_NOTEBOOK_TEST.md").read_text(encoding="utf-8"))

    def test_documentation_does_not_misstate_release(self):
        content = (ROOT/"docs/USB_V05_BUILD_STATUS.md").read_text()
        self.assertIn("Boot UEFI/OVMF", content)
        self.assertIn("Boot BIOS Legacy/SeaBIOS", content)
        self.assertIn("USB físico ainda não validado", content)
        self.assertIn("STOROS_V05_RAW_STRUCTURE_VERIFIED", content)
        self.assertIn("SHA-256", content)
        self.assertNotIn("No v0.5 RAW/IMG", content)

if __name__ == "__main__":
    unittest.main()
