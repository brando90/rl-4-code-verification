"""Wait for verified expansion, then dispatch the frozen replay continuation once."""
from __future__ import annotations
import argparse
from contextlib import ExitStack
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
import multinode_training as multi
from recovery_watch import ROOT, alive, identity, read, write

HERE = Path(__file__).resolve().parent
NEMO_PY = '/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'


def same_identity(left, right):
    return all(left.get(k) == right.get(k) and left.get(k) is not None
               for k in ('pid', 'boot_id', 'start_ticks'))


def transition(config, snapshot, now):
    """Pure gates: no stage completion is inferred from a disappearing process."""
    assert config['deadline_unix'] == snapshot['deadline_unix'], 'Original deadline changed'
    assert now < config['deadline_unix'], 'Original deadline reached'
    if snapshot['r_admission']:
        return 'PRESERVE_R_ADMISSION'
    admission = snapshot['e_admission']
    assert admission['root'] == config['e_root']
    assert same_identity(admission['identity'], config['e_identity']), 'Expansion identity changed'
    receipt = snapshot['e_receipt']
    if receipt:
        assert same_identity(receipt['identity'], config['e_identity']), 'Expansion receipt identity mismatch'
        if receipt.get('exit_code') is not None:
            assert receipt['exit_code'] == 0, 'Expansion native failure; no automatic replay'
        else:
            assert snapshot['e_alive'], 'Expansion disappeared without a terminal receipt'
            return 'WAIT_EXPANSION'
    else:
        assert snapshot['e_alive'], 'Expansion disappeared without a receipt'
        return 'WAIT_EXPANSION'
    result = snapshot['e_result']
    if not result:
        assert snapshot['e_coordinator_alive'], 'Expansion coordinator disappeared before cleanup receipt'
        return 'WAIT_EXPANSION_CLEANUP'
    assert result['status'] == 'PASS' and result['root'] == config['e_root'], 'Expansion route failed'
    assert set(result['transport_exits']) == set(multi.DEVICE_PLAN)
    assert all(code == 0 for code in result['transport_exits'].values())
    assert set(result['cleanup']) == set(multi.DEVICE_PLAN)
    assert all(r['status'] == 'STOPPED' and r['remaining_children'] == []
               and r['watchdog_exit_code'] is not None for r in result['cleanup'].values())
    assert all(r['root'] == config['e_root'] and r['status'] == 'RELEASED'
               for r in snapshot['participants']), 'Expansion leases not released'
    assert len(snapshot['participants']) == 3 and snapshot['local_lease_released']
    assert snapshot['scheduler_alive'], 'Phase B scheduler unavailable'
    verification = snapshot['jobs'].get('verify_E_14b', {})
    assert verification.get('status') != 'FAILED', 'Expansion verification failed'
    if verification.get('status') != 'DONE':
        return 'WAIT_EXPANSION_VERIFICATION'
    verified_exit = snapshot['verify_receipt']
    assert same_identity(verified_exit['identity'], verification['identity'])
    assert verified_exit['exit_code'] == verification['exit_code'] == 0
    replay = snapshot['jobs'].get('train_R_14b', {})
    assert replay.get('status') != 'FAILED', 'Replay controller failed'
    if not replay:
        return 'WAIT_REPLAY_CONTROLLER'
    assert replay['status'] == 'RUNNING' and snapshot['r_controller_alive'], 'Replay controller unavailable'
    return 'CHECK_CAPACITY'


def checked_sources(config):
    for relative, expected in config['source_sha256'].items():
        assert hashlib.sha256((HERE / relative).read_bytes()).hexdigest() == expected, relative


def snapshot(config):
    admission = read(multi.RUNTIME / 'remote_E_14b.json')
    phase = read(ROOT / 'phase_b_state.json')
    jobs = phase['jobs']; verify = jobs.get('verify_E_14b', {})
    replay = jobs.get('train_R_14b', {})
    registry = read(multi.LOCAL_PIPELINE / 'leases.json')
    return {
        'deadline_unix': read(ROOT / 'recovery_config.json')['recovery_deadline_unix'],
        'r_admission': read(multi.RUNTIME / 'remote_R_14b.json', {}),
        'e_admission': admission, 'e_receipt': read(Path(admission['receipt']), {}),
        'e_alive': alive(admission['identity']),
        'e_result': read(Path(config['e_root']) / 'result.json', {}),
        'e_coordinator_alive': alive(config['e_coordinator']),
        'participants': [read(multi.RUNTIME / f'remote_multinode_E_14b_{host}.json', {})
                         for host in multi.DEVICE_PLAN],
        'local_lease_released': registry.get('e08-v3-multinode-' + Path(config['e_root']).name, {}).get('released', False),
        'scheduler_alive': alive(config['scheduler']), 'jobs': jobs,
        'verify_receipt': read(Path(verify['exit_receipt']), {}) if verify.get('exit_receipt') else {},
        'r_controller_alive': alive(replay.get('identity', {})),
    }


