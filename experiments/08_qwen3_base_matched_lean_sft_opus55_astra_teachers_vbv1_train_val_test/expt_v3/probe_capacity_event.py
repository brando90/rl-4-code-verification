"""Wake a released capacity-wait owner only when an eligible alternate route appears."""
from __future__ import annotations

import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import subprocess
import time

from recovery_watch import ROOT, optional_record, read, write

SLURM_NODES = {f'ampere{i}' for i in (1, 2, 3, 4, 5, 6, 8, 9)} | {'blackwell1'}


def current_wait(root, now):
    """Never probe for an unarmed, stale or deadline-expired ownership release."""
    wait = optional_record(root / 'external_resource_wait.json')
    config = optional_record(root / 'recovery_config.json')
    ack = optional_record(root / 'owner_ack.json')
    release = optional_record(root / 'owner_handoff.json')
    state = optional_record(root / 'recovery_state.json')
    attempts = state.get('attempts', [])
    latest = attempts[-1] if isinstance(attempts, list) and attempts and isinstance(attempts[-1], dict) else {}
    deadline, started, recorded = config.get('recovery_deadline_unix'), latest.get('started_unix'), wait.get('recorded_unix')
    if not all(type(v) in (int, float) and math.isfinite(v) for v in (deadline, started, recorded, now)):
        return None
    expected = wait.get('expected_remote_admissions')
    if not (wait.get('schema') == 1 and wait.get('status') == 'EXTERNAL_RESOURCE_WAIT'
            and wait.get('independent_work_complete') is True
            and wait.get('admissions_absent_at_recording') is True
            and release.get('released') is True and release.get('mode') == 'EXTERNAL_RESOURCE_WAIT'
            and bool(ack.get('owner')) and wait.get('owner') == ack['owner'] == release.get('owner')
            and bool(latest.get('attempt'))
            and wait.get('attempt') == ack.get('attempt') == release.get('attempt') == latest['attempt']
            and wait.get('deadline_unix') == deadline and started <= recorded <= now < deadline
            and isinstance(expected, list) and bool(expected)
            and all(isinstance(name, str) and re.fullmatch(
                r'remote_(?:[ER]_(?:8b|14b)|gen_v3_[ER]_(?:8b|14b)_f(?:0p5|1p0))\.json', name)
                    for name in expected)
            and isinstance(wait.get('phase_snapshot'), dict) and set(wait['phase_snapshot']) == {'a', 'b'}):
        return None
    return wait


def local_four_devices():
    """Observe the existing local admission predicate; allocation is still atomic later."""
    from run_with_devices import leases
    foreign = Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases')
    with (foreign / 'registry.lock').open('a') as f, leases.LOCK.open('a') as g:
        fcntl.flock(f, fcntl.LOCK_SH | fcntl.LOCK_NB)
        fcntl.flock(g, fcntl.LOCK_SH | fcntl.LOCK_NB)
        e13 = read(foreign / 'registry.json')
        reserved = {r['index'] for r in e13['leases']
                    if r['status'] != 'RELEASED' and r['host'].split('.')[0] == 'skampere1'}
        reserved |= {gpu for r in leases.live_leases(leases.load()).values() for gpu in r['gpus']}
        table = leases.gpu_table()
        available = sorted(i for i, owners in table.items() if not owners and i not in reserved)
        candidates = [i for i in available if i != 0]
    return {'eligible': len(available) >= 5 and len(candidates) >= 4,
            'host': 'skampere1', 'requested_devices': 4, 'available': available,
            'candidates': candidates, 'requires_atomic_admission': True}


