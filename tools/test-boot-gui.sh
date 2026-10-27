#!/usr/bin/env bash
# Boot StorOS in a second, strictly isolated VM. No passthrough or physical disks.
set -Eeuo pipefail
ROOT=/mnt/user/rea/StorOS
NAME=StorOS-BootTest-GUI-Default
SOURCE="$ROOT/output/StorOS-gui-default.qcow2"
OVERLAY="$ROOT/lab/storos-boot-test-gui-default-overlay.qcow2"
VARS="$ROOT/lab/storos-boot-test-gui-default-vars.fd"
XML="$ROOT/lab/storos-boot-test-gui-default.xml"
test -f "$SOURCE" || { echo "Missing completed QCOW2 image: $SOURCE" >&2; exit 2; }
if virsh dominfo "$NAME" >/dev/null 2>&1; then
  echo "Refusing: test VM already exists; inspect before changing it" >&2
  exit 3
fi
test ! -L "$SOURCE" && test ! -L "$OVERLAY"
qemu-img check "$SOURCE" || { echo 'Invalid QCOW2 image' >&2; exit 4; }
if test ! -e "$OVERLAY"; then
  qemu-img create -f qcow2 -F qcow2 -b "$SOURCE" "$OVERLAY"
fi
if test ! -e "$VARS"; then
  cp /usr/share/qemu/ovmf-x64/OVMF_VARS-pure-efi.fd "$VARS"
fi
cat > "$XML" <<EOF
<domain type='kvm'>
  <name>$NAME</name>
  <memory unit='MiB'>4096</memory>
  <vcpu placement='static'>2</vcpu>
  <os>
    <type arch='x86_64'>hvm</type>
    <loader readonly='yes' type='pflash'>/usr/share/qemu/ovmf-x64/OVMF_CODE-pure-efi.fd</loader>
    <nvram>$VARS</nvram>
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
      <source file='$OVERLAY'/>
      <target dev='vda' bus='virtio'/>
    </disk>
    <interface type='network'>
      <source network='default'/>
      <model type='virtio'/>
    </interface>
    <serial type='pty'/><console type='pty'/>
    <channel type='unix'><target type='virtio' name='org.qemu.guest_agent.0'/></channel>
    <graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'/>
    <video><model type='virtio'/></video>
  </devices>
</domain>
EOF
virsh define "$XML"
virsh autostart --disable "$NAME" >/dev/null || :
virsh start "$NAME"
virsh dominfo "$NAME"
virsh domiflist "$NAME"
