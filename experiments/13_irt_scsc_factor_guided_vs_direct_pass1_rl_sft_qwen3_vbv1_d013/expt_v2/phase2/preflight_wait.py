"""Reconcile a device collision before any runtime or numbered gate admission, retaining every lease."""
from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path

from a6_technical_driver import authorize, dynamic_config, ORDER, reference
from technical_ledger import published, admit, check_preflight
from technical_resources import reserve
from technical_stage import prepare, launch_local
from training_checkpoint import digest, write_new
from anchor_storage import atomic_json
from costs import snapshot, stage_cost


def collision(dispatch):
    """Accept only the observed device guard before supervisor/runtime construction."""
    root = Path(dispatch)
    result = json.loads((root/'dispatch_result.json').read_text())
    cleanup = json.loads((root/'dispatch_cleanup.json').read_text())
    execution = json.loads((root/'execution.json').read_text())
    log = (root/'dispatch.log').read_text()
    if (execution.get('status') != 'PREFLIGHT_RESERVED' or execution.get('attempt') != 0
            or execution.get('admission_statistics_computed') is not False
            or result.get('exit_code') != 1 or result.get('supervisor_receipt') is not None
            or result.get('cleanup_verified') is not True or cleanup.get('verified') is not True
            or result.get('released', {}).get('status') != 'RELEASED'
            or (root/'supervisor').exists()
            or not log.rstrip().endswith('RuntimeError: another execution now occupies the leased device')
            or 'check_lease(config)' not in log):
        raise ValueError('not a verified pre-runtime device collision')
    return result


def tick(plan, recovery):
    lock, config, science = authorize(plan)
    fix = published(recovery, plan['repository'])
    if (fix.get('gate') != 'PREFLIGHT_DEVICE_WAIT' or fix.get('status') != 'FROZEN'
            or fix.get('LP') != plan['LP'] or fix.get('science_sha256') != science
            or fix.get('technical_gate') != plan['gate'] or fix.get('prospective_attempt') != plan['attempt']):
        raise ValueError('published unchanged-science wait reconciliation required')
    bound = {r['path']: r['sha256'] for r in fix['bindings']}
    if bound.get(str(Path(__file__).resolve())) != digest(__file__):
        raise ValueError('wait reconciliation implementation unbound')
    if any(digest(p) != sha for p, sha in bound.items()):
        raise ValueError('wait reconciliation evidence changed')
    gate = plan['gate']; root = Path(config['work_root'])/gate/f"attempt_{plan['attempt']}"
    with (root/'controller.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = root/'state.json'; state = json.loads(path.read_text())
        ledger = Path(lock['configuration']['technical_ledger'])/gate
        if (state.get('status') != 'HALTED' or state.get('next_stage') != 'preflight'
                or 'admission' in state or list(ledger.glob('attempt_*/attempt.json'))
                or state.get('LP_sha256') != plan['LP']['sha256']
                or state.get('configuration_sha256') != digest(plan['configuration'])):
            raise ValueError('only unadmitted preflight collisions may return to waiting')
        prior = Path(state.get('preflight_wait_dispatch', str(root/'preflight/dispatch')))
        collision(prior)
        polls = root/'preflight_wait'; polls.mkdir(exist_ok=True)
        if any(not (p/'terminal.json').exists() for p in polls.glob('poll_*')):
            raise RuntimeError('prior wait poll needs receipt reconciliation; never replay it')
        number = len(list(polls.glob('poll_*')))
        folder = polls/f'poll_{number:04d}'; folder.mkdir()
        write_new(folder/'before.json', state)
        seconds = config['stage_seconds'][gate]['preflight']
        resource = {**plan['resource_plan'], 'LP': plan['LP'], 'repository': plan['repository']}
        reserved = reserve(resource, gate=gate, attempt=plan['attempt'],
                           stage_key=f'preflight_wait_{number:04d}', seconds=seconds)
        write_new(folder/'reservation.json', reserved)
        if reserved['status'] in ('WAIT_FOR_IDLE_DEVICE', 'DEVICE_CHANGED_BEFORE_LAUNCH'):
            result = {'status': 'WAIT_FOR_IDLE_DEVICE', 'numbered_attempt_admitted': False}
            write_new(folder/'terminal.json', result)
            return result
        if reserved['status'] != 'RESERVED':
            write_new(folder/'terminal.json', reserved)
            return reserved
        lease = reserved['lease']; before = snapshot(root)
        try:
            runtime = dynamic_config(config, gate, 'preflight', folder, lease)
            stage_plan = prepare(LP=plan['LP'], repository=plan['repository'], gate=gate,
                stage_key='preflight', config_path=runtime, maximum_seconds=seconds,
                preparation_root=folder/'preflight/dispatch')
            result = launch_local(stage_plan, lease_root=resource['lease_root'],
                                  route_environment=config['environment'])
        finally:
            from resource_lease import release
            from lp1 import cleanup
            canonical_path = Path(resource['lease_root'])/(lease['id']+'.json')
            canonical = json.loads(canonical_path.read_text())
            if canonical['status'] != 'RELEASED':
                cleaned = cleanup(lease['id'])
                release(resource['lease_root'], lease['id'], cleanup_verified=cleaned['verified'])
            else:
                cp = folder/'preflight/dispatch/dispatch_cleanup.json'
                cleaned = json.loads(cp.read_text()) if cp.exists() else None
            canonical = json.loads(canonical_path.read_text())
            write_new(root/'costs'/f'preflight_wait_{number:04d}.json',
                stage_cost(before, snapshot(root), stage='preflight', lease=canonical, cleanup=cleaned))
        if result['status'] != 'RUNTIME_FINISHED':
            # Re-enter waiting only when the same no-runtime collision is proven.
            collision(folder/'preflight/dispatch')
            state['preflight_wait_dispatch'] = str(folder/'preflight/dispatch')
            state['stage_result'] = result
            atomic_json(path, state)
            result = {'status': 'WAIT_FOR_IDLE_DEVICE', 'numbered_attempt_admitted': False}
            write_new(folder/'terminal.json', result)
            return result
        health = reference(folder/'preflight/health/preflight.json'); check_preflight(health)
        attempt_root, admitted = admit(lock['configuration']['technical_ledger'], gate,
            LP=plan['LP'], repository=plan['repository'], preflight=health,
            prerequisites=plan['prerequisites'], successor=plan.get('successor'))
        if admitted['attempt'] != plan['attempt']:
            raise ValueError('numbered admission changed')
        state.update(status='READY', next_stage=ORDER[gate][0], last_stage='preflight',
            preflight=health, admission=str(attempt_root/'attempt.json'), preflight_wait_lock=recovery)
        state.pop('stage_result', None)
        atomic_json(path, state)
        write_new(folder/'completion.json', {'status': 'PREFLIGHT_RECOVERED', 'admission': state['admission'],
                                           'admission_statistics_computed': False})
        result = {'status': 'PREFLIGHT_RECOVERED', 'numbered_attempt_admitted': True}
        write_new(folder/'terminal.json', result)
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--recovery', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(tick(json.loads(args.plan.read_text()), json.loads(args.recovery.read_text()))))
