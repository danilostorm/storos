import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
import unittest

import storos_cli

UUID = '11111111-2222-3333-4444-555555555555'


class CLITests(unittest.TestCase):
    def fixtures(self, root):
        intent = {
            'schema_version': 1,
            'uuid': UUID,
            'name': 'demo',
            'desired_state': 'running',
            'resources': {'vcpus': 4, 'memory_mib': 4096},
        }
        snapshot = {
            'schema_version': 1,
            'collected_at': time.time(),
            'libvirt': {'status': 'ok', 'vms': []},
        }
        intent_path = Path(root) / 'intent.json'
        snapshot_path = Path(root) / 'snapshot.json'
        intent_path.write_text(json.dumps(intent))
        snapshot_path.write_text(json.dumps(snapshot))
        return intent_path, snapshot_path

    def call(self, args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = storos_cli.main(args)
        return code, json.loads(out.getvalue())

    def test_vm_plan_is_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            intent, snapshot = self.fixtures(tmp)
            code, result = self.call([
                'vm-plan', '--intent-file', str(intent), '--snapshot', str(snapshot),
            ])
            self.assertEqual(code, 0)
            self.assertFalse(result['can_apply'])
            self.assertTrue(all(a['executable'] is False for a in result['actions']))

    def test_persisted_intent_reconcile_records_preconditioned_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            intent, snapshot = self.fixtures(tmp)
            intents = Path(tmp) / 'intents'
            tasks = Path(tmp) / 'tasks'
            code, stored = self.call([
                'vm-intent-apply', '--intent-file', str(intent),
                '--intent-root', str(intents), '--expected-generation', '0',
            ])
            self.assertEqual(code, 0)
            self.assertEqual(stored['generation'], 1)

            code, planned = self.call([
                'vm-plan', '--vm-uuid', UUID, '--intent-root', str(intents),
                '--snapshot', str(snapshot),
            ])
            self.assertEqual(code, 0)
            self.assertEqual(planned['intent_sha256'], stored['intent_sha256'])

            code, result = self.call([
                'vm-reconcile-dry-run', '--vm-uuid', UUID,
                '--intent-root', str(intents), '--snapshot', str(snapshot),
                '--task-root', str(tasks),
            ])
            self.assertEqual(code, 0)
            self.assertFalse(result['executable'])
            self.assertEqual(result['preconditions']['intent_generation'], 1)
            self.assertEqual(result['preconditions']['intent_sha256'], stored['intent_sha256'])
            self.assertEqual(result['preconditions']['snapshot_sha256'], result['plan']['snapshot_sha256'])
            self.assertTrue((tasks / f"{result['task_id']}.json").exists())


if __name__ == '__main__':
    unittest.main()
