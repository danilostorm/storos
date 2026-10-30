"""StorOS app installation control for an isolated VM.

One-click installation is restricted to the built-in reviewed *template shape*,
NOT arbitrary supplied compose text or host paths. This module has no authority
by itself: it needs a dedicated private service, explicit feature enablement
and an authenticated administrator. Never invoke on the Unraid host.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import apps

SLUG = re.compile(r"^[a-z][a-z0-9-]{1,48}$")
LABEL = "storos-managed"
MAX_PROJECTS = 32


class AppActionError(ValueError):
    pass


def _json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _approved_manifest(slug: str):
    if not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug not in apps.CATALOG:
        raise AppActionError("Application is not in the StorOS catalog")
    preview = apps.compose_preview(slug)
    source = json.loads(preview["compose"])
    if source.get("name") != "storos-" + slug:
        raise AppActionError("Invalid catalog project name")
    if not isinstance(source.get("services"), dict) or len(source["services"]) != 1:
        raise AppActionError("Only one-service built-in app templates supported")
    service = next(iter(source["services"].values()))
    if not isinstance(service, dict) or not re.fullmatch(r"[a-zA-Z0-9./:_-]{2,200}", str(service.get("image", ""))):
        raise AppActionError("Untrusted image format")
    if any(x not in ("image", "restart", "ports", "volumes", "environment") for x in service):
        raise AppActionError("Unsupported privileged configuration")
    if service.get("restart") not in (None, "unless-stopped"):
        raise AppActionError("Unsupported restart policy")
    for port in service.get("ports", []):
        if not re.fullmatch(r"[0-9]{1,5}:[0-9]{1,5}", str(port)):
            raise AppActionError("Untrusted port mapping")
        a, b = [int(x) for x in port.split(":")]
        if not (1 <= a <= 65535 and 1 <= b <= 65535):
            raise AppActionError("Port out of range")
    volumes = source.get("volumes", {})
    if not isinstance(volumes, dict):
        raise AppActionError("Invalid volumes")
    for mount in service.get("volumes", []):
        if not isinstance(mount, str) or ":" not in mount:
            raise AppActionError("Invalid storage mapping")
        name, dst, *opts = mount.split(":")
        # Named Docker volumes only. Never auto-mount /etc, /var/run or host paths.
        if name not in volumes or not name.replace("_", "").isalnum():
            raise AppActionError("Host binds and external volumes are forbidden")
        if not dst.startswith("/") or dst == "/" or ".." in dst or "//" in dst:
            raise AppActionError("Invalid container path")
        if opts and opts != ["ro"]:
            raise AppActionError("Unsupported mount options")
    # Fixed Docker project and exact fields: external templates cannot be submitted.
    return source


def plan(slug: str):
    compose = _approved_manifest(slug)
    encoded = (_json(compose) + "\n").encode("utf-8")
    return {
        "slug": slug,
        "project": compose["name"],
        "compose": encoded.decode("utf-8"),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "image": next(iter(compose["services"].values()))["image"],
        "warnings": [
            "The chosen upstream Docker image is third-party software.",
            "Ports, volumes and image tags must be reviewed before installation.",
            "This laboratory action must run only inside an isolated StorOS VM.",
        ],
        "install_supported": True,
    }


class AppManager:
    """Private project files, safe command argv, never executes arbitrary YAML."""

    def __init__(self, root: Path, runner=None):
        self.root = Path(root)
        if not self.root.is_absolute():
            raise AppActionError("Data root must be absolute")
        self.runner = runner or subprocess.run

    def _check_dir(self):
        st = self.root.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_mode & 0o077:
            raise AppActionError("Project state directory must be private (0700)")

    def _run(self, args, timeout=90):
        if not shutil.which("docker"):
            raise AppActionError("Docker is not installed")
        try:
            result = self.runner(
                ["docker", "compose", *args],
                capture_output=True, text=True, timeout=timeout, check=False,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
                     "HOME": str(self.root)},
            )
        except (OSError, subprocess.TimeoutExpired):
            raise AppActionError("Docker Compose did not complete within limits")
        if result.returncode != 0:
            # Never return untrusted Docker stdout/stderr (may contain secrets).
            raise AppActionError("Docker Compose failed; inspect local audit and logs")
        return result

    def _ps_running(self, project: Path, config: Path) -> bool:
        """Verify the actual Compose container, not merely the 'up -d' exit code.

        docker compose ps produces either a JSON array or one JSON object per
        line, depending on the plugin version. Reject unexpected identities
        rather than trusting container output from another project.
        """
        if config.is_symlink() or not config.is_file():
            raise AppActionError("Application configuration is unavailable")
        slug = project.name.removeprefix("storos-")
        if project.name != "storos-" + slug:
            raise AppActionError("Unexpected project name")
        manifest = _approved_manifest(slug)
        # A status query must not parse a tampered Compose file either.
        expected = plan(slug)
        try:
            st = config.stat()
            if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077 or st.st_size > 100000:
                raise AppActionError("Unsafe Compose status source")
            if not hmac.compare_digest(
                    hashlib.sha256(config.read_bytes()).hexdigest(), expected["sha256"]):
                raise AppActionError("Compose status source differs from approved catalog")
        except OSError as exc:
            raise AppActionError("Compose status source cannot be read") from exc
        service = next(iter(manifest["services"]))
        argv = ["--project-directory", str(project), "-f", str(config),
                "ps", "--all", "--format", "json"]
        output = self._run(argv, timeout=15).stdout
        if not isinstance(output, str) or len(output) > 65536:
            raise AppActionError("Unexpected Compose status response")
        if not output.strip():
            return False
        try:
            items = json.loads(output)
        except ValueError:
            try:
                items = [json.loads(line) for line in output.splitlines() if line.strip()]
            except ValueError as exc:
                raise AppActionError("Invalid Compose status response") from exc
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list) or len(items) > 4:
            raise AppActionError("Unexpected Compose status structure")
        if any(not isinstance(item, dict) or
               item.get("Project") != project.name or
               item.get("Service") != service for item in items):
            raise AppActionError("Compose project identity mismatch")
        return bool(items) and all(item.get("State") == "running" for item in items)

    @staticmethod
    def _write_state(project, state):
        if state not in ("prepared", "deploying", "deployed", "stopped", "failed"):
            raise AppActionError("Invalid application state")
        fd, tmp = tempfile.mkstemp(prefix=".app-state-", dir=project)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump({"state": state}, stream)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, project / "state.json")
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def install(self, slug: str, accepted_sha256: str):
        self._check_dir()
        expected = plan(slug)
        if not isinstance(accepted_sha256, str) or accepted_sha256 != expected["sha256"]:
            raise AppActionError("Confirmation does not match approved application")
        project = self.root / ("storos-" + slug)
        if project.exists() or project.is_symlink():
            raise AppActionError("Application already installed or directory exists")
        # Enforced before ANY docker control: this preview is only for an isolated VM.
        try:
            probe = subprocess.run(["systemd-detect-virt", "--vm"],
                                   capture_output=True, timeout=4, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise AppActionError("VM isolation check unavailable")
        if probe.returncode != 0:
            raise AppActionError("Installation is allowed only inside a VM laboratory")
        if len([p for p in self.root.iterdir() if p.is_dir()]) >= MAX_PROJECTS:
            raise AppActionError("Application limit reached")
        project.mkdir(mode=0o700)
        config = project / "compose.json"
        self._write_state(project, "prepared")
        try:
            fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         getattr(os, "O_NOFOLLOW", 0), 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(expected["compose"].encode())
                stream.flush()
                os.fsync(stream.fileno())
            # Parse locally with Compose before contacting registry.
            argv = ["--project-directory", str(project), "-f", str(config)]
            self._run([*argv, "config", "--quiet"], timeout=25)
            self._write_state(project, "deploying")
            self._run([*argv, "up", "-d", "--pull", "always"], timeout=180)
            if not self._ps_running(project, config):
                raise AppActionError("Application did not stay running after Compose deployment")
            self._write_state(project, "deployed")
        except Exception:
            # Keep metadata on failed deployment for post-mortem; never
            # silently delete Docker volumes or any partly-created container.
            self._write_state(project, "failed")
            raise
        return {"name": expected["project"], "slug": slug,
                "state": "deployed", "storage": "named Docker volumes"}

    def control(self, slug: str, action: str, accepted_sha256: str):
        """Control ONLY a previously registered Compose app inside a VM.

        Does not delete or recreate project files, containers or named volumes.
        Every request verifies the original catalog config SHA to prevent a
        modified compose file from becoming an arbitrary privileged command.
        """
        self._check_dir()
        if action not in ("start", "stop", "restart"):
            raise AppActionError("Unsupported lifecycle action")
        expected = plan(slug)
        if (not isinstance(accepted_sha256, str)
                or not hmac.compare_digest(accepted_sha256, expected["sha256"])):
            raise AppActionError("Confirmation does not match approved application")
        project = self.root / ("storos-" + slug)
        if project.is_symlink() or not project.is_dir():
            raise AppActionError("Application has not been installed by StorOS")
        project_stat = project.stat()
        if project_stat.st_mode & 0o077:
            raise AppActionError("Project permissions are unsafe")
        config = project / "compose.json"
        try:
            fd = os.open(config, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                st = os.fstat(fd)
                if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o077 or st.st_size > 100000:
                    raise AppActionError("Unsafe application configuration")
                with os.fdopen(fd, "rb", closefd=False) as stream:
                    content = stream.read(100001)
            finally:
                os.close(fd)
        except OSError as exc:
            raise AppActionError("Cannot read approved application configuration") from exc
        if not hmac.compare_digest(hashlib.sha256(content).hexdigest(), expected["sha256"]):
            raise AppActionError("Application config differs from approved catalog")
        try:
            probe = subprocess.run(["systemd-detect-virt", "--vm"],
                                   capture_output=True, timeout=4, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AppActionError("Cannot verify VM isolation") from exc
        if probe.returncode != 0:
            raise AppActionError("App controls are restricted to a VM laboratory")
        argv = ["--project-directory", str(project), "-f", str(config)]
        try:
            self._run([*argv, action], timeout=60)
            running = self._ps_running(project, config)
            if action in ("start", "restart") and not running:
                raise AppActionError("Application did not reach running state")
            if action == "stop" and running:
                raise AppActionError("Application is still running")
            self._write_state(project, "stopped" if action == "stop" else "deployed")
        except Exception:
            self._write_state(project, "failed")
            raise
        return {"project": expected["project"], "slug": slug,
                "action": action, "state": "stopped" if action == "stop" else "deployed",
                "running": running}

    def list_installed(self):
        self._check_dir()
        rows = []
        for entry in sorted(self.root.iterdir()):
            if not entry.is_dir() or entry.is_symlink() or not entry.name.startswith("storos-"):
                continue
            if not (entry / "compose.json").is_file():
                continue
            state = "unknown"
            try:
                doc = json.loads((entry / "state.json").read_text(encoding="utf-8"))
                state = doc.get("state") if doc.get("state") in (
                    "prepared", "deploying", "deployed", "stopped", "failed") else "unknown"
            except (OSError, ValueError, TypeError):
                pass
            running = None
            if state in ("deployed", "stopped", "failed"):
                try:
                    running = self._ps_running(entry, entry / "compose.json")
                except AppActionError:
                    # The state on disk remains authoritative for deployment
                    # history; daemon outages must not masquerade as stopped.
                    pass
            rows.append({"project": entry.name, "state": state, "running": running})
        return rows[:MAX_PROJECTS]
