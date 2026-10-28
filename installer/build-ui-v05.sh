#!/usr/bin/env bash
# Run exclusively inside the StorOS-BuildLab Fedora VM. Never writes a device.
set -Eeuo pipefail
source /etc/os-release
[[ "${ID:-}" = "fedora" ]] || { echo 'Fedora only' >&2; exit 2; }
systemd-detect-virt --vm >/dev/null || { echo 'Refusing non-VM' >&2; exit 2; }
[[ "$#" -eq 0 ]] || { echo 'No disk arguments accepted' >&2; exit 2; }
for tool in sudo podman image-builder sfdisk sha256sum flock mktemp python3; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 2; }
done

cd "$HOME/StorOS"
python3 -m unittest discover -s tests -q
for f in web/index.html web/app.js web/storage.js web/ca-import.js backend/storage.py backend/app_manager.py backend/auth_socket.py tools/storosctl.py; do
  test -s "$f"
done

OUT="$HOME/StorOS/output/ui-v05"
NAME="StorOS-v0.5-USB-Preview.raw"
RAW="$OUT/$NAME"
mkdir -p "$OUT"
# The lock is advisory and limited to this output directory. A stale lock file
# does not block new runs once its process has exited.
exec 9>"$OUT/.build.lock"
flock -n 9 || { echo 'Another StorOS v0.5 build is running' >&2; exit 3; }
for artifact in "$RAW" "$RAW.sha256" "$RAW.structure.json" "$RAW.structure-ok"; do
  [[ ! -e "$artifact" && ! -L "$artifact" ]] || { echo "Refusing overwrite: $artifact" >&2; exit 3; }
done

sudo podman image exists localhost/storos:usb-preview
sudo podman build --pull=never -f installer/Containerfile.ui-v05 -t localhost/storos:ui-v05 .
sudo podman run --rm --entrypoint sh localhost/storos:ui-v05 -c \
  'test "$(readlink /usr/lib/systemd/system/sshd.service)" = /dev/null && test -s /usr/lib/storos/web/ca-import.js && test -s /usr/lib/storos/web/modules.js && test -s /usr/lib/storos/backend/storage.py && test -x /usr/local/bin/storosctl'
echo 'STOROS_V05_OCI_VERIFIED'

# Build and verify in an isolated staging directory before presenting a public
# artifact path. On failure the staging directory remains for diagnosis.
STAGE="$(mktemp -d "$OUT/.build-staging.XXXXXXXX")"
trap 'echo "Incomplete build; inspect private staging directory: $STAGE" >&2' ERR
sudo image-builder build --bootc-ref localhost/storos:ui-v05 \
  --output-dir "$STAGE" --output-name StorOS-v0.5-USB-Preview raw
sudo chown -R -- "$(id -u):$(id -g)" "$STAGE"
test -s "$STAGE/$NAME"
python3 tools/check_usb_image.py "$STAGE/$NAME" > "$STAGE/$NAME.structure.json"
(cd "$STAGE" && sha256sum "$NAME" > "$NAME.sha256")

# A structure-ok marker is written LAST; a partially published file is not a
# validated deliverable and must not be distributed for flashing.
mv -- "$STAGE/$NAME" "$RAW"
mv -- "$STAGE/$NAME.sha256" "$RAW.sha256"
mv -- "$STAGE/$NAME.structure.json" "$RAW.structure.json"
printf 'Structure and SHA-256 recorded. Boot testing still required.\n' > "$STAGE/$NAME.structure-ok"
mv -- "$STAGE/$NAME.structure-ok" "$RAW.structure-ok"
rmdir "$STAGE" 2>/dev/null || echo 'Build staging metadata retained for inspection' >&2
trap - ERR
echo 'STOROS_V05_RAW_STRUCTURE_VERIFIED'
