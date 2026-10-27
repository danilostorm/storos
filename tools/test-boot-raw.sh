#!/usr/bin/env bash
# Start a completely isolated UEFI/KVM guest from a RAW USB image using a QCOW2 overlay.
# Never writes to the raw image or passes through a physical host block device.
set -Eeuo pipefail
ROOT=/mnt/user/rea/StorOS
RAW="${1:?RAW path required}"
VM="${2:?VM name required}"
WS="${3:?WebSocket port required}"
case "$RAW" in "$ROOT"/lab/*.raw|"$ROOT"/output/*.raw|"$ROOT"/output/*.img) ;; *) echo 'RAW must be in StorOS lab or output' >&2; exit 2;; esac
[[ "$VM" =~ ^StorOS-BootTest-RAW-[A-Za-z0-9-]{1,35}$ ]] || { echo 'Unsafe VM name'; exit 2; }
[[ "$WS" =~ ^[0-9]{4,5}$ ]] && (( WS >= 5700 && WS <= 5799 )) || { echo 'WebSocket must be 5700-5799'; exit 2; }
test -f "$RAW" && test ! -L "$RAW" || { echo 'Missing or symlink RAW'; exit 2; }
test "$(qemu-img info -f raw --output=json "$RAW" | python3 -c 'import json,sys;print(json.load(sys.stdin)["format"])')" = raw
if virsh dominfo "$VM" >/dev/null 2>&1; then echo 'VM already exists, refusing overwrite'; exit 3; fi
OVERLAY="$ROOT/lab/${VM}-overlay.qcow2"
XML="$ROOT/lab/${VM}.xml"
VARS="$ROOT/lab/${VM}-vars.fd"
for file in "$OVERLAY" "$XML" "$VARS"; do test ! -e "$file" || { echo "File already exists: $file"; exit 4; }; done
test -f /usr/share/qemu/ovmf-x64/OVMF_CODE-pure-efi.fd
cp /usr/share/qemu/ovmf-x64/OVMF_VARS-pure-efi.fd "$VARS"
qemu-img create -f qcow2 -F raw -b "$RAW" "$OVERLAY"
cat > "$XML" <<EOT
<domain type='kvm'>
  <name>$VM</name>
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
    <graphics type='vnc' port='-1' autoport='yes' websocket='$WS' listen='127.0.0.1'/>
    <video><model type='virtio'/></video>
  </devices>
</domain>
EOT
virsh define "$XML"
virsh autostart --disable "$VM" >/dev/null || :
virsh start "$VM"
virsh dominfo "$VM"
virsh domdisplay "$VM"
