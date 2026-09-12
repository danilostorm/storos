import json
from pathlib import Path
import tempfile
import unittest

from storos_tasks import TaskError, create_dry_run_task, list_tasks, read_task

UUID = '11111111-2222-3333-4444-555555555555'


def plan():
    return {
        'schema_version': 1,
        'mode': 'dry_run',
        'vm_uuid': UUID,
        'intent_sha256': 'a' * 64,
        'snapshot_sha256': 'b' * 64,
        'observed_present': True,
        'status': 'changes_planned',
        'can_apply': False,
        'actions': [{
            'sequence': 1,
            'type': 'set_vcpus',
            'executable': False,
            'blocked': False,
            'reason': 'test',
            'before': 2,
            'after': 4,
        }],
        'warnings': [],
    }


def preconditions():
    return {
        'intent_generation': 3,
        'intent_sha256': 'a' * 64,
        'snapshot_sha256': 'b' * 64,
    }


class TaskTests(unittest.TestCase):
    def test_create_read_and_list_dry_run_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = create_dry_run_task(plan(), preconditions(), tmp)
            self.assertFalse(task['executable'])
            self.assertEqual(task['preconditions']['intent_generation'], 3)
            stored = read_task(task['task_id'], tmp)
            self.assertEqual(stored, task)
            self.assertEqual(list_tasks(tmp), [task])
            self.assertEqual((Path(tmp) / f"{task['task_id']}.json").stat().st_mode & 0o777, 0o640)
            self.assertEqual((Path(tmp) / '.locks' / f'{UUID}.lock').stat().st_mode & 0o777, 0o600)

    def test_rejects_executable_action(self):
        bad = plan()
        bad['actions'][0]['executable'] = True
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TaskError):
                create_dry_run_task(bad, preconditions(), tmp)

    def test_rejects_precondition_drift(self):
        wrong = preconditions()
        wrong['intent_sha256'] = 'c' * 64
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TaskError):
                create_dry_run_task(plan(), wrong, tmp)

    def test_corrupt_records_are_skipped_by_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = create_dry_run_task(plan(), preconditions(), tmp)
            (Path(tmp) / 'not-a-task.json').write_text('{bad')
            self.assertEqual([item['task_id'] for item in list_tasks(tmp)], [task['task_id']])


if __name__ == '__main__':
    unittest.main()
