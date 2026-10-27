#!/usr/bin/env bash
# Isolated cloud-image VM, never passes through physical disks.
set -Eeuo pipefail
LAB=/mnt/user/rea/StorOS/lab
NAME=StorOS-BuildLab
BASE="$LAB/Fedora-Cloud-Base-Generic-44-1.7.x86_64.qcow2"
DISK="$LAB/storos-fedora-build.qcow2"
SEED="$LAB/seed-cidata.img"
KEY="$LAB/storos-lab-ed25519"
XML="$LAB/storos-buildlab.xml"
EXPECTED="28680fe5b371a5a82ebf43a31926e086a168e59949d03969c5093e7071f90b7f"
if virsh dominfo "$NAME" >/dev/null 2>&1; then
  echo "Refusing: VM already exists" >&2
  exit 2
fi
test "$(id -u)" -eq 0
test -d "$LAB" && ! test -L "$LAB"
echo "$EXPECTED  $BASE" | sha256sum -c
test -f "$KEY" || ssh-keygen -q -t ed25519 -N '' -C 'storos-lab-only' -f "$KEY"
chmod 600 "$KEY"
umask 077
if test ! -e "$DISK"; then
  qemu-img create -f qcow2 -F qcow2 -b "$BASE" "$DISK" 75G
fi
if test ! -e "$SEED"; then
  PUBKEY="$(cat "$KEY.pub")"
  cat > "$LAB/user-data" <<EOF
#cloud-config
hostname: storos-lab
manage_etc_hosts: true
disable_root: true
ssh_pwauth: false
users:
  - name: storbuilder
    gecos: StorOS Builder
    groups: [wheel]
    shell: /bin/bash
    sudo: "ALL=(ALL) NOPASSWD:ALL"
    lock_passwd: true
    ssh_authorized_keys:
      - $PUBKEY
growpart:
  mode: auto
  devices: ["/"]
resize_rootfs: true
EOF
  cat > "$LAB/meta-data" <<EOF
instance-id: storos-buildlab-20261027
local-hostname: storos-lab
EOF
  truncate -s 32M "$SEED"
  mkfs.vfat -n CIDATA "$SEED" >/dev/null
  mcopy -i "$SEED" "$LAB/user-data" ::user-data
  mcopy -i "$SEED" "$LAB/meta-data" ::meta-data
fi
cat > "$XML" <<EOF
<domain type='kvm'>
  <name>$NAME</name>
  <memory unit='MiB'>8192</memory>
  <currentMemory unit='MiB'>8192</currentMemory>
  <vcpu placement='static'>4</vcpu>
  <os>
    <type arch='x86_64'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features><acpi/><apic/></features>
  <cpu mode='host-model' check='partial'/>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>destroy</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none'/>
      <source file='$DISK'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <disk type='file' device='disk'>
      <driver name='qemu' type='raw' cache='none'/>
      <source file='$SEED'/>
      <target dev='vdb' bus='virtio'/>
      <readonly/>
    </disk>
    <interface type='network'>
      <source network='default'/>
      <model type='virtio'/>
    </interface>
    <serial type='pty'/>
    <console type='pty'/>
    <channel type='unix'>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
    </channel>
    <graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'/>
    <video><model type='virtio'/></video>
    <memballoon model='virtio'/>
  </devices>
</domain>
EOF
virsh define "$XML"
virsh autostart --disable "$NAME" >/dev/null || true
virsh start "$NAME"
echo "StorOS isolated VM started. Disk: $DISK; network: default NAT."
virsh dominfo "$NAME" | head -15
virsh domiflist "$NAME"
