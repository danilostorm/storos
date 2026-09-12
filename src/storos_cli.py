"""StorOS command router: observer commands plus persistent configuration commands."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from storos_agent import main as agent_main
from storos_config import (
    CONFIG_ROOT,
    TOKEN_FILE,
    ConfigError,
    apply_settings,
    basic_auth_value,
    ensure_admin_token,
    init_config,
    list_revisions,
    read_config,
    rollback_config,
)

CONFIG_COMMANDS = {
    'config-init', 'config-show', 'config-history', 'config-apply', 'config-rollback',
    'web-token-init', 'web-token-show', 'web-marker',
}


def _json(data):
    print(json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True))


def _canonical_sha256(data):
    canonical = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def _probe_url(config):
    web = config['settings']['web']
    host = web['listen_host']
    if host in ('0.0.0.0', 'localhost'):
        host = '127.0.0.1'
    elif host == '::':
        host = '::1'
    if ':' in host and not host.startswith('['):
        host = f'[{host}]'
    return f'http://{host}:{web["port"]}/api/config'


def web_marker(config_root=CONFIG_ROOT, token_file=TOKEN_FILE, wait=60):
    if not isinstance(wait, int) or isinstance(wait, bool) or not 1 <= wait <= 300:
        raise ConfigError('A espera do painel deve ser de 1 a 300 segundos')
    deadline = time.monotonic() + wait
    opener = build_opener(ProxyHandler({}))
    last_error = 'painel indisponível'
    while time.monotonic() < deadline:
        try:
            config = read_config(config_root)
            token = ensure_admin_token(token_file)
            request = Request(
                _probe_url(config),
                headers={'Authorization': basic_auth_value(token), 'Accept': 'application/json'},
                method='GET',
            )
            remaining = max(0.2, deadline - time.monotonic())
            with opener.open(request, timeout=min(3.0, remaining)) as response:
                if response.status != 200:
                    raise ConfigError(f'Painel respondeu HTTP {response.status}')
                remote = json.load(response)
            if remote != config:
                raise ConfigError('Painel respondeu configuração diferente da persistida')
            print(
                'STOROS_WEB_READY auth=ok '
                f'config_generation={config["generation"]} '
                f'config_sha256={_canonical_sha256(config)} '
                f'token_sha256={hashlib.sha256(token.encode("utf-8")).hexdigest()}',
                flush=True,
            )
            return 0
        except (ConfigError, OSError, ValueError, TypeError, json.JSONDecodeError, HTTPError, URLError, TimeoutError) as exc:
            last_error = str(exc)
            time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
    raise ConfigError(f'Painel local não ficou pronto no prazo: {last_error}')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in CONFIG_COMMANDS:
        return agent_main(argv)

    parser = argparse.ArgumentParser(description='Configuração persistente StorOS.')
    parser.add_argument('command', choices=sorted(CONFIG_COMMANDS))
    parser.add_argument('--config-root', default=str(CONFIG_ROOT))
    parser.add_argument('--config-file')
    parser.add_argument('--expected-generation', type=int)
    parser.add_argument('--target-generation', type=int)
    parser.add_argument('--token-file', default=str(TOKEN_FILE))
    parser.add_argument('--wait', type=int, default=60)
    args = parser.parse_args(argv)

    try:
        if args.command == 'config-init':
            _json(init_config(args.config_root))
            return 0
        if args.command == 'config-show':
            _json(read_config(args.config_root))
            return 0
        if args.command == 'config-history':
            _json(list_revisions(args.config_root))
            return 0
        if args.command == 'config-apply':
            if not args.config_file:
                parser.error('config-apply exige --config-file')
            payload = json.loads(Path(args.config_file).read_text())
            settings = payload.get('settings', payload) if isinstance(payload, dict) else payload
            _json(apply_settings(settings, args.config_root, args.expected_generation, reason='cli-apply'))
            return 0
        if args.command == 'config-rollback':
            if args.target_generation is None:
                parser.error('config-rollback exige --target-generation')
            _json(rollback_config(args.target_generation, args.config_root, args.expected_generation))
            return 0
        if args.command == 'web-token-init':
            ensure_admin_token(args.token_file)
            print(f'STOROS_WEB_TOKEN_READY path={args.token_file}')
            return 0
        if args.command == 'web-token-show':
            print(ensure_admin_token(args.token_file))
            return 0
        if args.command == 'web-marker':
            return web_marker(args.config_root, args.token_file, args.wait)
    except (ConfigError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({'error': 'configuration_error', 'message': str(exc)}, ensure_ascii=True))
        return 2
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
