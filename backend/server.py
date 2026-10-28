#!/usr/bin/env python3
"""StorOS prototype: read-only observability API. Never writes to host storage."""
import argparse
import json
import os
import shutil
import socket
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import apps
import billing
import observability
import storage
import modules

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"

def run_readonly(argv, timeout=3):
    """Execute only hardcoded observation commands; never accept user-provided args."""
    if not shutil.which(argv[0]):
        return {"available": False, "reason": argv[0] + " not installed", "lines": []}
    try:
        result = subprocess.run(argv, capture_output=True, text=True,
                                timeout=timeout, check=False)
        if result.returncode:
            return {"available": False, "reason": (result.stderr or "command failed")[:250], "lines": []}
        return {"available": True, "lines": result.stdout.splitlines()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "reason": str(exc)[:250], "lines": []}

def parse_meminfo(body):
    info = {}
    for line in body.splitlines():
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        part = value.strip().split()
        if part and part[0].isdigit():
            info[name] = int(part[0]) * (1024 if len(part) > 1 and part[1] == "kB" else 1)
    return info

def read_text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""

def system_status():
    mem = parse_meminfo(read_text("/proc/meminfo"))
    uptime_content = read_text("/proc/uptime").split()
    uptime = int(float(uptime_content[0])) if uptime_content else None
    os_release = {}
    for line in read_text("/etc/os-release").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            os_release[k] = v.strip('"')
    load = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
    return {
        "host": socket.gethostname(),
        "os": os_release.get("PRETTY_NAME", "Linux"),
        "uptime_seconds": uptime,
        "cpu_load": [round(v, 2) for v in load],
        "ram_total_bytes": mem.get("MemTotal", 0),
        "ram_available_bytes": mem.get("MemAvailable", 0),
        "mode": "read-only prototype"
    }

def disk_status():
    out = run_readonly(["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL"])
    if not out["available"]:
        return out
    try:
        obj = json.loads("\n".join(out["lines"]))
        return {"available": True, "devices": obj.get("blockdevices", [])}
    except ValueError:
        return {"available": False, "reason": "Invalid lsblk response", "devices": []}

def container_status():
    # Actual live Docker metadata only. Docker may deny this read-only observation.
    out = run_readonly(["docker", "ps", "--no-trunc", "--format", "{{json .}}"], timeout=5)
    if not out["available"]:
        return out
    items = []
    for line in out["lines"][:100]:
        try:
            meta = json.loads(line)
        except ValueError:
            continue
        items.append({"name": meta.get("Names"), "image": meta.get("Image"),
                      "status": meta.get("Status"), "cpu_percent": None, "memory": None})
    return {"available": True, "items": items}

def vm_status():
    out = run_readonly(["virsh", "-c", "qemu:///system", "list", "--all", "--name"])
    if not out["available"]:
        return out
    return {"available": True, "items": [{"name": line, "status": "listed"} for line in out["lines"] if line.strip()]}

API = {"/api/status": system_status, "/api/disks": disk_status,
       "/api/containers": container_status, "/api/vms": vm_status,
       "/api/apps/catalog": apps.catalog, "/api/apps/engine": apps.engine,
       "/api/billing/model": billing.configured_model,
       "/api/overview": observability.live_overview,
       "/api/storage": storage.inventory,
       "/api/modules": modules.inventory}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in API or path in ("/api/apps/compose", "/api/apps/hub", "/api/billing/estimate"):
            status = 200
            try:
                if path == "/api/apps/compose":
                    args = parse_qs(urlsplit(self.path).query)
                    data = apps.compose_preview(args.get("slug", [""])[0])
                elif path == "/api/billing/estimate":
                    required = ("cpu_watts", "board_watts", "ram_watts", "threads", "host_ram_gib",
                                "vcpus", "ram_gib", "gpu_watts", "hours", "electricity_kwh",
                                "uptime_hour", "plan_price", "total_cycle_gb", "item_cycle_gb")
                    params = parse_qs(urlsplit(self.path).query)
                    if set(params) != set(required) or any(len(v) != 1 for v in params.values()):
                        raise ValueError("Informe os 14 campos de cálculo")
                    data = billing.estimated_item(**{name: params[name][0] for name in required})
                elif path == "/api/apps/hub":
                    args = parse_qs(urlsplit(self.path).query)
                    data = apps.hub_search(args.get("q", [""])[0])
                else:
                    data = API[path]()
            except ValueError as exc:
                status, data = 400, {"error": str(exc)[:120]}
            except Exception:
                status, data = 503, {"error": "Serviço externo ou módulo indisponível"}
            content = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        if path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        self.send_error(405, "StorOS prototype does not accept changes")

def main():
    parser = argparse.ArgumentParser(description="StorOS read-only development dashboard")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    # Deliberately inaccessible from LAN/WAN; use SSH port forwarding.
    bind = "127.0.0.1"
    server = ThreadingHTTPServer((bind, args.port), Handler)
    print(f"StorOS preview: http://{bind}:{args.port} (read only, Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