def parse_slurm(accounts, nodes):
    association = any(re.fullmatch(r'\s*\S+\s+brando9\s+infolab\s*', line)
                      for line in accounts.splitlines())
    eligible = []
    inventory = []
    for line in nodes.splitlines():
        fields = dict(re.findall(r'(\w+)=([^\s]+)', line))
        name = fields.get('NodeName')
        if name not in SLURM_NODES:
            continue
        state = fields.get('State')
        gres = fields.get('Gres', '')
        gpu_match = re.fullmatch(r'gpu:(a100|b200):8(?:\([^)]*\))?', gres)
        inventory.append({'node': name, 'state': state, 'gres': gres})
        if state == 'IDLE' and gpu_match:
            eligible.append(name)
    if not inventory:
        raise ValueError('No recognized eligible-hardware nodes in Slurm response')
    return {'eligible': association and bool(eligible), 'association_present': association,
            'idle_eight_gpu_nodes': sorted(eligible), 'inventory': sorted(inventory, key=lambda r: r['node']),
            'requires_allocation_and_preparation': True}


def slurm_route():
    # One SSH connection per 15-minute host cron, no allocations or model calls.
    code = ('import json,subprocess; print(json.dumps({k: subprocess.check_output(v,text=True) '
            'for k,v in {"accounts":["showaccount"],"nodes":["scontrol","show","nodes","-o"]}.items()}))')
    command = shlex.join(['python3', '-c', code])
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'ilc', command],
                            capture_output=True, text=True, timeout=45, check=True)
    native = json.loads(result.stdout)
    return parse_slurm(native['accounts'], native['nodes'])


def observe(root=ROOT, now=None, local_probe=local_four_devices, slurm_probe=slurm_route, clock=time.time):
    now = clock() if now is None else now
    with (root / 'capacity_event_probe.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'LOCKED'}
        wait = current_wait(root, now)
        if wait is None:
            return {'status': 'UNARMED_OR_EXPIRED'}
        observation = {'observed_unix': now, 'attempt': wait['attempt'], 'routes': {}, 'errors': {}}
        pending = wait['expected_remote_admissions']
        pending_local = any(re.fullmatch(r'remote_(?:[ER]_8b|gen_v3_[ER]_(?:8b|14b)_f(?:0p5|1p0))\.json', name)
                         for name in pending)
        for name, probe in [('local_four_devices', local_probe), ('slurm', slurm_probe)]:
            if name == 'local_four_devices' and not pending_local:
                continue
            try:
                observation['routes'][name] = probe()
            except Exception as exc:
                observation['errors'][name] = f'{type(exc).__name__}: {exc}'
        # Only actionable eligibility enters the stable event fingerprint. No clock,
        # poll counter, unavailable-device churn or error message can wake a model.
        route = {'eligible': False, 'alternates': {}}
        for name, result in observation['routes'].items():
            if result['eligible']:
                route['alternates'][name] = ({'host': 'skampere1', 'devices': 4} if name == 'local_four_devices'
                                             else {'nodes': result['idle_eight_gpu_nodes'], 'account': 'infolab'})
        route['eligible'] = bool(route['alternates'])
        fingerprint = hashlib.sha256(json.dumps(route, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        # Serialize the final fence with owner recovery; neither an expired wait nor
        # a changed owner can receive an event from this prior observation.
        with (root / 'recovery.lock').open('a') as recovery_lock:
            try:
                fcntl.flock(recovery_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return {'status': 'RECOVERY_LOCKED'}
            if current_wait(root, clock()) != wait:
                return {'status': 'STALE_BEFORE_WRITE'}
            previous_path = root / 'external_capacity_event.json'
            previous = optional_record(previous_path)
            if previous_path.exists() and (type(previous.get('sequence')) is not int or previous['sequence'] < 0):
                return {'status': 'INVALID_PREVIOUS_EVENT'}
            sequence = previous.get('sequence', 0) + (fingerprint != previous.get('fingerprint'))
            event = {'route': route, 'fingerprint': fingerprint, 'sequence': sequence, 'observed_unix': now,
                     'attempt': wait['attempt'], 'deadline_unix': wait['deadline_unix']}
            write(root / 'external_capacity_event.json', event)
            write(root / 'capacity_event_observation.json', observation)
        return {'status': 'OBSERVED', **event}


if __name__ == '__main__':
    print(json.dumps(observe()))
