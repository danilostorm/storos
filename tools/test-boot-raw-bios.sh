#!/usr/bin/env bash
# SeaBIOS validation VM from a StorOS RAW image; no physical disks or network.
set -Eeuo pipefail
ROOT=/mnt/user/rea/StorOS
if [[ "$#" -ne 2 ]]; then
  echo "Usage: test-boot-raw-bios.sh StorOS-USB-Preview.raw StorOS-BootTest-RAW-v050-BIOS" >&2
  exit 2
fi
RAW="$1"
VM="$2"
# Only the StorOS output file, never a block device or arbitrary host path.
case "$RAW" in
  "$ROOT"/output/StorOS-v*-USB-Preview.raw) ;;
  *) echo "Refusing non-StorOS RAW path" >&2; exit 2 ;;
esac
[[ "$VM" =~ ^StorOS-BootTest-RAW-v[0-9]+-BIOS$ ]] || { echo "Invalid BIOS test VM name" >&2; exit 2; }
test -f "$RAW" && test ! -L "$RAW" || { echo "Missing or symlink source image" >&2; exit 2; }
test "$(qemu-img info -f raw --output=json "$RAW" | python3 -c 'import sys,json;print(json.load(sys.stdin)["format"])')" = "raw"
if virsh -c qemu:///system dominfo "$VM" >/dev/null 2>&1; then
  echo "VM already exists; refusing to replace it" >&2
  exit 3
fi
OVERLAY="$ROOT/lab/$VM-overlay.qcow2"
XML="$ROOT/lab/$VM.xml"
for file in "$OVERLAY" "$XML"; do
  test ! -e "$file" && test ! -L "$file" || { echo "Existing test artifact: $file" >&2; exit 4; }
done
# A disposable overlay means the original USB image is never modified.
qemu-img create -f qcow2 -F raw -b "$RAW" "$OVERLAY"
cat > "$XML" <<EOF
<domain type='kvm'>
  <name>$VM</name>
  <memory unit='MiB'>3072</memory>
  <vcpu placement='static'>2</vcpu>
  <os><type arch='x86_64'>hvm</type><boot dev='hd'/></os>
  <features><acpi/><apic/></features>
  <cpu mode='host-model' check='partial'/>
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
    <serial type='pty'/><console type='pty'/>
    <channel type='unix'><target type='virtio' name='org.qemu.guest_agent.0'/></channel>
    <graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'/>
    <video><model type='virtio'/></video>
  </devices>
</domain>
EOF
virsh -c qemu:///system define "$XML"
virsh -c qemu:///system autostart --disable "$VM"
virsh -c qemu:///system start "$VM"
virsh -c qemu:///system dominfo "$VM"
virsh -c qemu:///system domdisplay "$VM"
echo "SeaBIOS laboratory boot started; validate VNC and guest agent separately"
