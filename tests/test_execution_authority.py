import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import storos_execution_authority as authority

UUID='11111111-2222-3333-4444-555555555555'
OTHER_UUID='99999999-8888-7777-6666-555555555555'
TASK_ID='22222222-3333-4444-5555-666666666666'
PREFLIGHT_ID='33333333-4444-5555-6666-777777777777'
PLAN_FP='a'*64

def task(action_type='start_vm'):
    return {'schema_version':3,'task_id':TASK_ID,'vm_uuid':UUID,'status':'planned','mode':'dry_run','executable':False,
            'preconditions':{'plan_fingerprint_sha256':PLAN_FP},
            'plan':{'status':'changes_planned','mode':'dry_run','can_apply':False,'plan_fingerprint_sha256':PLAN_FP,
                    'actions':[{'sequence':1,'type':action_type,'executable':False,'blocked':False,'reason':'test','before':'stopped','after':'running'}]}}

def preflight():
    return {'preflight_id':PREFLIGHT_ID,'task_id':TASK_ID,'vm_uuid':UUID,'status':'blocked','can_execute':False,'executed':False,
            'observed':{'plan_fingerprint_sha256':PLAN_FP},
            'blockers':[{'code':'feature_gate_disabled','message':'disabled'},{'code':'authorization_unavailable','message':'legacy preflight blocker'},{'code':'mutating_backend_unavailable','message':'disabled'}]}

def policy(uid=1000,gid=1000,scopes=None,vms=None):
    ident=authority.identity_record('operator.local',uid,gid,scopes or ['vm:action:start_vm'],vms or [UUID])
    return {'schema_version':1,'generation':1,'identities':[ident]}

class ExecutionAuthorityTests(unittest.TestCase):
    def test_policy_roundtrip_is_private_and_normalized(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'policy.json'
            saved=authority.write_identity_policy(policy(),path)
            self.assertEqual(path.stat().st_mode & 0o777,0o640)
            self.assertEqual(authority.read_identity_policy(path),saved)

    def test_matching_os_principal_authenticates_and_authorizes(self):
        ident=authority.authenticate_local_identity(1000,1000,policy())
        self.assertTrue(ident['authenticated'])
        decision=authority.authorize_execution_action(ident,'start_vm',UUID)
        self.assertTrue(decision['granted'])
        self.assertEqual(decision['matched_scope'],'vm:action:start_vm')

    def test_unknown_os_principal_is_not_authenticated(self):
        ident=authority.authenticate_local_identity(2000,2000,policy())
        self.assertFalse(ident['authenticated'])
        self.assertIsNone(ident['identity_id'])

    def test_missing_scope_is_denied(self):
        ident=authority.authenticate_local_identity(1000,1000,policy(scopes=['vm:action:shutdown_vm']))
        self.assertEqual(authority.authorize_execution_action(ident,'start_vm',UUID)['reason_code'],'scope_missing')

    def test_wrong_vm_is_denied(self):
        ident=authority.authenticate_local_identity(1000,1000,policy(vms=[OTHER_UUID]))
        self.assertEqual(authority.authorize_execution_action(ident,'start_vm',UUID)['reason_code'],'vm_not_allowed')
    def test_capability_provider_has_no_apply_and_never_eligible(self):
        provider=authority.DenyOnlyCapabilityProvider()
        self.assertFalse(hasattr(provider,'apply'))
        desc=provider.describe()
        self.assertFalse(desc['mutating_available'])
        self.assertFalse(desc['apply_method_available'])
        negotiated=provider.negotiate('start_vm')
        self.assertTrue(negotiated['contract_supported'])
        self.assertFalse(negotiated['mutating_supported'])
        self.assertFalse(negotiated['eligible'])

    def test_authenticated_and_authorized_action_still_denied(self):
        record=authority.evaluate_execution_authority(task(),preflight(),1000,1000,policy())
        self.assertTrue(record['identity']['authenticated'])
        self.assertTrue(record['requirements']['all_actions_authorized'])
        self.assertFalse(record['requirements']['capabilities_satisfied'])
        self.assertFalse(record['requirements']['feature_gate_enabled'])
        self.assertEqual(record['status'],'denied')
        self.assertFalse(record['can_execute'])
        action=record['actions'][0]
        self.assertTrue(action['authorization']['granted'])
        self.assertFalse(action['eligible'])
        self.assertFalse(action['result']['executed'])
        self.assertFalse(action['result']['applied'])
    def test_unauthenticated_identity_is_denied(self):
        record=authority.evaluate_execution_authority(task(),preflight(),2000,2000,policy())
        self.assertFalse(record['identity']['authenticated'])
        self.assertFalse(record['requirements']['all_actions_authorized'])
        self.assertIn('identity_authentication_failed',record['blocker_codes'])
        self.assertIn('authorization_denied',record['blocker_codes'])

    def test_plan_fingerprint_drift_is_rejected(self):
        raw=preflight()
        raw['observed']['plan_fingerprint_sha256']='b'*64
        with self.assertRaises(authority.AuthorityError):
            authority.evaluate_execution_authority(task(),raw,1000,1000,policy())

    def test_unknown_action_fails_closed(self):
        with self.assertRaises(authority.AuthorityError):
            authority.evaluate_execution_authority(task('unknown_action'),preflight(),1000,1000,policy())

    def test_provider_with_apply_is_rejected(self):
        class BadProvider(authority.DenyOnlyCapabilityProvider):
            def apply(self):
                return None
        with self.assertRaises(authority.AuthorityError):
            authority.negotiate_execution_capabilities(['start_vm'],BadProvider())
    def test_run_persists_private_audit_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            policy_path=root/'policy.json'
            decision_root=root/'decisions'
            authority.write_identity_policy(policy(os.geteuid(),os.getegid()),policy_path)
            with patch.object(authority,'read_task',return_value=task()), patch.object(
                authority,'run_vm_preflight',return_value=preflight()
            ):
                record=authority.run_execution_authority_check(
                    TASK_ID,policy_path=policy_path,decision_root=decision_root
                )
            path=decision_root/f"{record['authority_check_id']}.json"
            self.assertEqual(path.stat().st_mode & 0o777,0o640)
            self.assertEqual(authority.read_authority_check(record['authority_check_id'],decision_root),record)
            self.assertEqual(authority.list_authority_checks(decision_root),[record])

    def test_corrupt_records_are_skipped_by_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'bad.json').write_text('{')
            self.assertEqual(authority.list_authority_checks(tmp),[])

if __name__=='__main__':
    unittest.main()
