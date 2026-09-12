"""StorOS command router: observer commands plus persistent configuration commands."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from storos_agent import main as agent_main
from storos_config import (
    CONFIG_ROOT,
    TOKEN_FILE,
    ConfigError,
    apply_settings,
    ensure_admin_token,
    init_config,
    list_revisions,
    read_config,
    rollback_config,
)

CONFIG_COMMANDS = {
    'config-init', 'config-show', 'config-history', 'config-apply', 'config-rollback',
    'web-token-init', 'web-token-show',
}


def _json(data):
    print(json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True))


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
    except (ConfigError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({'error': 'configuration_error', 'message': str(exc)}, ensure_ascii=True))
        return 2
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
