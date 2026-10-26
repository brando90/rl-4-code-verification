"""Poll idle devices under published per-gate and per-attempt limits without admitting a gate statistic."""
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
from technical_ledger import pilot_lock
from training_checkpoint import digest

RUN_KEY = re.compile(r'(T[1-4])/([1-3])/([a-z][a-z0-9_]*)')


def limits(allocation, gate):
    caps = allocation['technical_gate_caps']
    if set(caps) != {'T1', 'T2', 'T3', 'T4'}:
        raise ValueError('all technical gate limits must be frozen')
    for entry in caps.values():
        values = [entry[k] for k in ('per_attempt_device_hours', 'cumulative_device_hours')]
        if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in values):
            raise ValueError('invalid technical gate device-hour limit')
        if values[0] > values[1]: raise ValueError('attempt limit exceeds cumulative gate limit')
    if gate not in caps: raise ValueError('unknown technical gate')
    return caps[gate]


def remaining(registry, allocation, allocation_sha, gate, attempt):
    """Count all health leases and failed launches, retaining other attempts' costs."""
    cap = limits(allocation, gate)
    if type(attempt) is not int or not 1 <= attempt <= 3:
        raise ValueError('technical attempt outside A4 allowance')
    spent, reserved = accounting(registry, 'v2-S2-technical', allocation_sha)
    gate_used = attempt_used = 0.
    keys = set()
    for row in registry['leases']:
        if row.get('phase') != 'v2-S2-technical': continue
        match = RUN_KEY.fullmatch(row['run_key'])
        if match is None or row['run_key'] in keys:
            raise ValueError('technical lease history has invalid or duplicate execution identities')
        keys.add(row['run_key'])
        value = float(row['device_hours'] if row['status'] == 'RELEASED' else row['reserved_device_hours'])
        if match[1] == gate:
            gate_used += value
            if int(match[2]) == attempt: attempt_used += value
    return {'allocation_hours': allocation['cumulative_device_hours']-spent-reserved,
            'gate_hours': cap['cumulative_device_hours']-gate_used,
            'attempt_hours': cap['per_attempt_device_hours']-attempt_used,
            'run_keys': keys}


@contextmanager
def dispatch_fence(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    with (root/'technical_resources.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def reserve(plan, *, gate, attempt, stage_key, seconds):
    """One poll and claim; busy devices return WAIT and never consume a numbered attempt."""
    lock, science_sha = pilot_lock(plan['LP'], plan['repository'])
    allocation, allocation_sha = verify_allocation(plan['allocation_plan'])
    if (allocation['phase'] != 'v2-S2-technical'
            or lock['science']['resource_caps']['technical_allocation_sha256'] != allocation_sha):
        raise ValueError('technical allocation differs from the pilot science lock')
    bound = {str(Path(r['path']).resolve()): r['sha256'] for r in lock['bindings']}
    for path in (Path(__file__).resolve(), HERE/'resource_lease.py', HERE.parent/'phase1/device_watch.py'):
        if bound.get(str(path)) != digest(path): raise ValueError('unbound resource polling implementation')
    from reservation_observations import reconcile
    allocation = reconcile(allocation, lock)
    for key in ('lease_root', 'resource_poll_root'):
        if Path(plan[key]).resolve() != Path(lock['configuration'][key]).resolve():
            raise ValueError('resource registry or observation ledger moved')
    run_key = f'{gate}/{attempt}/{stage_key}'
    if RUN_KEY.fullmatch(run_key) is None or type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 90:
        raise ValueError('invalid bounded technical stage')
    root = Path(plan['resource_poll_root'])
    with dispatch_fence(root):
        registry = json.loads((Path(plan['lease_root'])/'registry.json').read_text())
        available = remaining(registry, allocation, allocation_sha, gate, attempt)
        if run_key in available.pop('run_keys'):
            raise RuntimeError('stage already claimed a lease; reconcile it without an automatic retry')
        record = {'condition': 'v2-S2', 'gate': gate, 'prospective_attempt': attempt,
                  'stage_key': stage_key, 'science_sha256': science_sha,
                  'admission_statistics_computed': False, 'remaining_device_hours': available,
                  'device_claims': 0, 'observations': [], 'candidate_rejections': []}
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
