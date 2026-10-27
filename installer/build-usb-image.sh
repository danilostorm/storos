#!/usr/bin/env bash
# Build in an isolated Fedora VM ONLY. No disk device is ever written by this script.
set -Eeuo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY_FILE="${1:-}"
if [[ -z "$KEY_FILE" || ! -f "$KEY_FILE" ]]; then
  printf >&2 'Usage: %s /path/to/public-ssh-key.pub\n' "$0"
  exit 2
fi
if [[ "$(source /etc/os-release; echo "${ID:-}")" != "fedora" ]]; then
  echo "REFUSED: this builder must run on Fedora, not on the AEROCOOL Unraid host." >&2
  exit 3
fi
if ! systemd-detect-virt --vm >/dev/null; then
  echo "REFUSED: launch a dedicated Fedora virtual machine for this first build." >&2
  exit 3
fi
for tool in podman image-builder; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 4; }
done
SSH_KEY="$(head -n1 "$KEY_FILE")"
if [[ ! "$SSH_KEY" =~ ^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256)[[:space:]] ]]; then
  echo "SSH key must be a valid-looking one-line public key." >&2
  exit 5
fi
# Avoid shell injection in TOML by rendering the key as a JSON-escaped quoted string.
umask 077
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
KEY_TOML="$(printf '%s' "$SSH_KEY" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
cat > "$TMP/blueprint.toml" <<EOF
[[customizations.user]]
name = "storadmin"
key = $KEY_TOML
groups = ["wheel"]
EOF
mkdir -p "$BASE/output"
echo "Building immutable StorOS bootc OCI image in the Fedora VM..."
sudo podman build --pull=always -f "$BASE/installer/Containerfile" -t localhost/storos:dev "$BASE"
echo "Creating QCOW2 virtual test disk (does not attach to any VM)..."
sudo image-builder build --bootc-ref localhost/storos:dev \
  --blueprint "$TMP/blueprint.toml" --output-dir "$BASE/output/qcow2" --output-name StorOS-test qcow2
echo "Creating RAW USB-bootable whole-disk image (DOES NOT write to a USB device)..."
sudo image-builder build --bootc-ref localhost/storos:dev \
  --blueprint "$TMP/blueprint.toml" --output-dir "$BASE/output/raw" --output-name StorOS-usb raw
sudo chown -R -- "$(id -u):$(id -g)" "$BASE/output"
echo "Produced files (not yet hardware-validated):"
find "$BASE/output" -maxdepth 2 -type f -printf '%p %k KiB\n'
echo "IMPORTANT: Test QCOW2 boot/login first. Do NOT flash USB until validation passes."
