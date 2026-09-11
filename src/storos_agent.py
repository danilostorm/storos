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
from uuid import UUID

from collect_host import inventory

URIS = ('qemu:///system', 'test:///default')
SNAPSHOT = '/run/storos/status.json'


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
        # Do not publish stderr: it may contain host paths or other private data.
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
            result['vms'].append(parse_info(query(['dominfo', uid]), uid))
        except ProbeError as exc:
            result['errors'].append(dict(uuid=uid, code=exc.code, message=str(exc)))
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
        lines.append(f"{safe_text(vm['name'])} | {vm['uuid']} | {safe_text(vm['state'])} | {vm['vcpus_reported']} vCPU | RAM informada: {ram}")
    for error in guests['errors']:
        lines.append('Diagnóstico: ' + error['message'])
    lines.append('Observação somente; RAM informada pelo libvirt não é consumo medido dos aplicativos.')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Inventário StorOS e descoberta de VMs; não altera recursos.')
    parser.add_argument('command', choices=('status', 'discover', 'daemon'), nargs='?', default='status')
    parser.add_argument('--uri', choices=URIS, default=URIS[0])
    parser.add_argument('--snapshot', default=SNAPSHOT)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--interval', type=float, default=10)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args(argv)
    if not 1 <= args.interval <= 3600:
        parser.error('O intervalo deve ser de 1 a 3600 segundos.')
    try:
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
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(error='snapshot_or_host_unavailable',
                              message='Inventário indisponível. Verifique storos-agent e permissões; use discover para consulta direta.')))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
