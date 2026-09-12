from pathlib import Path
import tempfile
import unittest

from storos_agent import read_boot_state, record_boot


class BootStateTests(unittest.TestCase):
    def test_distinct_boot_ids_increment_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / 'boot-state.json'
            boot_id = root / 'boot_id'
            boot_id.write_text('11111111-1111-4111-8111-111111111111\n')
            self.assertEqual(record_boot(state, boot_id)['boot_count'], 1)
            self.assertEqual(record_boot(state, boot_id)['boot_count'], 1)
            boot_id.write_text('22222222-2222-4222-8222-222222222222\n')
            self.assertEqual(record_boot(state, boot_id)['boot_count'], 2)
            self.assertEqual(read_boot_state(state)['last_boot_id'], '22222222-2222-4222-8222-222222222222')

    def test_state_permissions_are_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / 'boot-state.json'
            boot_id = root / 'boot_id'
            boot_id.write_text('33333333-3333-4333-8333-333333333333\n')
            record_boot(state, boot_id)
            self.assertEqual(state.stat().st_mode & 0o777, 0o640)

    def test_invalid_boot_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            boot_id = root / 'boot_id'
            boot_id.write_text('invalid\n')
            with self.assertRaises(ValueError):
                record_boot(root / 'boot-state.json', boot_id)


if __name__ == '__main__':
    unittest.main()
