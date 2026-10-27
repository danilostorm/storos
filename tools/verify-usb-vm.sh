#!/usr/bin/env bash
# Black-box validation of a USB-preview RAW boot. No SSH or privileged guest agent commands.
set -Eeuo pipefail
VM="${1:-StorOS-BootTest-RAW-Preview031}"
[[ "$VM" =~ ^StorOS-BootTest-RAW-[a-zA-Z0-9-]+$ ]] || { echo 'Unexpected VM name' >&2; exit 2; }
test "$(virsh domstate "$VM")" = running
virsh qemu-agent-command "$VM" '{"execute":"guest-ping"}' | grep -Fq '"return":{}'
IP="$(virsh domifaddr "$VM" --source lease | awk '/ipv4/ {split($4,ip,"/");print ip[1];exit}')"
test -n "$IP" || { echo 'No IPv4 address assigned' >&2; exit 2; }
printf 'RAW_PREVIEW_BOOT_OK: %s (%s)\n' "$VM" "$IP"
python3 - "$IP" <<'PY'
import socket, sys
ip = sys.argv[1]
for port in (22, 80, 8765):
    s = socket.socket()
    s.settimeout(3)
    try:
        result = s.connect_ex((ip, port))
        if result == 0:
            raise SystemExit(f"Unexpected LAN-reachable service: {ip}:{port}")
        print(f"LAN_RESTRICTED: {ip}:{port} not reachable")
    finally:
        s.close()
PY
OUT="/mnt/user/rea/StorOS/lab/${VM}-verified.png"
virsh screenshot "$VM" "$OUT" >/dev/null
echo "SCREENSHOT=$OUT"
echo "NOTE: Check visually for the StorOS kiosk; this is not a filesystem or data-persistence test."
