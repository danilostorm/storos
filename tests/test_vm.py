import copy
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


def hardware_intent():
    return {
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
    }


def intent_v2(**overrides):
    data = {
        'schema_version': 2,
        'uuid': UUID,
        'name': 'demo',
        'desired_state': 'running',
        'resources': {'vcpus': 4, 'memory_mib': 4096},
        'hardware': hardware_intent(),
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


def observed_hardware():
    return {
        'status': 'ok',
        'firmware': {
            'mode': 'efi',
            'secure_boot': True,
            'nvram_present': True,
        },
        'disks': [{
            'device': 'disk',
            'type': 'file',
            'target': {'dev': 'vda', 'bus': 'virtio'},
            'source': {'kind': 'file', 'value': '/var/lib/libvirt/images/demo.qcow2'},
            'format': 'qcow2',
            'readonly': False,
            'boot_order': 1,
        }],
        'interfaces': [{
            'type': 'network',
            'mac': '52:54:00:12:34:56',
            'source': {'network': 'default'},
            'model': 'virtio',
            'target_dev': 'vnet0',
            'link_state': 'up',
        }],
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
        'hardware': observed_hardware(),
    }
    data.update(overrides)
    return data


class VMPlannerTests(unittest.TestCase):
    def test_intent_rejects_unknown_fields(self):
        bad = intent()
        bad['command'] = 'virsh destroy x'
        with self.assertRaises(VMError):
            validate_vm_intent(bad)

    def test_v1_intent_shape_is_preserved_exactly(self):
        original = intent()
        self.assertEqual(validate_vm_intent(original), original)
        self.assertNotIn('hardware', validate_vm_intent(original))

    def test_v2_intent_normalizes_mac_and_managed_list_order(self):
        wanted = intent_v2()
        wanted['hardware']['interfaces'][0]['mac'] = '52:54:00:AA:BB:CC'
        wanted['hardware']['disks'].insert(0, {
            'target': 'vdb',
            'bus': 'virtio',
            'source': {'kind': 'block', 'value': '/dev/mapper/vm-data'},
            'format': 'raw',
            'readonly': False,
            'boot_order': None,
        })
        normalized = validate_vm_intent(wanted)
        self.assertEqual([d['target'] for d in normalized['hardware']['disks']], ['vda', 'vdb'])
        self.assertEqual(normalized['hardware']['interfaces'][0]['mac'], '52:54:00:aa:bb:cc')

    def test_v2_rejects_duplicate_device_identity_and_unsafe_source(self):
        duplicate = intent_v2()
        duplicate['hardware']['disks'].append(copy.deepcopy(duplicate['hardware']['disks'][0]))
        with self.assertRaises(VMError):
            validate_vm_intent(duplicate)

        duplicate_mac = intent_v2()
        duplicate_mac['hardware']['interfaces'].append(copy.deepcopy(duplicate_mac['hardware']['interfaces'][0]))
        with self.assertRaises(VMError):
            validate_vm_intent(duplicate_mac)

        relative = intent_v2()
        relative['hardware']['disks'][0]['source']['value'] = '../demo.qcow2'
        with self.assertRaises(VMError):
            validate_vm_intent(relative)

    def test_missing_vm_plans_create_and_start_but_never_executable(self):
        plan = plan_vm(intent(), snapshot([]))
        self.assertEqual(plan['status'], 'changes_planned')
        self.assertFalse(plan['can_apply'])
        self.assertEqual([a['type'] for a in plan['actions']], ['create_vm', 'start_vm'])
        self.assertTrue(all(a['executable'] is False for a in plan['actions']))

    def test_v2_missing_vm_keeps_hardware_inside_non_executable_create(self):
        plan = plan_vm(intent_v2(), snapshot([]))
        self.assertEqual([a['type'] for a in plan['actions']], ['create_vm', 'start_vm'])
        self.assertEqual(plan['actions'][0]['after']['hardware'], plan['intent']['hardware'])
        self.assertTrue(all(a['executable'] is False for a in plan['actions']))
        self.assertFalse(plan['can_apply'])

    def test_converged_vm_has_no_actions(self):
        plan = plan_vm(intent(), snapshot([observed()]))
        self.assertEqual(plan['status'], 'converged')
        self.assertEqual(plan['actions'], [])

    def test_v2_converged_hardware_has_no_actions(self):
        plan = plan_vm(intent_v2(), snapshot([observed()]))
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

    def test_v2_plans_deterministic_hardware_differences(self):
        vm = observed()
        vm['hardware']['firmware']['mode'] = 'bios'
        vm['hardware']['disks'][0]['readonly'] = True
        vm['hardware']['interfaces'][0]['source'] = {'network': 'old-network'}
        vm['hardware']['interfaces'][0]['model'] = 'e1000e'
        plan = plan_vm(intent_v2(), snapshot([vm]))
        self.assertEqual(
            [a['type'] for a in plan['actions']],
            ['set_firmware_mode', 'reconfigure_disk', 'reconfigure_interface'],
        )
        self.assertEqual(plan['status'], 'changes_planned')
        self.assertTrue(all(a['executable'] is False for a in plan['actions']))

    def test_v2_missing_managed_devices_plans_attach_without_detach(self):
        vm = observed()
        vm['hardware']['disks'] = []
        vm['hardware']['interfaces'] = []
        plan = plan_vm(intent_v2(), snapshot([vm]))
        self.assertEqual([a['type'] for a in plan['actions']], ['attach_disk', 'attach_interface'])
        self.assertNotIn('detach_disk', [a['type'] for a in plan['actions']])
        self.assertNotIn('detach_interface', [a['type'] for a in plan['actions']])

    def test_v2_unmanaged_observed_hardware_is_ignored(self):
        vm = observed()
        vm['hardware']['disks'].append({
            'device': 'cdrom',
            'type': 'file',
            'target': {'dev': 'sda', 'bus': 'sata'},
            'source': {'kind': 'file', 'value': '/var/lib/libvirt/images/install.iso'},
            'format': 'raw',
            'readonly': True,
            'boot_order': None,
        })
        vm['hardware']['interfaces'].append({
            'type': 'bridge',
            'mac': '52:54:00:65:43:21',
            'source': {'bridge': 'br0'},
            'model': 'virtio',
            'target_dev': 'vnet1',
            'link_state': 'up',
        })
        plan = plan_vm(intent_v2(), snapshot([vm]))
        self.assertEqual(plan['status'], 'converged')
        self.assertEqual(plan['actions'], [])

    def test_v2_unavailable_hardware_blocks_without_inference(self):
        vm = observed(hardware={
            'status': 'unavailable',
            'firmware': None,
            'disks': None,
            'interfaces': None,
        })
        plan = plan_vm(intent_v2(), snapshot([vm], status='partial'))
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual([a['type'] for a in plan['actions']], ['inspect_hardware'])
        self.assertTrue(plan['actions'][0]['blocked'])

    def test_v2_unknown_firmware_blocks_only_firmware_inference(self):
        vm = observed()
        vm['hardware']['firmware']['mode'] = 'unknown'
        plan = plan_vm(intent_v2(), snapshot([vm]))
        self.assertEqual(plan['status'], 'blocked')
        self.assertEqual([a['type'] for a in plan['actions']], ['inspect_firmware'])

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
