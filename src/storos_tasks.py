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

from storos_fingerprints import (
    PLAN_FINGERPRINT_VERSION,
    SNAPSHOT_FINGERPRINT_VERSION,
    plan_fingerprint_sha256,
)

TASK_ROOT = Path('/var/lib/storos/tasks')
TASK_SCHEMA_VERSION = 3
TASK_SCHEMA_VERSIONS = (2, 3)


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


def validate_dry_run_plan(plan, require_stable=False):
    if not isinstance(plan, dict):
        raise TaskError('Plano inválido')
    if plan.get('schema_version') != 1 or plan.get('mode') != 'dry_run':
        raise TaskError('Plano incompatível')
    if plan.get('can_apply') is not False:
        raise TaskError('Plano dry-run não pode ser aplicável')
    _validate_vm_uuid(plan.get('vm_uuid'))
    _validate_sha256(plan.get('intent_sha256'), 'intent_sha256 do plano')
    _validate_sha256(plan.get('snapshot_sha256'), 'snapshot_sha256 do plano')
    status = plan.get('status')
    if status not in ('blocked', 'converged', 'changes_planned'):
        raise TaskError('Status do plano incompatível')
    actions = plan.get('actions')
    if not isinstance(actions, list):
        raise TaskError('Ações do plano inválidas')
    for index, action in enumerate(actions, 1):
        if not isinstance(action, dict) or action.get('executable') is not False:
            raise TaskError('Plano contém ação executável')
        if action.get('sequence') != index or not isinstance(action.get('type'), str) or not action.get('type'):
            raise TaskError('Ação do plano inválida')
        if not isinstance(action.get('blocked'), bool) or not isinstance(action.get('reason'), str) or not action.get('reason'):
            raise TaskError('Ação do plano inválida')
    warnings = plan.get('warnings')
    if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        raise TaskError('Warnings do plano inválidos')
    blocked = any(action.get('blocked') is True for action in actions)
    if status == 'blocked' and not blocked:
        raise TaskError('Plano bloqueado sem ação bloqueante')
    if status != 'blocked' and blocked:
        raise TaskError('Plano não bloqueado contém ação bloqueante')
    if status == 'converged' and actions:
        raise TaskError('Plano convergido contém ações')
    if status == 'changes_planned' and not actions:
        raise TaskError('Plano de mudanças não contém ações')
    stable_fields = {
        'snapshot_fingerprint_version',
        'snapshot_fingerprint_sha256',
        'plan_fingerprint_version',
        'plan_fingerprint_sha256',
    }
    present = stable_fields.intersection(plan)
    if present and present != stable_fields:
        raise TaskError('Plano contém fingerprint estável incompleto')
    if require_stable and present != stable_fields:
        raise TaskError('Plano não contém fingerprint estável obrigatório')
    if present:
        if plan.get('snapshot_fingerprint_version') != SNAPSHOT_FINGERPRINT_VERSION:
            raise TaskError('Versão do fingerprint de snapshot incompatível')
        _validate_sha256(plan.get('snapshot_fingerprint_sha256'), 'snapshot_fingerprint_sha256 do plano')
        if plan.get('plan_fingerprint_version') != PLAN_FINGERPRINT_VERSION:
            raise TaskError('Versão do fingerprint de plano incompatível')
        expected = _validate_sha256(plan.get('plan_fingerprint_sha256'), 'plan_fingerprint_sha256 do plano')
        if expected != plan_fingerprint_sha256(plan):
            raise TaskError('Fingerprint semântico do plano inválido')
    return plan


def validate_preconditions(preconditions, plan, schema_version=TASK_SCHEMA_VERSION):
    if not isinstance(preconditions, dict):
        raise TaskError('Precondições da tarefa são obrigatórias')
    if schema_version == 2:
        expected_fields = {'intent_generation', 'intent_sha256', 'snapshot_sha256'}
    elif schema_version == 3:
        expected_fields = {
            'intent_generation',
            'intent_sha256',
            'snapshot_sha256',
            'snapshot_fingerprint_version',
            'snapshot_fingerprint_sha256',
            'plan_fingerprint_version',
            'plan_fingerprint_sha256',
        }
    else:
        raise TaskError('schema_version da tarefa incompatível')
    if set(preconditions) != expected_fields:
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
    result = {
        'intent_generation': generation,
        'intent_sha256': intent_sha256,
        'snapshot_sha256': snapshot_sha256,
    }
    if schema_version == 3:
        validate_dry_run_plan(plan, require_stable=True)
        snapshot_version = preconditions.get('snapshot_fingerprint_version')
        plan_version = preconditions.get('plan_fingerprint_version')
        if snapshot_version != SNAPSHOT_FINGERPRINT_VERSION:
            raise TaskError('Versão da precondição de snapshot incompatível')
        if plan_version != PLAN_FINGERPRINT_VERSION:
            raise TaskError('Versão da precondição de plano incompatível')
        snapshot_fingerprint = _validate_sha256(
            preconditions.get('snapshot_fingerprint_sha256'), 'snapshot_fingerprint_sha256'
        )
        plan_fingerprint = _validate_sha256(
            preconditions.get('plan_fingerprint_sha256'), 'plan_fingerprint_sha256'
        )
        if snapshot_fingerprint != plan.get('snapshot_fingerprint_sha256'):
            raise TaskError('Fingerprint de snapshot diverge do plano')
        if plan_fingerprint != plan.get('plan_fingerprint_sha256'):
            raise TaskError('Fingerprint de plano diverge do plano persistido')
        result.update({
            'snapshot_fingerprint_version': snapshot_version,
            'snapshot_fingerprint_sha256': snapshot_fingerprint,
            'plan_fingerprint_version': plan_version,
            'plan_fingerprint_sha256': plan_fingerprint,
        })
    return result


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
    plan = validate_dry_run_plan(plan, require_stable=True)
    preconditions = validate_preconditions(preconditions, plan, TASK_SCHEMA_VERSION)
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
    expected_fields = {
        'schema_version', 'task_id', 'created_at', 'kind', 'mode', 'status',
        'vm_uuid', 'executable', 'preconditions', 'plan',
    }
    if not isinstance(task, dict) or set(task) != expected_fields:
        raise TaskError('Registro de tarefa contém campos ausentes ou desconhecidos')
    schema_version = task.get('schema_version')
    if schema_version not in TASK_SCHEMA_VERSIONS or task.get('task_id') != task_id:
        raise TaskError('Registro de tarefa incompatível')
    if task.get('kind') != 'vm_reconcile':
        raise TaskError('Tipo de tarefa incompatível')
    if task.get('mode') != 'dry_run' or task.get('executable') is not False:
        raise TaskError('Registro de tarefa não é dry-run')
    if not isinstance(task.get('created_at'), str) or not task['created_at']:
        raise TaskError('created_at da tarefa inválido')
    plan = validate_dry_run_plan(task.get('plan'), require_stable=(schema_version == 3))
    vm_uuid = _validate_vm_uuid(task.get('vm_uuid'))
    if vm_uuid != plan.get('vm_uuid'):
        raise TaskError('UUID da tarefa diverge do plano')
    expected_status = (
        'blocked' if plan.get('status') == 'blocked'
        else 'converged' if plan.get('status') == 'converged'
        else 'planned'
    )
    if task.get('status') != expected_status:
        raise TaskError('Status da tarefa diverge do plano')
    validate_preconditions(task.get('preconditions'), plan, schema_version)
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
