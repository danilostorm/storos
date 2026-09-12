import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from storos_agent import (
    ProbeError,
    discover,
    main,
    parse_domain_xml,
    parse_info,
    read_snapshot,
    run_virsh,
    write_snapshot,
)

VM1 = '11111111-1111-4111-8111-111111111111'
VM2 = '22222222-2222-4222-8222-222222222222'


def info(uid=VM1, name='Zorin OS', state='shut off', ident='-'):
    return f'''Id: {ident}
Name: {name}
UUID: {uid}
State: {state}
CPU(s): 16
Max memory: 16777216 KiB
Used memory: 8388608 KiB
'''


def domain_xml(uid=VM1):
    return f'''<domain type="kvm">
  <name>Zorin OS</name>
  <uuid>{uid}</uuid>
  <os firmware="efi">
    <type arch="x86_64" machine="q35">hvm</type>
    <loader readonly="yes" secure="yes" type="pflash">/usr/share/OVMF/OVMF_CODE.secboot.fd</loader>
    <nvram>/var/lib/libvirt/qemu/nvram/{uid}_VARS.fd</nvram>
    <firmware><feature enabled="yes" name="secure-boot"/></firmware>
  </os>
  <devices>
    <disk type="file" device="disk">
      <driver name="qemu" type="qcow2"/>
      <source file="/var/lib/libvirt/images/zorin.qcow2"/>
      <target dev="vda" bus="virtio"/>
      <boot order="1"/>
    </disk>
    <disk type="file" device="cdrom">
      <driver name="qemu" type="raw"/>
      <source file="/var/lib/libvirt/images/install.iso"/>
      <target dev="sda" bus="sata"/>
      <readonly/>
    </disk>
    <interface type="network">
      <mac address="52:54:00:12:34:56"/>
      <source network="default"/>
      <target dev="vnet0"/>
      <model type="virtio"/>
      <link state="up"/>
    </interface>
  </devices>
</domain>'''


