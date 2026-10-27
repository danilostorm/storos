#!/usr/bin/env bash
set -Eeuo pipefail
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test "$(source /etc/os-release; echo "${ID:-}")" = fedora || { echo 'REFUSED: Fedora lab only'; exit 3; }
systemd-detect-virt --vm >/dev/null || { echo 'REFUSED: VM only'; exit 3; }
KEY_FILE="${1:?Supply one-line public SSH key file}"
test -f "$KEY_FILE"
umask 077
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
KEY="$(head -n1 "$KEY_FILE")"
case "$KEY" in ssh-ed25519\ *|ssh-rsa\ *|ecdsa-sha2-nistp256\ *) ;; *) echo 'Invalid SSH public key'; exit 5;; esac
TOML_KEY="$(printf '%s' "$KEY" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))')"
cat > "$TMP/blueprint.toml" <<EOF
[[customizations.user]]
name = "storadmin"
key = $TOML_KEY
groups = ["wheel"]
EOF
OUT="$BASE/output/v0.1.1"
mkdir -p "$OUT/qcow2" "$OUT/raw"
echo 'STOROS_011_OCI_BUILD_START'
sudo podman build --pull=never -f "$BASE/installer/Containerfile" -t localhost/storos:v0.1.1 "$BASE"
echo 'STOROS_011_OCI_BUILD_DONE'
echo 'STOROS_011_QCOW2_START'
sudo image-builder build --bootc-ref localhost/storos:v0.1.1 --blueprint "$TMP/blueprint.toml" --output-dir "$OUT/qcow2" --output-name StorOS-v0.1.1 qcow2
echo 'STOROS_011_QCOW2_DONE'
echo 'STOROS_011_RAW_START'
sudo image-builder build --bootc-ref localhost/storos:v0.1.1 --blueprint "$TMP/blueprint.toml" --output-dir "$OUT/raw" --output-name StorOS-v0.1.1 raw
echo 'STOROS_011_RAW_DONE'
sudo chown -R "$(id -u):$(id -g)" "$OUT"
find "$OUT" -maxdepth 2 -type f -printf '%p %s bytes\n'
