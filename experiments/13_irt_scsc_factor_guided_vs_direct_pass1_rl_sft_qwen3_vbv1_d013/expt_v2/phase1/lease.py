"""Claim an idle device in the experiment-13 registry after foreign reservation checks."""
from __future__ import annotations

import contextlib
import fcntl
import json
import os
from pathlib import Path
import time
import uuid

from panel import digest


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    with temp.open('x') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    temp.replace(path)


@contextlib.contextmanager
def registry_lock(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    with (root/'registry.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def foreign_conflicts(host, index, gpu_uuid, sources):
    """Only explicit released records stop reserving; expiry alone is insufficient."""
    conflicts = []; evidence = []
    for source in sources:
        path = Path(source['path'])
        data = json.loads(path.read_text())
        records = list(data.values()) if isinstance(data, dict) else data
        if not isinstance(records, list):
            raise ValueError('unknown foreign registry schema')
        evidence.append({'path': str(path), 'sha256': digest(path), 'records': len(records)})
        for record in records:
            if not isinstance(record, dict):
                raise ValueError('unknown foreign lease record')
            if record.get('released') is True or record.get('status') == 'RELEASED':
                continue
            identity = record.get('identity', {})
            node = record.get('host', identity.get('host', source.get('default_host')))
            if not node:
                raise ValueError('foreign reservation has unknown host')
            if node.split('.')[0] != host:
                continue
            devices = record.get('gpus', record.get('devices'))
            if devices is None and 'gpu' in record: devices = [record['gpu']]
            if devices is None or index in devices or str(index) in devices or gpu_uuid in devices:
                conflicts.append({'path': str(path), 'owner': record.get('owner', 'unknown')})
    return conflicts, evidence


def claim(root, inventory, index, *, sources, reservation_bindings, seconds,
          cumulative_limit_hours, storage_required_bytes, minimum_memory_mib,
          minimum_host_available_bytes=0, now=None):
    now = time.time() if now is None else now
    if not 0 < seconds <= 7200 or not 0 < cumulative_limit_hours <= 8:
        raise ValueError('undeclared resource budget')
    if not inventory['inventory_complete'] or index not in inventory['idle_device_indices']:
        raise RuntimeError('device is busy or its inventory is incomplete')
    device = next(d for d in inventory['devices'] if d['index'] == index)
    if device['memory_mib'] < minimum_memory_mib:
        raise RuntimeError('device memory below frozen route requirement')
    if inventory['local_storage']['available_bytes'] < storage_required_bytes:
        raise RuntimeError('bounded storage requirement is not met')
    if minimum_host_available_bytes:
        memory = inventory.get('host_memory')
        if not memory or memory['available_bytes'] < minimum_host_available_bytes:
            raise RuntimeError('host memory headroom is insufficient or unknown')
    for b in reservation_bindings:
        if digest(b['path']) != b['sha256']:
            raise RuntimeError('reservation evidence changed; refresh it before claiming')
    root = Path(root)
    with registry_lock(root):
        registry = json.loads((root/'registry.json').read_text())
        if registry['owner'] != 'e13v2':
            raise RuntimeError('not the experiment-13 registry')
        if any(r['status'] != 'RELEASED' for r in registry['leases']):
            raise RuntimeError('an experiment-13 lease needs adoption or cleanup')
        if registry['device_hours'] + seconds/3600 > cumulative_limit_hours:
            raise RuntimeError('cumulative resource budget exhausted')
        conflicts, evidence = foreign_conflicts(inventory['host'], index, device['uuid'], sources)
        if conflicts:
            raise RuntimeError('foreign lease or reservation exists')
        lease_id = 'e13v2-' + uuid.uuid4().hex
        record = {'id': lease_id, 'owner': 'e13v2', 'status': 'ACTIVE',
                  'host': inventory['host'], 'index': index, 'uuid': device['uuid'],
                  'started_unix': now, 'expires_unix': now+seconds,
                  'reserved_device_hours': seconds/3600, 'foreign_registry_evidence': evidence,
                  'reservation_bindings': reservation_bindings,
                  'supervisor_pid': os.getpid(),
                  'supervisor_start_ticks': Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
                  'supervisor_boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  'inventory': inventory}
        registry['leases'].append(record)
        atomic_json(root/'registry.json', registry)
        atomic_json(root/(lease_id+'.json'), record)
        return record


def release(root, lease_id, *, cleanup_verified, now=None):
    now = time.time() if now is None else now
    root = Path(root)
    with registry_lock(root):
        registry = json.loads((root/'registry.json').read_text())
        matches = [r for r in registry['leases'] if r['id'] == lease_id]
        if len(matches) != 1: raise ValueError('unknown lease')
        record = matches[0]
        if record['status'] == 'RELEASED': return record
        if not cleanup_verified:
            record['status'] = 'CLEANUP_REQUIRED'
        else:
            elapsed = max(0., (now-record['started_unix'])/3600)
            registry['device_hours'] += elapsed
            record.update(status='RELEASED', released_unix=now, device_hours=elapsed)
        atomic_json(root/'registry.json', registry)
        atomic_json(root/(lease_id+'.json'), record)
        return record
