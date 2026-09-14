import unittest

from storos_preflight import SUPPORTED_ACTION_TYPES
from storos_execution_contract import (
    ACTION_CONTRACTS,
    ExecutionContractError,
    action_contract,
    authorization_decision,
    backend_capabilities,
    execution_contract,
    non_execution_result,
    validate_execution_result,
    validate_planned_action,
)

UUID = '11111111-2222-3333-4444-555555555555'
EXPECTED = {
    'create_vm', 'rename_vm', 'set_vcpus', 'set_memory', 'start_vm', 'shutdown_vm',
    'set_firmware_mode', 'attach_disk', 'reconfigure_disk', 'attach_interface',
    'reconfigure_interface',
}


def action(action_type, before=None, after=None):
    result = {
        'sequence': 1,
        'type': action_type,
        'executable': False,
        'blocked': False,
        'reason': 'test',
    }
    if before is not None:
        result['before'] = before
    if after is not None:
        result['after'] = after
    return result


class ExecutionContractTests(unittest.TestCase):
    def test_catalog_is_closed_and_every_action_is_non_executable(self):
        self.assertEqual(set(ACTION_CONTRACTS), EXPECTED)
        self.assertEqual(set(SUPPORTED_ACTION_TYPES), EXPECTED)
        contract = execution_contract()
        self.assertEqual(contract['stage'], 'contract_only')
        self.assertFalse(contract['executable'])
        self.assertFalse(contract['worker_available'])
        self.assertFalse(contract['feature_gate_may_enable_write'])
        self.assertEqual({item['type'] for item in contract['actions']}, EXPECTED)
        self.assertTrue(all(item['executable'] is False for item in contract['actions']))

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(ExecutionContractError):
            action_contract('destroy_vm')

    def test_typed_action_payloads_accept_current_planner_shapes(self):
        cases = [
            action('create_vm', after={'uuid': UUID, 'name': 'demo', 'vcpus': 2, 'memory_mib': 1024}),
            action('rename_vm', before='old', after='new'),
            action('set_vcpus', before=2, after=4),
            action('set_memory', before=1024, after=2048),
            action('start_vm', before='stopped', after='running'),
            action('shutdown_vm', before='running', after='stopped'),
            action('set_firmware_mode', before={'mode': 'bios'}, after={'mode': 'efi'}),
            action('attach_disk', after={'target': 'vda', 'bus': 'virtio', 'source': {'kind': 'file', 'value': '/var/lib/vm.qcow2'}, 'format': 'qcow2', 'readonly': False, 'boot_order': 1}),
            action('reconfigure_interface', before={'mac': '52:54:00:00:00:01', 'type': 'network', 'source': {'network': 'default'}, 'model': 'virtio'}, after={'mac': '52:54:00:00:00:01', 'type': 'bridge', 'source': {'bridge': 'br0'}, 'model': 'virtio'}),
        ]
        for item in cases:
            with self.subTest(action=item['type']):
                envelope = validate_planned_action(item, UUID)
                self.assertEqual(envelope['action_type'], item['type'])
                self.assertFalse(envelope['executable'])

    def test_malformed_or_blocked_action_is_rejected(self):
        malformed = action('set_vcpus', before=2, after='4')
        with self.assertRaises(ExecutionContractError):
            validate_planned_action(malformed, UUID)
        blocked = action('start_vm', before='stopped', after='running')
        blocked['blocked'] = True
        with self.assertRaises(ExecutionContractError):
            validate_planned_action(blocked, UUID)

    def test_backend_is_deny_only_for_every_action(self):
        capabilities = backend_capabilities()
        self.assertEqual(capabilities['backend_id'], 'disabled')
        self.assertFalse(capabilities['mutating_available'])
        self.assertEqual(set(capabilities['actions']), EXPECTED)
        self.assertTrue(all(item['supported'] is False for item in capabilities['actions'].values()))

    def test_authorization_is_typed_and_always_denied(self):
        decision = authorization_decision('local-admin', 'start_vm', UUID)
        self.assertEqual(decision['identity'], 'local-admin')
        self.assertEqual(decision['vm_uuid'], UUID)
        self.assertFalse(decision['granted'])
        self.assertEqual(decision['reason_code'], 'authorization_unavailable')
        self.assertEqual(decision['scopes'], [])

    def test_result_cannot_claim_execution_or_apply(self):
        result = non_execution_result('set_vcpus', UUID, 'contract_only')
        self.assertEqual(validate_execution_result(result), result)
        forged = dict(result)
        forged['status'] = 'applied'
        forged['executed'] = True
        forged['applied'] = True
        with self.assertRaises(ExecutionContractError):
            validate_execution_result(forged)


if __name__ == '__main__':
    unittest.main()
