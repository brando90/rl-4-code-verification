"""Observe experiment and owner identities; recover a dead writer through a bounded CLI inventory."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2) + '\n')
    tmp.replace(path)


def identity(pid):
    """Return boot and start identity; zombies are dead, reused PIDs never match."""
    try:
        stat = Path(f'/proc/{pid}/stat').read_text()
        fields = stat[stat.rfind(')') + 2:].split()
        if fields[0] == 'Z':
            return None
        return {'pid': int(pid), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'start_ticks': fields[19]}
    except (FileNotFoundError, ProcessLookupError):
        return None


def alive(record):
    current = identity(record['pid']) if record else None
    return bool(current and all(str(current[k]) == str(record.get(k)) for k in current))


def phase_observation(root, phase, now):
    path = root / f'phase_{phase}_state.json'
    state = read(path, {})
    if not state:
        return {'status': 'NOT_STARTED', 'jobs': {}}
    jobs = {}
    for key, job in state.get('jobs', {}).items():
        status = job.get('status')
        rec = job.get('identity')
        if status == 'RUNNING':
            # Legacy scheduler records PID only: observation may flag death but never kill/restart it.
            live = alive(rec) if rec else bool(identity(job.get('pid', 0)))
            status = 'RUNNING' if live else 'CHILD_DEAD'
        log = root / f'phase_{phase}_logs/{key}.log'
        jobs[key] = {'status': status, 'pid': job.get('pid'), 'identity_verified': bool(rec),
                     'log_age_seconds': now - log.stat().st_mtime if log.exists() else None}
    latest = []
    for pattern in ('ckpt/*/driver_logs/*.log', 'ckpt/*/logs/**/events.out.tfevents.*',
                    'ladder/validation/raw/*.jsonl', 'ladder/validation/logs/*.log',
                    'namespace_diagnostic/*/*/*/*.json'):
        latest.extend(p.stat().st_mtime for p in root.glob(pattern))
    return {'status': state.get('status'), 'scheduler_pid': state.get('pid'),
            'scheduler_alive': alive(state['identity']) if state.get('identity') else bool(identity(state.get('pid', 0))),
            'heartbeat_age_seconds': now - path.stat().st_mtime,
            'work_progress_age_seconds': now - max(latest) if latest else None,
            'analysis_error': state.get('analysis_error'), 'jobs': jobs}


def completed(root, here):
    """A success marker alone cannot complete the experiment."""
    receipt = read(root / 'completion_receipt.json', {})
    summary = read(here / 'results/validation_summary_v3.json', {})
    return bool(receipt.get('status') == 'COMPLETE' and receipt.get('published_commit')
                and receipt.get('notification_sent') and receipt.get('training_verified')
                and receipt.get('namespace_complete') and receipt.get('forecast_assessed')
                and summary.get('known_cells') == summary.get('declared_cells') == 17280
                and len(summary.get('systems', {})) == 16)


def tick(root, config, launch=True):
    now = time.time()
    here = Path(config['experiment'])
    state_path = root / 'recovery_state.json'
    state = read(state_path, {'attempts': [], 'incidents': []})
    ack = read(root / 'owner_ack.json', {})
    runner = read(root / 'recovery_owner_process.json', {})
    release = read(root / 'owner_handoff.json', {})
    owner_live = alive(ack.get('owner'))
    released = (release.get('released') is True and release.get('owner') == ack.get('owner')
                and release.get('attempt') == ack.get('attempt'))
    runner_live = alive(runner.get('identity'))
    phases = {p: phase_observation(root, p, now) for p in ('a', 'b')}
    issues = []
    for phase, obs in phases.items():
        if obs['status'] == 'NOT_STARTED':
            continue
        if obs.get('analysis_error'):
            issues.append(f'phase_{phase}:analysis_error')
        if obs['status'] not in ('DONE', 'COMPLETE') and not obs['scheduler_alive']:
            issues.append(f'phase_{phase}:scheduler_dead')
        if obs.get('heartbeat_age_seconds', 0) > 180:
            issues.append(f'phase_{phase}:stale_heartbeat')
        if obs.get('work_progress_age_seconds') is not None and obs['work_progress_age_seconds'] > 7200:
            if any(j['status'] == 'RUNNING' for j in obs['jobs'].values()):
                issues.append(f'phase_{phase}:stale_work_progress')
        for key, job in obs['jobs'].items():
            if job['status'] in ('FAILED', 'CHILD_DEAD'):
                issues.append(f'{key}:{job["status"]}')
    events = root / (f'{ack["attempt"]}_events.jsonl' if ack.get('attempt', '').startswith('recovery-') else 'owner_events.jsonl')
    owner_age = now - events.stat().st_mtime if events.exists() else None
    if owner_live and owner_age is not None and owner_age > 3600:
        issues.append('owner:stale_output_inspect_before_fencing')
    state.update(checked_unix=now, owner_alive=owner_live, owner_released=released,
                 recovery_runner_alive=runner_live, phase_observations=phases,
                 issues=issues, free_bytes=os.statvfs(root).f_bavail * os.statvfs(root).f_frsize)
    if completed(root, here):
        state['status'] = 'COMPLETE'
    elif runner_live or (owner_live and not released):
        state['status'] = 'OBSERVING_ISSUES' if issues else 'OBSERVING'
    else:
        # Recent tmux launch has not written its PID yet. Do not duplicate it.
        pending = state.get('pending_launch', {})
        if pending and now - pending['started_unix'] < 300:
            state['status'] = 'AWAITING_RECOVERY_PROCESS'
        elif now > config['recovery_deadline_unix']:
            state['status'] = 'RECOVERY_DEADLINE_REACHED'
        elif len(state['attempts']) >= config['max_recoveries']:
            state['status'] = 'RECOVERY_ATTEMPTS_EXHAUSTED'
        else:
            candidates = []
            for candidate in config['candidates']:
                used = sum(a['candidate'] == candidate['name'] for a in state['attempts'])
                if candidate['eligible'] and used < candidate['max_attempts']:
                    candidates.append(candidate)
            if not candidates:
                state['status'] = 'NO_VERIFIED_RECOVERY_ROUTE'
            elif launch:
                candidate = candidates[0]
                number = len(state['attempts']) + 1
                attempt = f'recovery-{number:02d}'
                session = f'{config.get("session_prefix", "codex-rl4cv-e08v3")}-{attempt}'
                record = {'attempt': attempt, 'candidate': candidate['name'],
                          'session': session, 'started_unix': now, 'reason': issues or ['owner_exited']}
                # Preserve exactly the continuation inputs at the handoff boundary.
                paths = ['CKPT_e08_v3.md', 'RUNBOOK_continuation_owner.md', 'PROTOCOL.md',
                         'results/sft_schedule_v3_E.json', 'results/sft_schedule_v3_R.json',
                         'forecasts/e08_v3_forecast.json']
                packet = {**record, 'input_hashes': {p: hashlib.sha256((here / p).read_bytes()).hexdigest() for p in paths}}
                write(root / 'recovery_dispatch.json', packet)
                state['attempts'].append(record)
                state['pending_launch'] = record
                state['status'] = 'RECOVERY_LAUNCHING'
                write(state_path, state)  # durable reservation precedes launch
                command = [config['python'], str(here / 'recovery_owner.py'), '--root', str(root),
                           '--candidate', candidate['name'], '--attempt', attempt]
                result = subprocess.run(['tmux', 'new-session', '-d', '-s', session, *command],
                                        capture_output=True, text=True, timeout=30)
                record['launch_returncode'] = result.returncode
                record['launch_stderr'] = result.stderr[-1000:]
                state['status'] = 'RECOVERY_STARTED_UNVERIFIED' if result.returncode == 0 else 'RECOVERY_LAUNCH_FAILED'
            else:
                state['status'] = 'RECOVERY_NEEDED'
    write(state_path, state)
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--observe-only', action='store_true')
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    with (args.root / 'recovery.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        state = tick(args.root, read(args.root / 'recovery_config.json'), not args.observe_only)
    print(json.dumps({k: state[k] for k in ('checked_unix', 'status', 'owner_alive', 'issues')}))


if __name__ == '__main__':
    main()
