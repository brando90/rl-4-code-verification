#!/usr/bin/env python3
"""Restart only dead v3 pilot trajectories with the owner's own resume steps; never touch a live trajectory.

Why this exists: a pilot runner aborts by design when another user's process lands on its leased GPU,
because the hash-bound device guard cannot read a foreign `/proc/<pid>/environ` (PermissionError) and
must not share the device. The frozen admission binds `pilot_run.py` and `device_guard.py`, and every
completed update records the admission digest, so those files cannot change mid-pilot. This
supervisor therefore changes no bound file and no scientific setting. It only stops a death from
becoming a stall: each tick it applies the owner's archive / account / retry / launch steps
(`resume_pilot_after_foreign_gpu.py`) to trajectories with no live session or process, keeps the dead
pane's output as evidence, and stops restarting an update that keeps dying.

Safety (light QA 10-20-2026): probes fail closed; liveness is any tmux session, any process naming the
trajectory (runner, owner retry, or surviving stage process) and the runner's own controller.lock;
liveness is rechecked immediately before each action; attempts are reserved durably before acting.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get('E13V3_WORK', '/lfs/skampere1/0/brando9/rl4cv_e13v3'))
PILOT = WORK / 'phase2/pilot'
STATE = WORK / 'phase2/autoresume_state.json'
STATUS = WORK / 'phase2/autoresume_status.json'
LOG = WORK / 'phase2/autoresume.log'
DEATHS = WORK / 'phase2/autoresume_deaths'
LOCK = WORK / 'phase2/autoresume.lock'
PAUSED = WORK / 'phase2/autoresume_paused.json'
ARMS = ('A', 'B', 'P')
SEEDS = (1301, 1302)
GENERATIONS = 256
MAX_RESTARTS_PER_UPDATE = 3


class ProbeError(RuntimeError):
    """A liveness probe failed; the tick must not act on uncertain state."""


def paused_trajectories():
    """Absent means unchanged behavior; malformed pause state fails closed."""
    if not PAUSED.exists():return set()
    try:
        data=json.loads(PAUSED.read_text())
        names=data['trajectories']
        allowed={'A_1301','A_1302','B_1302','P_1301','P_1302'}
        if not isinstance(names,(list,dict)) or not set(names)<=allowed:
            raise ValueError('invalid V4-A3 pause list')
        return set(names)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        raise ProbeError('pause list unreadable or invalid') from exc


def pilot_session(arm, seed):
    return f'rl4cv-e13v3-pilot-{arm}-{seed}'


def retry_prefix(arm, seed):
    return f'rl4cv-e13v3-retry-{arm}-{seed}-u'


def decide(*, live, complete, partials, restarts, next_update):
    """Pure decision for one trajectory.

    partials: list of dicts for live update directories without summary.json, each with keys
      update, generations, scored, optimizer_result.
    restarts: mapping str(update) -> number of attempts this supervisor already reserved for it.
    Returns (action, update, detail) with action in
      skip | launch | account_then_launch | archive_then_launch | retry | diagnose.
    """
    if live:
        return ('skip', None, 'live session or process')
    if complete:
        return ('skip', None, 'trajectory complete')
    if len(partials) > 1:
        return ('diagnose', None, 'more than one partial update')
    if not partials:
        action, update, detail = 'launch', next_update, 'no partial update'
    else:
        p = partials[0]
        update = p['update']
        if p['optimizer_result']:
            action, detail = 'account_then_launch', 'optimizer result present, summary missing'
        elif p['generations'] == 0:
            action, detail = 'archive_then_launch', 'zero generations (infrastructure failure)'
        elif p['generations'] == GENERATIONS and p['scored']:
            if update == 1:
                return ('diagnose', update, 'update 1 optimizer retry unsupported by the owner helper '
                                            '(it reads update_00000/summary.json)')
            action, detail = 'retry', 'complete scored generation, optimizer step missing'
        else:
            return ('diagnose', update, f"partial or unscored generation ({p['generations']}/{GENERATIONS}); "
                                        'owner policy forbids automatic resampling')
    if restarts.get(str(update), 0) >= MAX_RESTARTS_PER_UPDATE:
        return ('diagnose', update, f'restart limit {MAX_RESTARTS_PER_UPDATE} reached for this update')
    return (action, update, detail)


def numbered_updates(root):
    """Live update directories only (archived attempts carry a longer suffix)."""
    return sorted((p for p in root.glob('update_*') if p.is_dir() and len(p.name) == 12 and p.name[7:].isdigit()),
                  key=lambda p: p.name)


def generation_count(work):
    output = work / 'generate/output'
    return len(list(output.glob('*.generation.json'))) if output.exists() else 0


def trajectory_state(arm, seed, pilot=None):
    pilot = PILOT if pilot is None else pilot
    root = pilot / f'{arm}_{seed}'
    updates = numbered_updates(root) if root.exists() else []
    partials = []
    for work in updates:
        if (work / 'summary.json').exists():
            continue
        partials.append({'update': int(work.name.split('_')[1]), 'generations': generation_count(work),
                         'scored': (work / 'score/groups.json').exists(),
                         'optimizer_result': (work / 'update/output/result.json').exists()})
    complete = any((root / f'result_{h}.json').exists() for h in (30, 60))
    last = max((int(w.name[7:]) for w in updates), default=0)
    return {'partials': partials, 'complete': complete, 'next_update': last + 1,
            'completed_updates': sum((w / 'summary.json').exists() for w in updates)}


def sessions(run=subprocess.run):
    """Map session name -> pane_dead. Fails closed: any tmux error other than 'no server' raises."""
    result = run(['tmux', 'list-sessions', '-F', '#{session_name}\t#{pane_dead}'], capture_output=True, text=True)
    if result.returncode != 0:
        if 'no server running' in (result.stderr or '') or 'error connecting' in (result.stderr or ''):
            return {}
        raise ProbeError(f'tmux list-sessions failed: {(result.stderr or "").strip()[:200]}')
    out = {}
    for line in result.stdout.splitlines():
        name, sep, dead = line.partition('\t')
        if not sep or dead.strip() not in ('0', '1'):
            raise ProbeError(f'unparseable tmux row: {line[:120]!r}')
        out[name] = dead.strip() == '1'
    return out


def trajectory_sessions(arm, seed, table):
    names = [n for n in table if n == pilot_session(arm, seed) or n.startswith(retry_prefix(arm, seed))]
    return {n: table[n] for n in names}


def trajectory_processes(arm, seed, run=subprocess.run):
    """Live processes naming this trajectory: its runner, an owner retry, or any surviving stage process."""
    pattern = (f'pilot_run\\.py --arm {arm} --seed {seed}( |$)|resume_pilot_after_foreign_gpu\\.py retry {arm} {seed} '
               f'|/phase2/pilot/{arm}_{seed}/')
    result = run(['pgrep', '-af', pattern], capture_output=True, text=True)
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        raise ProbeError(f'pgrep failed ({result.returncode})')
    return [line for line in result.stdout.splitlines() if line.strip() and 'autoresume_watchdog' not in line]


def full_resume_running(run=subprocess.run):
    """A full or targeted resume driver owns the tree while it runs; retry sessions do not count."""
    result = run(['pgrep', '-af', 'resume_pilot_after_foreign_gpu\\.py|e13v3_targeted_resume'],
                 capture_output=True, text=True)
    if result.returncode not in (0, 1):
        raise ProbeError(f'pgrep failed ({result.returncode})')
    for line in result.stdout.splitlines():
        if 'pgrep' in line:
            continue
        if 'e13v3_targeted_resume' in line or ('resume_pilot_after_foreign_gpu.py' in line and ' retry ' not in line):
            return True
    return False


def is_live(arm, seed, run=subprocess.run):
    """Return (live, dead_sessions). Raises ProbeError on any uncertain probe."""
    own = trajectory_sessions(arm, seed, sessions(run=run))
    if any(not dead for dead in own.values()):
        return True, []
    if trajectory_processes(arm, seed, run=run):
        return True, []
    return False, [name for name, dead in own.items() if dead]


def log(event):
    event = {'time': time.strftime('%m-%d-%Y %H:%M:%S %Z'), **event}
    with LOG.open('a') as stream:
        stream.write(json.dumps(event, sort_keys=True) + '\n')
    print(json.dumps(event, sort_keys=True), flush=True)


def write_atomic(path, text):
    tmp = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    tmp.write_text(text)
    os.replace(tmp, path)


def reserve_attempt(state, key, update):
    """Durably count an attempt before acting, so a crash mid-action cannot bypass the restart limit."""
    restarts = state.setdefault(key, {})
    restarts[str(update)] = restarts.get(str(update), 0) + 1
    write_atomic(STATE, json.dumps(state, indent=2, sort_keys=True) + '\n')
    return restarts[str(update)]


def preserve_dead(name, run=subprocess.run):
    DEATHS.mkdir(parents=True, exist_ok=True)
    pane = run(['tmux', 'capture-pane', '-p', '-S', '-200', '-t', name], capture_output=True, text=True)
    path = DEATHS / f"{name}_{time.strftime('%m-%d-%Y_%H%M%S')}.log"
    path.write_text(pane.stdout if pane.returncode == 0 else f'capture failed: {pane.stderr}')
    killed = run(['tmux', 'kill-session', '-t', name], capture_output=True, text=True)
    if killed.returncode != 0:
        raise ProbeError(f'could not remove dead session {name}: {killed.stderr.strip()[:200]}')
    return path


def keep_pane(name, run=subprocess.run):
    """Fallback only; the session-created hook (installed at deployment) retains panes from creation."""
    run(['tmux', 'set-option', '-t', name, 'remain-on-exit', 'on'], capture_output=True, text=True)


def ensure_gpu_filter(R):
    """Install the owner's wrapper only if missing or different, atomically; never truncate a live executable."""
    R.BIN.mkdir(parents=True, exist_ok=True)
    target = R.BIN / 'nvidia-smi'
    if not (target.exists() and target.read_text() == R.WRAPPER):
        tmp = R.BIN / f'.nvidia-smi.{os.getpid()}.tmp'
        tmp.write_text(R.WRAPPER)
        tmp.chmod(0o755)
        os.replace(tmp, target)
    os.environ['PATH'] = f'{R.BIN}{os.pathsep}{os.environ.get("PATH", "")}'


