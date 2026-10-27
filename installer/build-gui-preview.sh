#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$(source /etc/os-release; echo "$ID")" == fedora ]] || { echo 'Fedora VM only' >&2; exit 3; }
systemd-detect-virt --vm >/dev/null || { echo 'VM only' >&2; exit 3; }
KEYFILE="${1:?Usage: build-gui-preview.sh /path/to/public-key}"
[[ -f "$KEYFILE" ]] || exit 2
KEY="$(head -n1 "$KEYFILE")"
[[ "$KEY" == ssh-ed25519\ * || "$KEY" == ssh-rsa\ * ]] || { echo 'Invalid SSH public key' >&2; exit 2; }
OUT="$ROOT/output/gui-preview"
mkdir -p "$OUT/qcow2" "$OUT/raw"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
TOML_KEY="$(printf %s "$KEY" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')"
printf '[[customizations.user]]
name = "storadmin"
key = %s
groups = ["wheel"]
' "$TOML_KEY" > "$TMP/blueprint.toml"
sudo podman build --pull=never -f "$ROOT/installer/Containerfile.gui" -t localhost/storos:gui-preview "$ROOT"
sudo image-builder build --bootc-ref localhost/storos:gui-preview --blueprint "$TMP/blueprint.toml" --output-dir "$OUT/qcow2" --output-name StorOS-gui-preview qcow2
sudo chown -R "$(id -u):$(id -g)" "$OUT"
qemu-img check "$OUT/qcow2/StorOS-gui-preview.qcow2"
echo 'GUI_PREVIEW_QCOW2_READY_FOR_VM_TEST'
