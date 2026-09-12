import unittest
from storos_vm import VMError, plan_vm, validate_vm_intent


UUID = '11111111-2222-3333-4444-555555555555'


def intent(**overrides):
    data = {
        'schema_version': 1,
        'uuid': UUID,
        'name': 'demo',
        'desired_state': 'running',
        'resources': {'vcpus': 4, 'memory_mib': 4096},
    }
    data.update(overrides)
    return data


def snapshot(vms, status='ok'):
    return {
        'schema_version': 1,
        'libvirt': {
            'status': status,
            'vms': vms,
        },
    }


def observed(**overrides):
    data = {
        'uuid': UUID,
        'name': 'demo',
        'state': 'running',
        'active': True,
        'vcpus_reported': 4,
        'memory_reported_kib': 4 * 1024 * 1024,
        'max_memory_reported_kib': 4096 * 1024,
    }
    data.update(overrides)
    return data


class VMPlannerTests(unittest.TestCase):
    def test_intent_rejects_unknown_fields(self):
        bad = intent()
        bad['command'] = 'virsh destroy x'
        with self.assertRaises(VMError):
            validate_vm_intent(bad)

    def test_missing_vm_plans_create_and_start_but_never_executable(self):
        plan = plan_vm(intent(), snapshot([]))
        self.assertEqual(plan['status'], 'changes_planned')
        self.assertFalse(plan['can_apply'])
        self.assertEqual([a['type'] for a in plan['actions']], ['create_vm', 'start_vm'])
        self.assertTrue(all(a['executable'] is False for a in plan['actions']))

    def test_converged_vm_has_no_actions(self):
        plan = plan_vm(intent(), snapshot([observed()]))
        self.assertEqual(plan['status'], 'converged')
        self.assertEqual(plan['actions'], [])

    def test_plans_deterministic_differences(self):
        vm = observed(name='old', active=False, state='shut off', vcpus_reported=2,
                      max_memory_reported_kib=2048 * 1024)
        plan = plan_vm(intent(), snapshot([vm]))
        self.assertEqual(
            [a['type'] for a in plan['actions']],
            ['rename_vm', 'set_vcpus', 'set_memory', 'start_vm'],
        )
        self.assertFalse(plan['can_apply'])

    def test_running_vm_can_plan_shutdown(self):
        wanted = intent(desired_state='stopped')
        plan = plan_vm(wanted, snapshot([observed()]))
        self.assertEqual([a['type'] for a in plan['actions']], ['shutdown_vm'])

    def test_missing_observation_blocks_resource_change(self):
        vm = observed(vcpus_reported=None, max_memory_reported_kib=None)
        plan = plan_vm(intent(), snapshot([vm]))
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual([a['type'] for a in plan['actions']], ['inspect_vcpus', 'inspect_memory'])
        self.assertTrue(all(a['blocked'] for a in plan['actions']))

    def test_partial_inventory_does_not_propose_create(self):
        plan = plan_vm(intent(), snapshot([], status='partial'))
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual([a['type'] for a in plan['actions']], ['inspect_inventory'])
        self.assertNotIn('create_vm', [a['type'] for a in plan['actions']])

    def test_stale_snapshot_blocks_reconciliation(self):
        stale = snapshot([observed()])
        stale['stale'] = True
        stale['age_seconds'] = 99.0
        plan = plan_vm(intent(), stale)
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual([a['type'] for a in plan['actions']], ['refresh_snapshot'])

    def test_unavailable_inventory_is_rejected(self):
        with self.assertRaises(VMError):
            plan_vm(intent(), snapshot(None, status='unavailable'))

    def test_duplicate_uuid_is_rejected(self):
        with self.assertRaises(VMError):
            plan_vm(intent(), snapshot([observed(), observed()]))


if __name__ == '__main__':
    unittest.main()
