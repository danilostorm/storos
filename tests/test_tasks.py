import json
from pathlib import Path
import tempfile
import unittest

from storos_tasks import TaskError, create_dry_run_task, list_tasks, read_task


def plan():
    return {
        'schema_version': 1,
        'mode': 'dry_run',
        'vm_uuid': '11111111-2222-3333-4444-555555555555',
        'intent_sha256': 'a' * 64,
        'observed_present': True,
        'status': 'changes_planned',
        'can_apply': False,
        'actions': [
            {
                'sequence': 1,
                'type': 'set_vcpus',
                'executable': False,
                'blocked': False,
                'reason': 'test',
                'before': 2,
                'after': 4,
            }
        ],
        'warnings': [],
    }


class TaskTests(unittest.TestCase):
    def test_create_read_and_list_dry_run_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = create_dry_run_task(plan(), tmp)
            self.assertFalse(task['executable'])
            self.assertEqual(task['mode'], 'dry_run')
            stored = read_task(task['task_id'], tmp)
            self.assertEqual(stored, task)
            self.assertEqual(list_tasks(tmp), [task])
            self.assertEqual((Path(tmp) / f"{task['task_id']}.json").stat().st_mode & 0o777, 0o640)

    def test_rejects_executable_action(self):
        bad = plan()
        bad['actions'][0]['executable'] = True
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TaskError):
                create_dry_run_task(bad, tmp)

    def test_corrupt_records_are_skipped_by_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = create_dry_run_task(plan(), tmp)
            (Path(tmp) / 'not-a-task.json').write_text('{bad')
            self.assertEqual([item['task_id'] for item in list_tasks(tmp)], [task['task_id']])


if __name__ == '__main__':
    unittest.main()
