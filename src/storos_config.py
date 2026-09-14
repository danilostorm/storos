"""Persistent transactional configuration store for StorOS."""
from __future__ import annotations

import base64
import fcntl
import json
import os
from pathlib import Path
import secrets
import tempfile
from datetime import datetime, timezone

CONFIG_ROOT = Path('/var/lib/storos/config')
TOKEN_FILE = Path('/var/lib/storos/auth/admin.token')
SCHEMA_VERSION = 1


class ConfigError(ValueError):
    pass


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _paths(root):
    root = Path(root)
    return root, root / 'current.json', root / 'revisions', root / '.lock'


def default_settings():
    return {
        'web': {
            'listen_host': '127.0.0.1',
            'port': 8080,
            'allow_insecure_lan': False,
        },
        'features': {
            'vm_write_enabled': False,
        },
    }


def _validate_host(host):
    if not isinstance(host, str) or not host or len(host) > 255:
        raise ConfigError('web.listen_host inválido')
    if any(ch.isspace() for ch in host):
        raise ConfigError('web.listen_host inválido')
    return host


def validate_settings(settings):
    if not isinstance(settings, dict) or set(settings) != {'web', 'features'}:
        raise ConfigError('Configuração deve conter somente web e features')
    web = settings['web']
    features = settings['features']
    if not isinstance(web, dict) or set(web) != {'listen_host', 'port', 'allow_insecure_lan'}:
        raise ConfigError('Seção web incompatível')
    if not isinstance(features, dict) or set(features) != {'vm_write_enabled'}:
        raise ConfigError('Seção features incompatível')
    host = _validate_host(web['listen_host'])
    port = web['port']
    allow_lan = web['allow_insecure_lan']
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ConfigError('web.port inválida')
    if not isinstance(allow_lan, bool):
        raise ConfigError('web.allow_insecure_lan deve ser booleano')
    if host not in ('127.0.0.1', '::1', 'localhost') and not allow_lan:
        raise ConfigError('Exposição fora do loopback exige allow_insecure_lan=true')
    if features['vm_write_enabled'] is not False:
        raise ConfigError('Escrita em VMs permanece bloqueada nesta fase')
    return {
        'web': {
            'listen_host': host,
            'port': port,
            'allow_insecure_lan': allow_lan,
        },
        'features': {'vm_write_enabled': False},
    }


def validate_document(document):
    if not isinstance(document, dict):
        raise ConfigError('Documento inválido')
    if document.get('schema_version') != SCHEMA_VERSION:
        raise ConfigError('schema_version incompatível')
    generation = document.get('generation')
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise ConfigError('generation inválida')
    updated_at = document.get('updated_at')
    if not isinstance(updated_at, str) or not updated_at:
        raise ConfigError('updated_at ausente')
    settings = validate_settings(document.get('settings'))
    result = dict(document)
    result['settings'] = settings
    return result


def _fsync_directory(path):
    directory_fd = os.open(Path(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_write_json(path, data, mode=0o640):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), mode)
            json.dump(data, stream, ensure_ascii=True, allow_nan=False, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _lock(lock_path):
    parent = Path(lock_path).parent
    parent.mkdir(parents=True, exist_ok=True)
    os.chmod(parent, 0o750)
    handle = open(lock_path, 'a+')
    os.chmod(lock_path, 0o600)
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def read_config(root=CONFIG_ROOT):
    _, current, _, _ = _paths(root)
    return validate_document(json.loads(current.read_text()))


def init_config(root=CONFIG_ROOT):
    root, current, revisions, lock_path = _paths(root)
    with _lock(lock_path):
        if current.exists():
            return read_config(root)
        revisions.mkdir(parents=True, exist_ok=True)
        os.chmod(revisions, 0o750)
        document = {
            'schema_version': SCHEMA_VERSION,
            'generation': 1,
            'updated_at': _utc_now(),
            'settings': validate_settings(default_settings()),
            'reason': 'initial',
        }
        revision = revisions / '000001.json'
        _atomic_write_json(revision, document)
        _atomic_write_json(current, document)
        return document


def apply_settings(settings, root=CONFIG_ROOT, expected_generation=None, reason='apply'):
    root, current, revisions, lock_path = _paths(root)
    validated = validate_settings(settings)
    if not current.exists():
        init_config(root)
    with _lock(lock_path):
        previous = read_config(root)
        if expected_generation is not None and previous['generation'] != expected_generation:
            raise ConfigError('Conflito de geração')
        generation = previous['generation'] + 1
        document = {
            'schema_version': SCHEMA_VERSION,
            'generation': generation,
            'updated_at': _utc_now(),
            'settings': validated,
            'reason': str(reason)[:160],
        }
        revisions.mkdir(parents=True, exist_ok=True)
        os.chmod(revisions, 0o750)
        revision = revisions / f'{generation:06d}.json'
        if revision.exists():
            raise ConfigError('Revisão já existe')
        _atomic_write_json(revision, document)
        _atomic_write_json(current, document)
        return document


def rollback_config(target_generation, root=CONFIG_ROOT, expected_generation=None):
    root, current, revisions, lock_path = _paths(root)
    if not isinstance(target_generation, int) or isinstance(target_generation, bool) or target_generation < 1:
        raise ConfigError('Geração de rollback inválida')
    with _lock(lock_path):
        previous = read_config(root)
        if expected_generation is not None and previous['generation'] != expected_generation:
            raise ConfigError('Conflito de geração')
        target_path = revisions / f'{target_generation:06d}.json'
        target = validate_document(json.loads(target_path.read_text()))
        generation = previous['generation'] + 1
        document = {
            'schema_version': SCHEMA_VERSION,
            'generation': generation,
            'updated_at': _utc_now(),
            'settings': target['settings'],
            'reason': f'rollback:{target_generation}',
        }
        revision = revisions / f'{generation:06d}.json'
        _atomic_write_json(revision, document)
        _atomic_write_json(current, document)
        return document


def list_revisions(root=CONFIG_ROOT):
    _, _, revisions, _ = _paths(root)
    if not revisions.exists():
        return []
    result = []
    for path in sorted(revisions.glob('*.json')):
        try:
            result.append(validate_document(json.loads(path.read_text())))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return result


def ensure_admin_token(path=TOKEN_FILE):
    path = Path(path)
    if path.exists():
        token = path.read_text().strip()
        if len(token) < 32:
            raise ConfigError('Token administrativo inválido')
        os.chmod(path, 0o600)
        return token
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o750)
    token = secrets.token_urlsafe(32)
    fd, temporary = tempfile.mkstemp(prefix='.admin-token-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(token + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return token


def basic_auth_value(token):
    raw = ('admin:' + token).encode('utf-8')
    return 'Basic ' + base64.b64encode(raw).decode('ascii')
