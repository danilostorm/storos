"""Deny-only execution contract for the future StorOS JOBS -> COMPUTE boundary.

VM-004B defines typed action payloads, backend capabilities, authorization
and non-execution results. It deliberately provides no worker, apply entrypoint
or mutating hypervisor backend.
"""
from __future__ import annotations

import re
from uuid import UUID

CONTRACT_SCHEMA_VERSION = 1
BACKEND_CAPABILITY_SCHEMA_VERSION = 1
AUTHORIZATION_SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1

ACTION_CONTRACTS = {
    'create_vm': ('vm', 'create', 'vm_present_and_observed', 'not_defined'),
    'rename_vm': ('vm', 'update', 'name_matches_observed', 'restore_previous_name'),
    'set_vcpus': ('vm', 'update', 'vcpus_match_observed', 'restore_previous_value'),
    'set_memory': ('vm', 'update', 'memory_matches_observed', 'restore_previous_value'),
    'start_vm': ('vm', 'lifecycle', 'vm_observed_running', 'shutdown_if_safe'),
    'shutdown_vm': ('vm', 'lifecycle', 'vm_observed_stopped', 'start_if_previously_running_and_safe'),
    'set_firmware_mode': ('firmware', 'update', 'firmware_mode_matches_observed', 'manual_or_backend_specific'),
    'attach_disk': ('disk', 'attach', 'disk_present_and_matches_observed', 'detach_only_if_created_by_same_operation'),
    'reconfigure_disk': ('disk', 'update', 'disk_matches_observed', 'restore_previous_definition_if_safe'),
    'attach_interface': ('interface', 'attach', 'interface_present_and_matches_observed', 'detach_only_if_created_by_same_operation'),
    'reconfigure_interface': ('interface', 'update', 'interface_matches_observed', 'restore_previous_definition_if_safe'),
}


class ExecutionContractError(ValueError):
    pass


def _normalize_uuid(value, field):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ExecutionContractError(f'{field} inválido') from exc


def _nonempty(value, field, maximum=160):
    if not isinstance(value, str):
        raise ExecutionContractError(f'{field} inválido')
    value = value.strip()
    if not value or len(value) > maximum or any(ord(ch) < 32 for ch in value):
        raise ExecutionContractError(f'{field} inválido')
    return value


