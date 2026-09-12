"""StorOS VM intent model and deterministic dry-run planner.

This module never executes hypervisor mutations.
"""
from __future__ import annotations

import hashlib
import json
import re
from uuid import UUID

VM_INTENT_SCHEMA_VERSION = 2
VM_INTENT_SCHEMA_VERSIONS = (1, 2)
VM_PLAN_SCHEMA_VERSION = 1
DESIRED_STATES = ('running', 'stopped')
FIRMWARE_MODES = ('bios', 'efi')
DISK_BUSES = ('virtio', 'sata', 'scsi')
DISK_SOURCE_KINDS = ('file', 'block')
DISK_FORMATS = ('raw', 'qcow2')
INTERFACE_TYPES = ('network', 'bridge')


class VMError(ValueError):
    pass


def _positive_int(value, field, minimum=1, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise VMError(f'{field} inválido')
    if maximum is not None and value > maximum:
        raise VMError(f'{field} excede o limite suportado')
    return value


def _canonical_sha256(data):
    canonical = json.dumps(
        data, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def _normalize_uuid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise VMError('uuid da VM inválido') from exc


def _normalize_name(value):
    if not isinstance(value, str):
        raise VMError('name da VM inválido')
    value = value.strip()
    if not value or len(value) > 80 or any(ord(ch) < 32 for ch in value):
        raise VMError('name da VM inválido')
    return value


def _validate_resources(resources):
    if not isinstance(resources, dict) or set(resources) != {'vcpus', 'memory_mib'}:
        raise VMError('resources deve conter somente vcpus e memory_mib')
    return {
        'vcpus': _positive_int(resources.get('vcpus'), 'resources.vcpus', maximum=1024),
        'memory_mib': _positive_int(
            resources.get('memory_mib'), 'resources.memory_mib',
            minimum=128, maximum=4 * 1024 * 1024,
        ),
    }


def _safe_token(value, field, maximum=128):
    if not isinstance(value, str):
        raise VMError(f'{field} inválido')
    value = value.strip()
    if not value or len(value) > maximum or not re.fullmatch(r'[A-Za-z0-9._:+-]+', value):
        raise VMError(f'{field} inválido')
    return value


def _safe_text(value, field, maximum=128):
    if not isinstance(value, str):
        raise VMError(f'{field} inválido')
    value = value.strip()
    if not value or len(value) > maximum or any(ord(ch) < 32 for ch in value):
        raise VMError(f'{field} inválido')
    return value


def _validate_firmware_intent(firmware):
    if firmware is None:
        return None
    if not isinstance(firmware, dict) or set(firmware) != {'mode'}:
        raise VMError('hardware.firmware deve conter somente mode')
    mode = firmware.get('mode')
    if mode not in FIRMWARE_MODES:
        raise VMError('hardware.firmware.mode deve ser bios ou efi')
    return {'mode': mode}


def _validate_disk_intent(disk):
    if not isinstance(disk, dict):
        raise VMError('hardware.disks deve conter objetos')
    expected = {'target', 'bus', 'source', 'format', 'readonly', 'boot_order'}
    if set(disk) != expected:
        raise VMError('Disco desejado contém campos ausentes ou desconhecidos')
    target = _safe_token(disk.get('target'), 'hardware.disks.target', maximum=64)
    bus = disk.get('bus')
    if bus not in DISK_BUSES:
        raise VMError('hardware.disks.bus fora do subconjunto suportado')
    source = disk.get('source')
    if not isinstance(source, dict) or set(source) != {'kind', 'value'}:
        raise VMError('hardware.disks.source deve conter kind e value')
    kind = source.get('kind')
    if kind not in DISK_SOURCE_KINDS:
        raise VMError('hardware.disks.source.kind fora do subconjunto suportado')
    value = source.get('value')
    if not isinstance(value, str) or not value.startswith('/') or len(value) > 4096 or any(ord(ch) < 32 for ch in value):
        raise VMError('hardware.disks.source.value deve ser caminho local absoluto')
    disk_format = disk.get('format')
    if disk_format not in DISK_FORMATS:
        raise VMError('hardware.disks.format fora do subconjunto suportado')
    readonly = disk.get('readonly')
    if not isinstance(readonly, bool):
        raise VMError('hardware.disks.readonly deve ser booleano')
    boot_order = disk.get('boot_order')
    if boot_order is not None:
        boot_order = _positive_int(boot_order, 'hardware.disks.boot_order', maximum=999)
    return {
        'target': target,
        'bus': bus,
        'source': {'kind': kind, 'value': value},
        'format': disk_format,
        'readonly': readonly,
        'boot_order': boot_order,
    }


def _validate_interface_intent(interface):
    if not isinstance(interface, dict):
        raise VMError('hardware.interfaces deve conter objetos')
    expected = {'mac', 'type', 'source', 'model'}
    if set(interface) != expected:
        raise VMError('Interface desejada contém campos ausentes ou desconhecidos')
    mac = interface.get('mac')
    if not isinstance(mac, str) or not re.fullmatch(r'(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
        raise VMError('hardware.interfaces.mac inválido')
    mac = mac.lower()
    interface_type = interface.get('type')
    if interface_type not in INTERFACE_TYPES:
        raise VMError('hardware.interfaces.type fora do subconjunto suportado')
    source = interface.get('source')
    expected_source_key = interface_type
    if not isinstance(source, dict) or set(source) != {expected_source_key}:
        raise VMError(f'hardware.interfaces.source deve conter somente {expected_source_key}')
    source_value = _safe_text(
        source.get(expected_source_key),
        f'hardware.interfaces.source.{expected_source_key}',
        maximum=128,
    )
    model = _safe_token(interface.get('model'), 'hardware.interfaces.model', maximum=64)
    return {
        'mac': mac,
        'type': interface_type,
        'source': {expected_source_key: source_value},
        'model': model,
    }


def _validate_hardware_intent(hardware):
    if not isinstance(hardware, dict) or set(hardware) != {'firmware', 'disks', 'interfaces'}:
        raise VMError('hardware deve conter somente firmware, disks e interfaces')
    disks = hardware.get('disks')
    interfaces = hardware.get('interfaces')
    if not isinstance(disks, list) or len(disks) > 64:
        raise VMError('hardware.disks deve ser lista com no máximo 64 itens')
    if not isinstance(interfaces, list) or len(interfaces) > 64:
        raise VMError('hardware.interfaces deve ser lista com no máximo 64 itens')
    normalized_disks = [_validate_disk_intent(item) for item in disks]
    normalized_interfaces = [_validate_interface_intent(item) for item in interfaces]
    disk_targets = [item['target'] for item in normalized_disks]
    interface_macs = [item['mac'] for item in normalized_interfaces]
    if len(set(disk_targets)) != len(disk_targets):
        raise VMError('hardware.disks contém target duplicado')
    if len(set(interface_macs)) != len(interface_macs):
        raise VMError('hardware.interfaces contém MAC duplicado')
    return {
        'firmware': _validate_firmware_intent(hardware.get('firmware')),
        'disks': sorted(normalized_disks, key=lambda item: item['target']),
        'interfaces': sorted(normalized_interfaces, key=lambda item: item['mac']),
    }


def validate_vm_intent(document):
    if not isinstance(document, dict):
        raise VMError('Intenção de VM deve ser um objeto JSON')
    schema_version = document.get('schema_version')
    if schema_version not in VM_INTENT_SCHEMA_VERSIONS:
        raise VMError('schema_version da intenção incompatível')
    expected = {'schema_version', 'uuid', 'name', 'desired_state', 'resources'}
    if schema_version == 2:
        expected.add('hardware')
    if set(document) != expected:
        raise VMError('Intenção de VM contém campos ausentes ou desconhecidos')

    vm_uuid = _normalize_uuid(document.get('uuid'))
    name = _normalize_name(document.get('name'))
    desired_state = document.get('desired_state')
    if desired_state not in DESIRED_STATES:
        raise VMError('desired_state deve ser running ou stopped')
    resources = _validate_resources(document.get('resources'))

    normalized = {
        'schema_version': schema_version,
        'uuid': vm_uuid,
        'name': name,
        'desired_state': desired_state,
        'resources': resources,
    }
    if schema_version == 2:
        normalized['hardware'] = _validate_hardware_intent(document.get('hardware'))
    return normalized


def _validate_observed_vm(vm):
    if not isinstance(vm, dict):
        raise VMError('Registro observado de VM inválido')
    try:
        vm_uuid = str(UUID(str(vm.get('uuid'))))
    except (ValueError, TypeError, AttributeError) as exc:
        raise VMError('UUID observado inválido') from exc
    name = vm.get('name')
    if not isinstance(name, str) or not name:
        raise VMError('Nome observado inválido')
    active = vm.get('active')
    if not isinstance(active, bool):
        raise VMError('Estado active observado inválido')
    vcpus = vm.get('vcpus_reported')
    if vcpus is not None:
        _positive_int(vcpus, 'vcpus_reported', minimum=0, maximum=1024)
    max_memory_kib = vm.get('max_memory_reported_kib')
    if max_memory_kib is not None:
        _positive_int(max_memory_kib, 'max_memory_reported_kib', minimum=1)
    return {
        'uuid': vm_uuid,
        'name': name,
        'active': active,
        'vcpus_reported': vcpus,
        'max_memory_reported_kib': max_memory_kib,
        'state': vm.get('state'),
        'hardware': vm.get('hardware'),
    }


def observed_vm_from_snapshot(snapshot, vm_uuid):
    if not isinstance(snapshot, dict):
        raise VMError('Snapshot observado inválido')
    if snapshot.get('schema_version') != 1:
        raise VMError('schema_version do snapshot incompatível')
    libvirt = snapshot.get('libvirt')
    if not isinstance(libvirt, dict):
        raise VMError('Seção libvirt ausente no snapshot')
    status = libvirt.get('status')
    if status not in ('ok', 'partial'):
        raise VMError('Inventário libvirt indisponível para planejar reconciliação')
    vms = libvirt.get('vms')
    if not isinstance(vms, list):
        raise VMError('Lista de VMs observadas inválida')
    target = str(UUID(vm_uuid))
    found = []
    for raw in vms:
        vm = _validate_observed_vm(raw)
        if vm['uuid'] == target:
            found.append(vm)
    if len(found) > 1:
        raise VMError('Snapshot contém UUID de VM duplicado')
    return found[0] if found else None


def _action(sequence, action_type, reason, before=None, after=None, blocked=False):
    action = {
        'sequence': sequence,
        'type': action_type,
        'executable': False,
        'blocked': bool(blocked),
        'reason': reason,
    }
    if before is not None:
        action['before'] = before
    if after is not None:
        action['after'] = after
    return action


def _base_plan(intent, snapshot, observed):
    plan = {
        'schema_version': VM_PLAN_SCHEMA_VERSION,
        'mode': 'dry_run',
        'vm_uuid': intent['uuid'],
        'intent': intent,
        'intent_sha256': _canonical_sha256(intent),
        'snapshot_sha256': _canonical_sha256(snapshot),
        'observed_present': observed is not None,
        'can_apply': False,
    }
    if 'age_seconds' in snapshot:
        plan['snapshot_age_seconds'] = snapshot['age_seconds']
    return plan


def _validate_observed_hardware(raw):
    if not isinstance(raw, dict):
        return {'status': 'unavailable'}
    status = raw.get('status')
    if status != 'ok':
        return {'status': 'unavailable'}
    firmware = raw.get('firmware')
    disks = raw.get('disks')
    interfaces = raw.get('interfaces')
    if not isinstance(firmware, dict) or not isinstance(disks, list) or not isinstance(interfaces, list):
        raise VMError('Hardware observado inválido')
    mode = firmware.get('mode')
    if mode not in ('bios', 'efi', 'unknown'):
        raise VMError('Firmware observado inválido')

    normalized_disks = []
    for disk in disks:
        if not isinstance(disk, dict):
            raise VMError('Disco observado inválido')
        target = disk.get('target')
        target_dev = None
        target_bus = None
        if target is not None:
            if not isinstance(target, dict):
                raise VMError('Target de disco observado inválido')
            target_dev = target.get('dev')
            target_bus = target.get('bus')
        source = disk.get('source')
        source_data = None
        if source is not None:
            if not isinstance(source, dict):
                raise VMError('Source de disco observado inválido')
            source_data = {'kind': source.get('kind'), 'value': source.get('value')}
        readonly = disk.get('readonly')
        if not isinstance(readonly, bool):
            raise VMError('Readonly de disco observado inválido')
        normalized_disks.append({
            'device': disk.get('device'),
            'target': target_dev,
            'bus': target_bus,
            'source': source_data,
            'format': disk.get('format'),
            'readonly': readonly,
            'boot_order': disk.get('boot_order'),
        })

    normalized_interfaces = []
    for interface in interfaces:
        if not isinstance(interface, dict):
            raise VMError('Interface observada inválida')
        mac = interface.get('mac')
        if mac is not None:
            if not isinstance(mac, str):
                raise VMError('MAC observado inválido')
            mac = mac.lower()
        source = interface.get('source')
        if source is not None and not isinstance(source, dict):
            raise VMError('Source de interface observado inválido')
        normalized_interfaces.append({
            'mac': mac,
            'type': interface.get('type'),
            'source': source,
            'model': interface.get('model'),
        })

    return {
        'status': 'ok',
        'firmware': {'mode': mode},
        'disks': normalized_disks,
        'interfaces': normalized_interfaces,
    }


def _plan_hardware(intent, observed, sequence):
    desired = intent['hardware']
    hardware = _validate_observed_hardware(observed.get('hardware'))
    actions = []
    warnings = []
    if hardware['status'] != 'ok':
        return [
            _action(
                sequence, 'inspect_hardware',
                'Hardware virtual não foi observado com segurança; reconciliação de hardware está bloqueada',
                after=desired, blocked=True,
            )
        ], ['hardware virtual indisponível; nenhuma mudança de firmware/disco/rede foi inferida'], sequence + 1

    firmware = desired['firmware']
    if firmware is not None:
        observed_mode = hardware['firmware']['mode']
        if observed_mode == 'unknown':
            actions.append(_action(
                sequence, 'inspect_firmware',
                'Modo de firmware observado é desconhecido',
                after=firmware, blocked=True,
            ))
            sequence += 1
        elif observed_mode != firmware['mode']:
            actions.append(_action(
                sequence, 'set_firmware_mode',
                'Modo de firmware observado diverge da intenção',
                before={'mode': observed_mode}, after=firmware,
            ))
            sequence += 1

    disks_by_target = {}
    for disk in hardware['disks']:
        target = disk['target']
        if target is not None:
            disks_by_target.setdefault(target, []).append(disk)
    for desired_disk in desired['disks']:
        matches = disks_by_target.get(desired_disk['target'], [])
        if len(matches) > 1:
            actions.append(_action(
                sequence, 'inspect_disk',
                'Snapshot contém mais de um disco com o target desejado',
                after=desired_disk, blocked=True,
            ))
            sequence += 1
            continue
        if not matches:
            actions.append(_action(
                sequence, 'attach_disk',
                'Disco desejado não foi encontrado pelo target',
                after=desired_disk,
            ))
            sequence += 1
            continue
        current = matches[0]
        if (
            current['device'] != 'disk'
            or current['bus'] is None
            or current['source'] is None
            or current['source'].get('kind') is None
            or current['source'].get('value') is None
            or current['format'] is None
        ):
            actions.append(_action(
                sequence, 'inspect_disk',
                'Disco observado não possui dados suficientes para comparação segura',
                before=current, after=desired_disk, blocked=True,
            ))
            sequence += 1
            continue
        comparable = {
            'target': current['target'],
            'bus': current['bus'],
            'source': {
                'kind': current['source'].get('kind'),
                'value': current['source'].get('value'),
            },
            'format': current['format'],
            'readonly': current['readonly'],
            'boot_order': current['boot_order'],
        }
        if comparable != desired_disk:
            actions.append(_action(
                sequence, 'reconfigure_disk',
                'Configuração observada do disco diverge da intenção gerenciada',
                before=comparable, after=desired_disk,
            ))
            sequence += 1

    interfaces_by_mac = {}
    for interface in hardware['interfaces']:
        mac = interface['mac']
        if mac is not None:
            interfaces_by_mac.setdefault(mac, []).append(interface)
    for desired_interface in desired['interfaces']:
        matches = interfaces_by_mac.get(desired_interface['mac'], [])
        if len(matches) > 1:
            actions.append(_action(
                sequence, 'inspect_interface',
                'Snapshot contém mais de uma interface com o MAC desejado',
                after=desired_interface, blocked=True,
            ))
            sequence += 1
            continue
        if not matches:
            actions.append(_action(
                sequence, 'attach_interface',
                'Interface desejada não foi encontrada pelo MAC',
                after=desired_interface,
            ))
            sequence += 1
            continue
        current = matches[0]
        source_key = desired_interface['type']
        if (
            current['type'] is None
            or current['source'] is None
            or current['source'].get(source_key) is None
            or current['model'] is None
        ):
            actions.append(_action(
                sequence, 'inspect_interface',
                'Interface observada não possui dados suficientes para comparação segura',
                before=current, after=desired_interface, blocked=True,
            ))
            sequence += 1
            continue
        comparable = {
            'mac': current['mac'],
            'type': current['type'],
            'source': {source_key: current['source'].get(source_key)},
            'model': current['model'],
        }
        if comparable != desired_interface:
            actions.append(_action(
                sequence, 'reconfigure_interface',
                'Configuração observada da interface diverge da intenção gerenciada',
                before=comparable, after=desired_interface,
            ))
            sequence += 1

    return actions, warnings, sequence


def plan_vm(intent_document, snapshot):
    intent = validate_vm_intent(intent_document)
    observed = observed_vm_from_snapshot(snapshot, intent['uuid'])
    base = _base_plan(intent, snapshot, observed)

    if snapshot.get('stale') is True:
        return {
            **base,
            'status': 'blocked',
            'actions': [_action(
                1, 'refresh_snapshot',
                'Snapshot observado está desatualizado; reconciliação exige nova coleta',
                blocked=True,
            )],
            'warnings': ['snapshot stale; nenhuma mudança de VM deve ser inferida desta coleta'],
        }

    inventory_status = snapshot['libvirt']['status']
    if observed is None and inventory_status == 'partial':
        return {
            **base,
            'status': 'blocked',
            'actions': [_action(
                1, 'inspect_inventory',
                'Inventário parcial não prova que a VM desejada está ausente',
                after=intent['uuid'], blocked=True,
            )],
            'warnings': ['inventário libvirt parcial; create_vm não foi proposto'],
        }

    actions = []
    warnings = []
    sequence = 1

    if observed is None:
        after = {
            'uuid': intent['uuid'],
            'name': intent['name'],
            'vcpus': intent['resources']['vcpus'],
            'memory_mib': intent['resources']['memory_mib'],
        }
        if intent['schema_version'] == 2:
            after['hardware'] = intent['hardware']
        actions.append(_action(
            sequence, 'create_vm',
            'VM desejada não existe no inventário observado',
            after=after,
        ))
        sequence += 1
        if intent['desired_state'] == 'running':
            actions.append(_action(
                sequence, 'start_vm',
                'Estado desejado é running após a definição da VM',
                before='absent', after='running',
            ))
    else:
        if observed['name'] != intent['name']:
            actions.append(_action(
                sequence, 'rename_vm', 'Nome observado diverge da intenção',
                before=observed['name'], after=intent['name'],
            ))
            sequence += 1

        observed_vcpus = observed['vcpus_reported']
        if observed_vcpus is None:
            warnings.append('vcpus_reported indisponível; alteração de vCPU não pode ser planejada com segurança')
            actions.append(_action(
                sequence, 'inspect_vcpus',
                'vcpus_reported indisponível no snapshot',
                after=intent['resources']['vcpus'], blocked=True,
            ))
            sequence += 1
        elif observed_vcpus != intent['resources']['vcpus']:
            actions.append(_action(
                sequence, 'set_vcpus', 'vCPU observada diverge da intenção',
                before=observed_vcpus, after=intent['resources']['vcpus'],
            ))
            sequence += 1

        observed_memory_kib = observed['max_memory_reported_kib']
        desired_memory_kib = intent['resources']['memory_mib'] * 1024
        if observed_memory_kib is None:
            warnings.append('max_memory_reported_kib indisponível; alteração de RAM não pode ser planejada com segurança')
            actions.append(_action(
                sequence, 'inspect_memory',
                'Memória configurável observada indisponível no snapshot',
                after=intent['resources']['memory_mib'], blocked=True,
            ))
            sequence += 1
        elif observed_memory_kib != desired_memory_kib:
            actions.append(_action(
                sequence, 'set_memory', 'RAM máxima observada diverge da intenção',
                before=(observed_memory_kib // 1024 if observed_memory_kib % 1024 == 0
                        else {'kib': observed_memory_kib}),
                after=intent['resources']['memory_mib'],
            ))
            sequence += 1

        if intent['schema_version'] == 2:
            hardware_actions, hardware_warnings, sequence = _plan_hardware(intent, observed, sequence)
            actions.extend(hardware_actions)
            warnings.extend(hardware_warnings)

        if intent['desired_state'] == 'running' and not observed['active']:
            actions.append(_action(
                sequence, 'start_vm', 'VM está inativa e a intenção exige running',
                before='stopped', after='running',
            ))
        elif intent['desired_state'] == 'stopped' and observed['active']:
            actions.append(_action(
                sequence, 'shutdown_vm', 'VM está ativa e a intenção exige stopped',
                before='running', after='stopped',
            ))

    blocked = any(action['blocked'] for action in actions)
    return {
        **base,
        'status': 'blocked' if blocked else ('changes_planned' if actions else 'converged'),
        'actions': actions,
        'warnings': warnings,
    }
