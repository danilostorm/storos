"""StorOS VM intent model and deterministic dry-run planner.

This module never executes hypervisor mutations.
"""
from __future__ import annotations

import hashlib
import json
from uuid import UUID

VM_INTENT_SCHEMA_VERSION = 1
VM_PLAN_SCHEMA_VERSION = 1
DESIRED_STATES = ('running', 'stopped')


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


def validate_vm_intent(document):
    if not isinstance(document, dict):
        raise VMError('Intenção de VM deve ser um objeto JSON')
    if set(document) != {'schema_version', 'uuid', 'name', 'desired_state', 'resources'}:
        raise VMError('Intenção de VM contém campos ausentes ou desconhecidos')
    if document.get('schema_version') != VM_INTENT_SCHEMA_VERSION:
        raise VMError('schema_version da intenção incompatível')

    try:
        vm_uuid = str(UUID(str(document.get('uuid'))))
    except (ValueError, TypeError, AttributeError) as exc:
        raise VMError('uuid da VM inválido') from exc

    name = document.get('name')
    if not isinstance(name, str):
        raise VMError('name da VM inválido')
    name = name.strip()
    if not name or len(name) > 80 or any(ord(ch) < 32 for ch in name):
        raise VMError('name da VM inválido')

    desired_state = document.get('desired_state')
    if desired_state not in DESIRED_STATES:
        raise VMError('desired_state deve ser running ou stopped')

    resources = document.get('resources')
    if not isinstance(resources, dict) or set(resources) != {'vcpus', 'memory_mib'}:
        raise VMError('resources deve conter somente vcpus e memory_mib')
    vcpus = _positive_int(resources.get('vcpus'), 'resources.vcpus', maximum=1024)
    memory_mib = _positive_int(
        resources.get('memory_mib'), 'resources.memory_mib',
        minimum=128, maximum=4 * 1024 * 1024,
    )

    return {
        'schema_version': VM_INTENT_SCHEMA_VERSION,
        'uuid': vm_uuid,
        'name': name,
        'desired_state': desired_state,
        'resources': {'vcpus': vcpus, 'memory_mib': memory_mib},
    }


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
        actions.append(_action(
            sequence, 'create_vm',
            'VM desejada não existe no inventário observado',
            after={
                'uuid': intent['uuid'],
                'name': intent['name'],
                'vcpus': intent['resources']['vcpus'],
                'memory_mib': intent['resources']['memory_mib'],
            },
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
