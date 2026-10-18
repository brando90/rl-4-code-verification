#!/usr/bin/env python3
"""Reconcile the dead expansion-14B admission and relaunch it when its eight devices are free.

Brando approved this on 10-18-2026. The half-segment checkpoint does not exist, so training
starts again from the step-658 weights. Token budgets, device layout and sampling stay frozen.
"""
from __future__ import annotations

import json
import os
import socket
from contextlib import ExitStack
from pathlib import Path
import shutil
import subprocess
import sys
import time

CODE = Path('/lfs/skampere1/0/brando9/rl4cv_e08/wt_v3/rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3')
ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')
RUNTIME = Path('/dfs/scratch0/brando9/rl4cv_e08_v3_remote/sft_v3')
OLD_DEADLINE = 1792383686.05276
NEW_DEADLINE = 1793593286.05276  # 11-01-2026 21:21 PDT
LEASE = 'e08-v3-multinode-multinode_E_14b_1792159855671537768'
MULTINODE_ROOT = RUNTIME / 'multinode_E_14b_1792159855671537768'
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE.parent / 'expt_v1/scripts'))

from recovery_watch import alive, read, write  # noqa: E402
import multinode_training as multi  # noqa: E402


def log(message):
    stamp = time.strftime('%m-%d-%Y %H:%M:%S %Z')
    line = f'{stamp} {message}'
    print(line, flush=True)
    with (ROOT / 'resume_e14_after_oom.log').open('a') as stream:
        stream.write(line + '\n')


def extend_deadlines():
    """Move only the wall-clock recovery deadline. Scientific caps stay in the frozen protocol."""
    config = read(ROOT / 'recovery_config.json')
    assert config['recovery_deadline_unix'] in (OLD_DEADLINE, NEW_DEADLINE)
    config['recovery_deadline_unix'] = NEW_DEADLINE
    config['deadline_extension_10_18_2026'] = {
        'previous_unix': OLD_DEADLINE,
        'new_unix': NEW_DEADLINE,
        'new_human': '11-01-2026 21:21 PDT',
        'authorized': 'Brando 10-18-2026: do it all, I approve all',
        'scientific_caps_unchanged': True,
    }
    write(ROOT / 'recovery_config.json', config)
    arm = read(ROOT / 'native_continuation_arm.json')
    if arm.get('deadline_unix') in (OLD_DEADLINE, NEW_DEADLINE):
        arm['deadline_unix'] = NEW_DEADLINE
        write(ROOT / 'native_continuation_arm.json', arm)
    sequence = read(ROOT / 'multinode_sequence_recovery02_config.json')
    if sequence.get('deadline_unix') in (OLD_DEADLINE, NEW_DEADLINE):
        sequence['deadline_unix'] = NEW_DEADLINE
        sequence['deadline_extension_note'] = 'Wall-clock only; replay still waits for a successful expansion.'
        write(ROOT / 'multinode_sequence_recovery02_config.json', sequence)
    log('deadline extended to 11-01-2026 21:21 PDT')


def remote_dead(host, ident):
    pid = (ident or {}).get('pid')
    assert pid, f'{host} watchdog has no pid'
    if host in ('skampere1', socket.gethostname().split('.')[0]):
        assert not alive(ident), f'{host} watchdog still alive'
        return
    probe = subprocess.run(
        ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', host, f'test ! -d /proc/{int(pid)}'],
        capture_output=True, text=True, timeout=20)
    assert probe.returncode == 0, f'{host} watchdog pid {pid} still exists or could not be checked'


def reconcile_dead_admission():
    canonical = RUNTIME / 'remote_E_14b.json'
    if not canonical.exists():
        log('canonical admission already absent')
        return
    admission = read(canonical)
    assert admission.get('root') == str(MULTINODE_ROOT)
    assert not alive(admission.get('identity')), 'Expansion coordinator is still alive; refusing to reconcile'
    for host in multi.DEVICE_PLAN:
        participant = read(RUNTIME / f'remote_multinode_E_14b_{host}.json', {})
        if participant.get('root') == str(MULTINODE_ROOT):
            remote_dead(host, participant.get('identity'))
    command = ['pgrep', '-af', 'multinode_E_14b_1792159855671537768']
    found = subprocess.run(command, capture_output=True, text=True)
    leftovers = [line for line in found.stdout.splitlines() if 'resume_e14_after_oom' not in line and line.strip()]
    assert not leftovers, f'Owned multinode processes still exist: {leftovers}'
    preserved = ROOT / 'E14_oom_step183_preserved_10-18-2026'
    preserved.mkdir(exist_ok=True)
    for name in ('remote_E_14b.json', 'remote_E_14b.exit.json'):
        source = RUNTIME / name
        if source.exists():
            shutil.copy2(source, preserved / name)
    receipt = read(Path(admission['receipt']))
    assert receipt.get('exit_code') == 1
    assert receipt.get('identity') == admission.get('identity')
    archived = RUNTIME / 'remote_E_14b.admission.oom_step183.json'
    if not archived.exists():
        os.replace(canonical, archived)
    elif canonical.exists():
        archived_again = RUNTIME / f'remote_E_14b.admission.oom_step183.{time.time_ns()}.json'
        os.replace(canonical, archived_again)
    for host in multi.DEVICE_PLAN:
        path = RUNTIME / f'remote_multinode_E_14b_{host}.json'
        participant = read(path, {})
        if participant.get('root') == str(MULTINODE_ROOT) and participant.get('status') != 'RELEASED':
            participant.update(status='RELEASED', released_unix=time.time(),
                               reconciliation='10-18-2026 owner reconcile after CUDA OOM at step 183; watchdog dead')
            write(path, participant)
    import gpu_lease_e08 as leases
    with leases.LOCK.open('a') as lock:
        import fcntl
        fcntl.flock(lock, fcntl.LOCK_EX)
        registry = leases.load()
        lease = registry.get(LEASE)
        if lease and not lease.get('released'):
            identity = lease.get('identity') or {}
            assert leases.identity_alive(identity) is False, 'Multinode lease holder is still alive'
            lease.update(released=True, released_at=leases.ts(),
                         note=(lease.get('note') or '') + ' | released 10-18-2026 after dead OOM coordinator')
            leases.save(registry)
    write(preserved / 'reconciliation.json', {
        'status': 'RECONCILED', 'exit_code': 1, 'last_completed_step': 183, 'target_step': 335,
        'reason': 'CUDA out of memory on skampere3 during step 184; no step_335 checkpoint',
        'reconciled_unix': time.time(),
    })
    log('dead expansion admission reconciled and preserved')


