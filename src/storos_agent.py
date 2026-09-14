"""StorOS host observer. All hypervisor connections are read-only."""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from uuid import UUID

from collect_host import inventory

URIS = ('qemu:///system', 'test:///default')
SNAPSHOT = '/run/storos/status.json'
BOOT_STATE = '/var/lib/storos/boot-state.json'
BOOT_ID = '/proc/sys/kernel/random/boot_id'
MAX_DOMAIN_XML_BYTES = 1024 * 1024


class ProbeError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def run_virsh(uri, args, timeout):
    try:
        result = subprocess.run(
            ['virsh', '--readonly', '--no-pkttyagent', '--connect', uri, *args],
            capture_output=True, text=True, timeout=timeout, check=False,
            env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'},
        )
    except FileNotFoundError as exc:
        raise ProbeError('missing_virsh', 'Ferramenta virsh indisponível.') from exc
    except subprocess.TimeoutExpired as exc:
        raise ProbeError('timeout', 'O libvirt não respondeu no prazo.') from exc
    except (OSError, UnicodeError) as exc:
        raise ProbeError('command_failed', 'Não foi possível consultar o libvirt.') from exc
    if result.returncode:
        raise ProbeError('libvirt_error', 'Consulta recusada ou libvirt indisponível; verifique serviço e permissões.')
    return result.stdout


def parse_info(text, expected_uuid):
    fields = dict(line.split(':', 1) for line in text.splitlines() if ':' in line)
    fields = {k.strip(): v.strip() for k, v in fields.items()}
    try:
        if str(UUID(fields['UUID'])) != expected_uuid:
            raise ValueError('UUID mismatch')
        if not fields['Name'] or not fields['State']:
            raise ValueError('Missing identity')
        cpus = int(fields['CPU(s)'])
        if cpus < 0:
            raise ValueError('Invalid CPU count')
        def memory(key):
            value = fields.get(key)
            if value is None:
                return None
            match = re.fullmatch(r'(\d+) KiB', value)
            if not match:
                raise ValueError('Unknown memory unit')
            return int(match.group(1))
        return dict(uuid=expected_uuid, name=fields['Name'], state=fields['State'],
                    active=fields['Id'] != '-', vcpus_reported=cpus,
                    memory_reported_kib=memory('Used memory'),
                    max_memory_reported_kib=memory('Max memory'))
    except (KeyError, ValueError) as exc:
        raise ProbeError('invalid_response', 'Resposta de VM incompleta ou inconsistente.') from exc


def _explicit_bool(value):
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in ('yes', 'on', 'true', '1'):
        return True
    if lowered in ('no', 'off', 'false', '0'):
        return False
    return None


def _source_descriptor(source, domain_type):
    if source is None:
        return None
    candidates = (
        ('file', 'file'),
        ('dev', 'block'),
        ('volume', 'volume'),
        ('name', 'network'),
        ('path', 'path'),
    )
    for attribute, kind in candidates:
        value = source.get(attribute)
        if value:
            descriptor = {'kind': kind, 'value': value[:4096]}
            if attribute == 'volume' and source.get('pool'):
                descriptor['pool'] = source.get('pool')[:1024]
            if kind == 'network' and source.get('protocol'):
                descriptor['protocol'] = source.get('protocol')[:128]
            return descriptor
    if domain_type:
        return {'kind': domain_type[:128], 'value': None}
    return {'kind': 'unknown', 'value': None}


