"""StorOS security primitives for a *future* isolated administrator service.

This is NOT a network login endpoint, does not grant sudo and never executes
Docker, libvirt, mount, pool, filesystem or host commands. The public preview
continues read-only; do not enable mutating routes by importing this module.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

USER_NAME = re.compile(r"^[a-z][a-z0-9_.-]{2,31}$")
ROLES = frozenset(("viewer", "admin"))
READ_PERMISSIONS = frozenset((
    "system.status.read", "storage.inventory.read", "shares.inventory.read",
    "docker.inventory.read", "vm.inventory.read", "audit.own.read",
))
AUTH_AUDIT_EVENTS = frozenset(("auth.login", "auth.logout"))
MUTATING_ACTIONS = frozenset((
    "docker.compose.deploy", "docker.container.remove", "vm.create",
    "vm.destroy", "storage.format", "storage.pool.create",
    "shares.create", "user.create", "system.shutdown",
))
HASH_PARAMS = (2**14, 8, 1)
MAX_PASSWORD_BYTES = 256


class IdentityError(ValueError):
    """Generic identity error; callers must not expose account existence."""


def _password_bytes(password: str) -> bytes:
    if not isinstance(password, str):
        raise IdentityError("Invalid credential")
    encoded = password.encode("utf-8")
    if not 12 <= len(encoded) <= MAX_PASSWORD_BYTES or b"\x00" in encoded:
        raise IdentityError("Password length or content invalid")
    return encoded


def password_hash(password: str) -> str:
    secret = _password_bytes(password)
    salt = secrets.token_bytes(16)
    n, r, p = HASH_PARAMS
    digest = hashlib.scrypt(secret, salt=salt, n=n, r=r, p=p, dklen=32)
    return "$".join((
        "scrypt-v1", str(n), str(r), str(p),
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    ))


def verify_password(password: str, stored: str) -> bool:
    try:
        secret = _password_bytes(password)
        kind, n, r, p, salt, known = stored.split("$")
        # Strictly reject attacker-controlled expensive/malformed KDF metadata.
        if kind != "scrypt-v1" or (int(n), int(r), int(p)) != HASH_PARAMS:
            return False
        salt = base64.urlsafe_b64decode(salt.encode("ascii"))
        known = base64.urlsafe_b64decode(known.encode("ascii"))
        if len(salt) != 16 or len(known) != 32:
            return False
        candidate = hashlib.scrypt(
            secret, salt=salt, n=HASH_PARAMS[0], r=HASH_PARAMS[1],
            p=HASH_PARAMS[2], dklen=32,
        )
        return hmac.compare_digest(candidate, known)
    except (ValueError, TypeError, AttributeError, UnicodeError):
        return False


class AccountStore:
    """Bootstrap-only account file; caller must provision a private directory.

    Refuses symlinks, insecure modes and replacing an existing account file.
    No methods to delete/modify admins or change system users are exposed.
    """

    def __init__(self, destination: Path):
        self.path = Path(destination)
        if not self.path.is_absolute():
            raise IdentityError("Account path must be absolute")

    def _check_parent(self):
        parent = self.path.parent
        info = parent.stat()
        if not stat.S_ISDIR(info.st_mode) or (info.st_mode & 0o077):
            raise IdentityError("Account directory must be private (0700)")

    def bootstrap_admin(self, username: str, password: str) -> None:
        if not isinstance(username, str) or not USER_NAME.fullmatch(username):
            raise IdentityError("Invalid username")
        self._check_parent()
        record = {"version": 1, "accounts": [{
            "name": username, "role": "admin", "password_hash": password_hash(password),
        }]}
        blob = json.dumps(record, separators=(",", ":")).encode("utf-8") + b"\n"
        fd, temporary = tempfile.mkstemp(prefix=".storos-account-", dir=self.path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb", closefd=True) as handle:
                handle.write(blob)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, self.path, follow_symlinks=False)
            except FileExistsError as exc:
                raise IdentityError("Administrator already provisioned") from exc
            dirfd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(dirfd)
            finally:
                os.close(dirfd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def read(self) -> dict:
        self._check_parent()
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(self.path, flags)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or (info.st_mode & 0o077):
                raise IdentityError("Account file permissions are unsafe")
            if info.st_size > 65536:
                raise IdentityError("Account file unexpectedly large")
            with os.fdopen(fd, "rb", closefd=False) as handle:
                data = json.load(handle)
        finally:
            os.close(fd)
        if data.get("version") != 1 or not isinstance(data.get("accounts"), list):
            raise IdentityError("Invalid account database")
        return data

    def check_login(self, username: str, password: str) -> str | None:
        if not isinstance(username, str) or not USER_NAME.fullmatch(username):
            return None
        for account in self.read()["accounts"]:
            if account.get("name") == username and account.get("role") in ROLES:
                if verify_password(password, account.get("password_hash", "")):
                    return account["role"]
                break
        return None


class LoginThrottle:
    """Limited, in-process failed-login counter; storage for one daemon only."""

    def __init__(self, max_failures=5, window_seconds=300):
        self.max_failures = max_failures
        self.window = window_seconds
        self._lock = threading.Lock()
        self._failures: dict[str, list[float]] = {}

    def allowed(self, username: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            remaining = [x for x in self._failures.get(username, []) if now - x < self.window]
            self._failures[username] = remaining
            return len(remaining) < self.max_failures

    def fail(self, username: str, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        with self._lock:
            records = [x for x in self._failures.get(username, []) if now - x < self.window]
            self._failures[username] = (records + [now])[-self.max_failures:]

    def succeed(self, username: str) -> None:
        with self._lock:
            self._failures.pop(username, None)


class SessionRegistry:
    """In-memory opaque tokens, SHA-256 stored; sessions die on service restart."""

    def __init__(self, idle_seconds=1800, lifetime_seconds=28800):
        self.idle = idle_seconds
        self.life = lifetime_seconds
        self._lock = threading.Lock()
        self._sessions: dict[str, dict] = {}

    def issue(self, name: str, role: str, now: float | None = None) -> tuple[str, str]:
        if role not in ROLES or not USER_NAME.fullmatch(name):
            raise IdentityError("Invalid principal")
        now = time.monotonic() if now is None else now
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        key = hashlib.sha256(token.encode()).hexdigest()
        with self._lock:
            self._sessions[key] = {
                "name": name, "role": role, "csrf_hash": hashlib.sha256(csrf.encode()).digest(),
                "created": now, "last_seen": now,
            }
        return token, csrf

    def validate(self, token: str, role: str = "viewer",
                 csrf: str | None = None, mutate=False,
                 now: float | None = None) -> str | None:
        if role not in ROLES or not isinstance(token, str) or len(token) > 128:
            return None
        now = time.monotonic() if now is None else now
        key = hashlib.sha256(token.encode()).hexdigest()
        with self._lock:
            session = self._sessions.get(key)
            if not session:
                return None
            if now - session["last_seen"] >= self.idle or now - session["created"] >= self.life:
                self._sessions.pop(key, None)
                return None
            if role == "admin" and session["role"] != "admin":
                return None
            if mutate:
                if not isinstance(csrf, str) or len(csrf) > 128:
                    return None
                if not hmac.compare_digest(session["csrf_hash"], hashlib.sha256(csrf.encode()).digest()):
                    return None
            session["last_seen"] = now
            return session["name"]

    def revoke(self, token: str) -> None:
        if not isinstance(token, str):
            return
        with self._lock:
            self._sessions.pop(hashlib.sha256(token.encode()).hexdigest(), None)

    @staticmethod
    def secure_cookie(token: str) -> str:
        if not isinstance(token, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{40,128}", token):
            raise IdentityError("Invalid session token")
        return "__Host-storos_session=" + token + "; Path=/; Secure; HttpOnly; SameSite=Strict"


def policy_allows(role: str, action: str) -> bool:
    """Explicit read-only authorization, *all* mutating actions fail closed."""
    if role not in ROLES or not isinstance(action, str):
        return False
    if action == "audit.own.read":
        return role in ROLES
    return action in READ_PERMISSIONS and role in ROLES


class AuditLog:
    """Append sanitized decision metadata only; NEVER passwords/session tokens."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def record(self, actor: str, action: str, outcome: str) -> None:
        if (not isinstance(actor, str) or not USER_NAME.fullmatch(actor)
                or action not in READ_PERMISSIONS | MUTATING_ACTIONS | AUTH_AUDIT_EVENTS
                or outcome not in ("allowed", "denied", "failed")):
            raise IdentityError("Invalid audit event")
        event = {
            "utc": datetime.now(timezone.utc).isoformat(),
            "actor": actor, "action": action, "result": outcome,
        }
        data = (json.dumps(event, separators=(",", ":")) + "\n").encode()
        fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT |
                     getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or (info.st_mode & 0o077):
                raise IdentityError("Unsafe audit log")
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)


def security_status() -> dict:
    """Truthful read-only status for preview. Does not inspect credentials."""
    return {
        "available": True,
        "scope": "Instância StorOS local",
        "mode": "foundation-only",
        "login_enabled": False,
        "native_sessions_enabled": False,
        "privileged_service_enabled": False,
        "mutations_enabled": False,
        "foundations": {
            "password_hash": "scrypt + random salt",
            "bootstrap": "one-time private account file (not provisioned)",
            "sessions": "temporary in-memory and CSRF checks (not connected)",
            "policy": "default deny for all mutating actions",
            "audit": "append-only event metadata (not connected)",
        },
        "warnings": [
            "O login do laboratório é do gateway HTTPS; não é login nativo do StorOS.",
            "Os controles administrativos continuam desligados.",
            "Nenhuma conta nativa foi criada automaticamente.",
        ],
    }
