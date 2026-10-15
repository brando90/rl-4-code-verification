"""Allocate bounded S2 anchor segments in the canonical registry with shared budget accounting."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import time
import uuid
import subprocess

from lease import foreign_conflicts, registry_lock, release as original_release
from anchor_storage import atomic_json,sync_directory
from panel import digest

PHASE = 'v2-S2-anchors'
MAX_DEVICE_HOURS = 144.
MAX_SEGMENT_SECONDS = 7200
MAX_ACTIVE_DEVICES = 3


def accounting(registry):
    records = [r for r in registry['leases'] if r.get('phase') == PHASE]
    spent = reserved = 0.
    for record in records:
        key = 'device_hours' if record['status']=='RELEASED' else 'reserved_device_hours'
        hours = float(record[key])
        if not math.isfinite(hours) or hours<0:
            raise ValueError('invalid anchor budget accounting')
        if record['status']=='RELEASED': spent += hours
        else: reserved += hours
    return spent, reserved


def remaining_seconds(root):
    """Return separately the true unspent budget and currently unreserved budget."""
    with registry_lock(root):
        registry=json.loads((Path(root)/'registry.json').read_text())
        spent,reserved=accounting(registry)
        return max(0,int((MAX_DEVICE_HOURS-spent)*3600)),max(0,int((MAX_DEVICE_HOURS-spent-reserved)*3600))


def release(root,lease_id,*,cleanup_verified,now=None):
    result=original_release(root,lease_id,cleanup_verified=cleanup_verified,now=now)
    sync_directory(root)
    return result


def claim(root, inventory, index, *, sources, reservation_bindings, batch,
          seconds=MAX_SEGMENT_SECONDS, now=None, reservation_inventory=None):
    """No historical budget is reset; other devices may serve independent anchor policies."""
    now = time.time() if now is None else now
    if batch not in ('base','half','full1','full2') or not 0 < seconds <= MAX_SEGMENT_SECONDS:
        raise ValueError('undeclared anchor allocation')
    if not inventory['inventory_complete'] or index not in inventory['idle_device_indices']:
        raise RuntimeError('busy device or incomplete inventory')
    device = next(d for d in inventory['devices'] if d['index']==index)
    if device['memory_mib'] < 40000:
        raise RuntimeError('anchor route needs at least 40000 MiB device memory')
    if inventory['local_storage']['available_bytes'] < 25*1024**3:
        raise RuntimeError('anchor route needs 25 GiB free storage')
    for binding in reservation_bindings:
        if digest(binding['path']) != binding['sha256']:
            raise RuntimeError('reservation evidence changed')
    if reservation_inventory is not None:
        found=set()
        for directory in reservation_inventory['roots']:
            result=subprocess.run(['rg','--files',directory,'-g','*lease*.json','-g','*reservation*.json'],
                                  capture_output=True,text=True,timeout=30)
            if result.returncode not in (0,1):raise RuntimeError('foreign lease inventory unavailable')
            found.update(p for p in result.stdout.splitlines() if 'preservation' not in Path(p).name)
        if found!=set(reservation_inventory['paths']):
            raise RuntimeError('foreign lease/reservation path inventory changed; reconcile before claiming')
    root = Path(root)
    with registry_lock(root):
        registry = json.loads((root/'registry.json').read_text())
        if registry['owner']!='e13v2':
            raise RuntimeError('not the experiment-13 registry')
        active = [r for r in registry['leases'] if r['status']!='RELEASED']
        if any(r.get('phase')!=PHASE or r['status']!='ACTIVE' or r['expires_unix']<=now for r in active):
            raise RuntimeError('an owned allocation needs reconciliation or cleanup')
        if len(active)>=MAX_ACTIVE_DEVICES:
            raise RuntimeError('all three anchor device slots are reserved')
        if any(r.get('batch')==batch for r in active):
            raise RuntimeError('this anchor batch already has a lease')
        if any(r['host']==inventory['host'] and (r['index']==index or r['uuid']==device['uuid']) for r in active):
            raise RuntimeError('device already reserved in experiment-13 registry')
        same_host = sum(r['host']==inventory['host'] for r in active)
        if inventory.get('host_memory',{}).get('available_bytes',0)<64*1024**3*(1+same_host):
            raise RuntimeError('insufficient host memory headroom for simultaneous anchor launches')
        spent,reserved = accounting(registry)
        if spent+reserved+seconds/3600>MAX_DEVICE_HOURS:
            raise RuntimeError('S2 anchor cumulative device budget exhausted')
        conflicts,evidence = foreign_conflicts(inventory['host'],index,device['uuid'],sources)
        if conflicts: raise RuntimeError('foreign lease or reservation exists')
        record = {'id':'e13v2-'+uuid.uuid4().hex,'owner':'e13v2','phase':PHASE,'batch':batch,
                  'status':'ACTIVE','host':inventory['host'],'index':index,'uuid':device['uuid'],
                  'started_unix':now,'expires_unix':now+seconds,'reserved_device_hours':seconds/3600,
                  'foreign_registry_evidence':evidence,'reservation_bindings':reservation_bindings,
                  'supervisor_pid':os.getpid(),
                  'supervisor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
                  'supervisor_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                  'inventory':inventory}
        registry['leases'].append(record)
        atomic_json(root/'registry.json',registry);atomic_json(root/(record['id']+'.json'),record)
        return record
