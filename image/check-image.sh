#!/usr/bin/env bash
# Filesystem/package smoke check only: does not boot or start a VM.
set -euo pipefail
test -s /usr/share/storos/release
test -s /usr/libexec/storos/collect_host.py
for executable in virsh virt-install qemu-system-x86_64 python3; do
    command -v "$executable"
done
virsh --version
qemu-system-x86_64 --version
python3 -c 'import ast; ast.parse(open("/usr/libexec/storos/collect_host.py").read())'
rpm -q libvirt-daemon-kvm
systemctl is-enabled storos-agent.service
snapshot=$(mktemp)
trap 'rm -f "$snapshot"' EXIT
storosctl discover --uri test:///default --json > "$snapshot"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert d["source"] == "simulation"; assert d["libvirt"]["status"] == "ok"; assert d["libvirt"]["vms"]; print("StorOS discovery passed against libvirt test driver (no real VM).")' "$snapshot"
printf '%s\n' 'StorOS image content check passed; boot and GPU sharing NOT tested.'
