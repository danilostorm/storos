#!/usr/bin/env bash
# Reproducible USB/QCOW2 lab image: never runs on Unraid host or flashes disks.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ "$(source /etc/os-release; echo "${ID}")" == fedora ]] || { echo 'Only Fedora VM supported'; exit 3; }
systemd-detect-virt --vm >/dev/null || { echo 'Refusing to build outside a VM'; exit 3; }
KEYFILE="${1:?Usage: build-v0.3-apps-gui.sh /path/to/SSH_public_key.pub}"
[[ -r "$KEYFILE" ]] || exit 2
KEY="$(head -n1 "$KEYFILE")"
[[ "$KEY" == ssh-ed25519\ * || "$KEY" == ssh-rsa\ * ]] || { echo 'Invalid public key'; exit 2; }
OUT="$ROOT/output/v0.3.0"
mkdir -p "$OUT/qcow2" "$OUT/raw"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
TOML_KEY="$(printf %s "$KEY" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
printf '[[customizations.user]]\nname = "storadmin"\nkey = %s\ngroups = ["wheel"]\n' "$TOML_KEY" > "$TMP/blueprint.toml"
python3 -m unittest discover -s "$ROOT/tests" -q
sudo podman build --pull=never -f "$ROOT/installer/Containerfile.gui" -t localhost/storos:v0.3.0 "$ROOT"
echo 'STOROS_V030_OCI_READY'
sudo image-builder build --bootc-ref localhost/storos:v0.3.0 --blueprint "$TMP/blueprint.toml" --output-dir "$OUT/qcow2" --output-name StorOS-v0.3.0-GUI qcow2
sudo chown -R "$(id -u):$(id -g)" "$OUT/qcow2"
qemu-img check "$OUT/qcow2/StorOS-v0.3.0-GUI.qcow2"
echo 'STOROS_V030_QCOW2_READY'
sudo image-builder build --bootc-ref localhost/storos:v0.3.0 --blueprint "$TMP/blueprint.toml" --output-dir "$OUT/raw" --output-name StorOS-v0.3.0-USB raw
sudo chown -R "$(id -u):$(id -g)" "$OUT/raw"
echo 'STOROS_V030_RAW_READY'
sha256sum "$OUT"/qcow2/* "$OUT"/raw/* > "$OUT/SHA256SUMS"
