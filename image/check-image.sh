#!/usr/bin/env bash
# Filesystem/package smoke check only: does not boot or start a VM.
set -euo pipefail

test -s /usr/share/storos/release
test -s /usr/libexec/storos/collect_host.py
test -s /usr/libexec/storos/storos_agent.py
test -s /usr/libexec/storos/storos_config.py
test -s /usr/libexec/storos/storos_vm.py
test -s /usr/libexec/storos/storos_vm_store.py
test -s /usr/libexec/storos/storos_tasks.py
test -s /usr/libexec/storos/storos_cli.py
test -s /usr/libexec/storos/storos_web.py
test -s /usr/lib/systemd/system/storos-agent.service
test -s /usr/lib/systemd/system/storos-web.service
test -s /usr/lib/systemd/system-preset/10-storos.preset
grep -Fxq 'enable storos-agent.service' /usr/lib/systemd/system-preset/10-storos.preset
grep -Fxq 'enable storos-web.service' /usr/lib/systemd/system-preset/10-storos.preset
grep -Fxq 'Wants=storos-agent.service' /usr/lib/systemd/system/storos-web.service
grep -Fxq 'After=network.target' /usr/lib/systemd/system/storos-web.service
if grep -Fxq 'After=storos-agent.service' /usr/lib/systemd/system/storos-web.service; then
    echo 'storos-web.service must not serialize panel startup behind storos-agent.service' >&2
    exit 1
fi

for executable in virsh virt-install qemu-system-x86_64 python3; do
    command -v "$executable"
done
virsh --version
qemu-system-x86_64 --version
python3 - <<'PY'
import ast
for path in (
    '/usr/libexec/storos/collect_host.py',
    '/usr/libexec/storos/storos_agent.py',
    '/usr/libexec/storos/storos_config.py',
    '/usr/libexec/storos/storos_vm.py',
    '/usr/libexec/storos/storos_vm_store.py',
    '/usr/libexec/storos/storos_tasks.py',
    '/usr/libexec/storos/storos_cli.py',
    '/usr/libexec/storos/storos_web.py',
):
    ast.parse(open(path).read())
PY
rpm -q libvirt-daemon-kvm
systemctl is-enabled storos-agent.service
systemctl is-enabled storos-web.service

scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
storosctl config-init --config-root "$scratch/config" >/dev/null
storosctl config-show --config-root "$scratch/config" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["generation"] == 1; assert d["settings"]["features"]["vm_write_enabled"] is False'
storosctl web-token-init --token-file "$scratch/admin.token" >/dev/null
test "$(stat -c '%a' "$scratch/admin.token")" = 600

snapshot="$scratch/status.json"
storosctl discover --uri test:///default --json > "$snapshot"
python3 - "$snapshot" <<'PY'
import json
import sys

d = json.load(open(sys.argv[1]))
assert d['source'] == 'simulation'
assert d['libvirt']['status'] == 'ok'
vms = d['libvirt']['vms']
assert vms
for vm in vms:
    hardware = vm.get('hardware')
    assert hardware is not None
    assert hardware['status'] == 'ok'
    assert isinstance(hardware['firmware'], dict)
    assert set(hardware['firmware']) == {'mode', 'secure_boot', 'nvram_present'}
    assert isinstance(hardware['disks'], list)
    assert isinstance(hardware['interfaces'], list)
print('StorOS discovery and virtual hardware observation passed against libvirt test driver (no real VM).')
PY

# Legacy schema 1 must remain valid and hash-stable through the existing store/planner/task path.
vm_uuid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
cat > "$scratch/intent.json" <<'JSON'
{
  "schema_version": 1,
  "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "name": "image-smoke-dry-run",
  "desired_state": "running",
  "resources": {
    "vcpus": 2,
    "memory_mib": 1024
  }
}
JSON

