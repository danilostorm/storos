"""Read-only, real observations for StorOS's mockup-faithful UI.

Missing sensors are returned as null. No privileged actions and no synthetic values.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return ""


def _command(parts, timeout=4):
    if not shutil.which(parts[0]):
        return None
    try:
        result = subprocess.run(parts, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, timeout=timeout, check=False)
        return result.stdout if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _cpu_totals():
    try:
        parts = _read("/proc/stat").splitlines()[0].split()
        if parts[0] != "cpu":
            return None
        values = [int(i) for i in parts[1:]]
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        return sum(values), idle
    except (ValueError, IndexError):
        return None


def cpu_percent():
    first = _cpu_totals()
    if first is None:
        return None
    time.sleep(0.12)
    second = _cpu_totals()
    if second is None:
        return None
    total_delta = second[0] - first[0]
    idle_delta = second[1] - first[1]
    if total_delta <= 0 or idle_delta < 0:
        return None
    return round(100 * (1 - idle_delta / total_delta), 1)


def cpu_details():
    cpu = _read("/proc/cpuinfo")
    name = None
    for line in cpu.splitlines():
        if line.startswith("model name") or line.startswith("Hardware"):
            name = line.split(":", 1)[-1].strip()
            break
    return {"percent": cpu_percent(), "model": name, "logical_cores": os.cpu_count()}


def mount_usage(mountpoint):
    if not mountpoint or not mountpoint.startswith("/") or not os.path.isdir(mountpoint):
        return None
    try:
        data = os.statvfs(mountpoint)
        total = data.f_blocks * data.f_frsize
        available = data.f_bavail * data.f_frsize
        if total <= 0:
            return None
        return {"total_bytes": total, "used_bytes": total - available,
                "percent": round((total - available) / total * 100, 1)}
    except (OSError, ValueError):
        return None


def _flatten(devices):
    for item in devices:
        yield item
        yield from _flatten(item.get("children") or [])


def storage_overview():
    root = mount_usage("/")
    root_mount = "/"
    # On ostree/bootc, / may be a tiny immutable overlay unrelated to data capacity.
    # Prefer the writable /var mount instead of reporting a fictitious 100%-full root.
    if root is not None and root["total_bytes"] < 1024**3:
        persistent = mount_usage("/var")
        if persistent is not None and persistent["total_bytes"] > root["total_bytes"]:
            root = persistent
            root_mount = "/var"
    raw = _command(["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL"])
    if raw is None:
        return {"available": False, "root": root, "root_mount": root_mount, "items": []}
    try:
        blocks = json.loads(raw).get("blockdevices", [])
    except (ValueError, TypeError):
        return {"available": False, "root": root, "root_mount": root_mount, "items": []}
    result = []
    for block in blocks:
        if block.get("type") != "disk" or str(block.get("name", "")).startswith("zram"):
            continue
        fs_types = list(dict.fromkeys(
            d.get("fstype") for d in _flatten([block]) if d.get("fstype")))
        mountpoints = [d.get("mountpoint") for d in _flatten([block])
                       if d.get("mountpoint")]
        size = block.get("size")
        try:
            size = int(size) if size is not None else None
        except (TypeError, ValueError):
            size = None
        # Do not invent disk-use percentage from partition lengths; they are not used space.
        result.append({"name": block.get("name"), "size_bytes": size,
                       "filesystem": ", ".join(fs_types) or None,
                       "usage": mount_usage(mountpoints[0]) if len(mountpoints) == 1 else None,
                       "model": block.get("model") or None})
    return {"available": True, "root": root, "root_mount": root_mount, "items": result}


def network_overview():
    addresses = _command(["ip", "-j", "addr", "show"])
    if addresses is None:
        return {"available": False, "interfaces": []}
    try:
        records = json.loads(addresses)
    except (TypeError, ValueError):
        return {"available": False, "interfaces": []}
    routes = _read("/proc/net/route")
    main_iface = None
    for row in routes.splitlines()[1:]:
        cols = row.split()
        if len(cols) > 2 and cols[1] == "00000000":
            main_iface = cols[0]
            break
    items = []
    for iface in records:
        name = iface.get("ifname")
        if not name or name == "lo":
            continue
        ip4 = next((x.get("local") for x in iface.get("addr_info", [])
                    if x.get("family") == "inet"), None)
        speed_str = _read("/sys/class/net/" + name + "/speed")
        try:
            speed = int(speed_str)
            if speed <= 0 or speed > 1000000:
                speed = None
        except ValueError:
            speed = None
        items.append({"name": name, "ip": ip4, "speed_mbps": speed,
                      "state": iface.get("operstate") or None,
                      "primary": name == main_iface})
    return {"available": True, "interfaces": items}


def compose_overview():
    raw = _command(["docker", "compose", "ls", "--format", "json"], timeout=5)
    if raw is None:
        return {"available": False, "items": [], "reason": "Acesso ao Docker Compose indisponível"}
    try:
        stacks = json.loads(raw)
        return {"available": True, "items": [
            {"name": s.get("Name"), "status": s.get("Status"),
             "config_files": None} for s in stacks[:60]]}
    except (TypeError, ValueError):
        return {"available": False, "items": []}


def live_overview():
    # Never claim user login, array parity, energy bills, installed apps or alert history.
    return {"cpu": cpu_details(), "storage": storage_overview(),
            "network": network_overview(), "compose": compose_overview(),
            "privileged_controls_enabled": False,
            "measurement_scope": "local Linux instance",
            "history_available": False}
