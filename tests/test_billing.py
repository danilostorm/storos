import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from billing import configured_model, estimated_item, split_plan

def example(**patch):
    args = dict(cpu_watts=135, board_watts=95, ram_watts=24, threads=40,
                host_ram_gib=128, vcpus=4, ram_gib=8, gpu_watts=0, hours=24,
                electricity_kwh=1, uptime_hour=0, plan_price=60,
                total_cycle_gb=100, item_cycle_gb=25)
    args.update(patch)
    return estimated_item(**args)

class BillingTests(unittest.TestCase):
    def test_cpu_allocation_matches_tower_formula(self):
        row = example()
        self.assertEqual(row["watts_cpu"], 13.5)
        self.assertEqual(row["watts_platform"], 9.5)
        self.assertEqual(row["watts_ram"], 1.5)
        self.assertEqual(row["watts_total"], 24.5)
        self.assertEqual(row["kwh"], 0.588)
        self.assertEqual(row["cost_energy"], 0.59)
        self.assertEqual(row["cost_internet"], 15.0)
        self.assertEqual(row["cost_total"], 15.59)

    def test_gpu_only_full_passthrough(self):
        self.assertEqual(example(gpu_watts=75)["watts_gpu"], 75)
        self.assertEqual(example(gpu_watts=75)["watts_total"], 99.5)

    def test_plan_shares_sum_exactly(self):
        rows = split_plan(60, [("vm:one", 1), ("vm:two", 1), ("vm:three", 1)])
        self.assertEqual(sum(int(r["cost"] * 100) for r in rows), 6000)
        self.assertEqual(max(r["cost"] for r in rows), 20.0)

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            example(threads=0)
        with self.assertRaises(ValueError):
            example(total_cycle_gb=10, item_cycle_gb=20)

    def test_default_profile_has_no_fake_watts(self):
        profile = configured_model()
        self.assertTrue(profile["threads"] > 0)
        self.assertTrue(all(x["watts"] == 0 for x in profile["hardware"]))

if __name__ == "__main__":
    unittest.main()
