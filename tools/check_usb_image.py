#!/usr/bin/env python3
"""Read-only integrity and partition checks for a candidate StorOS USB IMG/RAW.

Checks structure only, not graphical boot success. Never writes to devices.
Requires a regular FILE (rejects devices, pipes and symlinks).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

BIOS = "21686148-6449-6e6f-744e-656564454649"
EFI = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
ROOTS = {"4f68bce3-e8cd-4db1-96e7-fbcaf984b709", "0fc63daf-8483-4772-8e79-3d69d8477de4"}


class ImageCheckError(ValueError):
    pass


def read_structure(path: Path):
    p = Path(path)
    if not p.is_absolute():
        raise ImageCheckError("Use an absolute image path")
    info = p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size < 2 * 1024**3:
        raise ImageCheckError("Expected a regular USB image file of at least 2 GiB")
    if info.st_size > 128 * 1024**3 or info.st_size % 512:
        raise ImageCheckError("Invalid image size or sector alignment")
    with open(p, "rb") as stream:
        stream.seek(510)
        signature = stream.read(2)
    if signature != b"\x55\xaa":
        raise ImageCheckError("No MBR signature")
    try:
        run = subprocess.run(["sfdisk", "--json", str(p)], timeout=10,
                             capture_output=True, text=True, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ImageCheckError("sfdisk unavailable")
    if run.returncode != 0:
        raise ImageCheckError("Unable to parse partition table")
    try:
        layout = json.loads(run.stdout)["partitiontable"]
        if layout.get("label") != "gpt":
            raise ImageCheckError("Not GPT")
        partitions = layout["partitions"]
        types = [str(item.get("type", "")).lower() for item in partitions]
    except (ValueError, KeyError, TypeError):
        raise ImageCheckError("Partition structure invalid")
    for required, label in ((BIOS, "BIOS Boot"), (EFI, "EFI System")):
        if required not in types:
            raise ImageCheckError("Missing " + label + " partition")
    if not any(t in ROOTS for t in types):
        raise ImageCheckError("Missing recognized Linux root partition")
    sectors = int(layout.get("sectorsize", 512))
    ranges = sorted((int(e["start"]), int(e["start"]) + int(e["size"])) for e in partitions)
    if not ranges or sectors <= 0 or ranges[-1][1] * sectors > info.st_size:
        raise ImageCheckError("Partition exceeds file")
    if any(b[0] < a[1] for a, b in zip(ranges, ranges[1:])):
        raise ImageCheckError("Overlapping partitions")
    return {
        "image": str(p), "size_bytes": info.st_size,
        "partition_table": "gpt",
        "bios_partition": True, "efi_partition": True,
        "linux_root_partition": True, "partitions": len(partitions),
        "boot_tested": False, "meaning": "Structure only; SeaBIOS+OVMF boot still required",
    }


def hash_file(path: Path):
    checksum = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate candidate StorOS USB image, read-only")
    parser.add_argument("image", type=Path)
    parser.add_argument("--verify-sha256", metavar="HEX", help="Expected SHA-256, verifies entire file")
    args = parser.parse_args(argv)
    report = read_structure(args.image)
    if args.verify_sha256:
        value = args.verify_sha256.lower()
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ImageCheckError("Invalid SHA-256 string")
        actual = hash_file(args.image)
        if actual != value:
            raise ImageCheckError("SHA-256 mismatch")
        report["sha256"] = actual
        report["checksum_verified"] = True
    else:
        report["checksum_verified"] = False
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImageCheckError, OSError) as exc:
        print("IMAGE REJECTED:", str(exc), file=__import__("sys").stderr)
        raise SystemExit(2)
