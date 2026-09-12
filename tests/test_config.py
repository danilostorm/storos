import json
from pathlib import Path
import tempfile
import unittest

from storos_config import ConfigError, apply_settings, default_settings, ensure_admin_token, init_config, read_config, rollback_config


class ConfigStoreTests(unittest.TestCase):
    def test_init_apply_and_rollback_create_monotonic_revisions(self):
        with tempfile.TemporaryDirectory() as directory:
            first = init_config(directory)
            self.assertEqual(first['generation'], 1)
            settings = default_settings()
            settings['web']['port'] = 8181
            second = apply_settings(settings, directory, expected_generation=1, reason='test')
            self.assertEqual(second['generation'], 2)
            self.assertEqual(read_config(directory)['settings']['web']['port'], 8181)
            third = rollback_config(1, directory, expected_generation=2)
            self.assertEqual(third['generation'], 3)
            self.assertEqual(third['settings']['web']['port'], 8080)
            revisions = sorted((Path(directory) / 'revisions').glob('*.json'))
            self.assertEqual([p.name for p in revisions], ['000001.json', '000002.json', '000003.json'])

    def test_optimistic_generation_conflict_preserves_current(self):
        with tempfile.TemporaryDirectory() as directory:
            init_config(directory)
            settings = default_settings()
            settings['web']['port'] = 8181
            with self.assertRaises(ConfigError):
                apply_settings(settings, directory, expected_generation=99)
            self.assertEqual(read_config(directory)['generation'], 1)

    def test_non_loopback_requires_explicit_insecure_lan_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            init_config(directory)
            settings = default_settings()
            settings['web']['listen_host'] = '0.0.0.0'
            with self.assertRaises(ConfigError):
                apply_settings(settings, directory)
            settings['wec']['allow_insecure_lan'] = True
            applied = apply_settings(settings, directory)
            self.assertEqual(applied['settings']['web']['listen_host'], '0.0.0.0')

    def test_vm_write_cannot_be_enabled(self):
        with tempfile.TemporaryDirectory() as directory:
            init_config(directory)
            settings = default_settings()
            settings['features']['vm_write_enabled'] = True
            with self.assertRaises(ConfigError):
                apply_settings(settings, directory)

    def test_admin_token_is_persistent_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'auth' / 'admin.token'
            first = ensure_admin_token(path)
            second = ensure_admin_token(path)
            self.assertEqual(first, second)
            self.assertGreaterEqual(len(first), 32)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
