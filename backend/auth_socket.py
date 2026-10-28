"""StorOS native-auth lab service, exposed ONLY through a private Unix socket.

No host storage, libvirt, users or systemd operations. An explicitly enabled\nVM-only laboratory mode can control allowlisted Docker Compose applications.
The web panel, LAN gateway and API remain read-only and are NOT connected to
this service. Operators must create the private account state separately.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socketserver
import stat
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

from app_manager import AppManager, AppActionError, plan as app_plan
from security_core import (
    AccountStore, AuditLog, LoginThrottle, SessionRegistry,
    USER_NAME, IdentityError,
)

MAX_BODY = 2048
MAX_AUTH = 192
ALLOWED_PATHS = frozenset(("/v1/health", "/v1/login", "/v1/me", "/v1/logout",
                             "/v1/apps/plan", "/v1/apps/install", "/v1/apps/installed"))
BEARER = re.compile(r"^Bearer ([A-Za-z0-9_-]{40,128})$")


class PrivateAuthServer(socketserver.UnixStreamServer):
    """Single-process and single-threaded to avoid cross-worker session races."""
    allow_reuse_address = False

    def __init__(self, socket_path: Path, account_file: Path, audit_file: Path, app_manager=None):
        self.accounts = AccountStore(account_file)
        # Reject unsecured account state before binding any socket.
        self.accounts.read()
        self.sessions = SessionRegistry()
        self.throttle = LoginThrottle()
        self.audit = AuditLog(audit_file)
        self.app_manager = app_manager
        self.socket_path = Path(socket_path)
        super().__init__(str(socket_path), AuthHandler, bind_and_activate=False)
        try:
            self.server_bind()
            os.chmod(socket_path, 0o600)
            self.server_activate()
        except Exception:
            self.server_close()
            raise


class AuthHandler(BaseHTTPRequestHandler):
    server_version = "StorOS-PrivateAuth/0.1"
    sys_version = ""
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # Do not write credentials, request body, session tokens or headers.
        return

    def _reply(self, status: int, value: dict):
        # Single response per connection avoids unread request-body pipelining.
        self.close_connection = True
        body = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _path(self):
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment or parsed.path not in ALLOWED_PATHS:
            return None
        return parsed.path

    def _token(self):
        header = self.headers.get("Authorization", "")
        if not isinstance(header, str) or len(header) > MAX_AUTH:
            return None
        match = BEARER.fullmatch(header)
        return match.group(1) if match else None

    def _json(self):
        # Require finite, bounded body size; never read an unbounded stream.
        length = self.headers.get("Content-Length", "")
        if not length.isdigit() or int(length) > MAX_BODY:
            raise ValueError("Invalid request size")
        if self.headers.get("Content-Type", "").lower().strip() != "application/json":
            raise ValueError("Only JSON requests accepted")
        raw = self.rfile.read(int(length))
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON object")
        return data

    def _audit(self, actor, action, outcome):
        actor = actor if isinstance(actor, str) and USER_NAME.fullmatch(actor) else "unknown"
        self.server.audit.record(actor, action, outcome)

    def do_GET(self):
        path = self._path()
        if path == "/v1/health":
            return self._reply(200, {
                "ready": True, "transport": "unix-socket",
                "host_mutations": False, "web_login_exposed": False,
            })
        if path == "/v1/me":
            token = self._token()
            name = self.server.sessions.validate(token) if token else None
            if not name:
                return self._reply(401, {"error": "Unauthorized"})
            try:
                accounts = self.server.accounts.read()["accounts"]
                profile = next((a for a in accounts if a.get("name") == name), None)
            except (OSError, ValueError, AttributeError):
                return self._reply(503, {"error": "Account store unavailable"})
            if not profile:
                return self._reply(401, {"error": "Unauthorized"})
            return self._reply(200, {
                "name": name, "role": profile["role"],
                "host_mutations": False, "allowed": ["read-only"],
            })
        if path == "/v1/apps/installed":
            token = self._token()
            principal = self.server.sessions.validate(token, role="admin") if token else None
            if not principal:
                return self._reply(401, {"error": "Admin login required"})
            if self.server.app_manager is None:
                return self._reply(403, {"error": "App management disabled"})
            try:
                rows = self.server.app_manager.list_installed()
            except (OSError, AppActionError):
                return self._reply(503, {"error": "App inventory unavailable"})
            return self._reply(200, {"items": rows, "scope": "isolated VM lab"})
        if path is None:
            return self._reply(404, {"error": "No such resource"})
        return self._reply(405, {"error": "Method not allowed"})

    def do_POST(self):
        path = self._path()
        if path == "/v1/login":
            try:
                data = self._json()
                if set(data) != {"username", "password"}:
                    raise ValueError("Unexpected fields")
                name = data["username"]
                password = data["password"]
                if not isinstance(name, str) or len(name) > 32 or not isinstance(password, str):
                    raise ValueError("Invalid credentials")
            except (ValueError, TypeError, UnicodeError):
                return self._reply(400, {"error": "Invalid request"})
            # Unknown users still accrue failures, without username disclosure.
            if not self.server.throttle.allowed(name):
                return self._reply(429, {"error": "Try again later"})
            try:
                role = self.server.accounts.check_login(name, password)
            except (OSError, ValueError, AttributeError):
                return self._reply(503, {"error": "Identity store unavailable"})
            if not role:
                self.server.throttle.fail(name)
                try:
                    self._audit(name, "auth.login", "denied")
                except (OSError, IdentityError):
                    return self._reply(503, {"error": "Audit unavailable"})
                return self._reply(401, {"error": "Invalid credentials"})
            # Fail closed when the audit sink cannot record the session creation.
            try:
                self._audit(name, "auth.login", "allowed")
            except (OSError, IdentityError):
                return self._reply(503, {"error": "Audit unavailable"})
            self.server.throttle.succeed(name)
            token, csrf = self.server.sessions.issue(name, role)
            return self._reply(200, {
                "session_token": token, "csrf_token": csrf,
                "role": role, "host_mutations": False,
            })
        if path in ("/v1/apps/plan", "/v1/apps/install"):
            # Bounded body read before authorization avoids terminating the
            # connection while an authorized/unauthorized client is uploading.
            try:
                data = self._json()
            except (ValueError, TypeError, UnicodeError):
                return self._reply(400, {"error": "Invalid request"})
            token = self._token()
            csrf = self.headers.get("X-StorOS-CSRF", "")
            principal = self.server.sessions.validate(
                token, role="admin", csrf=csrf, mutate=True) if token else None
            if not principal:
                return self._reply(403, {"error": "Administrator and CSRF required"})
            if self.server.app_manager is None:
                return self._reply(403, {"error": "App management disabled"})
            try:
                required = {"slug"} if path.endswith("/plan") else {"slug", "accepted_sha256"}
                if set(data) != required:
                    raise AppActionError("Invalid application request")
                slug = data["slug"]
                if path.endswith("/plan"):
                    result = app_plan(slug)
                    self._audit(principal, "apps.plan", "allowed")
                    return self._reply(200, result)
                if not isinstance(data["accepted_sha256"], str):
                    raise AppActionError("Invalid confirmation")
                # This action must not run without a successful durable audit entry.
                self._audit(principal, "apps.install", "allowed")
                result = self.server.app_manager.install(slug, data["accepted_sha256"])
                return self._reply(200, result)
            except (ValueError, TypeError):
                try:
                    self._audit(principal, "apps.install" if path.endswith("/install")
                                else "apps.plan", "denied")
                except (OSError, IdentityError):
                    return self._reply(503, {"error": "Audit unavailable"})
                return self._reply(400, {"error": "Invalid or unsupported application configuration"})
            except (OSError, IdentityError):
                return self._reply(503, {"error": "Private app management unavailable"})
            except Exception:
                # Do not expose errors from Docker or filesystems.
                return self._reply(503, {"error": "Application operation failed"})
        if path == "/v1/logout":
            token = self._token()
            csrf = self.headers.get("X-StorOS-CSRF", "")
            name = self.server.sessions.validate(token, csrf=csrf, mutate=True) if token else None
            if not name:
                return self._reply(403, {"error": "Authentication and CSRF required"})
            try:
                self._audit(name, "auth.logout", "allowed")
            except (OSError, IdentityError):
                return self._reply(503, {"error": "Audit unavailable"})
            self.server.sessions.revoke(token)
            return self._reply(200, {"signed_out": True})
        if path is None:
            return self._reply(404, {"error": "No such resource"})
        return self._reply(405, {"error": "Method not allowed"})

    def do_PUT(self):
        return self._reply(405, {"error": "Method not allowed"})

    def do_DELETE(self):
        return self._reply(405, {"error": "Method not allowed"})

    def do_PATCH(self):
        return self._reply(405, {"error": "Method not allowed"})


def create_server(private_dir: Path, *, enable_apps=False):
    """Refuse a non-private or symlinked directory, accounts or socket."""
    path = Path(private_dir)
    if not path.is_absolute():
        raise IdentityError("Require an absolute private directory")
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or (info.st_mode & 0o077):
        raise IdentityError("Private directory must be 0700")
    socket_path = path / "auth.sock"
    if os.path.lexists(socket_path):
        raise IdentityError("Socket path exists: do not overwrite")
    manager = None
    if enable_apps:
        # Only intended in VM laboratory; production/Unraid host refused.
        import subprocess
        try:
            result = subprocess.run(["systemd-detect-virt", "--vm"], capture_output=True,
                                    timeout=4, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise IdentityError("Cannot verify VM isolation")
        if result.returncode != 0:
            raise IdentityError("Native app control is restricted to VM laboratory")
        app_dir = path / "apps"
        app_dir.mkdir(mode=0o700, exist_ok=True)
        manager = AppManager(app_dir)
        manager._check_dir()
    return PrivateAuthServer(socket_path, path / "accounts.json",
                             path / "audit.jsonl", app_manager=manager)


def main():
    parser = argparse.ArgumentParser(description="StorOS private auth lab daemon (Unix socket only)")
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--enable-lab-apps", action="store_true",
                        help="VM lab only; disabled by default; requires separate private account")
    args = parser.parse_args()
    server = create_server(args.private_dir, enable_apps=args.enable_lab_apps)
    try:
        with server:
            server.serve_forever(poll_interval=0.25)
    finally:
        try:
            info = os.lstat(server.socket_path)
            if stat.S_ISSOCK(info.st_mode):
                os.unlink(server.socket_path)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
