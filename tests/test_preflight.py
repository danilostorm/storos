import json
from pathlib import Path
import tempfile
import time
import unittest

from storos_agent import read_snapshot
from storos_config import init_config
from storos_fingerprints import decorate_plan_fingerprints, plan_fingerprint_sha256
from storos_preflight import list_preflights, read_preflight, run_vm_preflight
from storos_tasks import create_dry_run_task
from storos_vm import plan_vm
from storos_vm_store import apply_vm_intent, intent_preconditions

UUID = '11111111-2222-3333-4444-555555555555'


def intent(name='demo'):
    return {
        'schema_version': 1,
        'uuid': UUID,
        'name': name,
        'desired_state': 'running',
        'resources': {'vcpus': 4, 'memory_mib': 4096},
    }


def snapshot_data(status='ok', collected_at=None):
    return {
        'schema_version': 1,
        'source': 'simulation',
        'collected_at': time.time() if collected_at is None else collected_at,
        'libvirt': {'status': status, 'vms': [], 'errors': []},
    }


class PreflightTests(unittest.TestCase):
    def prepare(self, tmp):
        root = Path(tmp)
        intents = root / 'intents'
        tasks = root / 'tasks'
        config = root / 'config'
        snapshot_path = root / 'snapshot.json'
        preflights = root / 'preflights'
        init_config(config)
        record = apply_vm_intent(intent(), intents, expected_generation=0, reason='test')
        snapshot_path.write_text(json.dumps(snapshot_data()))
        snapshot = read_snapshot(snapshot_path, max_age=30)
        plan = decorate_plan_fingerprints(plan_vm(record['intent'], snapshot), snapshot)
        preconditions = intent_preconditions(record)
        preconditions.update({
            'snapshot_sha256': plan['snapshot_sha256'],
            'snapshot_fingerprint_version': plan['snapshot_fingerprint_version'],
            'snapshot_fingerprint_sha256': plan['snapshot_fingerprint_sha256'],
            'plan_fingerprint_version': plan['plan_fingerprint_version'],
            'plan_fingerprint_sha256': plan['plan_fingerprint_sha256'],
        })
        task = create_dry_run_task(plan, preconditions, tasks)
        return intents, tasks, config, snapshot_path, preflights, task

    def _run_preflight(self, paths, task_id):
        intents, tasks, config, snapshot_path, preflights, _ = paths
        return run_vm_preflight(
            task_id,
            task_root=tasks,
            intent_root=intents,
            snapshot_path=snapshot_path,
            config_root=config,
            preflight_root=preflights,
        )

    def test_consistent_task_is_still_blocked_by_three_safety_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.prepare(tmp)
            task = paths[-1]
            result = self._run_preflight(paths, task['task_id'])
            codes = {item['code'] for item in result['blockers']}
            self.assertEqual(codes, {
                'feature_gate_disabled',
                'authorization_unavailable',
                'mutating_backend_unavailable',
            })
            self.assertFalse(result['can_execute'])
            self.assertFalse(result['executed'])
            self.assertEqual(result['status'], 'blocked')
            self.assertTrue(all(value is False for value in result['requirements'].values()))
            stored = read_preflight(result['preflight_id'], paths[4])
            self.assertEqual(stored, result)
            self.assertEqual(list_preflights(paths[4]), [result])
            self.assertEqual((paths[4] / f"{result['preflight_id']}.json").stat().st_mode & 0o777, 0o640)
            locks = list((paths[4] / '.locks').glob('*.lock'))
            self.assertTrue(locks)
            self.assertTrue(all((path.stat().st_mode & 0o777) == 0o600 for path in locks))

    def test_intent_drift_is_detected_under_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.prepare(tmp)
            task = paths[-1]
            apply_vm_intent(intent(name='changed'), paths[0], expected_generation=1, reason='drift')
            result = self._run_preflight(paths, task['task_id'])
            codes = {item['code'] for item in result['blockers']}
            self.assertIn('intent_generation_drift', codes)
            self.assertIn('intent_hash_drift', codes)
            self.assertIn('plan_drift', codes)

    def test_semantic_snapshot_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.prepare(tmp)
            task = paths[-1]
            paths[3].write_text(json.dumps(snapshot_data(status='partial')))
            result = self._run_preflight(paths, task['task_id'])
            codes = {item['code'] for item in result['blockers']}
            self.assertIn('snapshot_drift', codes)
            self.assertIn('plan_drift', codes)
            self.assertIn('current_plan_not_actionable', codes)

    def test_stale_snapshot_is_blocked_even_when_semantic_fingerprint_is_same(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.prepare(tmp)
            task = paths[-1]
            paths[3].write_text(json.dumps(snapshot_data(collected_at=time.time() - 60)))
            result = self._run_preflight(paths, task['task_id'])
            codes = {item['code'] for item in result['blockers']}
            self.assertIn('snapshot_stale', codes)
            self.assertNotIn('snapshot_drift', codes)
            self.assertIn('plan_drift', codes)

    def test_unknown_action_is_rejected_even_with_recomputed_task_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.prepare(tmp)
            task = paths[-1]
            path = paths[1] / f"{task['task_id']}.json"
            raw = json.loads(path.read_text())
            raw['plan']['actions'][0]['type'] = 'unsupported_test_action'
            raw['plan']['plan_fingerprint_sha256'] = plan_fingerprint_sha256(raw['plan'])
            raw['preconditions']['plan_fingerprint_sha256'] = raw['plan']['plan_fingerprint_sha256']
            path.write_text(json.dumps(raw))
            result = self._run_preflight(paths, task['task_id'])
            codes = {item['code'] for item in result['blockers']}
            self.assertIn('unsupported_action', codes)
            self.assertIn('plan_drift', codes)

    def test_schema2_task_is_readable_but_never_eligible_for_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.prepare(tmp)
            task = paths[-1]
            path = paths[1] / f"{task['task_id']}.json"
            raw = json.loads(path.read_text())
            raw['schema_version'] = 2
            for field in (
                'snapshot_fingerprint_version', 'snapshot_fingerprint_sha256',
                'plan_fingerprint_version', 'plan_fingerprint_sha256',
            ):
                raw['plan'].pop(field)
            raw['preconditions'] = {
                'intent_generation': raw['preconditions']['intent_generation'],
                'intent_sha256': raw['preconditions']['intent_sha256'],
                'snapshot_sha256': raw['preconditions']['snapshot_sha256'],
            }
            path.write_text(json.dumps(raw))
            result = self._run_preflight(paths, task['task_id'])
            codes = {item['code'] for item in result['blockers']}
            self.assertIn('legacy_task_preconditions', codes)
            self.assertFalse(result['can_execute'])


if __name__ == '__main__':
    unittest.main()
