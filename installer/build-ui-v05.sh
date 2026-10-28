#!/usr/bin/env bash
# Run exclusively in StorOS-BuildLab Fedora VM. No physical device access.
set -Eeuo pipefail
source /etc/os-release
[[ "$ID" = "fedora" ]] || { echo 'Fedora only' >&2;exit 2; }
systemd-detect-virt --vm >/dev/null || { echo 'Refusing non-VM' >&2;exit 2; }
[[ "$#" -eq 0 ]] || { echo 'No disk arguments accepted' >&2;exit 2; }
cd "$HOME/StorOS"
python3 -m unittest discover -s tests -q
for f in web/index.html web/app.js web/storage.js web/ca-import.js backend/storage.py backend/app_manager.py backend/auth_socket.py tools/storosctl.py; do test -s "$f"; done
sudo podman image exists localhost/storos:usb-preview
sudo podman build --pull=never -f installer/Containerfile.ui-v05 -t localhost/storos:ui-v05 .
sudo podman run --rm --entrypoint sh localhost/storos:ui-v05 -c \
  'test "$(readlink /usr/lib/systemd/system/sshd.service)" = /dev/null && test -s /usr/lib/storos/web/ca-import.js && test -s /usr/lib/storos/web/modules.js && test -s /usr/lib/storos/backend/storage.py && test -x /usr/local/bin/storosctl'
echo 'STOROS_V05_OCI_VERIFIED'
OUT="$HOME/StorOS/output/ui-v05"
mkdir -p "$OUT"
test ! -e "$OUT/StorOS-v0.5-USB-Preview.raw" || { echo 'Refusing overwrite'; exit 3; }
sudo image-builder build --bootc-ref localhost/storos:ui-v05 \
  --output-dir "$OUT" --output-name StorOS-v0.5-USB-Preview raw
sudo chown -R "$(id -u):$(id -g)" "$OUT"
sha256sum "$OUT/StorOS-v0.5-USB-Preview.raw" > "$OUT/StorOS-v0.5-USB-Preview.raw.sha256"
echo 'STOROS_V05_RAW_BUILT'
