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
printf '%s\n' 'StorOS image content check passed; boot and GPU sharing NOT tested.'