def capacity():
    import fcntl
    import gpu_lease_e08 as leases
    with ExitStack() as stack:
        for path in (multi.E13 / 'registry.lock', leases.LOCK, RUNTIME / 'remote_admission.lock'):
            lock = stack.enter_context(path.open('a'))
            fcntl.flock(lock, fcntl.LOCK_EX)
        if (RUNTIME / 'remote_E_14b.json').exists():
            return 'CANONICAL_PRESENT'
        inventories = {host: multi.inspect_host(host) for host in multi.DEVICE_PLAN}
        try:
            multi.select_devices(inventories, read(multi.E13 / 'registry.json')['leases'],
                                 leases.live_leases(leases.load()), multi.live_remote_reservations())
        except multi.WaitingCapacity as error:
            return 'WAIT: ' + str(error)
    return 'READY'


def mark_running():
    admission = read(RUNTIME / 'remote_E_14b.json', {})
    if not admission or not alive(admission.get('identity')):
        return False
    state_path = ROOT / 'phase_b_state.json'
    state = read(state_path)
    job = state['jobs'].get('train_E_14b', {})
    job.update(status='RUNNING', pid=admission['identity']['pid'], identity=admission['identity'],
               key='train_E_14b', exit_receipt=admission['receipt'], started_unix=admission.get('started_unix', time.time()),
               attempt=int(job.get('attempt') or 1) + (0 if job.get('status') == 'RUNNING' else 1),
               command=['multinode_training.py', 'E'], resume_after_oom='step 183 lost; restarted from step_658')
    state['jobs']['train_E_14b'] = job
    state['failed_jobs'] = [key for key in state.get('failed_jobs', []) if key != 'train_E_14b']
    state['status'] = 'RUNNING'
    write(state_path, state)
    log('phase B records expansion 14B as RUNNING')
    return True


def notify_resume():
    receipt = CODE / 'results/email_e14_resume_10-18-2026.json'
    if receipt.exists():
        log('resume mail already recorded')
        return
    body = (
        'Expansion 14B for the matched Qwen3 Lean warm start was admitted again after the '
        '10-17-2026 22:03 PDT CUDA out-of-memory at step 183 of 335. No half-segment checkpoint '
        'existed, so this restarts from the step-658 weights toward step 335. The wall-clock '
        'recovery deadline is now 11-01-2026 21:21 PDT. Token budgets are unchanged. API spend remains $0.\n'
    )
    sys.path.insert(0, str(CODE))
    from notify_run import deliver, smtp_sender
    subject = '[RUN START] rl4cv-e08-v3 expansion 14B resume after out-of-memory'
    try:
        outcome = deliver(receipt, subject, body, smtp_sender())
        log(f'resume mail {outcome}')
    except Exception as error:
        log(f'resume mail not sent: {type(error).__name__}: {error}')


def main():
    assert time.time() < NEW_DEADLINE
    extend_deadlines()
    reconcile_dead_admission()
    while time.time() < NEW_DEADLINE:
        try:
            state = capacity()
        except Exception as error:
            log(f'capacity check failed: {type(error).__name__}: {error}')
            time.sleep(600)
            continue
        log(state)
        if state != 'READY':
            time.sleep(600)
            continue
        log('eight devices free; launching frozen multinode expansion 14B')
        launch_log = ROOT / 'resume_e14_launch.log'
        with launch_log.open('a') as stream:
            stream.write('\n----- launch -----\n')
            stream.flush()
            process = subprocess.Popen(
                ['/usr/bin/python3', str(CODE / 'multinode_training.py'), 'E'],
                cwd=str(CODE), stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            launched = time.time()
            notified = False
            while process.poll() is None and time.time() < NEW_DEADLINE:
                if not notified and mark_running():
                    notify_resume()
                    notified = True
                time.sleep(30)
        code = process.poll()
        log(f'multinode expansion exited {code}')
        if code == 0:
            return 0
        tail = launch_log.read_text(errors='replace')[-4000:]
        if time.time() - launched < 1200 and 'WaitingCapacity' in tail:
            log('capacity changed before admission; waiting')
            time.sleep(600)
            continue
        log('stopping after a non-capacity failure')
        return code if code is not None else 1
    log('recovery deadline reached before expansion 14B finished')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
