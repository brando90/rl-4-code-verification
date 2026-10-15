"""Account the separately frozen A6 diagnostic allocation in the canonical experiment-13 lease registry."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from lease import registry_lock,foreign_conflicts
from anchor_lease import release
from anchor_storage import atomic_json
from g1_driver import verify_publication
from training_checkpoint import digest

PHASES=('v2-S2-A6-diagnostic',)


def verify_allocation(plan):
    allocation=verify_publication(plan['allocation'],plan['repository'],plan['published_revision'])
    if allocation.get('gate')!='RESOURCE_ALLOCATION' or allocation.get('status')!='FROZEN' or allocation.get('phase') not in PHASES:
        raise ValueError('published Phase 2 resource allocation required')
    required=(HERE/'a6_lease.py',HERE.parent/'phase1/lease.py',HERE.parent/'phase1/anchor_lease.py',
        HERE.parent/'phase1/anchor_storage.py',HERE.parent/'phase1/g1_driver.py',HERE/'training_checkpoint.py')
    bound={b['path']:b['sha256'] for b in allocation['bindings']}
    for path in required:
        if bound.get(str(path))!=digest(path):raise ValueError('resource allocator source is not bound')
    return allocation,digest(plan['allocation'])


def accounting(registry,phase,allocation_sha):
    spent=reserved=0.
    for record in registry['leases']:
        if record.get('phase')!=phase:continue
        if record.get('allocation_sha256')!=allocation_sha:raise ValueError('allocation changed after a lease; budget cannot reset')
        value=float(record['device_hours'] if record['status']=='RELEASED' else record['reserved_device_hours'])
        if not math.isfinite(value) or value<0:raise ValueError('invalid recorded device time')
        if record['status']=='RELEASED':spent+=value
        else:reserved+=value
    return spent,reserved


def claim(root,inventory,index,*,allocation,allocation_sha,seconds,run_key,now=None):
    now=time.time() if now is None else now;phase=allocation['phase']
    cap=allocation['cumulative_device_hours'];maximum=allocation['maximum_lease_seconds'];slots=allocation['maximum_active_devices']
    if (phase not in PHASES or not all(math.isfinite(x) and x>0 for x in (cap,maximum,seconds))
            or seconds>maximum or type(slots) is not int or slots<1 or not run_key):raise ValueError('invalid frozen resource envelope')
    if not inventory['inventory_complete'] or index not in inventory['idle_device_indices']:
        raise RuntimeError('device busy or inventory incomplete; wait')
    device=next(d for d in inventory['devices'] if d['index']==index)
    if device.get('processes'):raise RuntimeError('compute process present; wait')
    route=allocation['routes'].get(inventory['host'])
    if route is None:raise ValueError('unfrozen device host')
    if device['memory_mib']<route['minimum_device_memory_mib']:raise RuntimeError('insufficient device memory')
    if inventory['local_storage']['available_bytes']<route['minimum_free_storage_bytes']:raise RuntimeError('insufficient local storage')
    for b in allocation['reservation_bindings']:
        if digest(b['path'])!=b['sha256']:raise RuntimeError('reservation evidence changed; reconcile before claim')
    discovery=allocation['reservation_inventory'];found=set()
    for directory in discovery['roots']:
        result=subprocess.run(['rg','--files',directory,'-g','*lease*.json','-g','*reservation*.json'],capture_output=True,text=True,timeout=30)
        if result.returncode not in (0,1):raise RuntimeError('foreign reservation inventory unavailable')
        found.update(p for p in result.stdout.splitlines() if 'preservation' not in Path(p).name)
    if found!=set(discovery['paths']):raise RuntimeError('foreign reservation paths changed; reconcile before claim')
    root=Path(root)
    with registry_lock(root):
        registry=json.loads((root/'registry.json').read_text())
        if registry['owner']!='e13v2':raise ValueError('not the experiment-13 registry')
        active=[r for r in registry['leases'] if r['status']!='RELEASED']
        if any(r.get('phase')!=phase or r['status']!='ACTIVE' or r['expires_unix']<=now for r in active):
            raise RuntimeError('existing owned lease requires adoption or cleanup')
        if len(active)>=slots or any(r.get('run_key')==run_key for r in active):raise RuntimeError('owned run or device slots already reserved')
        if any(r['host']==inventory['host'] and (r['index']==index or r['uuid']==device['uuid']) for r in active):
            raise RuntimeError('device already reserved')
        same_host=sum(r['host']==inventory['host'] for r in active)
        if inventory.get('host_memory',{}).get('available_bytes',0)<route['minimum_host_available_bytes']*(1+same_host):
            raise RuntimeError('insufficient host memory headroom')
        spent,reserved=accounting(registry,phase,allocation_sha)
        if spent+reserved+seconds/3600>cap:raise RuntimeError('frozen cumulative resource limit exhausted')
        conflicts,evidence=foreign_conflicts(inventory['host'],index,device['uuid'],allocation['foreign_registries'])
        if conflicts:raise RuntimeError('foreign lease or reservation exists; wait')
        record={'id':'e13v2-'+uuid.uuid4().hex,'owner':'e13v2','phase':phase,'run_key':run_key,
            'allocation_sha256':allocation_sha,'status':'ACTIVE','host':inventory['host'],'index':index,'uuid':device['uuid'],
            'started_unix':now,'expires_unix':now+seconds,'reserved_device_hours':seconds/3600,
            'foreign_registry_evidence':evidence,'reservation_bindings':allocation['reservation_bindings'],
            'supervisor_pid':os.getpid(),'supervisor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
            'supervisor_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'inventory':inventory}
        registry['leases'].append(record);atomic_json(root/'registry.json',registry);atomic_json(root/(record['id']+'.json'),record)
        return record
