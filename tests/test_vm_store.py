import json
from pathlib import Path
import tempfile
import unittest

from storos_vm_store import (
    VMIntentStoreError,
    apply_vm_intent,
    list_vm_intent_revisions,
    list_vm_intents,
    read_vm_intent,
    rollback_vm_intent,
)

UUID = '11111111-2222-3333-4444-555555555555'


def intent(name='demo', vcpus=4):
    return {
        'schema_version': 1,
        'uuid': UUID,
        'name': name,
        'desired_state': 'running',
        'resources': {'vcpus': vcpus, 'memory_mib': 4096},
    }


def intent_v2(name='demo', vcpus=4):
    return {
        'schema_version': 2,
        'uuid': UUID,
        'name': name,
        'desired_state': 'running',
        'resources': {'vcpus': vcpus, 'memory_mib': 4096},
        'hardware': {
            'firmware': {'mode': 'efi'},
            'disks': [{
                'target': 'vda',
                'bus': 'virtio',
                'source': {'kind': 'file', 'value': '/var/lib/libvirt/images/demo.qcow2'},
                'format': 'qcow2',
                'readonly': False,
                'boot_order': 1,
            }],
            'interfaces': [{
                'mac': '52:54:00:12:34:56',
                'type': 'network',
                'source': {'network': 'default'},
                'model': 'virtio',
            }],
        },
    }


class VMIntentStoreTests(unittest.TestCase):
    def test_create_update_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = apply_vm_intent(intent(), tmp, expected_generation=0)
            second = apply_vm_intent(intent(vcpus=6), tmp, expected_generation=1)
            self.assertEqual(first['generation'], 1)
            self.assertEqual(second['generation'], 2)
            self.assertEqual(read_vm_intent(UUID, tmp), second)
            self.assertEqual([r['generation'] for r in list_vm_intent_revisions(UUID, tmp)], [1, 2])
            self.assertEqual([r['vm_uuid'] for r in list_vm_intents(tmp)], [UUID])
            self.assertEqual((Path(tmp) / UUID / 'current.json').stat().st_mode & 0o777, 0o640)
            self.assertEqual((Path(tmp) / UUID / '.lock').stat().st_mode & 0o777, 0o600)

    def test_v2_round_trip_is_persisted_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            wanted = intent_v2()
            wanted['hardware']['interfaces'][0]['mac'] = '52:54:00:AA:BB:CC'
            record = apply_vm_intent(wanted, tmp, expected_generation=0)
            self.assertEqual(record['intent']['schema_version'], 2)
            self.assertEqual(record['intent']['hardware']['interfaces'][0]['mac'], '52:54:00:aa:bb:cc')
            self.assertEqual(read_vm_intent(UUID, tmp), record)

    def test_v1_hash_survives_v2_update_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = apply_vm_intent(intent(name='legacy'), tmp, expected_generation=0)
            second = apply_vm_intent(intent_v2(name='modern'), tmp, expected_generation=1)
            rolled = rollback_vm_intent(UUID, 1, tmp, expected_generation=2)
            self.assertEqual(first['intent']['schema_version'], 1)
            self.assertNotIn('hardware', first['intent'])
            self.assertEqual(second['intent']['schema_version'], 2)
            self.assertEqual(rolled['generation'], 3)
            self.assertEqual(rolled['intent'], first['intent'])
            self.assertEqual(rolled['intent_sha256'], first['intent_sha256'])
            self.assertEqual(rolled['reason'], 'rollback:1')
            self.assertEqual(
                [r['intent']['schema_version'] for r in list_vm_intent_revisions(UUID, tmp)],
                [1, 2, 1],
            )

    def test_generation_conflict_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            apply_vm_intent(intent(), tmp, expected_generation=0)
            with self.assertRaises(VMIntentStoreError):
                apply_vm_intent(intent(vcpus=8), tmp, expected_generation=0)

    def test_rollback_creates_new_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = apply_vm_intent(intent(name='one'), tmp, expected_generation=0)
            apply_vm_intent(intent(name='two'), tmp, expected_generation=1)
            rolled = rollback_vm_intent(UUID, 1, tmp, expected_generation=2)
            self.assertEqual(rolled['generation'], 3)
            self.assertEqual(rolled['intent'], first['intent'])
            self.assertEqual(rolled['reason'], 'rollback:1')

    def test_tampered_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = apply_vm_intent(intent(), tmp, expected_generation=0)
            path = Path(tmp) / UUID / 'current.json'
            record['intent_sha256'] = '0' * 64
            path.write_text(json.dumps(record))
            with self.assertRaises(VMIntentStoreError):
                read_vm_intent(UUID, tmp)


if __name__ == '__main__':
    unittest.main()
