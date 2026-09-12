"""Stable fingerprints for StorOS reconciliation safety preconditions."""
from __future__ import annotations

import hashlib
import json

SNAPSHOT_FINGERPRINT_VERSION = 1
PLAN_FINGERPRINT_VERSION = 1
_SNAPSHOT_EPHEMERAL_FIELDS = {
    'collection_started_at', 'collected_at', 'age_seconds', 'stale',
}
_PLAN_EPHEMERAL_FIELDS = {
    'snapshot_sha256', 'snapshot_age_seconds',
    'plan_fingerprint_version', 'plan_fingerprint_sha256',
}


def _canonical_json(data):
    return json.dumps(
        data, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':')
    )


def canonical_sha256(data):
    return hashlib.sha256(_canonical_json(data).encode('utf-8')).hexdigest()


def snapshot_semantic_view(snapshot):
    if not isinstance(snapshot, dict):
        raise ValueError('Snapshot inválido para fingerprint')
    view = {
        key: value for key, value in snapshot.items()
        if key not in _SNAPSHOT_EPHEMERAL_FIELDS
    }
    libvirt = view.get('libvirt')
    if isinstance(libvirt, dict):
        libvirt = dict(libvirt)
        vms = libvirt.get('vms')
        if isinstance(vms, list):
            libvirt['vms'] = sorted(
                vms,
                key=lambda item: (
                    str(item.get('uuid', '')) if isinstance(item, dict) else '',
                    _canonical_json(item),
                ),
            )
        errors = libvirt.get('errors')
        if isinstance(errors, list):
            libvirt['errors'] = sorted(errors, key=_canonical_json)
        view['libvirt'] = libvirt
    return view


def snapshot_fingerprint_sha256(snapshot):
    return canonical_sha256(snapshot_semantic_view(snapshot))


def plan_semantic_view(plan):
    if not isinstance(plan, dict):
        raise ValueError('Plano inválido para fingerprint')
    return {
        key: value for key, value in plan.items()
        if key not in _PLAN_EPHEMERAL_FIELDS
    }


def plan_fingerprint_sha256(plan):
    return canonical_sha256(plan_semantic_view(plan))


def decorate_plan_fingerprints(plan, snapshot):
    if not isinstance(plan, dict):
        raise ValueError('Plano inválido')
    decorated = dict(plan)
    decorated['snapshot_fingerprint_version'] = SNAPSHOT_FINGERPRINT_VERSION
    decorated['snapshot_fingerprint_sha256'] = snapshot_fingerprint_sha256(snapshot)
    decorated['plan_fingerprint_version'] = PLAN_FINGERPRINT_VERSION
    decorated['plan_fingerprint_sha256'] = plan_fingerprint_sha256(decorated)
    return decorated
