#!/usr/bin/env bash
# Filesystem/package smoke check only: does not boot or start a VM.
set -euo pipefail

test -s /usr/share/storos/release
test -s /usr/libexec/storos/collect_host.py
test -s /usr/libexec/storos/storos_agent.py
test -s /usr/libexec/storos/storos_config.py
test -s /usr/libexec/storos/storos_cli.py
test -s /usr/libexec/storos/storos_web.py
test -s /usr/lib/systemd/system/storos-agent.service
test -s /usr/lib/systemd/system/storos-web.service
test -s /usr/lib/systemd/system-preset/10-storos.preset
grep -Fxq 'enable storos-agent.service' /usr/lib/systemd/system-preset/10-storos.preset
grep -Fxq 'enable storos-web.service' /usr/lib/systemd/system-preset/10-storos.preset

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
printf '%s\n' 'StorOS image content check passed; this smoke check does not prove boot, physical media, or GPU sharing.'
