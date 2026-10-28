#!/usr/bin/env python3
"""StorOS local operator tool. Talks only to a private Unix socket.

Never asks for password on command line. Does not contact the Unraid host,
Docker or network directly; all actions are delegated to the off-by-default
StorOS lab auth service running under a local unprivileged Unix account.
"""
import argparse
import getpass
import http.client
import json
import os
import socket
import sys

class OperatorError(RuntimeError):
    pass

class UnixHTTP(http.client.HTTPConnection):
    def __init__(self, path):
        self.socket_path = str(path)
        super().__init__("localhost", timeout=15)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.socket_path)

def request(socket_path, method, route, payload=None, token=None, csrf=None):
    connection = UnixHTTP(socket_path)
    headers = {"Accept": "application/json"}
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    if csrf:
        headers["X-StorOS-CSRF"] = csrf
    try:
        connection.request(method, route, body=data, headers=headers)
        response = connection.getresponse()
        content = response.read(100_001)
        if len(content) > 100_000:
            raise OperatorError("Service returned excessive output")
        result = json.loads(content)
        if response.status != 200:
            raise OperatorError(str(result.get("error", "Request refused")))
        return result
    except (OSError, ValueError, http.client.HTTPException) as exc:
        raise OperatorError("Cannot complete private socket request") from exc
    finally:
        connection.close()

def authenticate(socket_path):
    username = input("StorOS admin: ").strip()
    password = getpass.getpass("Senha (não exibida): ")
    if not username or not password:
        raise OperatorError("Login required")
    result = request(socket_path, "POST", "/v1/login",
                     {"username": username, "password": password})
    if result.get("role") != "admin":
        raise OperatorError("Administrator access required")
    return result["session_token"], result["csrf_token"]

def main(argv=None):
    parser = argparse.ArgumentParser(description="StorOS local lab administration")
    parser.add_argument("--socket", default="/var/lib/storos/private/auth.sock",
                        help="Absolute private StorOS Unix socket")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status", help="Local authentication service health")
    sub.add_parser("installed", help="Configured app projects, requires admin")
    app = sub.add_parser("plan", help="Get verified Compose plan, requires admin")
    app.add_argument("slug")
    app = sub.add_parser("install", help="Install catalog app after confirmation (VM lab only)")
    app.add_argument("slug")
    args = parser.parse_args(argv)
    if not args.socket.startswith("/"):
        parser.error("An absolute Unix socket path is required")
    if args.action == "status":
        print(json.dumps(request(args.socket, "GET", "/v1/health"), indent=2, ensure_ascii=False))
        return 0
    token, csrf = authenticate(args.socket)
    try:
        if args.action == "installed":
            result = request(args.socket, "GET", "/v1/apps/installed", token=token)
        elif args.action in ("plan", "install"):
            result = request(args.socket, "POST", "/v1/apps/plan",
                             {"slug": args.slug}, token=token, csrf=csrf)
            print("App:", result["slug"], "\nImagem:", result["image"])
            print("Compose:", result["compose"], sep="\n")
            print("SHA-256:", result["sha256"])
            for warning in result["warnings"]:
                print("AVISO:", warning)
            if args.action == "install":
                confirm = input("Para instalar no laboratório, digite o nome do app: ").strip()
                if confirm != args.slug:
                    raise OperatorError("Installation cancelled")
                result = request(args.socket, "POST", "/v1/apps/install",
                                 {"slug": args.slug, "accepted_sha256": result["sha256"]},
                                 token=token, csrf=csrf)
        else:
            raise OperatorError("Unsupported command")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    finally:
        try:
            request(args.socket, "POST", "/v1/logout", token=token, csrf=csrf)
        except OperatorError:
            pass

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OperatorError, KeyboardInterrupt) as exc:
        print("StorOS:", str(exc) if str(exc) else "Cancelado", file=sys.stderr)
        sys.exit(1)
