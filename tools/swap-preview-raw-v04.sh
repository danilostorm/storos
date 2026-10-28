#!/usr/bin/env bash
# Reuse the existing test VM for a new verified RAW, keeping old disks.
set -Eeuo pipefail
BASE=/mnt/user/rea/StorOS
VM=StorOS-BootTest-RAW-Preview031
IMG="$BASE/output/StorOS-v0.4-USB-Preview.img"
LAB="$BASE/lab"
BACKUP="$LAB/$VM-before-v04.xml"
XML="$LAB/$VM-v04.xml"
OVERLAY="$LAB/$VM-v04-overlay.qcow2"
VARS="$LAB/$VM-v04-vars.fd"
OLD="$LAB/$VM-overlay.qcow2"
OLDVARS="$LAB/$VM-vars.fd"
EXPECTED=3999ccc910da41052f7ba6e683249a526fbaf3ef4140711b768922e74312cae8
[[ -f "$IMG" && ! -L "$IMG" ]] || { echo 'Missing verified image'; exit 2; }
for FILE in "$BACKUP" "$XML" "$OVERLAY" "$VARS"; do
  [[ ! -e "$FILE" ]] || { echo "Refusing overwrite of $FILE"; exit 2; }
done
[[ "$(stat -c %s "$IMG")" = 10737418240 ]] || { echo 'Unexpected image size'; exit 2; }
[[ "$(cut -d' ' -f1 "$IMG.sha256")" = "$EXPECTED" ]] || { echo 'Checksum manifest mismatch'; exit 2; }
[[ "$(virsh domstate "$VM")" = running ]] || { echo 'Test VM not running'; exit 3; }
virsh domblklist "$VM" --details | grep -Fq "$OLD" || { echo 'VM disk changed unexpectedly'; exit 4; }
virsh dumpxml --inactive "$VM" > "$BACKUP"
test -s "$BACKUP"
echo 'Requesting graceful shutdown of the existing test VM'
virsh shutdown "$VM"
for i in {1..45}; do
  [[ "$(virsh domstate "$VM")" = 'shut off' ]] && break
  sleep 2
done
if [[ "$(virsh domstate "$VM")" != 'shut off' ]]; then
  echo 'Guest did not shut down gracefully; preserving original XML and disk'
  exit 5
fi
cp --reflink=auto "$OLDVARS" "$VARS"
qemu-img create -f qcow2 -F raw -b "$IMG" "$OVERLAY"
python3 - "$BACKUP" "$XML" "$OLD" "$OVERLAY" "$OLDVARS" "$VARS" <<'PY'
import sys
from pathlib import Path
src, target, old_disk, new_disk, old_vars, new_vars=sys.argv[1:]
s=Path(src).read_text()
assert s.count(old_disk)==1 and s.count(old_vars)==1
Path(target).write_text(s.replace(old_disk,new_disk).replace(old_vars,new_vars))
PY
if ! virsh define "$XML"; then
  virsh define "$BACKUP" || :
  exit 6
fi
virsh autostart --disable "$VM" >/dev/null || :
if ! virsh start "$VM"; then
  virsh define "$BACKUP" || :
  virsh start "$VM" || :
  exit 7
fi
virsh domblklist "$VM" --details
echo "PREVIEW_REUSED_V04_STARTED $VM"
echo "To restore old boot disk: shut down this VM, then virsh define $BACKUP; virsh start $VM"
