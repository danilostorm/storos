import copy
import unittest

from storos_fingerprints import (
    decorate_plan_fingerprints,
    plan_fingerprint_sha256,
    snapshot_fingerprint_sha256,
)


class FingerprintTests(unittest.TestCase):
    def snapshot(self):
        return {
            'schema_version': 1,
            'source': 'simulation',
            'collection_started_at': 10.0,
            'collected_at': 11.0,
            'age_seconds': 1.0,
            'stale': False,
            'host': {'logical_cpus': 8},
            'libvirt': {
                'status': 'ok',
                'vms': [
                    {'uuid': '22222222-2222-2222-2222-222222222222', 'active': False},
                    {'uuid': '11111111-1111-1111-1111-111111111111', 'active': True},
                ],
                'errors': [],
            },
        }

    def test_snapshot_fingerprint_ignores_time_and_derived_freshness(self):
        first = self.snapshot()
        second = copy.deepcopy(first)
        second['collection_started_at'] = 100.0
        second['collected_at'] = 101.0
        second['age_seconds'] = 29.9
        second['stale'] = True
        second['libvirt']['vms'].reverse()
        self.assertEqual(
            snapshot_fingerprint_sha256(first),
            snapshot_fingerprint_sha256(second),
        )

    def test_snapshot_fingerprint_changes_with_observed_state(self):
        first = self.snapshot()
        second = copy.deepcopy(first)
        second['libvirt']['vms'][0]['active'] = True
        self.assertNotEqual(
            snapshot_fingerprint_sha256(first),
            snapshot_fingerprint_sha256(second),
        )

    def test_plan_fingerprint_ignores_legacy_snapshot_hash_and_age(self):
        snapshot = self.snapshot()
        plan = {
            'schema_version': 1,
            'mode': 'dry_run',
            'vm_uuid': '11111111-1111-1111-1111-111111111111',
            'intent_sha256': 'a' * 64,
            'snapshot_sha256': 'b' * 64,
            'snapshot_age_seconds': 1.0,
            'status': 'changes_planned',
            'can_apply': False,
            'actions': [{'sequence': 1, 'type': 'start_vm', 'executable': False, 'blocked': False, 'reason': 'test'}],
            'warnings': [],
        }
        decorated = decorate_plan_fingerprints(plan, snapshot)
        changed = copy.deepcopy(decorated)
        changed['snapshot_sha256'] = 'c' * 64
        changed['snapshot_age_seconds'] = 20.0
        self.assertEqual(
            plan_fingerprint_sha256(decorated),
            plan_fingerprint_sha256(changed),
        )
        self.assertEqual(
            decorated['plan_fingerprint_sha256'],
            plan_fingerprint_sha256(changed),
        )


if __name__ == '__main__':
    unittest.main()
