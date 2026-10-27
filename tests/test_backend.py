import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from server import parse_meminfo, system_status, run_readonly

class StorOSTest(unittest.TestCase):
    def test_meminfo(self):
        sample = "MemTotal: 2048 kB\nMemAvailable: 1024 kB\n"
        self.assertEqual(parse_meminfo(sample)["MemTotal"], 2097152)
        self.assertEqual(parse_meminfo(sample)["MemAvailable"], 1048576)

    def test_status_safe_shape(self):
        status = system_status()
        self.assertIn("host", status)
        self.assertEqual(status["mode"], "read-only prototype")
        self.assertGreaterEqual(status["ram_total_bytes"], 0)

    def test_missing_executable(self):
        result = run_readonly(["storos-command-does-not-exist"])
        self.assertFalse(result["available"])

if __name__ == "__main__":
    unittest.main()
