#!/usr/bin/env bash
# Filesystem/package smoke check only: does not boot or start a VM.
set -euo pipefail

test -s /usr/share/storos/release
test -s /usr/libexec/storos/collect_host.py
test -s /usr/libexec/storos/storos_agent.py
test -s /usr/libexec/storos/storos_config.py
test -s /usr/libexec/storos/storos_vm.py
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
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["source"] == "simulation"; assert d["libvirt"]["status"] == "ok"; assert d["libvirt"]["vms"]; print("StorOS discovery passed against libvirt test driver (no real VM).")' "$snapshot"

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

storosctl vm-plan --intent-file "$scratch/intent.json" --snapshot "$snapshot" > "$scratch/plan.json"
python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p["mode"] == "dry_run"; assert p["can_apply"] is False; assert p["status"] == "changes_planned"; assert p["actions"]; assert all(a["executable"] is False for a in p["actions"])' "$scratch/plan.json"

storosctl vm-reconcile-dry-run --intent-file "$scratch/intent.json" --snapshot "$snapshot" --task-root "$scratch/tasks" > "$scratch/task.json"
python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); assert t["mode"] == "dry_run"; assert t["executable"] is False; assert t["status"] == "planned"; assert t["plan"]["can_apply"] is False' "$scratch/task.json"

storosctl task-list --task-root "$scratch/tasks" > "$scratch/tasks.json"
python3 -c 'import json,sys; t=json.load(open(sys.argv[1])); assert len(t) == 1; assert t[0]["executable"] is False; assert all(a["executable"] is False for a in t[0]["plan"]["actions"])' "$scratch/tasks.json"

printf '%s\n' 'StorOS image content check passed; VM reconciliation is dry-run only and this smoke check does not prove boot, physical media, hypervisor mutation, or GPU sharing.'
