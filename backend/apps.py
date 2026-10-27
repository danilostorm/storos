"""StorOS Apps MVP: read-only Docker Hub discovery, curated catalog and Compose previews.

No Docker socket, sudo, shell execution with user input, downloads or installs.
Actual deployment requires a separately authenticated privileged management service
that is NOT provided by this prototype.
"""
import json
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

# Official/community images shown as examples, not security-reviewed installations.
# These Compose examples are not guaranteed compatible with every host or version.
_CATALOG = [
    {"slug": "uptime-kuma", "name": "Uptime Kuma", "category": "Monitoramento",
     "image": "louislam/uptime-kuma:1", "port": "3001",
     "description": "Monitora sites e serviços e avisa sobre interrupções.",
     "services": {"uptime-kuma": {"image": "louislam/uptime-kuma:1", "restart": "unless-stopped",
                                "ports": ["3001:3001"], "volumes": ["uptime_kuma_data:/app/data"]}},
     "volumes": {"uptime_kuma_data": {}}},
    {"slug": "jellyfin", "name": "Jellyfin", "category": "Mídia",
     "image": "jellyfin/jellyfin:latest", "port": "8096",
     "description": "Servidor multimídia para filmes, séries e músicas.",
     "services": {"jellyfin": {"image": "jellyfin/jellyfin:latest", "restart": "unless-stopped",
                              "ports": ["8096:8096"], "volumes": ["jellyfin_config:/config", "jellyfin_cache:/cache"]}},
     "volumes": {"jellyfin_config": {}, "jellyfin_cache": {}}},
    {"slug": "grafana", "name": "Grafana", "category": "Monitoramento",
     "image": "grafana/grafana-oss:latest", "port": "3300",
     "description": "Dashboards e visualizações de métricas.",
     "services": {"grafana": {"image": "grafana/grafana-oss:latest", "restart": "unless-stopped",
                             "ports": ["3300:3000"], "volumes": ["grafana_data:/var/lib/grafana"]}},
     "volumes": {"grafana_data": {}}},
    {"slug": "navidrome", "name": "Navidrome", "category": "Mídia",
     "image": "deluan/navidrome:latest", "port": "4533",
     "description": "Biblioteca musical com streaming pela rede.",
     "services": {"navidrome": {"image": "deluan/navidrome:latest", "restart": "unless-stopped",
                               "ports": ["4533:4533"], "volumes": ["navidrome_data:/data", "navidrome_music:/music:ro"]}},
     "volumes": {"navidrome_data": {}, "navidrome_music": {}}},
    {"slug": "gitea", "name": "Gitea", "category": "Desenvolvimento",
     "image": "gitea/gitea:latest", "port": "3301",
     "description": "Repositórios Git no seu servidor.",
     "services": {"gitea": {"image": "gitea/gitea:latest", "restart": "unless-stopped",
                            "ports": ["3301:3000"], "volumes": ["gitea_data:/data"]}},
     "volumes": {"gitea_data": {}}},
    {"slug": "nginx", "name": "Nginx", "category": "Web",
     "image": "nginx:stable-alpine", "port": "8088",
     "description": "Servidor web e proxy reverso de alto desempenho.",
     "services": {"nginx": {"image": "nginx:stable-alpine", "restart": "unless-stopped",
                            "ports": ["8088:80"]}}, "volumes": {}},
]
CATALOG = {p["slug"]: p for p in _CATALOG}
_HUB_CACHE = {}
_HUB_LOCK = threading.Lock()

def _run(cmd, timeout=3):
    if not shutil.which(cmd[0]):
        return {"ok": False, "message": "Comando não instalado"}
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           check=False, env={"PATH": "/usr/local/bin:/usr/bin:/bin",
                                             "LANG": "C.UTF-8", "HOME": "/tmp"})
        return {"ok": p.returncode == 0, "message": (p.stdout if p.returncode == 0 else p.stderr).strip()[:230]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": str(exc)[:230]}

def engine():
    docker = _run(["docker", "--version"])
    compose = _run(["docker", "compose", "version"])
    if not compose["ok"]:
        compose = _run(["docker-compose", "version"])
    status = _run(["systemctl", "is-active", "docker.service"])
    return {
        "docker_installed": docker["ok"], "docker_version": docker["message"] if docker["ok"] else "",
        "compose_installed": compose["ok"], "compose_version": compose["message"] if compose["ok"] else "",
        "daemon_active": status["ok"] and status["message"] == "active",
        "control_enabled": False,
        "notice": "Motor Docker/Compose nativo. Instalações pelo painel exigirão autorização administrativa; esta versão é leitura e prévia."
    }

def catalog():
    return {"items": [{key: app[key] for key in ("slug", "name", "category", "image", "port", "description")}
                      for app in _CATALOG],
            "installation_enabled": False,
            "notice": "Catálogo de exemplos; revisar imagens, portas e volumes antes de executar."}

def compose_preview(slug):
    if slug not in CATALOG:
        raise ValueError("Aplicativo não encontrado no catálogo")
    item = CATALOG[slug]
    # YAML is static, allowlisted and generated from our own entries, not user input.
    # JSON is valid YAML 1.2 and accepted by Docker Compose, avoiding an untrusted YAML parser.
    template = {"name": "storos-" + slug, "services": item["services"]}
    if item["volumes"]:
        template["volumes"] = item["volumes"]
    return {
        "slug": slug, "image": item["image"],
        "compose": json.dumps(template, ensure_ascii=False, indent=2) + "\n",
        "format": "compose.yaml (JSON válido como YAML 1.2)",
        "launch_command": "docker compose -f compose.yaml up -d",
        "warning": "Revise volumes, portas, tags e backups. Conteúdo de terceiros não auditado. Salve em disco de dados antes de usar permanentemente."
    }

def hub_search(query):
    query = query.strip()
    if not re.fullmatch(r"[a-zA-Z0-9._/ -]{2,45}", query):
        raise ValueError("Digite de 2 a 45 caracteres (letras, números, espaço, . _ / -)")
    key = query.lower()
    now = time.monotonic()
    with _HUB_LOCK:
        cached = _HUB_CACHE.get(key)
        if cached and now - cached[0] < 90:
            return cached[1]
    url = "https://hub.docker.com/v2/search/repositories/?" + urllib.parse.urlencode(
        {"query": query, "page_size": 12})
    req = urllib.request.Request(url, headers={"User-Agent": "StorOS-Preview/0.3", "Accept": "application/json"})
    try:
        # Hardcoded HTTPS domain and bounded response; no user-selected URL.
        with urllib.request.urlopen(req, timeout=7) as response:
            payload = response.read(200_001)
            if len(payload) > 200_000:
                raise ValueError("Resposta Docker Hub muito grande")
        result = json.loads(payload)
        items = []
        for r in result.get("results", [])[:12]:
            name = str(r.get("repo_name") or "")[:125]
            if not re.fullmatch(r"[\w./:-]{1,125}", name):
                continue
            items.append({"name": name,
                          "description": str(r.get("short_description") or "")[:200],
                          "official": bool(r.get("is_official", False)),
                          "star_count": int(r.get("star_count") or 0),
                          "url": "https://hub.docker.com/r/" + name if "/" in name else "https://hub.docker.com/_/" + name})
        out = {"query": query, "items": items, "source": "Docker Hub público", "count": len(items)}
        with _HUB_LOCK:
            if len(_HUB_CACHE) >= 32:
                _HUB_CACHE.clear()
            _HUB_CACHE[key] = (now, out)
        return out
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise RuntimeError("Docker Hub indisponível: " + str(exc)[:100]) from exc