def parse_domain_xml(text, expected_uuid):
    if not isinstance(text, str):
        raise ProbeError('invalid_response', 'XML de domínio inválido.')
    if len(text.encode('utf-8')) > MAX_DOMAIN_XML_BYTES:
        raise ProbeError('response_too_large', 'XML de domínio excede o limite de segurança.')
    lowered = text.lower()
    if '<!doctype' in lowered or '<!entity' in lowered:
        raise ProbeError('unsafe_xml', 'XML de domínio contém declaração não permitida.')
    try:
        root = ET.fromstring(text)
        if root.tag != 'domain':
            raise ValueError('Unexpected root')
        xml_uuid = root.findtext('./uuid')
        if str(UUID(xml_uuid or '')) != expected_uuid:
            raise ValueError('UUID mismatch')

        os_node = root.find('./os')
        firmware_mode = 'unknown'
        secure_boot = None
        nvram_present = False
        if os_node is not None:
            declared = os_node.get('firmware')
            if declared in ('bios', 'efi'):
                firmware_mode = declared
            loader = os_node.find('./loader')
            if firmware_mode == 'unknown' and loader is not None and loader.get('type') == 'pflash':
                firmware_mode = 'efi'
            # libvirt loader@secure means the firmware is Secure Boot capable;
            # it does not enable/disable Secure Boot. Only the explicit firmware
            # feature is represented as secure_boot in this observer.
            firmware = os_node.find('./firmware')
            if firmware is not None:
                for feature in firmware.findall('./feature'):
                    if feature.get('name') == 'secure-boot':
                        explicit = _explicit_bool(feature.get('enabled'))
                        if explicit is not None:
                            secure_boot = explicit
            nvram_present = os_node.find('./nvram') is not None

        disks = []
        for disk in root.findall('./devices/disk'):
            target = disk.find('./target')
            driver = disk.find('./driver')
            boot = disk.find('./boot')
            disks.append({
                'device': (disk.get('device') or 'unknown')[:64],
                'type': (disk.get('type') or 'unknown')[:64],
                'target': None if target is None else {
                    'dev': (target.get('dev') or '')[:128] or None,
                    'bus': (target.get('bus') or '')[:128] or None,
                },
                'source': _source_descriptor(disk.find('./source'), disk.get('type')),
                'format': None if driver is None else ((driver.get('type') or '')[:128] or None),
                'readonly': disk.find('./readonly') is not None,
                'boot_order': None if boot is None else (
                    int(boot.get('order')) if (boot.get('order') or '').isdigit() else None
                ),
            })

        interfaces = []
        for interface in root.findall('./devices/interface'):
            mac = interface.find('./mac')
            source = interface.find('./source')
            model = interface.find('./model')
            target = interface.find('./target')
            link = interface.find('./link')
            source_data = {}
            if source is not None:
                for key in ('network', 'bridge', 'dev', 'path', 'name'):
                    value = source.get(key)
                    if value:
                        source_data[key] = value[:4096]
            interfaces.append({
                'type': (interface.get('type') or 'unknown')[:64],
                'mac': None if mac is None else ((mac.get('address') or '')[:64].lower() or None),
                'source': source_data or None,
                'model': None if model is None else ((model.get('type') or '')[:128] or None),
                'target_dev': None if target is None else ((target.get('dev') or '')[:128] or None),
                'link_state': None if link is None else ((link.get('state') or '')[:64] or None),
            })

        return {
            'status': 'ok',
            'firmware': {
                'mode': firmware_mode,
                'secure_boot': secure_boot,
                'nvram_present': nvram_present,
            },
            'disks': disks,
            'interfaces': interfaces,
        }
    except (ET.ParseError, ValueError, TypeError) as exc:
        raise ProbeError('invalid_response', 'XML de domínio incompleto ou inconsistente.') from exc


def unavailable_hardware():
    return {'status': 'unavailable', 'firmware': None, 'disks': None, 'interfaces': None}


def discover(uri='qemu:///system', runner=run_virsh, budget=20):
    if uri not in URIS:
        raise ValueError('Somente libvirt local ou o driver de teste são permitidos.')
    deadline = time.monotonic() + budget
    def query(args):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ProbeError('deadline', 'Prazo total da descoberta esgotado.')
        return runner(uri, args, min(5, remaining))
    result = dict(uri=uri, status='unavailable', discovered_count=None, vms=None, errors=[])
    try:
        ids = list(dict.fromkeys(str(UUID(s.strip())) for s in query(['list', '--all', '--uuid']).splitlines() if s.strip()))
    except (ProbeError, ValueError) as exc:
        result['errors'].append(dict(code=getattr(exc, 'code', 'invalid_response'),
                                     message=str(exc) if isinstance(exc, ProbeError) else 'Lista de UUIDs inválida.'))
        return result
    result.update(status='ok', discovered_count=len(ids), vms=[])
    for uid in ids[:1024]:
        try:
            vm = parse_info(query(['dominfo', uid]), uid)
        except ProbeError as exc:
            result['errors'].append(dict(uuid=uid, scope='identity', code=exc.code, message=str(exc)))
            if time.monotonic() >= deadline:
                break
            continue
        try:
            vm['hardware'] = parse_domain_xml(query(['dumpxml', '--inactive', uid]), uid)
        except ProbeError as exc:
            vm['hardware'] = unavailable_hardware()
            result['errors'].append(dict(uuid=uid, scope='hardware', code=exc.code, message=str(exc)))
        result['vms'].append(vm)
        if time.monotonic() >= deadline:
            break
    if len(ids) > 1024:
        result['errors'].append(dict(code='limit', message='Inventário limitado a 1024 VMs.'))
    if result['errors']:
        result['status'] = 'partial'
    return result


def collect(uri='qemu:///system'):
    started = time.time()
    host = inventory()
    guests = discover(uri)
    return dict(schema_version=1, product='StorOS', mode='read_only',
                source='simulation' if uri.startswith('test:') else 'host',
                collection_started_at=started, collected_at=time.time(),
                host=host, libvirt=guests)


