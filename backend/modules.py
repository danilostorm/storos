"""Local StorOS capability inventory. Observation-only, no privileged operations."""
from __future__ import annotations
import json
import os
import pwd
import shutil
import subprocess
import time
from pathlib import Path

_CACHE = (0.0, None)
_TTL = 30


def _run(argv, timeout=4):
    if not shutil.which(argv[0]):
        return {"available": False, "reason": argv[0] + " não instalado", "items": []}
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        if result.returncode:
            return {"available": False, "reason": "Sem permissão ou serviço indisponível", "items": []}
        return {"available": True, "reason": None, "lines": result.stdout.splitlines()}
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "reason": "Serviço indisponível", "items": []}


def _json_lines(argv, fields, limit=80):
    result = _run(argv)
    if not result["available"]:
        return result
    items = []
    for line in result["lines"][:limit]:
        try:
            src = json.loads(line)
            if not isinstance(src, dict):
                continue
            items.append({k: src.get(k) for k in fields})
        except (ValueError, TypeError):
            continue
    return {"available": True, "reason": None, "items": items}


def _docker():
    return {
        "images": _json_lines(["docker", "image", "ls", "--format", "{{json .}}"],
                              ("Repository", "Tag", "Size", "ID")),
        "networks": _json_lines(["docker", "network", "ls", "--format", "{{json .}}"],
                                ("Name", "Driver", "Scope")),
        "volumes": _json_lines(["docker", "volume", "ls", "--format", "{{json .}}"],
                               ("Name", "Driver")),
    }


def _users():
    try:
        accounts = []
        for p in pwd.getpwall():
            if p.pw_uid == 0 or p.pw_uid >= 1000:
                if len(accounts) >= 50:
                    break
                accounts.append({
                    "name": p.pw_name,
                    "uid": p.pw_uid,
                    "home": p.pw_dir,
                    "login_enabled": p.pw_shell not in ("/sbin/nologin", "/usr/sbin/nologin", "/bin/false"),
                })
        return {"available": True, "items": accounts,
                "reason": "Somente contas locais visíveis; senhas e credenciais nunca são consultadas"}
    except (OSError, KeyError):
        return {"available": False, "items": [], "reason": "Leitura das contas indisponível"}


def _vm_networks():
    out = _run(["virsh", "-c", "qemu:///system", "net-list", "--all", "--name"])
    if not out["available"]:
        return out
    return {"available": True, "items": [{"name": n} for n in out["lines"] if n.strip()],
            "reason": None}


def _service(name):
    if not shutil.which("systemctl"):
        return "indisponível"
    try:
        out = subprocess.run(["systemctl", "is-active", name],
                             capture_output=True, text=True, timeout=1.5, check=False)
        status = out.stdout.strip()
        return status if status in ("active", "inactive", "failed", "activating",
                                    "deactivating", "unknown") else "indisponível"
    except (OSError, subprocess.TimeoutExpired):
        return "indisponível"


def _system():
    try:
        data = Path("/etc/os-release").read_text(encoding="utf-8")
        pretty = next((s.split("=", 1)[1].strip().strip('"')
                       for s in data.splitlines() if s.startswith("PRETTY_NAME=")), None)
    except OSError:
        pretty = None
    return {"os": pretty, "kernel": os.uname().release, "architecture": os.uname().machine,
            "services": {k: _service(k) for k in ("docker.service", "containerd.service",
                                                  "libvirtd.service", "smb.service",
                                                  "nfs-server.service", "storos-dashboard.service")}}


def collect():
    return {
        "scope": "Instância StorOS local",
        "read_only": True,
        "users": _users(),
        "docker": _docker(),
        "vm_networks": _vm_networks(),
        "system": _system(),
        "capabilities": {
            "disks": "inventário de leitura",
            "array": "não implementado",
            "pools": "não implementado",
            "shares": "configuração de leitura",
            "users": "contas de leitura",
            "docker_images": "inventário de leitura",
            "docker_compose": "consulta; implantação não implementada",
            "vms": "inventário de leitura",
            "network": "inventário de leitura",
            "updates": "não implementado",
            "backup": "não implementado",
            "notifications": "não implementado",
            "tasks": "não implementado",
            "authentication": "gateway de laboratório; RBAC nativo não implementado",
            "admin_writes": "desativadas",
        },
    }


def inventory():
    global _CACHE
    now = time.monotonic()
    if _CACHE[1] is not None and now - _CACHE[0] < _TTL:
        return _CACHE[1]
    value = collect()
    _CACHE = (time.monotonic(), value)
    return value
