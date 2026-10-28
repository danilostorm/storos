#!/usr/bin/env python3
"""Document structural relationships in the owner's Unraid Main UI.

Reads only a fixed allowlist of UI module source files and prints hashes,
function names in this small allowlist and UI component markers. It does NOT
copy proprietary source, read keys, execute PHP or interact with the array.
"""
import hashlib
import json
from pathlib import Path

FILES = {
    "array": "dynamix/ArrayDevices.page",
    "pools": "dynamix/CacheDevices.page",
    "boot": "dynamix/BootDevice.page",
    "operations": "dynamix/ArrayOperation.page",
    "disks": "dynamix/DiskList.page",
    "unassigned": "unassigned.devices/UnassignedDevices.page",
}
SYMBOLS = ("main_filter", "cache_filter", "array_devices",
           "disk_status", "fsState", "parity", "flash", "mount", "disk_load")


def examine(root=Path("/usr/local/emhttp/plugins")):
    inventory = {}
    for feature, relative in FILES.items():
        path = root / relative
        if not path.is_file() or path.is_symlink():
            inventory[feature] = {"present": False, "file": relative}
            continue
        raw = path.read_bytes()
        # Only the symbols are reported, not snippets of the vendor implementation.
        inventory[feature] = {
            "present": True,
            "file": relative,
            "size_bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "symbols_detected": [sym for sym in SYMBOLS if sym.encode() in raw],
        }
    return inventory


if __name__ == "__main__":
    print(json.dumps(examine(), indent=2, ensure_ascii=False))
