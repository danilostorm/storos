"""Transactional persistent store for StorOS VM desired-state intents."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from uuid import UUID

from storos_vm import validate_vm_intent

VM_INTENT_ROOT = Path('/var/lib/storos/vm-intents')
VM_INTENT_STORE_SCHEMA_VERSION = 1


class VMIntentStoreError(ValueError):
    pass


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _canonical_sha256(data):
    canonical = json.dumps(data, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def _normalize_uuid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise VMIntentStoreError('vm_uuid inválido') from exc


def _paths(root, vm_uuid):
    vm_uuid = _normalize_uuid(vm_uuid)
    vm_root = Path(root) / vm_uuid
    return vm_root, vm_root / 'current.json', vm_root / 'revisions', vm_root / '.lock'


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


def _lock(lock_path):
    parent = Path(lock_path).parent
    parent.mkdir(parents=True, exist_ok=True)
    os.chmod(parent, 0o750)
    handle = open(lock_path, 'a+')
    os.chmod(lock_path, 0o600)
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def validate_intent_record(document):
    if not isinstance(document, dict):
        raise VMIntentStoreError('Registro de intenção inválido')
    expected = {'schema_version', 'vm_uuid', 'generation', 'updated_at', 'intent_sha256', 'intent', 'reason'}
    if set(document) != expected:
        raise VMIntentStoreError('Registro de intenção contém campos ausentes ou desconhecidos')
    if document.get('schema_version') != VM_INTENT_STORE_SCHEMA_VERSION:
        raise VMIntentStoreError('schema_version do store incompatível')
    vm_uuid = _normalize_uuid(document.get('vm_uuid'))
    generation = document.get('generation')
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise VMIntentStoreError('generation da intenção inválida')
    updated_at = document.get('updated_at')
    if not isinstance(updated_at, str) or not updated_at:
        raise VMIntentStoreError('updated_at da intenção ausente')
    reason = document.get('reason')
    if not isinstance(reason, str) or not reason or len(reason) > 160:
        raise VMIntentStoreError('reason da intenção inválido')
    intent = validate_vm_intent(document.get('intent'))
    if intent['uuid'] != vm_uuid:
        raise VMIntentStoreError('UUID do registro diverge da intenção')
    intent_sha256 = document.get('intent_sha256')
    if not isinstance(intent_sha256, str) or intent_sha256 != _canonical_sha256(intent):
        raise VMIntentStoreError('Hash da intenção inválido')
    return {'schema_version': VM_INTENT_STORE_SCHEMA_VERSION, 'vm_uuid': vm_uuid, 'generation': generation, 'updated_at': updated_at, 'intent_sha256': intent_sha256, 'intent': intent, 'reason': reason}


def read_vm_intent(vm_uuid, root=VM_INTENT_ROOT):
    _, current, _, _ = _paths(root, vm_uuid)
    return validate_intent_record(json.loads(current.read_text()))


def apply_vm_intent(intent_document, root=VM_INTENT_ROOT, expected_generation=None, reason='apply'):
    intent = validate_vm_intent(intent_document)
    vm_uuid = intent['uuid']
    _, current, revisions, lock_path = _paths(root, vm_uuid)
    if expected_generation is not None and (not isinstance(expected_generation, int) or isinstance(expected_generation, bool) or expected_generation < 0):
        raise VMIntentStoreError('expected_generation inválida')
    reason = str(reason)[:160] or 'apply'
    with _lock(lock_path):
        previous = None
        if current.exists():
            previous = read_vm_intent(vm_uuid, root)
            if expected_generation is not None and previous['generation'] != expected_generation:
                raise VMIntentStoreError('Conflito de geração da intenção')
        elif expected_generation not in (None, 0):
            raise VMIntentStoreError('Conflito de geração da intenção')
        generation = 1 if previous is None else previous['generation'] + 1
        document = {'schema_version': VM_INTENT_STORE_SCHEMA_VERSION, 'vm_uuid': vm_uuid, 'generation': generation, 'updated_at': _utc_now(), 'intent_sha256': _canonical_sha256(intent), 'intent': intent, 'reason': reason}
        revisions.mkdir(parents=True, exist_ok=True)
        os.chmod(revisions, 0o750)
        revision = revisions / f'{generation:06d}.json'
        if revision.exists():
            raise VMIntentStoreError('Revisão de intenção já existe')
        _atomic_write_json(revision, document)
        _atomic_write_json(current, document)
        return document


def rollback_vm_intent(vm_uuid, target_generation, root=VM_INTENT_ROOT, expected_generation=None):
    vm_uuid = _normalize_uuid(vm_uuid)
    if not isinstance(target_generation, int) or isinstance(target_generation, bool) or target_generation < 1:
        raise VMIntentStoreError('Geração de rollback inválida')
    if expected_generation is not None and (not isinstance(expected_generation, int) or isinstance(expected_generation, bool) or expected_generation < 1):
        raise VMIntentStoreError('expected_generation inválida')
    _, current, revisions, lock_path = _paths(root, vm_uuid)
    with _lock(lock_path):
        previous = read_vm_intent(vm_uuid, root)
        if expected_generation is not None and previous['generation'] != expected_generation:
            raise VMIntentStoreError('Conflito de geração da intenção')
        target = validate_intent_record(json.loads((revisions / f'{target_generation:06d}.json').read_text()))
        generation = previous['generation'] + 1
        document = {'schema_version': VM_INTENT_STORE_SCHEMA_VERSION, 'vm_uuid': vm_uuid, 'generation': generation, 'updated_at': _utc_now(), 'intent_sha256': target['intent_sha256'], 'intent': target['intent'], 'reason': f'rollback:{target_generation}'}
        revision = revisions / f'{generation:06d}.json'
        if revision.exists():
            raise VMIntentStoreError('Revisão de intenção já existe')
        _atomic_write_json(revision, document)
        _atomic_write_json(current, document)
        return document


def list_vm_intent_revisions(vm_uuid, root=VM_INTENT_ROOT):
    _, _, revisions, _ = _paths(root, vm_uuid)
    if not revisions.exists():
        return []
    result = []
    for path in sorted(revisions.glob('*.json')):
        try:
            result.append(validate_intent_record(json.loads(path.read_text())))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return result


def list_vm_intents(root=VM_INTENT_ROOT):
    root = Path(root)
    if not root.exists():
        return []
    result = []
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        try:
            result.append(read_vm_intent(path.name, root))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return sorted(result, key=lambda item: item['vm_uuid'])


def intent_preconditions(record):
    record = validate_intent_record(record)
    return {'intent_generation': record['generation'], 'intent_sha256': record['intent_sha256']}
