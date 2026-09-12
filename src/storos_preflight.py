"""Fail-closed StorOS VM execution preflight.

VM-004A validates persisted reconciliation intent and drift, but deliberately
contains no hypervisor mutation adapter and can never execute a task.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from uuid import UUID, uuid4

from storos_agent import SNAPSHOT, read_snapshot
from storos_config import CONFIG_ROOT, read_config
from storos_fingerprints import (
    PLAN_FINGERPRINT_VERSION,
    SNAPSHOT_FINGERPRINT_VERSION,
    decorate_plan_fingerprints,
)
from storos_tasks import TASK_ROOT, read_task
from storos_vm import plan_vm
from storos_vm_store import VM_INTENT_ROOT, read_vm_intent

PREFLIGHT_ROOT = Path('/var/lib/storos/preflight')
PREFLIGHT_SCHEMA_VERSION = 1

SUPPORTED_ACTION_TYPES = frozenset({
    'create_vm',
    'rename_vm',
    'set_vcpus',
    'set_memory',
    'start_vm',
    'shutdown_vm',
    'set_firmware_mode',
    'attach_disk',
    'reconfigure_disk',
    'attach_interface',
    'reconfigure_interface',
})


class PreflightError(ValueError):
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


def _normalize_uuid(value, field):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise PreflightError(f'{field} inválido') from exc


def _resource_keys(task):
    vm_uuid = _normalize_uuid(task.get('vm_uuid'), 'vm_uuid')
    keys = {f'vm:{vm_uuid}'}
    for action in task.get('plan', {}).get('actions', []):
        action_type = action.get('type')
        before = action.get('before')
        after = action.get('after')
        if action_type == 'set_firmware_mode':
            keys.add(f'firmware:{vm_uuid}')
        elif action_type in ('attach_disk', 'reconfigure_disk'):
            descriptor = after if isinstance(after, dict) else before if isinstance(before, dict) else {}
            target = descriptor.get('target')
            if isinstance(target, str) and target:
                keys.add(f'disk:{vm_uuid}:{target}')
        elif action_type in ('attach_interface', 'reconfigure_interface'):
            descriptor = after if isinstance(after, dict) else before if isinstance(before, dict) else {}
            mac = descriptor.get('mac')
            if isinstance(mac, str) and mac:
                keys.add(f'interface:{mac.lower()}')
    return sorted(keys)


@contextmanager
def _resource_locks(root, keys):
    root = Path(root)
    lock_dir = root / '.locks'
    lock_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(lock_dir, 0o750)
    handles = []
    try:
        for key in sorted(set(keys)):
            digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
            path = lock_dir / f'{digest}.lock'
            handle = open(path, 'a+')
            os.chmod(path, 0o600)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handles.append(handle)
        yield
    finally:
        for handle in reversed(handles):
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()


def _add_blocker(blockers, code, message):
    if any(item.get('code') == code for item in blockers):
        return
    blockers.append({'code': code, 'message': message})


def _validate_preflight_record(record):
    if not isinstance(record, dict):
        raise PreflightError('Registro de preflight inválido')
    expected = {
        'schema_version', 'preflight_id', 'task_id', 'vm_uuid', 'checked_at',
        'status', 'can_execute', 'executed', 'task_schema_version',
        'requirements', 'resource_keys', 'blockers', 'observed',
    }
    if set(record) != expected or record.get('schema_version') != PREFLIGHT_SCHEMA_VERSION:
        raise PreflightError('Registro de preflight incompatível')
    _normalize_uuid(record.get('preflight_id'), 'preflight_id')
    _normalize_uuid(record.get('task_id'), 'task_id')
    _normalize_uuid(record.get('vm_uuid'), 'vm_uuid')
    if record.get('status') != 'blocked' or record.get('can_execute') is not False or record.get('executed') is not False:
        raise PreflightError('Preflight não pode registrar execução nesta fase')
    blockers = record.get('blockers')
    if not isinstance(blockers, list) or not blockers:
        raise PreflightError('Preflight sem bloqueios é incompatível com VM-004A')
    if not all(
        isinstance(item, dict)
        and set(item) == {'code', 'message'}
        and isinstance(item.get('code'), str) and item['code']
        and isinstance(item.get('message'), str) and item['message']
        for item in blockers
    ):
        raise PreflightError('Blockers do preflight inválidos')
    requirements = record.get('requirements')
    if not isinstance(requirements, dict) or set(requirements) != {
        'feature_gate_enabled', 'authorization_granted', 'mutating_backend_available'
    } or not all(isinstance(value, bool) for value in requirements.values()):
        raise PreflightError('Requisitos do preflight inválidos')
    resource_keys = record.get('resource_keys')
    if not isinstance(resource_keys, list) or not resource_keys or not all(
        isinstance(item, str) and item for item in resource_keys
    ):
        raise PreflightError('Locks de recurso do preflight inválidos')
    if not isinstance(record.get('observed'), dict):
        raise PreflightError('Estado observado do preflight inválido')
    return record


def run_vm_preflight(
    task_id,
    task_root=TASK_ROOT,
    intent_root=VM_INTENT_ROOT,
    snapshot_path=SNAPSHOT,
    config_root=CONFIG_ROOT,
    preflight_root=PREFLIGHT_ROOT,
):
    task = read_task(task_id, task_root)
    resource_keys = _resource_keys(task)
    preflight_root = Path(preflight_root)
    preflight_root.mkdir(parents=True, exist_ok=True)
    os.chmod(preflight_root, 0o750)

    with _resource_locks(preflight_root, resource_keys):
        # Re-read every mutable input while holding the preflight locks.
        task = read_task(task_id, task_root)
        vm_uuid = _normalize_uuid(task['vm_uuid'], 'vm_uuid')
        intent_record = read_vm_intent(vm_uuid, intent_root)
        snapshot = read_snapshot(snapshot_path, max_age=30)
        config = read_config(config_root)
        current_plan = decorate_plan_fingerprints(
            plan_vm(intent_record['intent'], snapshot), snapshot
        )

        blockers = []
        preconditions = task['preconditions']
        if task['schema_version'] < 3:
            _add_blocker(
                blockers,
                'legacy_task_preconditions',
                'Tarefa schema 2 não possui fingerprints estáveis exigidos pelo preflight.',
            )

        if intent_record['generation'] != preconditions['intent_generation']:
            _add_blocker(
                blockers, 'intent_generation_drift',
                'A geração da intenção mudou desde a criação da tarefa.',
            )
        if intent_record['intent_sha256'] != preconditions['intent_sha256']:
            _add_blocker(
                blockers, 'intent_hash_drift',
                'O conteúdo da intenção mudou desde a criação da tarefa.',
            )
        if intent_record['intent']['uuid'] != vm_uuid:
            _add_blocker(
                blockers, 'intent_uuid_mismatch',
                'A intenção atual não pertence ao UUID da tarefa.',
            )

        if snapshot.get('stale') is True:
            _add_blocker(
                blockers, 'snapshot_stale',
                'O snapshot observado não está fresco o suficiente para preflight.',
            )

        if task['schema_version'] >= 3:
            if preconditions.get('snapshot_fingerprint_version') != SNAPSHOT_FINGERPRINT_VERSION:
                _add_blocker(
                    blockers, 'snapshot_fingerprint_version',
                    'Versão do fingerprint de snapshot não é suportada.',
                )
            if preconditions.get('snapshot_fingerprint_sha256') != current_plan['snapshot_fingerprint_sha256']:
                _add_blocker(
                    blockers, 'snapshot_drift',
                    'O estado observado semanticamente mudou desde a criação da tarefa.',
                )
            if preconditions.get('plan_fingerprint_version') != PLAN_FINGERPRINT_VERSION:
                _add_blocker(
                    blockers, 'plan_fingerprint_version',
                    'Versão do fingerprint de plano não é suportada.',
                )
            if preconditions.get('plan_fingerprint_sha256') != current_plan['plan_fingerprint_sha256']:
                _add_blocker(
                    blockers, 'plan_drift',
                    'O plano recalculado diverge semanticamente da tarefa persistida.',
                )

        if task.get('status') != 'planned' or task['plan'].get('status') != 'changes_planned':
            _add_blocker(
                blockers, 'task_not_planned',
                'Somente tarefas com mudanças planejadas podem atravessar o preflight futuro.',
            )
        if current_plan.get('status') != 'changes_planned':
            _add_blocker(
                blockers, 'current_plan_not_actionable',
                'O plano recalculado não está no estado changes_planned.',
            )

        for action in task['plan'].get('actions', []):
            if action.get('blocked') is True:
                _add_blocker(
                    blockers, 'blocked_action',
                    'A tarefa contém ação marcada como bloqueante.',
                )
            if action.get('type') not in SUPPORTED_ACTION_TYPES:
                _add_blocker(
                    blockers, 'unsupported_action',
                    'A tarefa contém ação fora da whitelist do VM-004A.',
                )

        # These requirements are intentionally impossible to satisfy in VM-004A.
        feature_gate_enabled = config['settings']['features']['vm_write_enabled'] is True
        authorization_granted = False
        mutating_backend_available = False
        requirements = {
            'feature_gate_enabled': feature_gate_enabled,
            'authorization_granted': authorization_granted,
            'mutating_backend_available': mutating_backend_available,
        }
        if not feature_gate_enabled:
            _add_blocker(
                blockers, 'feature_gate_disabled',
                'features.vm_write_enabled permanece false.',
            )
        if not authorization_granted:
            _add_blocker(
                blockers, 'authorization_unavailable',
                'VM-004A não possui mecanismo de autorização para execução.',
            )
        if not mutating_backend_available:
            _add_blocker(
                blockers, 'mutating_backend_unavailable',
                'VM-004A não contém adaptador mutável de hipervisor.',
            )

        record = {
            'schema_version': PREFLIGHT_SCHEMA_VERSION,
            'preflight_id': str(uuid4()),
            'task_id': task['task_id'],
            'vm_uuid': vm_uuid,
            'checked_at': _utc_now(),
            'status': 'blocked',
            'can_execute': False,
            'executed': False,
            'task_schema_version': task['schema_version'],
            'requirements': requirements,
            'resource_keys': resource_keys,
            'blockers': blockers,
            'observed': {
                'intent_generation': intent_record['generation'],
                'intent_sha256': intent_record['intent_sha256'],
                'snapshot_age_seconds': snapshot.get('age_seconds'),
                'snapshot_stale': snapshot.get('stale'),
                'snapshot_fingerprint_version': current_plan['snapshot_fingerprint_version'],
                'snapshot_fingerprint_sha256': current_plan['snapshot_fingerprint_sha256'],
                'plan_fingerprint_version': current_plan['plan_fingerprint_version'],
                'plan_fingerprint_sha256': current_plan['plan_fingerprint_sha256'],
                'plan_status': current_plan.get('status'),
                'action_types': [action.get('type') for action in current_plan.get('actions', [])],
            },
        }
        _validate_preflight_record(record)
        _atomic_write_json(preflight_root / f"{record['preflight_id']}.json", record)
        return record


def read_preflight(preflight_id, root=PREFLIGHT_ROOT):
    preflight_id = _normalize_uuid(preflight_id, 'preflight_id')
    record = _validate_preflight_record(
        json.loads((Path(root) / f'{preflight_id}.json').read_text())
    )
    if record['preflight_id'] != preflight_id:
        raise PreflightError('ID do registro de preflight diverge do arquivo')
    return record


def list_preflights(root=PREFLIGHT_ROOT):
    root = Path(root)
    if not root.exists():
        return []
    records = []
    for path in sorted(root.glob('*.json')):
        try:
            records.append(read_preflight(path.stem, root))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return sorted(records, key=lambda item: (item.get('checked_at', ''), item.get('preflight_id', '')))