def _positive_int(value, field, minimum=1, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ExecutionContractError(f'{field} inválido')
    if maximum is not None and value > maximum:
        raise ExecutionContractError(f'{field} inválido')
    return value


def _validate_disk(value, field):
    if not isinstance(value, dict) or set(value) != {'target', 'bus', 'source', 'format', 'readonly', 'boot_order'}:
        raise ExecutionContractError(f'{field} inválido')
    target = _nonempty(value['target'], f'{field}.target', 64)
    if not re.fullmatch(r'[A-Za-z0-9._:+-]+', target):
        raise ExecutionContractError(f'{field}.target inválido')
    if value['bus'] not in ('virtio', 'sata', 'scsi'):
        raise ExecutionContractError(f'{field}.bus inválido')
    source = value['source']
    if not isinstance(source, dict) or set(source) != {'kind', 'value'} or source['kind'] not in ('file', 'block'):
        raise ExecutionContractError(f'{field}.source inválido')
    path = source['value']
    if not isinstance(path, str) or not path.startswith('/') or len(path) > 4096 or any(ord(ch) < 32 for ch in path):
        raise ExecutionContractError(f'{field}.source.value inválido')
    if value['format'] not in ('raw', 'qcow2') or not isinstance(value['readonly'], bool):
        raise ExecutionContractError(f'{field} inválido')
    boot_order = value['boot_order']
    if boot_order is not None:
        _positive_int(boot_order, f'{field}.boot_order', maximum=999)
    return {
        'target': target,
        'bus': value['bus'],
        'source': {'kind': source['kind'], 'value': path},
        'format': value['format'],
        'readonly': value['readonly'],
        'boot_order': boot_order,
    }


def _validate_interface(value, field):
    if not isinstance(value, dict) or set(value) != {'mac', 'type', 'source', 'model'}:
        raise ExecutionContractError(f'{field} inválido')
    mac = value['mac']
    if not isinstance(mac, str) or not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
        raise ExecutionContractError(f'{field}.mac inválido')
    interface_type = value['type']
    if interface_type not in ('network', 'bridge'):
        raise ExecutionContractError(f'{field}.type inválido')
    source = value['source']
    if not isinstance(source, dict) or set(source) != {interface_type}:
        raise ExecutionContractError(f'{field}.source inválido')
    source_value = _nonempty(source[interface_type], f'{field}.source.{interface_type}', 128)
    model = _nonempty(value['model'], f'{field}.model', 64)
    if not re.fullmatch(r'[A-Za-z0-9._:+-]+', model):
        raise ExecutionContractError(f'{field}.model inválido')
    return {
        'mac': mac.lower(),
        'type': interface_type,
        'source': {interface_type: source_value},
        'model': model,
    }


def _validate_create_payload(value):
    expected = {'uuid', 'name', 'vcpus', 'memory_mib'}
    if not isinstance(value, dict) or not expected.issubset(value) or set(value) - (expected | {'hardware'}):
        raise ExecutionContractError('create_vm.after inválido')
    result = {
        'uuid': _normalize_uuid(value['uuid'], 'create_vm.after.uuid'),
        'name': _nonempty(value['name'], 'create_vm.after.name', 80),
        'vcpus': _positive_int(value['vcpus'], 'create_vm.after.vcpus', maximum=1024),
        'memory_mib': _positive_int(value['memory_mib'], 'create_vm.after.memory_mib', minimum=128, maximum=4 * 1024 * 1024),
    }
    if 'hardware' in value:
        hardware = value['hardware']
        if not isinstance(hardware, dict) or set(hardware) != {'firmware', 'disks', 'interfaces'}:
            raise ExecutionContractError('create_vm.after.hardware inválido')
        firmware = hardware['firmware']
        if firmware is not None and (not isinstance(firmware, dict) or set(firmware) != {'mode'} or firmware['mode'] not in ('bios', 'efi')):
            raise ExecutionContractError('create_vm.after.hardware.firmware inválido')
        if not isinstance(hardware['disks'], list) or not isinstance(hardware['interfaces'], list):
            raise ExecutionContractError('create_vm.after.hardware inválido')
        result['hardware'] = {
            'firmware': None if firmware is None else {'mode': firmware['mode']},
            'disks': [_validate_disk(item, 'create_vm.after.hardware.disks') for item in hardware['disks']],
            'interfaces': [_validate_interface(item, 'create_vm.after.hardware.interfaces') for item in hardware['interfaces']],
        }
    return result


def action_contract(action_type):
    action_type = _nonempty(action_type, 'action_type', 64)
    try:
        scope, operation, verification, compensation = ACTION_CONTRACTS[action_type]
    except KeyError as exc:
        raise ExecutionContractError('Ação fora do contrato VM-004B') from exc
    return {
        'type': action_type,
        'resource_scope': scope,
        'operation': operation,
        'verification': verification,
        'compensation': compensation,
        'executable': False,
    }


def validate_planned_action(action, vm_uuid):
    vm_uuid = _normalize_uuid(vm_uuid, 'vm_uuid')
    if not isinstance(action, dict):
        raise ExecutionContractError('Ação planejada inválida')
    allowed = {'sequence', 'type', 'executable', 'blocked', 'reason', 'before', 'after'}
    if set(action) - allowed or not {'sequence', 'type', 'executable', 'blocked', 'reason'}.issubset(action):
        raise ExecutionContractError('Ação planejada contém campos incompatíveis')
    _positive_int(action['sequence'], 'sequence')
    action_type = action_contract(action['type'])['type']
    if action['executable'] is not False or action['blocked'] is not False:
        raise ExecutionContractError('Somente ação não executável e não bloqueada pode entrar no contrato futuro')
    _nonempty(action['reason'], 'reason', 512)
    before = action.get('before')
    after = action.get('after')

    if action_type == 'create_vm':
        normalized_after = _validate_create_payload(after)
        if normalized_after['uuid'] != vm_uuid or before is not None:
            raise ExecutionContractError('create_vm diverge do UUID/estado esperado')
    elif action_type == 'rename_vm':
        _nonempty(before, 'rename_vm.before', 80)
        normalized_after = _nonempty(after, 'rename_vm.after', 80)
    elif action_type == 'set_vcpus':
        _positive_int(before, 'set_vcpus.before', minimum=0, maximum=1024)
        normalized_after = _positive_int(after, 'set_vcpus.after', maximum=1024)
    elif action_type == 'set_memory':
        if isinstance(before, dict):
            if set(before) != {'kib'}:
                raise ExecutionContractError('set_memory.before inválido')
            _positive_int(before['kib'], 'set_memory.before.kib')
        else:
            _positive_int(before, 'set_memory.before', minimum=1)
        normalized_after = _positive_int(after, 'set_memory.after', minimum=128, maximum=4 * 1024 * 1024)
    elif action_type in ('start_vm', 'shutdown_vm'):
        allowed_transitions = (('stopped', 'running'), ('absent', 'running')) if action_type == 'start_vm' else (('running', 'stopped'),)
        if (before, after) not in allowed_transitions:
            raise ExecutionContractError(f'{action_type} transição inválida')
        normalized_after = after
    elif action_type == 'set_firmware_mode':
        if not isinstance(before, dict) or set(before) != {'mode'} or before['mode'] not in ('bios', 'efi'):
            raise ExecutionContractError('set_firmware_mode.before inválido')
        if not isinstance(after, dict) or set(after) != {'mode'} or after['mode'] not in ('bios', 'efi'):
            raise ExecutionContractError('set_firmware_mode.after inválido')
        normalized_after = {'mode': after['mode']}
    elif action_type in ('attach_disk', 'reconfigure_disk'):
        normalized_after = _validate_disk(after, f'{action_type}.after')
        if action_type == 'attach_disk' and before is not None:
            raise ExecutionContractError('attach_disk.before deve estar ausente')
        if action_type == 'reconfigure_disk':
            _validate_disk(before, 'reconfigure_disk.before')
    elif action_type in ('attach_interface', 'reconfigure_interface'):
        normalized_after = _validate_interface(after, f'{action_type}.after')
        if action_type == 'attach_interface' and before is not None:
            raise ExecutionContractError('attach_interface.before deve estar ausente')
        if action_type == 'reconfigure_interface':
            _validate_interface(before, 'reconfigure_interface.before')
    else:  # pragma: no cover - guarded by ACTION_CONTRACTS
        raise ExecutionContractError('Ação sem validador')

    return {
        'schema_version': CONTRACT_SCHEMA_VERSION,
        'vm_uuid': vm_uuid,
        'sequence': action['sequence'],
        'action_type': action_type,
        'resource_scope': action_contract(action_type)['resource_scope'],
        'normalized_after': normalized_after,
        'executable': False,
    }


def execution_contract():
    return {
        'schema_version': CONTRACT_SCHEMA_VERSION,
        'stage': 'contract_only',
        'executable': False,
        'worker_available': False,
        'feature_gate_may_enable_write': False,
        'actions': [action_contract(name) for name in sorted(ACTION_CONTRACTS)],
        'required_boundaries': [
            'authorization', 'backend_capabilities', 'preflight', 'resource_locks',
            'fresh_observation', 'persistent_audit', 'post_apply_observation',
        ],
    }


def backend_capabilities():
    return {
        'schema_version': BACKEND_CAPABILITY_SCHEMA_VERSION,
        'backend_id': 'disabled',
        'backend_kind': 'none',
        'mutating_available': False,
        'reason_code': 'mutating_backend_unavailable',
        'actions': {
            name: {'supported': False, 'reason_code': 'contract_only'}
            for name in sorted(ACTION_CONTRACTS)
        },
    }


def authorization_decision(identity, action_type, vm_uuid):
    identity = _nonempty(identity, 'identity', 128)
    action_type = action_contract(action_type)['type']
    vm_uuid = _normalize_uuid(vm_uuid, 'vm_uuid')
    return {
        'schema_version': AUTHORIZATION_SCHEMA_VERSION,
        'identity': identity,
        'action_type': action_type,
        'vm_uuid': vm_uuid,
        'granted': False,
        'reason_code': 'authorization_unavailable',
        'scopes': [],
    }


def non_execution_result(action_type, vm_uuid, reason_code):
    action_type = action_contract(action_type)['type']
    vm_uuid = _normalize_uuid(vm_uuid, 'vm_uuid')
    reason_code = _nonempty(reason_code, 'reason_code', 96)
    return {
        'schema_version': RESULT_SCHEMA_VERSION,
        'action_type': action_type,
        'vm_uuid': vm_uuid,
        'status': 'not_attempted',
        'executed': False,
        'applied': False,
        'observed_after_apply': None,
        'reason_code': reason_code,
    }


def validate_execution_result(result):
    if not isinstance(result, dict):
        raise ExecutionContractError('Resultado inválido')
    expected = {
        'schema_version', 'action_type', 'vm_uuid', 'status', 'executed',
        'applied', 'observed_after_apply', 'reason_code',
    }
    if set(result) != expected or result.get('schema_version') != RESULT_SCHEMA_VERSION:
        raise ExecutionContractError('Resultado incompatível')
    action_contract(result.get('action_type'))
    _normalize_uuid(result.get('vm_uuid'), 'vm_uuid')
    _nonempty(result.get('reason_code'), 'reason_code', 96)
    if result.get('status') != 'not_attempted':
        raise ExecutionContractError('VM-004B só aceita resultado not_attempted')
    if result.get('executed') is not False or result.get('applied') is not False:
        raise ExecutionContractError('VM-004B não pode registrar execução/aplicação')
    if result.get('observed_after_apply') is not None:
        raise ExecutionContractError('VM-004B não possui estado pós-aplicação')
    return result