def repair(R, action, arm, seed, update, run=subprocess.run):
    """Run one owner step while holding the trajectory's controller lock, then launch outside it."""
    root = PILOT / f'{arm}_{seed}'
    if action in ('account_then_launch', 'archive_then_launch'):
        with (root / 'controller.lock').open('a') as fence:
            fcntl.flock(fence, fcntl.LOCK_EX | fcntl.LOCK_NB)  # BlockingIOError: a runner holds it, skip
            if action == 'account_then_launch':
                R.account(arm, seed, update, R.ADMISSION)
            else:
                R.archive_without_generations(arm, seed, update)
    if action == 'retry':
        R.spawn_retry(arm, seed, update)
        keep_pane(f'{retry_prefix(arm, seed)}{update}', run=run)
    else:
        R.launch(arm, seed)
        keep_pane(pilot_session(arm, seed), run=run)


def tick(dry_run=False, run=subprocess.run, R=None):
    """One supervised pass. Holds an exclusive lock so ticks never overlap; dry_run only reports decisions."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open('a') as fence:
        try:
            fcntl.flock(fence, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'SKIPPED_OVERLAP'}
        try:
            if full_resume_running(run=run):
                if not dry_run:
                    log({'action': 'skip_tick', 'detail': 'a full or targeted resume driver is running'})
                return {'status': 'SKIPPED_RESUME_RUNNING'}
            sessions(run=run)  # fail closed before doing anything
        except ProbeError as error:
            if not dry_run:
                log({'action': 'skip_tick', 'detail': f'probe failed: {error}'})
            return {'status': 'SKIPPED_PROBE_ERROR', 'error': str(error)}
        if not dry_run and R is None:
            sys.path.insert(0, str(HERE))
            import resume_pilot_after_foreign_gpu as R  # owner's own steps; imported lazily
        if not dry_run:
            ensure_gpu_filter(R)
            R.check_admission(R.ADMISSION)
        paused = paused_trajectories()
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        report = {}
        for arm in ARMS:
            for seed in SEEDS:
                key = f'{arm}_{seed}'
                try:
                    if key in paused:
                        report[key] = {'action':'skip','update':None,'detail':'paused (V4-A3)'}
                        continue
                    live, dead = is_live(arm, seed, run=run)
                    if dead and not dry_run:
                        for name in dead:
                            evidence = preserve_dead(name, run=run)
                            log({'trajectory': key, 'action': 'preserved_dead_pane', 'session': name,
                                 'evidence': str(evidence)})
                    info = trajectory_state(arm, seed)
                    action, update, detail = decide(live=live, complete=info['complete'], partials=info['partials'],
                                                    restarts=state.get(key, {}), next_update=info['next_update'])
                    report[key] = {'action': action, 'update': update, 'detail': detail,
                                   'completed_updates': info['completed_updates']}
                    if dry_run or action in ('skip', 'diagnose'):
                        if action == 'diagnose' and not dry_run:
                            log({'trajectory': key, 'action': 'diagnose', 'update': update, 'detail': detail})
                        continue
                    live_again, _ = is_live(arm, seed, run=run)  # recheck immediately before acting
                    if live_again:
                        report[key].update(action='skip', detail='became live before action')
                        continue
                    attempt = reserve_attempt(state, key, update)
                    repair(R, action, arm, seed, update, run=run)
                    log({'trajectory': key, 'action': action, 'update': update, 'detail': detail,
                         'attempt_for_update': attempt})
                except Exception as error:  # one trajectory's failure never blocks the others
                    report.setdefault(key, {})['error'] = f'{type(error).__name__}: {error}'
                    if not dry_run:
                        log({'trajectory': key, 'action': 'error', 'error': report[key]['error']})
        if dry_run:
            return {'status': 'DRY_RUN', 'trajectories': report}
        write_atomic(STATUS, json.dumps({'time': time.strftime('%m-%d-%Y %H:%M:%S %Z'), 'trajectories': report,
                                         'api_spend_usd': 0}, indent=2, sort_keys=True) + '\n')
        return {'status': 'OK', 'trajectories': report}


if __name__ == '__main__':
    os.environ['HF_HUB_OFFLINE'] = '1'
    print(json.dumps(tick(dry_run='--dry-run' in sys.argv[1:]), sort_keys=True))