def capacity(deadline):
    """Read under the normal locks; the real dispatch repeats admission atomically."""
    sys.path.insert(0, str(HERE.parent / 'expt_v1/scripts'))
    import gpu_lease_e08 as leases
    assert leases.P == multi.LOCAL_PIPELINE
    with ExitStack() as stack:
        for path in (multi.E13 / 'registry.lock', leases.LOCK, multi.RUNTIME / 'remote_admission.lock'):
            multi.acquire(stack, path, min(deadline, time.time() + 20))
        if (multi.RUNTIME / 'remote_R_14b.json').exists():
            return 'PRESERVE_R_ADMISSION'
        inventories = {host: multi.inspect_host(host) for host in multi.DEVICE_PLAN}
        try:
            multi.select_devices(inventories, read(multi.E13 / 'registry.json')['leases'],
                                 leases.live_leases(leases.load()), multi.live_remote_reservations())
        except multi.WaitingCapacity as error:
            return 'WAIT_CAPACITY: ' + str(error)
    return 'READY'


def dispatch_once(config, state, path):
    assert not state.get('dispatch_claim'), 'Prior dispatch requires reconciliation; never replay automatically'
    assert time.time() < config['deadline_unix']
    if (multi.RUNTIME / 'remote_R_14b.json').exists():
        state['status'] = 'PRESERVE_R_ADMISSION'; write(path, state)
        return None
    receipt = ROOT / 'multinode_R_14b_sequence_recovery02.exit.json'
    assert not receipt.exists(), 'Prior replay receipt exists'
    state.update(status='DISPATCH_CLAIMED', dispatch_claim={'claimed_unix': time.time(), 'receipt': str(receipt)})
    write(path, state)  # A crash here requires explicit reconciliation, never a second launch.
    with (ROOT / 'multinode_R_14b_sequence_recovery02.log').open('a') as log:
        process = subprocess.Popen(['/usr/bin/python3', str(HERE / 'job_process.py'), '--receipt', str(receipt),
                                    '--', NEMO_PY, str(HERE / 'multinode_training.py'), 'R'],
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    state.update(status='REPLAY_DISPATCHED', child=identity(process.pid))
    write(path, state)
    return process


def run(config_path):
    config = read(config_path); path = ROOT / 'multinode_sequence_recovery02_state.json'
    with (ROOT / 'multinode_sequence_recovery02.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = read(path, {})
        assert not state.get('dispatch_claim'), 'Prior dispatch retained; reconcile before any continuation'
        assert state.get('status') not in ('BLOCKED', 'REPLAY_NATIVE_FINISHED', 'PRESERVE_R_ADMISSION')
        state.update(status='STARTING', identity=identity(os.getpid()), config=str(config_path),
                     deadline_unix=config['deadline_unix'], started_unix=time.time())
        write(path, state)
        try:
            while time.time() < config['deadline_unix']:
                checked_sources(config)
                status = transition(config, snapshot(config), time.time())
                if status == 'CHECK_CAPACITY':
                    status = capacity(config['deadline_unix'])
                state.update(status=status, checked_unix=time.time()); write(path, state)
                if status == 'PRESERVE_R_ADMISSION':
                    return state
                if status == 'READY':
                    # Recheck the non-capacity gates after potentially slow SSH inventory.
                    assert transition(config, snapshot(config), time.time()) in ('CHECK_CAPACITY', 'PRESERVE_R_ADMISSION')
                    process = dispatch_once(config, state, path)
                    if process is None:
                        return state
                    while process.poll() is None and time.time() < config['deadline_unix']:
                        time.sleep(min(10, max(0, config['deadline_unix'] - time.time())))
                    receipt = read(Path(state['dispatch_claim']['receipt']), {})
                    assert same_identity(receipt.get('identity', {}), state['child'])
                    assert process.poll() == receipt.get('exit_code') == 0, 'Replay failed or deadline reached; no retry'
                    admitted = read(multi.RUNTIME / 'remote_R_14b.json')
                    finished = read(Path(admitted['root']) / 'result.json')
                    assert finished['status'] == 'PASS', 'Replay route cleanup requires reconciliation'
                    assert same_identity(finished['native_exit']['identity'], admitted['identity'])
                    assert finished['native_exit']['exit_code'] == 0
                    state.update(status='REPLAY_NATIVE_FINISHED', ended_unix=time.time()); write(path, state)
                    return state
                time.sleep(min(30, max(0, config['deadline_unix'] - time.time())))
            raise TimeoutError('Original deadline reached')
        except BaseException as error:
            state.update(status='BLOCKED', error=f'{type(error).__name__}: {error}', checked_unix=time.time())
            write(path, state)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    print(run(args.config))
