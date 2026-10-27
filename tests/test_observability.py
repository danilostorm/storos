import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import observability


class RealObservabilityTests(unittest.TestCase):
    def test_cpu_percent_uses_os_ticks(self):
        with mock.patch.object(observability, '_cpu_totals', side_effect=[(100, 30), (200, 70)]):
            with mock.patch.object(observability.time, 'sleep'):
                self.assertEqual(observability.cpu_percent(), 60.0)

    def test_cpu_does_not_fabricate_missing(self):
        with mock.patch.object(observability, '_cpu_totals', return_value=None):
            self.assertIsNone(observability.cpu_percent())

    def test_empty_device_list(self):
        with mock.patch.object(observability, '_command', return_value='{"blockdevices":[]}'):
            result = observability.storage_overview()
            self.assertEqual(result['items'], [])
            self.assertTrue(result['available'])

    def test_immutable_small_root_uses_var(self):
        with mock.patch.object(observability, 'mount_usage',
            side_effect=lambda path: {'total_bytes': 5000000,'percent': 100}
            if path == '/' else {'total_bytes': 9 * 1024**3,'percent': 45}):
            with mock.patch.object(observability, '_command', return_value='{"blockdevices":[]}'):
                d=observability.storage_overview()
                self.assertEqual(d['root_mount'], '/var')
                self.assertEqual(d['root']['percent'], 45)

    def test_disk_usage_unknown_is_null(self):
        result=observability.mount_usage('/path/that/does/not/exist')
        self.assertIsNone(result)

    def test_compose_unavailable_does_not_invent_stacks(self):
        with mock.patch.object(observability, '_command', return_value=None):
            d=observability.compose_overview()
            self.assertFalse(d['available'])
            self.assertEqual(d['items'], [])

if __name__=='__main__':
    unittest.main()
