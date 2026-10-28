#!/usr/bin/env python3
"""Read-only, LAN-only HTTPS gateway for the isolated StorOS test VM.

The VM's API stays on guest loopback, reached via an SSH tunnel on HOST loopback.
Authentication is required before proxying any requests. This is laboratory-only.
"""
import argparse
import base64
import hmac
import http.client
import json
import re
import ipaddress
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlencode, parse_qs
from native_auth_bridge import AuthBridge, AuthBridgeError, CSRF_TOKEN, cookie_token, session_cookie, EXPIRED_COOKIE

ALLOWED = frozenset({"/", "/index.html", "/app.js", "/apps.js", "/style.css", "/navigation.js", "/navigation.css", "/storage.js", "/storage.css", "/hero.webp", "/api/status", "/api/disks", "/api/containers", "/api/vms", "/api/apps/catalog", "/api/apps/engine", "/api/apps/compose", "/api/apps/hub", "/api/billing/model", "/api/billing/estimate", "/api/overview", "/api/storage", "/api/modules", "/api/security/status", "/modules.js", "/modules.css", "/native-auth.js", "/native-auth.css", "/ca-import.js", "/ca-import.css"})
LAN = ipaddress.ip_network("192.168.30.0/24")

class Gateway(BaseHTTPRequestHandler):
    server_version = "StorOS-LabGateway"
    def log_message(self, fmt, *args):
        # Do not log Authorization headers, query strings or credentials.
        return

    def do_GET(self):
        self._route(False)

    def do_HEAD(self):
        self._route(True)

    def _authorized(self):
        try:
            if ipaddress.ip_address(self.client_address[0]) not in LAN:
                self.send_error(403, "LAN clients only")
                return False
        except ValueError:
            self.send_error(403, "LAN clients only")
            return False
        auth = self.headers.get("Authorization", "")
        ok = False
        if auth.startswith("Basic ") and len(auth) < 256:
            try:
                decoded = base64.b64decode(auth[6:], validate=True).decode("utf-8")
                ok = hmac.compare_digest(decoded, self.server.user_password)
            except (ValueError, UnicodeError):
                pass
        if not ok:
            self.send_response(401)
            self.send_header("WWW-Authenticate", 'Basic realm="StorOS-Laboratorio", charset="UTF-8"')
            self._security_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()
        return ok

    def _json_reply(self, status, payload, head=False, cookie=None):
        content = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._security_headers()
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if not head:
            self.wfile.write(content)

    def do_POST(self):
        parts = urlsplit(self.path)
        if parts.path not in ("/api/native/login", "/api/native/logout"):
            self.send_error(405, "This laboratory gateway does not allow host changes")
            return
        if not self._authorized():
            return
        if parts.query or parts.fragment or self.server.native_auth_bridge is None:
            self._json_reply(403, {"error": "Native web login is disabled"})
            return
        expected_origin = "https://192.168.30.10:" + str(self.server.server_port)
        if (self.headers.get("Origin") != expected_origin or
            self.headers.get("Host") != "192.168.30.10:" + str(self.server.server_port)):
            self._json_reply(403, {"error": "Origin not allowed"})
            return
        raw_length = self.headers.get("Content-Length", "")
        if not raw_length.isdigit() or int(raw_length) > 2048:
            self._json_reply(400, {"error": "Invalid request length"})
            return
        if parts.path.endswith("/login") and self.headers.get("Content-Type", "").strip().lower() != "application/json":
            self._json_reply(400, {"error": "JSON required"})
            return
        data = self.rfile.read(int(raw_length))
        try:
            bridge = self.server.native_auth_bridge
            if parts.path.endswith("/login"):
                request = json.loads(data)
                status, response = bridge.request("POST", "/v1/login", request)
                if status != 200:
                    return self._json_reply(status, {"error": response.get("error", "Login denied")})
                token, csrf = response["session_token"], response["csrf_token"]
                cookie = session_cookie(token)
                return self._json_reply(200, {"signed_in": True, "role": response.get("role"),
                                               "csrf_token": csrf}, cookie=cookie)
            if data:
                return self._json_reply(400, {"error": "Logout body must be empty"})
            token = cookie_token(self.headers.get("Cookie", ""))
            csrf = self.headers.get("X-StorOS-CSRF", "")
            if not token:
                return self._json_reply(401, {"error": "Not signed in"})
            if not CSRF_TOKEN.fullmatch(csrf):
                return self._json_reply(403, {"error": "Invalid CSRF"})
            status, response = bridge.request("POST", "/v1/logout", token=token, csrf=csrf)
            if status != 200:
                return self._json_reply(status, {"error": "Logout denied"})
            return self._json_reply(200, {"signed_out": True}, cookie=EXPIRED_COOKIE)
        except (AuthBridgeError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return self._json_reply(503, {"error": "Native authentication unavailable"})

    def _route(self, head):
        if not self._authorized():
            return
        parts = urlsplit(self.path)
        target = parts.path
        if target in ("/api/native/status", "/api/native/me"):
            if parts.query or parts.fragment:
                return self._json_reply(400, {"error": "Queries not supported"}, head=head)
            bridge = self.server.native_auth_bridge
            if target == "/api/native/status":
                return self._json_reply(200, {"enabled": bridge is not None,
                    "mode": "private-unix-auth" if bridge is not None else "disabled",
                    "host_mutations": False}, head=head)
            if bridge is None:
                return self._json_reply(403, {"error": "Native web login is disabled"}, head=head)
            token = cookie_token(self.headers.get("Cookie", ""))
            if not token:
                return self._json_reply(401, {"error": "Not signed in"}, head=head)
            try:
                status, info = bridge.request("GET", "/v1/me", token=token)
            except AuthBridgeError:
                return self._json_reply(503, {"error": "Native authentication unavailable"}, head=head)
            return self._json_reply(status, info if status == 200 else {"error": "Not signed in"}, head=head)
        if target not in ALLOWED:
            self.send_error(404, "Unsupported read-only resource")
            return
        # Only allow tiny, canonical query strings for the two search/preview APIs.
        if parts.query:
            if target not in ("/api/apps/hub", "/api/apps/compose", "/api/billing/estimate") or len(parts.query) > 480:
                self.send_error(400, "Unsupported query")
                return
            args = parse_qs(parts.query, keep_blank_values=False)
            if target == "/api/billing/estimate":
                names = {"cpu_watts", "board_watts", "ram_watts", "threads", "host_ram_gib",
                         "vcpus", "ram_gib", "gpu_watts", "hours", "electricity_kwh",
                         "uptime_hour", "plan_price", "total_cycle_gb", "item_cycle_gb"}
                if set(args) != names or any(len(v) != 1 or len(v[0]) > 16 for v in args.values()):
                    self.send_error(400, "Invalid estimate query")
                    return
                target += "?" + urlencode({k: args[k][0] for k in sorted(names)})
            else:
                arg_name = "q" if target == "/api/apps/hub" else "slug"
                if set(args) != {arg_name} or len(args[arg_name]) != 1:
                    self.send_error(400, "Invalid query")
                    return
                target += "?" + urlencode({arg_name: args[arg_name][0]})
        upstream = http.client.HTTPConnection("127.0.0.1", self.server.upstream_port, timeout=10)
        try:
            upstream.request("HEAD" if head else "GET", target, headers={"Host": "localhost", "Connection": "close"})
            response = upstream.getresponse()
            if response.status not in (200, 304, 400, 503):
                self.send_error(502, "StorOS responded unexpectedly")
                return
            body = b"" if head else response.read(4 * 1024 * 1024 + 1)
            if len(body) > 4 * 1024 * 1024:
                self.send_error(502, "Excessive upstream payload")
                return
            self.send_response(response.status)
            self.send_header("Content-Type", response.getheader("Content-Type") or "application/octet-stream")
            self._security_headers()
            self.send_header("Content-Length", str(response.getheader("Content-Length") if head else len(body)))
            self.end_headers()
            if not head:
                self.wfile.write(body)
        except (OSError, http.client.HTTPException):
            self.send_error(502, "StorOS VM unavailable; check SSH forwarding")
        finally:
            upstream.close()

    def _security_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")

class LabServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", required=True)
    parser.add_argument("--port", type=int, default=18443)
    parser.add_argument("--upstream-port", type=int, default=18766)
    parser.add_argument("--credentials", type=Path, required=True)
    parser.add_argument("--cert", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--auth-socket", type=Path,
                        help="Opt-in private Unix auth socket; no native auth by default")
    args = parser.parse_args()
    if args.bind != "192.168.30.10" or args.port not in (18443, 18444):
        parser.error("Refusing unsafe binding; laboratory gateway restricted to AEROCOOL LAN IP and port")
    if args.credentials.stat().st_mode & 0o077:
        parser.error("Credential file must not be accessible to group/others")
    credentials = args.credentials.read_text(encoding="utf-8").strip()
    if not credentials.startswith("storos:") or len(credentials) < 28:
        parser.error("Invalid laboratory credentials")
    server = LabServer((args.bind, args.port), Gateway)
    server.user_password = credentials
    server.upstream_port = args.upstream_port
    server.native_auth_bridge = None
    if args.auth_socket:
        candidate = AuthBridge(args.auth_socket)
        candidate._check()
        server.native_auth_bridge = candidate
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(args.cert, args.key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    print(f"StorOS HTTPS gateway is listening on {args.bind}:{args.port}; guest API remains localhost-only", flush=True)
    server.serve_forever(poll_interval=0.5)

if __name__ == "__main__":
    main()
