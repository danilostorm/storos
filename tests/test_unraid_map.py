import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import study_unraid_main

class ReverseEngineeringEvidenceTests(unittest.TestCase):
    def test_allowlisted_structure_only(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            path = root / "dynamix/ArrayDevices.page"
            path.parent.mkdir(parents=True)
            path.write_text("main_filter array_devices disk_status fsState")
            result = study_unraid_main.examine(root)
            self.assertTrue(result["array"]["present"])
            self.assertEqual(result["array"]["symbols_detected"],
                ["main_filter", "array_devices", "disk_status", "fsState"])
            self.assertFalse(result["pools"]["present"])
            self.assertFalse(any("source" in k for k in result["array"]))
    def test_mapping_has_no_php_source(self):
        text = (ROOT / "docs/UNRAID_MAIN_STATIC_MAP.json").read_text()
        for forbidden in ("<?php", "<script", "password="):
            self.assertNotIn(forbidden, text)
if __name__ == "__main__":
    unittest.main()
