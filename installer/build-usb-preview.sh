#!/usr/bin/env bash
# Build a local-only, unauthenticated-read-only GUI proof-of-boot on an isolated Fedora VM.
# No blueprint user, password or ssh key is injected.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /etc/os-release
test "${ID}" = fedora || { echo 'Refusing build: not Fedora' >&2; exit 2; }
systemd-detect-virt --vm >/dev/null || { echo 'Refusing build: requires a VM' >&2; exit 2; }
if test "$#" -ne 0; then echo 'Do not pass credentials to this build' >&2; exit 3; fi
cd "$ROOT"
python3 -m unittest discover -s tests -q
sudo podman image exists localhost/storos:v0.3.0 || { echo 'Build v0.3.0 base OCI first' >&2; exit 4; }
sudo podman build --pull=never -f installer/Containerfile.usb-preview -t localhost/storos:usb-preview .
sudo podman run --rm --entrypoint /bin/sh localhost/storos:usb-preview -c 'test "$(readlink /usr/lib/systemd/system/sshd.service)" = /dev/null; test -r /usr/lib/storos/web/apps.js; test -r /usr/lib/storos/backend/billing.py'
echo USB_PREVIEW_OCI_READY
OUT="$ROOT/output/usb-preview-0.3.1"
mkdir -p "$OUT"
test ! -e "$OUT/StorOS-v0.3.1-USB-Preview.raw" || { echo 'Refusing to overwrite previous image'; exit 5; }
# No custom blueprint => no storadmin/user public key in disk image.
sudo image-builder build --bootc-ref localhost/storos:usb-preview --output-dir "$OUT" --output-name StorOS-v0.3.1-USB-Preview raw
sudo chown -R "$(id -u):$(id -g)" "$OUT"
sha256sum "$OUT/StorOS-v0.3.1-USB-Preview.raw" > "$OUT/StorOS-v0.3.1-USB-Preview.raw.sha256"
echo USB_PREVIEW_RAW_GENERATED_NO_BLUEPRINT
