"""Restricted HTTPS-to-Unix-socket auth bridge for StorOS laboratory gateway.

This file does not listen on TCP. Only the three allowlisted auth operations
are forwarded; app installation, arbitrary paths and host operations never are.
"""
from __future__ import annotations

import http.client
import json
import os
import re
import socket
import stat
from pathlib import Path

AUTH_TOKEN = re.compile(r"^[A-Za-z0-9_-]{40,128}$")
CSRF_TOKEN = re.compile(r"^[A-Za-z0-9_-]{40,128}$")
MAX_RESPONSE = 4096
ROUTES = frozenset({
    ("POST", "/v1/login"),
    ("GET", "/v1/me"),
    ("POST", "/v1/logout"),
})


class AuthBridgeError(RuntimeError):
    pass


class UnixHTTPConnection(http.client.HTTPConnection):
    def __init__(self, path):
        self.socket_path = str(path)
        super().__init__("localhost", timeout=5)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)


class AuthBridge:
    def __init__(self, socket_path):
        self.path = Path(socket_path)
        if not self.path.is_absolute():
            raise AuthBridgeError("Auth socket must have an absolute path")

    def _check(self):
        try:
            parent = self.path.parent.lstat()
            file = self.path.lstat()
        except OSError as exc:
            raise AuthBridgeError("Auth socket not available") from exc
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_mode & 0o077 or
                not stat.S_ISSOCK(file.st_mode) or file.st_mode & 0o077):
            raise AuthBridgeError("Private auth socket permissions invalid")
        if parent.st_uid != os.geteuid() or file.st_uid != os.geteuid():
            raise AuthBridgeError("Socket must belong to gateway account")

    def request(self, method, route, payload=None, token=None, csrf=None):
        if (method, route) not in ROUTES:
            raise AuthBridgeError("Unsupported private endpoint")
        self._check()
        if token is not None and (not isinstance(token, str) or not AUTH_TOKEN.fullmatch(token)):
            raise AuthBridgeError("Invalid session")
        if csrf is not None and (not isinstance(csrf, str) or not CSRF_TOKEN.fullmatch(csrf)):
            raise AuthBridgeError("Invalid CSRF token")
        if payload is not None:
            if not isinstance(payload, dict) or set(payload) != {"username", "password"}:
                raise AuthBridgeError("Invalid login request")
            if not isinstance(payload["username"], str) or not isinstance(payload["password"], str):
                raise AuthBridgeError("Invalid credentials")
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if len(body) > 2048:
                raise AuthBridgeError("Excessive login request")
        else:
            body = None
        headers = {"Accept": "application/json", "Connection": "close"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        if csrf:
            headers["X-StorOS-CSRF"] = csrf
        con = UnixHTTPConnection(self.path)
        try:
            con.request(method, route, body=body, headers=headers)
            res = con.getresponse()
            data = res.read(MAX_RESPONSE + 1)
            if len(data) > MAX_RESPONSE:
                raise AuthBridgeError("Excessive private service response")
            if res.status not in (200, 400, 401, 403, 429, 503):
                raise AuthBridgeError("Unexpected private service response")
            result = json.loads(data)
            if not isinstance(result, dict):
                raise AuthBridgeError("Malformed private service response")
            return res.status, result
        except (OSError, ValueError, http.client.HTTPException) as exc:
            raise AuthBridgeError("Private auth service unavailable") from exc
        finally:
            con.close()


def cookie_token(raw: str) -> str | None:
    if not isinstance(raw, str) or len(raw) > 4096:
        return None
    candidates = []
    for segment in raw.split(";"):
        key, sep, val = segment.strip().partition("=")
        if sep and key == "__Host-storos_session":
            candidates.append(val)
    if len(candidates) != 1 or not AUTH_TOKEN.fullmatch(candidates[0]):
        return None
    return candidates[0]


def session_cookie(token):
    if not AUTH_TOKEN.fullmatch(token):
        raise AuthBridgeError("Invalid session from service")
    return "__Host-storos_session=" + token + "; Path=/; Secure; HttpOnly; SameSite=Strict"


EXPIRED_COOKIE = "__Host-storos_session=; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=0"
