"""StorOS read-only storage and share inventory for the *local* Linux instance.

Never opens disks for writing, mounts filesystems, reads secrets or calls sudo.
No host Unraid disks can be modified from this module.
"""
from __future__ import annotations

import configparser
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from observability import mount_usage, _command

_CACHE_SECONDS = 75
_cache = (0.0, None)
_DISK_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


def _bytes(value):
    try:
        n = int(value)
        return n if n >= 0 else None
    except (ValueError, TypeError):
        return None


def _mounts(raw):
    places = raw.get("mountpoints")
    if not isinstance(places, list):
        places = [raw.get("mountpoint")]
    return [p for p in places if isinstance(p, str) and p.startswith("/")]


def _partition(raw):
    mounts = _mounts(raw)
    return {
        "name": str(raw.get("name") or "")[:64],
        "type": raw.get("type"),
        "size_bytes": _bytes(raw.get("size")),
        "filesystem": raw.get("fstype") or None,
        "label": raw.get("label") or None,
        "mountpoints": mounts,
        "usage": mount_usage(mounts[0]) if mounts else None,
        "read_only": raw.get("ro") is True,
    }


def _smart(name, model, transport):
    if transport == "virtio" or (model and "QEMU" in model.upper()):
        return {"available": False, "health": None, "reason": "Dispositivo virtual: SMART físico não exposto"}
    if not shutil.which("smartctl"):
        return {"available": False, "health": None, "reason": "smartctl não instalado"}
    if not _DISK_NAME.fullmatch(name):
        return {"available": False, "health": None, "reason": "Nome de dispositivo inválido"}
    # Device path is derived ONLY from lsblk, not request input; no sudo.
    # -n standby avoids waking a sleeping disk. A nonzero exit can mean SMART
    # warnings, so parse the JSON only if a smart_status field is actually present.
    try:
        out = subprocess.run(
            ["smartctl", "-H", "-j", "-n", "standby", "/dev/" + name],
            capture_output=True, text=True, timeout=4, check=False,
        )
        data = json.loads(out.stdout)
        status = data.get("smart_status")
        if isinstance(status, dict) and isinstance(status.get("passed"), bool):
            return {"available": True, "health": "PASSED" if status["passed"] else "FAILED", "reason": None}
        return {"available": False, "health": None, "reason": "SMART não acessível nesta instância"}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"available": False, "health": None, "reason": "Falha ou permissão insuficiente para SMART"}


def _smb_shares(path=Path("/etc/samba/smb.conf")):
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {"available": False, "items": [], "reason": "Configuração Samba indisponível"}
    cfg = configparser.RawConfigParser(strict=False, interpolation=None, allow_no_value=True)
    try:
        cfg.read_string(content)
    except configparser.Error:
        return {"available": False, "items": [], "reason": "Configuração Samba não interpretável"}
    items = []
    for section in cfg.sections():
        if section.lower() in ("global", "homes", "printers", "print$"):
            continue
        items.append({
            "name": section[:120],
            "path": cfg.get(section, "path", fallback=None),
            "read_only": cfg.get(section, "read only", fallback=None),
        })
    return {"available": True, "items": items[:100], "reason": None}


def _nfs_shares(path=Path("/etc/exports")):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return {"available": False, "items": [], "reason": "Configuração NFS indisponível"}
    items = []
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line or not line.startswith("/"):
            continue
        fields = line.split()
        if len(fields) > 1:
            items.append({"path": fields[0][:512], "clients_configured": len(fields) - 1})
    return {"available": True, "items": items[:100], "reason": None}


def _collect():
    raw = _command(["lsblk", "-J", "-b", "-o", "NAME,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL,RO,TRAN"], timeout=5)
    if raw is None:
        return {
            "available": False, "reason": "lsblk indisponível ou sem permissão",
            "disks": [], "shares": {"smb": _smb_shares(), "nfs": _nfs_shares()},
            "scope": "Sistema StorOS local", "read_only": True,
        }
    try:
        devices = json.loads(raw)["blockdevices"]
        if not isinstance(devices, list):
            raise ValueError("Not a list")
    except (KeyError, ValueError, TypeError):
        return {
            "available": False, "reason": "Inventário lsblk inválido",
            "disks": [], "shares": {"smb": _smb_shares(), "nfs": _nfs_shares()},
            "scope": "Sistema StorOS local", "read_only": True,
        }
    disks = []
    for entry in devices:
        name = str(entry.get("name") or "")
        if entry.get("type") != "disk" or name.startswith("zram") or not _DISK_NAME.fullmatch(name):
            continue
        model = entry.get("model")
        transport = entry.get("tran")
        partitions = [_partition(p) for p in entry.get("children") or []
                      if p.get("type") in ("part", "lvm", "crypt")]
        disks.append({
            "name": name, "model": model or None, "transport": transport or None,
            "size_bytes": _bytes(entry.get("size")),
            "read_only": entry.get("ro") is True,
            "partitions": partitions,
            "smart": _smart(name, model, transport),
        })
    return {
        "available": True, "reason": None, "disks": disks[:64],
        "shares": {"smb": _smb_shares(), "nfs": _nfs_shares()},
        "scope": "Sistema StorOS local (não é inventário do Unraid hospedeiro)",
        "read_only": True,
    }


def inventory():
    global _cache
    now = time.monotonic()
    if _cache[1] is not None and now - _cache[0] < _CACHE_SECONDS:
        return _cache[1]
    result = _collect()
    _cache = (time.monotonic(), result)
    return result
