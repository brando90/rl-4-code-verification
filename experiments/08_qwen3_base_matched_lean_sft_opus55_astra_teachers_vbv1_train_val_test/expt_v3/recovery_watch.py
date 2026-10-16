"""Observe experiment and owner identities; recover a dead writer through a bounded CLI inventory."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
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
    basic = bool(receipt.get('status') == 'COMPLETE' and receipt.get('published_commit')
                and receipt.get('notification_sent') and receipt.get('training_verified')
                and receipt.get('namespace_complete') and receipt.get('forecast_assessed')
                and summary.get('known_cells') == summary.get('declared_cells') == 17280
                and len(summary.get('systems', {})) == 16)
    if not basic:
        return False
    try:
        validation_path = here / 'results/completion_validation_v3.json'
        mail_path = here / 'results/email_done_v3.json'
        validation, mail = read(validation_path, {}), read(mail_path, {})
        return bool(all(read(root / f'phase_{p}_state.json', {}).get('status') == 'DONE' for p in ('a', 'b'))
                    and receipt.get('final_tests', {}).get('status') == 'PASS'
                    and receipt.get('science_commit') and receipt.get('notification_commit') == receipt['published_commit']
                    and receipt.get('validation_sha256') == hashlib.sha256(validation_path.read_bytes()).hexdigest()
                    and receipt.get('email_sha256') == hashlib.sha256(mail_path.read_bytes()).hexdigest()
                    and validation.get('status') == 'VALIDATED' and validation.get('known_cells') == 17280
                    and validation.get('declared_cells') == 17280 and validation.get('systems') == 16
                    and mail.get('status') == 'SENT' and mail.get('all_recipients_accepted') is True
                    and mail.get('subject', '').endswith(': COMPLETE')
                    and mail.get('to') == 'brando.science@gmail.com'
                    and set(mail.get('cc', [])) == {'brandojazz@gmail.com', 'brando9@stanford.edu', 'brando@vals.ai'})
    except (OSError, ValueError, TypeError):
        return False


def resource_snapshot(root):
    """Ignore heartbeat/poll timestamps; retain execution and scheduler identities."""
    result = {}
    for phase in ('a', 'b'):
        state = read(root / f'phase_{phase}_state.json', {})
        result[phase] = {
            'status': state.get('status'), 'identity': state.get('identity'),
            'analysis_error': state.get('analysis_error'),
            'jobs': {key: {field: job.get(field) for field in
                           ('status', 'identity', 'exit_code', 'attempt')}
                     for key, job in state.get('jobs', {}).items()}}
    return result


def optional_record(path):
    """Optional wait metadata must never crash or disable ordinary recovery."""
    try:
        value = read(path, {})
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def resource_wait_observation(root, config, state, ack, release, issues, now):
    """Honor only a released owner's exact, finite, explicit capacity wait."""
    wait = optional_record(root / 'external_resource_wait.json')
    if not wait:
        return {'status': 'NOT_ARMED'}
    attempts = state.get('attempts', [])
    latest = attempts[-1] if attempts and isinstance(attempts[-1], dict) else {}
    expected = wait.get('expected_remote_admissions')
    valid = (
        wait.get('schema') == 1 and wait.get('status') == 'EXTERNAL_RESOURCE_WAIT'
        and wait.get('independent_work_complete') is True
        and wait.get('admissions_absent_at_recording') is True
        and release.get('released') is True and release.get('mode') == 'EXTERNAL_RESOURCE_WAIT'
        and bool(ack.get('owner')) and wait.get('owner') == ack.get('owner') == release.get('owner')
        and bool(latest.get('attempt')) and wait.get('attempt') == ack.get('attempt') == release.get('attempt') == latest['attempt']
        and wait.get('deadline_unix') == config['recovery_deadline_unix']
        and isinstance(wait.get('recorded_unix'), (int, float))
        and isinstance(latest.get('started_unix'), (int, float))
        and latest['started_unix'] <= wait['recorded_unix'] <= now < wait['deadline_unix']
        and isinstance(expected, list) and bool(expected)
        and all(isinstance(name, str) and re.fullmatch(
            r'remote_(?:[ER]_(?:8b|14b)|gen_v3_[ER]_(?:8b|14b)_f(?:0p5|1p0))\.json', name)
                for name in expected)
        and isinstance(wait.get('phase_snapshot'), dict) and set(wait['phase_snapshot']) == {'a', 'b'})
    if not valid:
        return {'status': 'INVALID_WAIT', 'reason': 'owner, attempt, release, deadline or schema mismatch'}
    # Capacity-idle controllers may have no useful scientific output for hours.
    # Every failure, dead process and unfinished-scheduler heartbeat still wakes recovery.
    urgent = [issue for issue in issues if not issue.endswith(':stale_work_progress')]
    if urgent:
        return {'status': 'WAKE', 'reason': 'execution_issue', 'issues': urgent}
    try:
        if resource_snapshot(root) != wait['phase_snapshot']:
            return {'status': 'WAKE', 'reason': 'execution_state_changed'}
    except (OSError, ValueError, TypeError):
        return {'status': 'WAKE', 'reason': 'execution_state_unreadable'}
    shared = Path(config.get('remote_runtime', '/dfs/scratch0/brando9/rl4cv_e08_v3_remote/sft_v3'))
    for name in expected:
        path = shared / name
        if path.exists():
            # This is a remote identity: never compare its PID to local /proc.
            remote = optional_record(path)
            ident = remote.get('identity')
            if not isinstance(ident, dict):
                ident = {}
            valid_remote = (remote.get('status') in ('RUNNING', 'DONE', 'DONE_RECONCILED')
                            and remote.get('host') in config.get('remote_hosts', ['skampere2', 'skampere3'])
                            and remote.get('gpus') and remote.get('receipt')
                            and all(ident.get(k) for k in ('pid', 'boot_id', 'start_ticks')))
            return {'status': 'WAKE', 'reason': 'remote_admitted' if valid_remote else 'remote_record_needs_inspection',
                    'record': name}
    baseline = wait.get('capacity_baseline')
    if not isinstance(baseline, dict):
        baseline = {}
    event = optional_record(root / 'external_capacity_event.json')
    route = event.get('route')
    if isinstance(route, dict) and route.get('eligible') is True:
        fingerprint = hashlib.sha256(json.dumps(route, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if (event.get('fingerprint') == fingerprint and isinstance(event.get('sequence'), int)
                and isinstance(baseline.get('sequence'), int) and event['sequence'] > baseline['sequence']
                and fingerprint != baseline.get('fingerprint')):
            return {'status': 'WAKE', 'reason': 'eligible_capacity_route_changed', 'fingerprint': fingerprint}
    return {'status': 'DEFER', 'reason': wait.get('reason'), 'expected_remote_admissions': expected}


def native_continuation_observation(root, config, ack, release, issues, now):
    """A tested ordinary-code publisher can own an explicitly released finite wait."""
    arm = optional_record(root / 'native_continuation_arm.json')
    native = optional_record(root / 'native_continuation_state.json')
    key = lambda r: {k: r.get(k) for k in ('pid', 'boot_id', 'start_ticks')}
    valid = (arm.get('schema') == 1 and arm.get('armed') is True and ack.get('owner')
             and key(arm.get('owner', {})) == key(ack['owner']) == key(release.get('owner', {}))
             and arm.get('attempt') == ack.get('attempt') == release.get('attempt')
             and release.get('released') is True and release.get('mode') == 'NATIVE_CONTINUATION'
             and arm.get('deadline_unix') == config['recovery_deadline_unix']
             and now < config['recovery_deadline_unix']
             and arm.get('max_recoveries') == config['max_recoveries']
             and arm.get('candidate_caps') == {c['name']: c['max_attempts'] for c in config['candidates']})
    if not valid:
        return {'status': 'NOT_ARMED'}
    if any(not issue.endswith(':stale_work_progress') for issue in issues):
        return {'status': 'NEEDS_RECOVERY', 'reason': 'native workload issue'}
    if native.get('status') == 'BLOCKED':
        return {'status': 'NEEDS_RECOVERY', 'reason': native.get('error', 'ambiguous notification')}
    if native.get('status') in ('MAIL_SENDING', 'NOTIFIED'):
        try:
            mail = read(Path(config['experiment']) / 'results/email_done_v3.json', {})
            valid_mail = (mail.get('status') == 'SENT' and mail.get('all_recipients_accepted') is True
                          and mail.get('subject') == '[RUN DONE] rl4cv-e08-v3-sft-continuation: COMPLETE'
                          and mail.get('body') == (root / 'completion_email_body.txt').read_text()
                          and mail.get('to') == 'brando.science@gmail.com'
                          and set(mail.get('cc', [])) == {'brandojazz@gmail.com', 'brando9@stanford.edu', 'brando@vals.ai'})
        except (OSError, ValueError, TypeError, KeyError):
            valid_mail = False
        if not valid_mail:
            return {'status': 'NEEDS_RECOVERY', 'reason': 'ambiguous notification'}
    if native.get('status') == 'RETRY_PUBLICATION' and not 0 < native.get('publication_failures', 0) < 3:
        return {'status': 'NEEDS_RECOVERY', 'reason': 'publication retry cap reached'}
    recent = native.get('checked_unix', arm.get('armed_unix', 0))
    if not isinstance(recent, (int, float)) or now - recent > 900:
        return {'status': 'NEEDS_RECOVERY', 'reason': 'native publisher heartbeat stale'}
    if native.get('status') not in (None, 'OWNER_ACTIVE', 'WAITING_NATIVE_WORK', 'WAITING_NATIVE_HANDOFF',
                                    'PUBLISHED_NATIVE_PROGRESS', 'RUNNING', 'MAIL_SENDING', 'NOTIFIED',
                                    'RETRY_PUBLICATION'):
        return {'status': 'NEEDS_RECOVERY', 'reason': native.get('status')}
    return {'status': 'DEFER', 'reason': 'finite tested native publication and closeout route'}


def tick(root, config, launch=True):
    now = time.time()
    here = Path(config['experiment'])
    state_path = root / 'recovery_state.json'
    state = read(state_path, {'attempts': [], 'incidents': []})
    ack = read(root / 'owner_ack.json', {})
    runner = read(root / 'recovery_owner_process.json', {})
    release = optional_record(root / 'owner_handoff.json')
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
        if obs['status'] not in ('DONE', 'COMPLETE') and obs.get('heartbeat_age_seconds', 0) > 180:
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
        resource_wait = resource_wait_observation(root, config, state, ack, release, issues, now)
        state['resource_wait_observation'] = resource_wait
        native_wait = native_continuation_observation(root, config, ack, release, issues, now)
        state['native_continuation_observation'] = native_wait
        # Recent tmux launch has not written its PID yet. Do not duplicate it.
        pending = state.get('pending_launch', {})
        if pending and now - pending['started_unix'] < 300:
            state['status'] = 'AWAITING_RECOVERY_PROCESS'
        elif now > config['recovery_deadline_unix']:
            state['status'] = 'RECOVERY_DEADLINE_REACHED'
        elif len(state['attempts']) >= config['max_recoveries']:
            state['status'] = 'RECOVERY_ATTEMPTS_EXHAUSTED'
        elif native_wait['status'] == 'DEFER':
            state['status'] = 'DEFERRED_NATIVE_CONTINUATION'
        elif owner_live and resource_wait['status'] in ('DEFER', 'WAKE'):
            state['status'] = 'AWAITING_RELEASED_OWNER_EXIT'
        elif resource_wait['status'] == 'DEFER':
            state['status'] = 'DEFERRED_EXTERNAL_RESOURCE'
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