storosctl vm-intent-apply --intent-file "$scratch/intent.json" --intent-root "$scratch/intents" --expected-generation 0 > "$scratch/intent-record.json"
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["generation"] == 1; assert r["vm_uuid"] == sys.argv[2]; assert r["intent"]["schema_version"] == 1; assert "hardware" not in r["intent"]; assert len(r["intent_sha256"]) == 64' "$scratch/intent-record.json" "$vm_uuid"

storosctl vm-plan --vm-uuid "$vm_uuid" --intent-root "$scratch/intents" --snapshot "$snapshot" > "$scratch/plan.json"
python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p["mode"] == "dry_run"; assert p["can_apply"] is False; assert p["status"] == "changes_planned"; assert p["actions"]; assert all(a["executable"] is False for a in p["actions"])' "$scratch/plan.json"

storosctl vm-reconcile-dry-run --vm-uuid "$vm_uuid" --intent-root "$scratch/intents" --snapshot "$snapshot" --task-root "$scratch/tasks" > "$scratch/task.json"
python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); assert t["schema_version"] == 2; assert t["mode"] == "dry_run"; assert t["executable"] is False; assert t["status"] == "planned"; assert t["preconditions"]["intent_generation"] == 1; assert t["preconditions"]["intent_sha256"] == t["plan"]["intent_sha256"]; assert t["preconditions"]["snapshot_sha256"] == t["plan"]["snapshot_sha256"]; assert t["plan"]["can_apply"] is False' "$scratch/task.json"

storosctl task-list --task-root "$scratch/tasks" > "$scratch/tasks.json"
python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); assert len(t) == 1; assert t[0]["executable"] is False; assert all(a["executable"] is False for a in t[0]["plan"]["actions"])' "$scratch/tasks.json"

# Schema 2 is built from the observed test-driver VM itself. Empty managed device lists
# mean "manage none", not detach observed extras; firmware is asserted only when known.
python3 - "$snapshot" "$scratch/intent-v2.json" <<'PY'
import json
import sys

snapshot = json.load(open(sys.argv[1]))
vm = snapshot['libvirt']['vms'][0]
assert vm['vcpus_reported'] is not None
assert vm['max_memory_reported_kib'] is not None
assert vm['max_memory_reported_kib'] % 1024 == 0
mode = vm['hardware']['firmware']['mode']
firmware = {'mode': mode} if mode in ('bios', 'efi') else None
intent = {
    'schema_version': 2,
    'uuid': vm['uuid'],
    'name': vm['name'],
    'desired_state': 'running' if vm['active'] else 'stopped',
    'resources': {
        'vcpus': vm['vcpus_reported'],
        'memory_mib': vm['max_memory_reported_kib'] // 1024,
    },
    'hardware': {
        'firmware': firmware,
        'disks': [],
        'interfaces': [],
    },
}
json.dump(intent, open(sys.argv[2], 'w'), sort_keys=True)
PY

vm_uuid_v2=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["uuid"])' "$scratch/intent-v2.json")
storosctl vm-intent-apply --intent-file "$scratch/intent-v2.json" --intent-root "$scratch/intents-v2" --expected-generation 0 > "$scratch/intent-v2-record.json"
python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); assert r["intent"]["schema_version"] == 2; assert set(r["intent"]["hardware"]) == {"firmware", "disks", "interfaces"}; assert len(r["intent_sha256"]) == 64' "$scratch/intent-v2-record.json"
storosctl vm-plan --vm-uuid "$vm_uuid_v2" --intent-root "$scratch/intents-v2" --snapshot "$snapshot" > "$scratch/plan-v2.json"
python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p["intent"]["schema_version"] == 2; assert p["mode"] == "dry_run"; assert p["can_apply"] is False; assert p["status"] == "converged"; assert p["actions"] == []' "$scratch/plan-v2.json"

printf '%s\n' 'StorOS image content check passed; VM intent schemas 1 and 2 remain dry-run only. This smoke check does not prove physical media, hypervisor mutation, or GPU sharing.'