class DiscoveryTests(unittest.TestCase):
    def test_stopped_vm_and_rename_preserve_uuid(self):
        a = parse_info(info(), VM1)
        b = parse_info(info(name='Outro nome'), VM1)
        self.assertFalse(a['active'])
        self.assertEqual(a['uuid'], b['uuid'])
        self.assertEqual(a['memory_reported_kib'], 8388608)
        calls = []

        def runner(uri, args, timeout):
            calls.append(args)
            if args[0] == 'list':
                return VM1
            if args[0] == 'dominfo':
                return info()
            if args[0] == 'dumpxml':
                return domain_xml()
            raise AssertionError(f'consulta inesperada: {args}')

        result = discover(runner=runner)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(len(result['vms']), 1)
        self.assertEqual(result['vms'][0]['hardware']['status'], 'ok')
        self.assertEqual(calls[0], ['list', '--all', '--uuid'])
        self.assertEqual(calls[1], ['dominfo', VM1])
        self.assertEqual(calls[2], ['dumpxml', '--inactive', VM1])

    def test_domain_xml_observes_firmware_disks_and_interfaces(self):
        hardware = parse_domain_xml(domain_xml(), VM1)
        self.assertEqual(hardware['status'], 'ok')
        self.assertEqual(hardware['firmware'], {
            'mode': 'efi',
            'secure_boot': True,
            'nvram_present': True,
        })
        self.assertEqual(len(hardware['disks']), 2)
        self.assertEqual(hardware['disks'][0]['device'], 'disk')
        self.assertEqual(hardware['disks'][0]['target'], {'dev': 'vda', 'bus': 'virtio'})
        self.assertEqual(hardware['disks'][0]['source']['kind'], 'file')
        self.assertEqual(hardware['disks'][0]['source']['value'], '/var/lib/libvirt/images/zorin.qcow2')
        self.assertEqual(hardware['disks'][0]['format'], 'qcow2')
        self.assertEqual(hardware['disks'][0]['boot_order'], 1)
        self.assertFalse(hardware['disks'][0]['readonly'])
        self.assertTrue(hardware['disks'][1]['readonly'])
        self.assertEqual(hardware['interfaces'], [{
            'type': 'network',
            'mac': '52:54:00:12:34:56',
            'source': {'network': 'default'},
            'model': 'virtio',
            'target_dev': 'vnet0',
            'link_state': 'up',
        }])

    def test_domain_xml_rejects_mismatch_and_declarations(self):
        with self.assertRaises(ProbeError) as mismatch:
            parse_domain_xml(domain_xml(VM2), VM1)
        self.assertEqual(mismatch.exception.code, 'invalid_response')

        unsafe = '<!DOCTYPE domain [<!ENTITY demo "value">]>' + domain_xml()
        with self.assertRaises(ProbeError) as declaration:
            parse_domain_xml(unsafe, VM1)
        self.assertEqual(declaration.exception.code, 'unsafe_xml')

    def test_hardware_probe_failure_preserves_vm_and_marks_partial(self):
        def runner(uri, args, timeout):
            if args[0] == 'list':
                return VM1
            if args[0] == 'dominfo':
                return info()
            if args[0] == 'dumpxml':
                raise ProbeError('libvirt_error', 'XML unavailable')
            raise AssertionError(f'consulta inesperada: {args}')

        result = discover(runner=runner)
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(len(result['vms']), 1)
        self.assertEqual(result['vms'][0]['uuid'], VM1)
        self.assertEqual(result['vms'][0]['hardware'], {
            'status': 'unavailable',
            'firmware': None,
            'disks': None,
            'interfaces': None,
        })
        self.assertEqual(result['errors'][0]['scope'], 'hardware')
        self.assertEqual(result['errors'][0]['uuid'], VM1)

    def test_unavailable_is_not_empty_success(self):
        def broken(*args):
            raise ProbeError('libvirt_error', 'Unavailable')
        result = discover(runner=broken)
        self.assertEqual(result['status'], 'unavailable')
        self.assertIsNone(result['vms'])
        empty = discover(runner=lambda *args: '')
        self.assertEqual(empty['status'], 'ok')
        self.assertEqual(empty['vms'], [])

    def test_vm_disappearing_returns_partial_inventory(self):
        def runner(uri, args, timeout):
            if args[0] == 'list':
                return VM1 + '\n' + VM2
            if args[0] == 'dominfo' and args[1] == VM2:
                raise ProbeError('libvirt_error', 'Gone')
            if args[0] == 'dominfo':
                return info()
            if args[0] == 'dumpxml':
                return domain_xml()
            raise AssertionError(f'consulta inesperada: {args}')

        result = discover(runner=runner)
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['discovered_count'], 2)
        self.assertEqual(len(result['vms']), 1)
        self.assertEqual(result['vms'][0]['hardware']['status'], 'ok')
        self.assertEqual(result['errors'][0]['uuid'], VM2)
        self.assertEqual(result['errors'][0]['scope'], 'identity')

    def test_malformed_identity_never_reaches_dominfo(self):
        calls = []
        def runner(uri, args, timeout):
            calls.append(args)
            return 'not-a-valid-uuid'
        result = discover(runner=runner)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(len(calls), 1)
        with self.assertRaises(ProbeError):
            parse_info(info(uid=VM2), VM1)
        with self.assertRaises(ProbeError):
            parse_info(info().replace('8388608 KiB', '8 GB'), VM1)

    def test_remote_uri_rejected(self):
        with self.assertRaises(ValueError):
            discover('qemu+ssh://example/system')

    def test_readonly_command_and_missing_tool(self):
        with patch('storos_agent.subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'ok')) as run:
            self.assertEqual(run_virsh('qemu:///system', ['dominfo', VM1], 2), 'ok')
            args, kwargs = run.call_args
            self.assertIn('--readonly', args[0])
            self.assertIn('--no-pkttyagent', args[0])
            self.assertFalse(kwargs.get('shell', False))
            self.assertEqual(kwargs['env']['LC_ALL'], 'C')
            self.assertEqual(kwargs['timeout'], 2)
        with patch('storos_agent.subprocess.run', side_effect=FileNotFoundError):
            with self.assertRaises(ProbeError) as raised:
                run_virsh('qemu:///system', ['list'], 2)
            self.assertEqual(raised.exception.code, 'missing_virsh')

    def test_timeout_is_explicit(self):
        with patch('storos_agent.subprocess.run', side_effect=subprocess.TimeoutExpired('virsh', 2)):
            result = discover()
        self.assertEqual(result['errors'][0]['code'], 'timeout')
        self.assertIsNone(result['vms'])


class SnapshotTests(unittest.TestCase):
    def test_failed_write_preserves_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'status.json'
            write_snapshot(target, {'old': True})
            with self.assertRaises(ValueError):
                write_snapshot(target, {'bad': float('nan')})
            self.assertEqual(json.loads(target.read_text()), {'old': True})
            self.assertEqual(target.stat().st_mode & 0o777, 0o640)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_stale_snapshot_is_not_healthy(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'status.json'
            data = dict(schema_version=1, collected_at=time.time() - 90,
                        libvirt=dict(status='ok', vms=[]))
            write_snapshot(target, data)
            self.assertTrue(read_snapshot(target)['stale'])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(['status', '--snapshot', str(target), '--json'])
            self.assertEqual(code, 2)
            self.assertTrue(json.loads(output.getvalue())['stale'])

    def test_missing_snapshot_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()) as output:
            code = main(['status', '--snapshot', str(Path(directory)/'absent'), '--json'])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())['error'], 'snapshot_or_host_unavailable')


if __name__ == '__main__':
    unittest.main()
