"""Persistent audit records for StorOS dry-run reconciliation tasks.

There is deliberately no task executor in this module.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from uuid import UUID, uuid4

TASK_ROOT = Path('/var/lib/storos/tasks')
TASK_SCHEMA_VERSION = 2


class TaskError(ValueError):
    pass


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _fsync_directory(path):
    directory_fd = os.open(Path(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_write_json(path, data, mode=0o640):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), mode)
            json.dump(data, stream, ensure_ascii=True, allow_nan=False, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _validate_task_id(task_id):
    try:
        return str(UUID(str(task_id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise TaskError('task_id inválido') from exc


def _validate_vm_uuid(vm_uuid):
    try:
        return str(UUID(str(vm_uuid)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise TaskError('vm_uuid inválido') from exc


def _validate_sha256(value, field):
    if not isinstance(value, str) or len(value) != 64:
        raise TaskError(f'{field} inválido')
    try:
        int(value, 16)
    except ValueError as exc:
        raise TaskError(f'{field} inválido') from exc
    return value.lower()


def validate_dry_run_plan(plan):
    if not isinstance(plan, dict):
        raise TaskError('Plano inválido')
    if plan.get('schema_version') != 1 or plan.get('mode') != 'dry_run':
        raise TaskError('Plano incompatível')
    if plan.get('can_apply') is not False:
        raise TaskError('Plano dry-run não pode ser aplicável')
    _validate_vm_uuid(plan.get('vm_uuid'))
    _validate_sha256(plan.get('intent_sha256'), 'intent_sha256 do plano')
    _validate_sha256(plan.get('snapshot_sha256'), 'snapshot_sha256 do plano')
    actions = plan.get('actions')
    if not isinstance(actions, list):
        raise TaskError('Ações do plano inválidas')
    for action in actions:
        if not isinstance(action, dict) or action.get('executable') is not False:
            raise TaskError('Plano contém ação executável')
    return plan


def validate_preconditions(preconditions, plan):
    if not isinstance(preconditions, dict):
        raise TaskError('Precondições da tarefa são obrigatórias')
    if set(preconditions) != {'intent_generation', 'intent_sha256', 'snapshot_sha256'}:
        raise TaskError('Precondições da tarefa incompatíveis')
    generation = preconditions.get('intent_generation')
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise TaskError('intent_generation inválida')
    intent_sha256 = _validate_sha256(preconditions.get('intent_sha256'), 'intent_sha256')
    snapshot_sha256 = _validate_sha256(preconditions.get('snapshot_sha256'), 'snapshot_sha256')
    if intent_sha256 != plan.get('intent_sha256'):
        raise TaskError('Precondição de intenção diverge do plano')
    if snapshot_sha256 != plan.get('snapshot_sha256'):
        raise TaskError('Precondição de snapshot diverge do plano')
    return {'intent_generation': generation, 'intent_sha256': intent_sha256, 'snapshot_sha256': snapshot_sha256}


def _task_lock(root, vm_uuid):
    root = Path(root)
    lock_dir = root / '.locks'
    lock_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(lock_dir, 0o750)
    lock_path = lock_dir / f'{_validate_vm_uuid(vm_uuid)}.lock'
    handle = open(lock_path, 'a+')
    os.chmod(lock_path, 0o600)
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def create_dry_run_task(plan, preconditions, root=TASK_ROOT):
    plan = validate_dry_run_plan(plan)
    preconditions = validate_preconditions(preconditions, plan)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o750)
    vm_uuid = _validate_vm_uuid(plan['vm_uuid'])
    with _task_lock(root, vm_uuid):
        task_id = str(uuid4())
        task = {
            'schema_version': TASK_SCHEMA_VERSION,
            'task_id': task_id,
            'created_at': _utc_now(),
            'kind': 'vm_reconcile',
            'mode': 'dry_run',
            'status': ('blocked' if plan.get('status') == 'blocked' else 'converged' if plan.get('status') == 'converged' else 'planned'),
            'vm_uuid': vm_uuid,
            'executable': False,
            'preconditions': preconditions,
            'plan': plan,
        }
        _atomic_write_json(root / f'{task_id}.json', task)
        return task


def read_task(task_id, root=TASK_ROOT):
    task_id = _validate_task_id(task_id)
    path = Path(root) / f'{task_id}.json'
    task = json.loads(path.read_text())
    if task.get('schema_version') != TASK_SCHEMA_VERSION or task.get('task_id') != task_id:
        raise TaskError('Registro de tarefa incompatível')
    if task.get('mode') != 'dry_run' or task.get('executable') is not False:
        raise TaskError('Registro de tarefa não é dry-run')
    plan = validate_dry_run_plan(task.get('plan'))
    vm_uuid = _validate_vm_uuid(task.get('vm_uuid'))
    if vm_uuid != plan.get('vm_uuid'):
        raise TaskError('UUID da tarefa diverge do plano')
    validate_preconditions(task.get('preconditions'), plan)
    return task


def list_tasks(root=TASK_ROOT):
    root = Path(root)
    if not root.exists():
        return []
    tasks = []
    for path in sorted(root.glob('*.json')):
        try:
            tasks.append(read_task(path.stem, root))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return sorted(tasks, key=lambda item: (item.get('created_at', ''), item.get('task_id', '')))
