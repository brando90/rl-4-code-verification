"""Poll idle devices for immutable learning stages under per-run and cumulative frozen limits."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'phase1'))
from device_watch import observe
from anchor_storage import atomic_json
from resource_lease import verify_allocation, accounting, claim, release
from learning_ledger import verify_learning
from training_checkpoint import digest

RUN_KEY = re.compile(r'([ABCP])/(1301|1302|13011|13012|13013)/([0-9]+)/([a-z][a-z0-9_]*)')


def remaining(registry, allocation, allocation_sha, arm, run_seed):
    """Charge all health, failed and unresolved leases to the same fixed arm/seed allowance."""
    phase=allocation['phase']; key=f'{arm}/{run_seed}'; caps=allocation['run_caps_device_hours']
    if key not in caps or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in caps.values()):
        raise ValueError('invalid or missing frozen learning run limit')
    spent,reserved=accounting(registry,phase,allocation_sha)
    used=0.; keys=set()
    for row in registry['leases']:
        if row.get('phase')!=phase:continue
        match=RUN_KEY.fullmatch(row['run_key'])
        if match is None or row['run_key'] in keys:raise ValueError('learning lease history has invalid or duplicate identities')
        keys.add(row['run_key'])
        if f'{match[1]}/{match[2]}'==key:
            used+=float(row['device_hours'] if row['status']=='RELEASED' else row['reserved_device_hours'])
    return {'allocation_hours':allocation['cumulative_device_hours']-spent-reserved,
            'run_hours':caps[key]-used,'run_keys':keys}


@contextmanager
def dispatch_fence(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    with (root/'learning_resources.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def reserve(plan, *, update, stage_key, seconds):
    """One idle-device poll; waiting does not reserve or execute a learning stage."""
    run=plan['run']; lp,execution,science=verify_learning(run)
    allocation,allocation_sha=verify_allocation(plan['allocation_plan'])
    expected_phase='v2-S2-learning-pilot' if run['phase']=='pilot' else 'v2-S2-main'
    if allocation['phase']!=expected_phase or execution['allocation_sha256']!=allocation_sha:
        raise ValueError('learning allocation differs from its execution lock')
    bound={str(Path(r['path']).resolve()):r['sha256'] for r in execution['bindings']}
    for path in (Path(__file__).resolve(),HERE/'resource_lease.py',HERE.parent/'phase1/device_watch.py'):
        if bound.get(str(path))!=digest(path):raise ValueError('unbound learning resource implementation')
    for key in ('lease_root','resource_poll_root'):
        if Path(plan[key]).resolve()!=Path(execution['configuration'][key]).resolve():
            raise ValueError('learning resource registry or observation ledger moved')
    run_key=f"{run['arm']}/{run['run_seed']}/{update}/{stage_key}"
    if (type(update) is not int or update<0 or RUN_KEY.fullmatch(run_key) is None
            or type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<=90):
        raise ValueError('invalid bounded learning stage')
    root = Path(plan['resource_poll_root'])
    with dispatch_fence(root):
        registry = json.loads((Path(plan['lease_root'])/'registry.json').read_text())
        available = remaining(registry, allocation, allocation_sha, run['arm'], run['run_seed'])
        if run_key in available.pop('run_keys'):
            raise RuntimeError('stage already claimed a lease; reconcile it without an automatic retry')
        record = {'condition':'v2-S2','phase':run['phase'],'arm':run['arm'],'run_seed':run['run_seed'],
                  'update':update,'stage_key':stage_key,'science_sha256':science,
                  'execution_sha256':run['execution_lock']['sha256'],
                  'remaining_device_hours':available,'device_claims':0,'observations':[],'candidate_rejections':[]}
        if seconds/3600 > min(available.values()):
            record['status'] = 'RESOURCE_EXHAUSTED'
        else:
            record['status'] = 'WAIT_FOR_IDLE_DEVICE'
            for host in allocation['routes']:
                inventory = observe(host); record['observations'].append(inventory)
                if not inventory['inventory_complete']: continue
                for index in inventory['idle_device_indices']:
                    try:
                        lease = claim(plan['lease_root'], inventory, index, allocation=allocation,
                                      allocation_sha=allocation_sha, seconds=seconds, run_key=run_key)
                    except RuntimeError as exc:
                        record['candidate_rejections'].append({'host': host, 'index': index, 'reason': str(exc)})
                        continue
                    record['device_claims'] = 1
                    # No child has launched. If another owner occupied the device
                    # between observations, release only this unused reservation.
                    fresh = observe(host); record['observations'].append(fresh)
                    valid = fresh['inventory_complete'] and index in fresh['idle_device_indices'] and any(
                        d['index'] == index and d['uuid'] == lease['uuid'] for d in fresh['devices'])
                    if not valid:
                        retired = release(plan['lease_root'], lease['id'], cleanup_verified=True)
                        record.update(status='DEVICE_CHANGED_BEFORE_LAUNCH', lease=retired)
                    else:
                        record.update(status='RESERVED', lease=lease)
                    break
                if record['device_claims']: break
        # Retain every poll. A wait is not an attempt, but a claimed/released
        # launch identity cannot be reused without explicit reconciliation.
        n = len(list(root.glob('poll_*.json')))
        path = root/f'poll_{n:06d}.json'
        if path.exists(): raise RuntimeError('resource observation ledger sequence changed')
        from training_checkpoint import write_new
        write_new(path, record); atomic_json(root/'latest.json', record)
        return record
