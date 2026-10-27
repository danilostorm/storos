#!/usr/bin/env bash
# Build only inside the existing isolated Fedora StorOS BuildLab VM.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source /etc/os-release
[[ "$ID" = fedora ]] || { echo 'Fedora only'; exit 2; }
systemd-detect-virt --vm >/dev/null || { echo 'Refusing to build on physical host'; exit 2; }
test "$#" = 0 || { echo 'No SSH credentials or user blueprint accepted'; exit 2; }
cd "$ROOT"
python3 -m unittest discover -s tests -q
sudo podman image exists localhost/storos:usb-preview || { echo 'Missing SSH-disabled base image'; exit 3; }
sudo podman build --pull=never -f installer/Containerfile.ui-v04 -t localhost/storos:ui-v04 .
sudo podman run --rm --entrypoint sh localhost/storos:ui-v04 -c 'test "$(readlink /usr/lib/systemd/system/sshd.service)" = /dev/null; test -f /usr/lib/storos/web/hero.webp; test -f /usr/lib/storos/backend/observability.py'
echo UI_V04_OCI_BUILT
OUT="$ROOT/output/ui-v04"
mkdir -p "$OUT"
test ! -e "$OUT/StorOS-v0.4-USB-Preview.raw" || { echo 'Refusing overwrite'; exit 4; }
sudo image-builder build --bootc-ref localhost/storos:ui-v04 --output-dir "$OUT" --output-name StorOS-v0.4-USB-Preview raw
sudo chown -R "$(id -u):$(id -g)" "$OUT"
sha256sum "$OUT/StorOS-v0.4-USB-Preview.raw" > "$OUT/StorOS-v0.4-USB-Preview.raw.sha256"
echo UI_V04_RAW_IMAGE_COMPLETED