def write_snapshot(path, data):
    path = Path(path)
    fd, temporary = tempfile.mkstemp(prefix='.status-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o640)
            json.dump(data, stream, ensure_ascii=True, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_snapshot(path, max_age=30):
    data = json.loads(Path(path).read_text())
    if data['schema_version'] != 1 or data['libvirt']['status'] not in ('ok', 'partial', 'unavailable'):
        raise ValueError('Snapshot incompatible')
    age = time.time() - float(data['collected_at'])
    data['age_seconds'] = round(age, 1)
    data['stale'] = age < -5 or age > max_age
    return data


def read_boot_state(path=BOOT_STATE):
    state = json.loads(Path(path).read_text())
    count = state.get('boot_count')
    last = state.get('last_boot_id')
    if state.get('schema_version') != 1 or not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise ValueError('Boot state incompatible')
    if not isinstance(last, str):
        raise ValueError('Boot id missing')
    UUID(last)
    return state


def write_boot_state(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.boot-state-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o640)
            json.dump(data, stream, ensure_ascii=True, allow_nan=False, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def record_boot(state_path=BOOT_STATE, boot_id_path=BOOT_ID):
    boot_id = Path(boot_id_path).read_text().strip()
    UUID(boot_id)
    try:
        state = read_boot_state(state_path)
    except FileNotFoundError:
        state = dict(schema_version=1, boot_count=0, last_boot_id=None)
    if state.get('last_boot_id') != boot_id:
        state = dict(schema_version=1, boot_count=int(state.get('boot_count', 0)) + 1, last_boot_id=boot_id)
        write_boot_state(state_path, state)
    return state


def wait_for_snapshot(path=SNAPSHOT, timeout=45):
    deadline = time.monotonic() + timeout
    path = Path(path)
    while time.monotonic() < deadline:
        if path.is_file() and path.stat().st_size > 0:
            return True
        time.sleep(1)
    return False


def safe_text(value):
    return ''.join(c if c.isprintable() else '?' for c in str(value))


def render(data):
    guests = data['libvirt']
    lines = ['StorOS — inventário', 'Origem: ' + data['source'],
             'CPU lógica: ' + str(data['host']['logical_cpus']),
             'RAM total: ' + str(data['host']['total_memory']),
             'Descoberta de VMs: ' + guests['status']]
    if data.get('stale'):
        lines.append('ATENÇÃO: coleta desatualizada; estes dados não representam o estado atual.')
    if guests['status'] == 'ok' and not guests['vms']:
        lines.append('Nenhuma VM encontrada nesta conexão.')
    for vm in guests['vms'] or []:
        memory = vm['memory_reported_kib']
        ram = 'indisponível' if memory is None else f'{memory / 1048576:.2f} GiB'
        hardware = vm.get('hardware') or unavailable_hardware()
        if hardware.get('status') == 'ok':
            hw = f" | firmware: {hardware['firmware']['mode']} | discos: {len(hardware['disks'])} | interfaces: {len(hardware['interfaces'])}"
        else:
            hw = ' | hardware virtual: indisponível'
        lines.append(f"{safe_text(vm['name'])} | {vm['uuid']} | {safe_text(vm['state'])} | {vm['vcpus_reported']} vCPU | RAM informada: {ram}{hw}")
    for error in guests['errors']:
        lines.append('Diagnóstico: ' + error['message'])
    lines.append('Observação somente; RAM informada pelo libvirt não é consumo medido dos aplicativos.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inventário StorOS e descoberta de VMs; não altera recursos.')
    parser.add_argument('command', choices=('status', 'discover', 'daemon', 'boot-record', 'boot-marker'), nargs='?', default='status')
    parser.add_argument('--uri', choices=URIS, default=URIS[0])
    parser.add_argument('--snapshot', default=SNAPSHOT)
    parser.add_argument('--boot-state', default=BOOT_STATE)
    parser.add_argument('--boot-id', default=BOOT_ID)
    parser.add_argument('--wait', type=int, default=45)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--interval', type=float, default=10)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args(argv)
    if not 1 <= args.interval <= 3600:
        parser.error('O intervalo deve ser de 1 a 3600 segundos.')
    if not 1 <= args.wait <= 300:
        parser.error('A espera deve ser de 1 a 300 segundos.')
    try:
        if args.command == 'boot-record':
            state = record_boot(args.boot_state, args.boot_id)
            print(f"STOROS_BOOT_STATE boot_count={state['boot_count']} last_boot_id={state['last_boot_id']}", flush=True)
            return 0
        if args.command == 'boot-marker':
            if not wait_for_snapshot(args.snapshot, args.wait):
                return 2
            state = read_boot_state(args.boot_state)
            print(f"STOROS_AGENT_READY snapshot=written boot_count={state['boot_count']}", flush=True)
            return 0
        if args.command == 'daemon':
            stop = threading.Event()
            for signum in (signal.SIGTERM, signal.SIGINT):
                signal.signal(signum, lambda *_: stop.set())
            while not stop.is_set():
                data = collect(args.uri)
                write_snapshot(args.snapshot, data)
                if args.once:
                    return 0 if data['libvirt']['status'] == 'ok' else 2
                stop.wait(args.interval)
            return 0
        data = collect(args.uri) if args.command == 'discover' else read_snapshot(args.snapshot)
        print(json.dumps(data, ensure_ascii=True, indent=2) if args.json else render(data))
        return 0 if data['libvirt']['status'] == 'ok' and not data.get('stale') else 2
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps(dict(error='snapshot_or_host_unavailable',
                              message='Inventário indisponível. Verifique storos-agent e permissões; use discover para consulta direta.')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
