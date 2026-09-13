"""Deny-only execution admission pipeline for StorOS VM reconciliation.

VM-004C connects a fresh VM-004A preflight with the VM-004B typed execution
contract, explicit claimed identity and backend capability declaration. The
adapter in this stage is simulation-only and has no apply/mutation method.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import tempfile
from uuid import UUID, uuid4

from storos_execution_contract import (
    ExecutionContractError,
    action_contract,
    authorization_decision,
    backend_capabilities,
    non_execution_result,
    validate_planned_action,
)
from storos_preflight import PREFLIGHT_ROOT, run_vm_preflight
from storos_tasks import TASK_ROOT, read_task
from storos_vm_store import VM_INTENT_ROOT
from storos_agent import SNAPSHOT
from storos_config import CONFIG_ROOT

ADMISSION_ROOT = Path('/var/lib/storos/execution-admissions')
ADMISSION_SCHEMA_VERSION = 1


class AdmissionError(ValueError):
    pass


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _normalize_uuid(value, field):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise AdmissionError(f'{field} inválido') from exc


def _nonempty(value, field, maximum=160):
    if not isinstance(value, str):
        raise AdmissionError(f'{field} inválido')
    value = value.strip()
    if not value or len(value) > maximum or any(ord(ch) < 32 for ch in value):
        raise AdmissionError(f'{field} inválido')
    return value


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


class DenyOnlySimulationAdapter:
    """Adapter facade that can describe/simulate denial but cannot apply."""

    adapter_id = 'simulation-deny-only'
    adapter_kind = 'simulation'
    mutating_available = False

    def describe(self):
        return {
            'adapter_id': self.adapter_id,
            'adapter_kind': self.adapter_kind,
            'mutating_available': False,
            'apply_method_available': False,
        }

    def simulate_non_execution(self, action_type, vm_uuid, reason_code):
        return non_execution_result(action_type, vm_uuid, reason_code)


def _blocker_codes(preflight):
    blockers = preflight.get('blockers')
    if not isinstance(blockers, list):
        raise AdmissionError('Preflight sem blockers válidos')
    codes = []
    for item in blockers:
        if not isinstance(item, dict) or not isinstance(item.get('code'), str) or not item['code']:
            raise AdmissionError('Blocker do preflight inválido')
        if item['code'] not in codes:
            codes.append(item['code'])
    return codes


def evaluate_execution_admission(task, preflight, claimed_identity):
    """Build a deterministic deny-only admission record from validated inputs."""
    claimed_identity = _nonempty(claimed_identity, 'claimed_identity', 128)
    if not isinstance(task, dict) or not isinstance(preflight, dict):
        raise AdmissionError('Tarefa/preflight inválidos')

    task_id = _normalize_uuid(task.get('task_id'), 'task_id')
    vm_uuid = _normalize_uuid(task.get('vm_uuid'), 'vm_uuid')
    preflight_id = _normalize_uuid(preflight.get('preflight_id'), 'preflight_id')
    if _normalize_uuid(preflight.get('task_id'), 'preflight.task_id') != task_id:
        raise AdmissionError('Preflight pertence a outra tarefa')
    if _normalize_uuid(preflight.get('vm_uuid'), 'preflight.vm_uuid') != vm_uuid:
        raise AdmissionError('Preflight pertence a outra VM')
    if preflight.get('status') != 'blocked' or preflight.get('can_execute') is not False or preflight.get('executed') is not False:
        raise AdmissionError('VM-004C exige preflight fail-closed')

    if (
        task.get('schema_version') != 3
        or task.get('status') != 'planned'
        or task.get('mode') != 'dry_run'
        or task.get('executable') is not False
    ):
        raise AdmissionError('VM-004C exige tarefa schema 3 planejada e não executável')

    plan = task.get('plan')
    if (
        not isinstance(plan, dict)
        or plan.get('status') != 'changes_planned'
        or plan.get('mode') != 'dry_run'
        or plan.get('can_apply') is not False
    ):
        raise AdmissionError('Tarefa sem plano dry-run changes_planned')

    preconditions = task.get('preconditions')
    observed = preflight.get('observed')
    if not isinstance(preconditions, dict) or not isinstance(observed, dict):
        raise AdmissionError('Fingerprint do plano ausente na tarefa/preflight')
    task_fingerprint = preconditions.get('plan_fingerprint_sha256')
    plan_fingerprint = plan.get('plan_fingerprint_sha256')
    observed_fingerprint = observed.get('plan_fingerprint_sha256')
    if not all(
        isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)
        for value in (task_fingerprint, plan_fingerprint, observed_fingerprint)
    ):
        raise AdmissionError('Fingerprint do plano inválido')
    if len({task_fingerprint, plan_fingerprint, observed_fingerprint}) != 1:
        raise AdmissionError('Tarefa e preflight não descrevem o mesmo plano')
    actions = plan.get('actions')
    if not isinstance(actions, list) or not actions:
        raise AdmissionError('Tarefa sem ações planejadas')

    capabilities = backend_capabilities()
    if capabilities.get('mutating_available') is not False:
        raise AdmissionError('Backend mutável não é permitido no VM-004C')

    adapter = DenyOnlySimulationAdapter()
    decisions = []
    for action in actions:
        try:
            normalized = validate_planned_action(action, vm_uuid)
            contract = action_contract(normalized['action_type'])
        except ExecutionContractError as exc:
            raise AdmissionError(f'Ação fora do contrato: {exc}') from exc

        action_type = normalized['action_type']
        authorization = authorization_decision(claimed_identity, action_type, vm_uuid)
        backend_action = capabilities.get('actions', {}).get(action_type)
        if not isinstance(backend_action, dict) or backend_action.get('supported') is not False:
            raise AdmissionError('Capacidade do backend incompatível com VM-004C')
        if authorization.get('granted') is not False:
            raise AdmissionError('Autorização concedida é incompatível com VM-004C')

        result = adapter.simulate_non_execution(
            action_type, vm_uuid, authorization.get('reason_code', 'authorization_unavailable')
        )
        decisions.append({
            'sequence': normalized['sequence'],
            'action_type': action_type,
            'resource_scope': contract['resource_scope'],
            'contract_valid': True,
            'authorization': authorization,
            'backend': {
                'backend_id': capabilities['backend_id'],
                'supported': False,
                'reason_code': backend_action.get('reason_code'),
            },
            'result': result,
        })

    blocker_codes = _blocker_codes(preflight)
    mandatory = {
        'feature_gate_disabled', 'authorization_unavailable',
        'mutating_backend_unavailable',
    }
    if not mandatory.issubset(blocker_codes):
        raise AdmissionError('Preflight não preserva os bloqueios obrigatórios desta etapa')
    for code in ('simulation_adapter_only',):
        if code not in blocker_codes:
            blocker_codes.append(code)

    record = {
        'schema_version': ADMISSION_SCHEMA_VERSION,
        'admission_id': str(uuid4()),
        'task_id': task_id,
        'preflight_id': preflight_id,
        'vm_uuid': vm_uuid,
        'plan_fingerprint_sha256': task_fingerprint,
        'checked_at': _utc_now(),
        'status': 'denied',
        'can_execute': False,
        'executed': False,
        'claimed_identity': claimed_identity,
        'identity_authenticated': False,
        'adapter': adapter.describe(),
        'requirements': {
            'preflight_passed': False,
            'authorization_granted': False,
            'mutating_backend_available': False,
        },
        'blocker_codes': blocker_codes,
        'actions': decisions,
    }
    return _validate_admission_record(record)


def _validate_admission_record(record):
    if not isinstance(record, dict):
        raise AdmissionError('Registro de admission inválido')
    expected = {
        'schema_version', 'admission_id', 'task_id', 'preflight_id', 'vm_uuid',
        'plan_fingerprint_sha256', 'checked_at', 'status', 'can_execute', 'executed', 'claimed_identity',
        'identity_authenticated', 'adapter', 'requirements', 'blocker_codes', 'actions',
    }
    if set(record) != expected or record.get('schema_version') != ADMISSION_SCHEMA_VERSION:
        raise AdmissionError('Registro de admission incompatível')
    for field in ('admission_id', 'task_id', 'preflight_id', 'vm_uuid'):
        _normalize_uuid(record.get(field), field)
    fingerprint = record.get('plan_fingerprint_sha256')
    if not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
        raise AdmissionError('Fingerprint do plano do admission inválido')
    _nonempty(record.get('claimed_identity'), 'claimed_identity', 128)
    if record.get('identity_authenticated') is not False:
        raise AdmissionError('Identidade não pode ser autenticada nesta etapa')
    if record.get('status') != 'denied' or record.get('can_execute') is not False or record.get('executed') is not False:
        raise AdmissionError('VM-004C não pode autorizar execução')
    adapter = record.get('adapter')
    if not isinstance(adapter, dict) or adapter != DenyOnlySimulationAdapter().describe():
        raise AdmissionError('Adaptador incompatível')
    requirements = record.get('requirements')
    if requirements != {
        'preflight_passed': False,
        'authorization_granted': False,
        'mutating_backend_available': False,
    }:
        raise AdmissionError('Requisitos incompatíveis')
    blocker_codes = record.get('blocker_codes')
    if not isinstance(blocker_codes, list) or not blocker_codes or not all(isinstance(item, str) and item for item in blocker_codes):
        raise AdmissionError('Blockers incompatíveis')
    actions = record.get('actions')
    if not isinstance(actions, list) or not actions:
        raise AdmissionError('Admission sem decisões por ação')
    for decision in actions:
        if not isinstance(decision, dict) or set(decision) != {
            'sequence', 'action_type', 'resource_scope', 'contract_valid',
            'authorization', 'backend', 'result',
        }:
            raise AdmissionError('Decisão de ação incompatível')
        if decision['contract_valid'] is not True:
            raise AdmissionError('Contrato de ação não validado')
        if decision['authorization'].get('granted') is not False:
            raise AdmissionError('Autorização não pode ser concedida')
        if decision['backend'].get('supported') is not False:
            raise AdmissionError('Backend não pode suportar mutação')
        result = decision['result']
        if result.get('status') != 'not_attempted' or result.get('executed') is not False or result.get('applied') is not False:
            raise AdmissionError('Resultado de ação incompatível')
    return record


def run_execution_admission(
    task_id,
    claimed_identity,
    task_root=TASK_ROOT,
    intent_root=VM_INTENT_ROOT,
    snapshot_path=SNAPSHOT,
    config_root=CONFIG_ROOT,
    preflight_root=PREFLIGHT_ROOT,
    admission_root=ADMISSION_ROOT,
):
    task = read_task(task_id, task_root)
    preflight = run_vm_preflight(
        task_id,
        task_root=task_root,
        intent_root=intent_root,
        snapshot_path=snapshot_path,
        config_root=config_root,
        preflight_root=preflight_root,
    )
    # Re-read the ledger after preflight so the admission binds to persisted state.
    task = read_task(task_id, task_root)
    record = evaluate_execution_admission(task, preflight, claimed_identity)
    admission_root = Path(admission_root)
    admission_root.mkdir(parents=True, exist_ok=True)
    os.chmod(admission_root, 0o750)
    _atomic_write_json(admission_root / f"{record['admission_id']}.json", record)
    return record


def read_admission(admission_id, root=ADMISSION_ROOT):
    admission_id = _normalize_uuid(admission_id, 'admission_id')
    record = _validate_admission_record(
        json.loads((Path(root) / f'{admission_id}.json').read_text())
    )
    if record['admission_id'] != admission_id:
        raise AdmissionError('ID do admission diverge do arquivo')
    return record


def list_admissions(root=ADMISSION_ROOT):
    root = Path(root)
    if not root.exists():
        return []
    records = []
    for path in sorted(root.glob('*.json')):
        try:
            records.append(read_admission(path.stem, root))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return sorted(records, key=lambda item: (item.get('checked_at', ''), item.get('admission_id', '')))
