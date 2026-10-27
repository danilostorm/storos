import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import apps

class AppsTests(unittest.TestCase):
    def test_catalog_has_unique_ids(self):
        rows = apps.catalog()["items"]
        self.assertGreaterEqual(len(rows), 6)
        self.assertEqual(len({row["slug"] for row in rows}), len(rows))
        self.assertFalse(apps.catalog()["installation_enabled"])

    def test_compose_generated_from_allowlist(self):
        for slug in apps.CATALOG:
            data = apps.compose_preview(slug)
            self.assertEqual(json.loads(data["compose"])["name"], "storos-" + slug)
            self.assertIn("docker compose", data["launch_command"])

    def test_untrusted_slug_rejected(self):
        with self.assertRaises(ValueError):
            apps.compose_preview("../../etc/passwd")

    def test_bad_hub_query_rejected_before_network(self):
        for query in ("", "x", "http://127.0.0.1:80", "x?" , "a" * 60):
            with self.assertRaises(ValueError):
                apps.hub_search(query)

    def test_engine_never_grants_dashboard_control(self):
        self.assertFalse(apps.engine()["control_enabled"])

if __name__ == "__main__":
    unittest.main()
