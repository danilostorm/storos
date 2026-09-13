import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import storos_execution_admission as admission

UUID = '11111111-2222-3333-4444-555555555555'
TASK_ID = '22222222-3333-4444-5555-666666666666'
PREFLIGHT_ID = '33333333-4444-5555-6666-777777777777'
PLAN_FP = 'a' * 64


def task(action_type='start_vm'):
    action = {
        'sequence': 1,
        'type': action_type,
        'executable': False,
        'blocked': False,
        'reason': 'test action',
        'before': 'stopped',
        'after': 'running',
    }
    return {
        'schema_version': 3,
        'task_id': TASK_ID,
        'vm_uuid': UUID,
        'status': 'planned',
        'mode': 'dry_run',
        'executable': False,
        'preconditions': {'plan_fingerprint_sha256': PLAN_FP},
        'plan': {
            'status': 'changes_planned',
            'mode': 'dry_run',
            'can_apply': False,
            'plan_fingerprint_sha256': PLAN_FP,
            'actions': [action],
        },
    }


def preflight():
    return {
        'preflight_id': PREFLIGHT_ID,
        'task_id': TASK_ID,
        'vm_uuid': UUID,
        'status': 'blocked',
        'can_execute': False,
        'executed': False,
        'observed': {'plan_fingerprint_sha256': PLAN_FP},
        'blockers': [
            {'code': 'feature_gate_disabled', 'message': 'disabled'},
            {'code': 'authorization_unavailable', 'message': 'unavailable'},
            {'code': 'mutating_backend_unavailable', 'message': 'unavailable'},
        ],
    }


class ExecutionAdmissionTests(unittest.TestCase):
    def test_valid_action_is_admitted_only_as_denied_non_execution(self):
        record = admission.evaluate_execution_admission(task(), preflight(), 'operator-claimed')
        self.assertEqual(record['status'], 'denied')
        self.assertFalse(record['can_execute'])
        self.assertFalse(record['executed'])
        self.assertFalse(record['identity_authenticated'])
        self.assertIn('simulation_adapter_only', record['blocker_codes'])
        decision = record['actions'][0]
        self.assertTrue(decision['contract_valid'])
        self.assertFalse(decision['authorization']['granted'])
        self.assertFalse(decision['backend']['supported'])
        self.assertEqual(decision['result']['status'], 'not_attempted')
        self.assertFalse(decision['result']['executed'])
        self.assertFalse(decision['result']['applied'])

    def test_adapter_has_no_apply_method(self):
        adapter = admission.DenyOnlySimulationAdapter()
        self.assertFalse(hasattr(adapter, 'apply'))
        self.assertFalse(adapter.describe()['apply_method_available'])
        self.assertFalse(adapter.describe()['mutating_available'])

    def test_preflight_task_mismatch_is_rejected(self):
        raw = preflight()
        raw['task_id'] = UUID
        with self.assertRaises(admission.AdmissionError):
            admission.evaluate_execution_admission(task(), raw, 'operator-claimed')

    def test_plan_fingerprint_drift_is_rejected(self):
        raw = preflight()
        raw['observed']['plan_fingerprint_sha256'] = 'b' * 64
        with self.assertRaises(admission.AdmissionError):
            admission.evaluate_execution_admission(task(), raw, 'operator-claimed')

    def test_unknown_action_fails_closed(self):
        with self.assertRaises(admission.AdmissionError):
            admission.evaluate_execution_admission(task('unknown_action'), preflight(), 'operator-claimed')

    def test_authenticated_identity_forgery_is_rejected(self):
        record = admission.evaluate_execution_admission(task(), preflight(), 'operator-claimed')
        record['identity_authenticated'] = True
        with self.assertRaises(admission.AdmissionError):
            admission._validate_admission_record(record)

    def test_run_persists_private_audit_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(admission, 'read_task', return_value=task()), patch.object(
                admission, 'run_vm_preflight', return_value=preflight()
            ):
                record = admission.run_execution_admission(
                    TASK_ID, 'operator-claimed', admission_root=root
                )
            path = root / f"{record['admission_id']}.json"
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            self.assertEqual(admission.read_admission(record['admission_id'], root), record)
            self.assertEqual(admission.list_admissions(root), [record])

    def test_corrupt_records_are_skipped_by_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'bad.json').write_text('{')
            self.assertEqual(admission.list_admissions(tmp), [])


if __name__ == '__main__':
    unittest.main()
