"""TLDR: Pause only designated silent v3 pilots at a verified process/disk allocation boundary."""
import argparse
from copy import deepcopy
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from operational_pause import selection, admitted_config

WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e13v3')
VETO_END = datetime.fromisoformat('2026-10-21T12:00:00-07:00').timestamp()
IDENTITY = ('pid', 'ppid', 'pgid', 'start_ticks', 'uid', 'arguments')
TRAJECTORIES = tuple(f'{arm}_{seed}' for arm in ('A', 'B', 'P') for seed in (1301, 1302))
OBSERVATION_INTERVAL = 1.0


def proc(pid):
    """Read identity twice so a recycled PID cannot form a mixed observation."""
    path = Path('/proc') / str(pid)
    before = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    arguments = [x.decode() for x in (path / 'cmdline').read_bytes().split(b'\0') if x]
    children = sorted({int(child) for task in (path / 'task').iterdir()
                       for child in (task / 'children').read_text().split()})
    wchan = (path / 'wchan').read_text().strip()
    after = (path / 'stat').read_text().rsplit(')', 1)[1].split()
    if before[19] != after[19]:
        raise ValueError('PID reused during observation')
    boot = int(next(line.split()[1] for line in Path('/proc/stat').read_text().splitlines()
                    if line.startswith('btime ')))
    return {'arguments': arguments, 'start_unix': boot + int(after[19]) / os.sysconf('SC_CLK_TCK'),
            'pid': int(pid), 'pgid': int(after[2]), 'ppid': int(after[1]),
            'start_ticks': after[19], 'state': after[0], 'wchan': wchan,
            'children': children, 'uid': path.stat().st_uid, 'command': ' '.join(arguments)}


def is_runner(arguments, arm, seed):
    # Shell command strings and the retired retry helper are not pilot_run.py runners.
    if len(arguments) < 2 or not Path(arguments[0]).name.startswith('python'):
        return False
    if Path(arguments[1]).name != 'pilot_run.py':
        return False
    rest = arguments[2:]
    try:
        return (rest.count('--arm') == rest.count('--seed') == 1 and
                rest[rest.index('--arm') + 1] == arm and rest[rest.index('--seed') + 1] == seed)
    except (ValueError, IndexError):
        return False


def isolated_group(runner, pane_pid, members):
    """Only the pane shell (group leader) and its direct Python child may be signalled."""
    if len(members) != 2:
        return False
    shell = next((m for m in members if m['pid'] == pane_pid), None)
    member = next((m for m in members if m['pid'] == runner['pid']), None)
    return bool(member and all(member.get(k) == runner.get(k) for k in IDENTITY) and shell and runner['pid'] != pane_pid and runner['ppid'] == pane_pid and
                runner['pgid'] == shell['pgid'] == pane_pid and shell['uid'] == runner['uid'] and
                shell['arguments'] and Path(shell['arguments'][0]).name in ('sh', 'bash', 'dash', 'zsh') and
                {m['pid'] for m in members} == {pane_pid, runner['pid']})


def disk_state(pilot):
    """Only the latest numbered opportunity may supply pre-allocation evidence."""
    updates = sorted(p for p in pilot.iterdir() if p.is_dir() and re.fullmatch(r'update_[0-9]{5}', p.name))
    if not updates:
        return {'latest_update': None, 'files': {}, 'leases': [], 'lease_files': []}
    latest = updates[-1]
    names = ('plans.json', 'cells.json', 'generate_lease.json', 'score/groups.json',
             'update_lease.json', 'summary.json')
    leases = sorted(latest.rglob('*_lease.json'))
    return {'latest_update': str(latest), 'files': {name: (latest / name).exists() for name in names},
            'lease_files': [str(p) for p in leases],
            'leases': [str(p) for p in leases if not p.with_name(p.stem + '_end.json').is_file()]}


def references(p, pilot):
    """Inspect argv, cwd and open descriptors without reading trajectory contents."""
    paths = {str(pilot), str(pilot.resolve())}
    refs = []
    for base in paths:
        if re.search(re.escape(base) + r'(?=$|[/\s\'"])', p['command']):
            refs.append('argv')
    root = Path('/proc') / str(p['pid'])
    try:
        descriptors = list((root / 'fd').iterdir())
    except PermissionError:
        descriptors = []
        p.setdefault('reference_inspection_unavailable', []).append('fd')
    for link in [root / 'cwd', *descriptors]:
        try:
            value = os.readlink(link).removesuffix(' (deleted)')
        except FileNotFoundError:
            continue
        except PermissionError:
            p.setdefault('reference_inspection_unavailable', []).append(str(link.relative_to(root)))
            continue
        if any(value == base or value.startswith(base + '/') for base in paths):
            refs.append(str(link.relative_to(root)))
    return sorted(set(refs))


def snapshot(key, work=WORK):
    """One read-only process/disk observation; terminal text is context only."""
    if key not in TRAJECTORIES:
        raise ValueError('unknown v3 trajectory')
    arm, seed = key.split('_')
    work = Path(work)
    panes = subprocess.check_output(['tmux', 'list-panes', '-a', '-F',
                                    '#{session_name}\t#{pane_id}\t#{pane_pid}'], text=True)
    matching = [line.split('\t') for line in panes.splitlines()
                if line.split('\t')[0] == f'rl4cv-e13v3-pilot-{arm}-{seed}']
    if len(matching) != 1:
        raise ValueError('exactly one owned trajectory pane required')
    session, pane, pane_pid = matching[0]
    pane_pid = int(pane_pid)
    text = subprocess.check_output(['tmux', 'capture-pane', '-p', '-S', '-30', '-t', pane], text=True)
    pilot = work / 'phase2/pilot' / key
    all_rows, errors, groups = [], [], {}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            stat = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            groups.setdefault(int(stat[2]), []).append(int(path.name))
            if path.stat().st_uid != os.getuid():
                continue
            row = proc(path.name)
            row['references'] = references(row, pilot)
            all_rows.append(row)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (PermissionError, ValueError) as exc:
            errors.append({'pid': int(path.name), 'error': type(exc).__name__})
    runners = [p for p in all_rows if is_runner(p['arguments'], arm, seed)]
    allowed = {pane_pid, *(p['pid'] for p in runners)}
    rows = [{**p, 'kind': 'stage'} for p in all_rows if p['pid'] not in allowed and p['references']]
    for runner in runners:
        # Check children of every thread as well as the census, regardless of their argv.
        fresh = proc(runner['pid'])
        if any(fresh[k] != runner[k] for k in IDENTITY):
            raise ValueError('runner identity changed during observation')
        fresh['children'] = sorted(set(fresh['children']) | {p['pid'] for p in all_rows if p['ppid'] == runner['pid']})
        fresh['kind'] = 'runner'
        fresh['process_group_members'] = [proc(pid) for pid in groups.get(fresh['pgid'], [])]
        rows.append(fresh)
    return {'completed_updates': len(list(pilot.glob('update_*/summary.json'))), 'planned_updates': 30,
            'trajectory': key, 'pane': pane, 'pane_pid': pane_pid, 'session': session, 'pane_text': text,
            'processes': rows, 'observation_errors': errors,
            'reference_scope': 'same-user argv plus readable cwd/fd; process-group census includes all users',
            'reference_inspection_unavailable': [
                {'pid': p['pid'], 'links': p['reference_inspection_unavailable']}
                for p in all_rows if p.get('reference_inspection_unavailable')],
            **disk_state(pilot),
            'observed_unix': time.time(), 'observed_monotonic': time.monotonic()}


def observation_status(snap, *, stopped=False):
    if any(p['kind'] == 'stage' for p in snap['processes']):
        return 'WAIT_STAGE_RUNNING'
    if snap.get('observation_errors'):
        return 'WAIT_OBSERVATION'
    runners = [p for p in snap['processes'] if p['kind'] == 'runner']
    if len(runners) != 1:
        return 'WAIT_RUNNER_IDENTITY'
    runner = runners[0]
    arm, seed = snap['trajectory'].split('_')
    if not is_runner(runner['arguments'], arm, seed) or not runner.get('start_ticks'):
        return 'WAIT_RUNNER_IDENTITY'
    if runner['children']:
        return 'WAIT_STAGE_RUNNING'
    if not isolated_group(runner, snap['pane_pid'], runner['process_group_members']):
        return 'WAIT_RUNNER_IDENTITY'
    if snap['leases']:
        return 'WAIT_LEASE_HELD'
    files = snap['files']
    if files.get('summary.json'):
        return 'WAIT_SUMMARY_PRESENT'
    if not snap['latest_update'] or not (
        files.get('plans.json') and files.get('cells.json') and not files.get('generate_lease.json') or
        files.get('score/groups.json') and not files.get('update_lease.json')
    ):
        return 'WAIT_PREALLOCATION'
    if stopped:
        # SIGSTOP changes hrtimer_nanosleep to do_signal_stop on Linux. Retain and
        # bind the pre-stop sleep evidence in boundary(..., frozen_from=...).
        if any(p['state'] != 'T' or p['wchan'] != 'do_signal_stop'
               for p in runner['process_group_members']):
            return 'WAIT_NOT_STOPPED'
        if runner['state'] != 'T' or runner['wchan'] != 'do_signal_stop':
            return 'WAIT_NOT_STOPPED'
    elif runner['state'] != 'S' or runner['wchan'] != 'hrtimer_nanosleep':
        return 'WAIT_WCHAN'
    return 'READY'


def identity(snap):
    runner = next(p for p in snap['processes'] if p['kind'] == 'runner')
    return (snap['trajectory'], snap['pane'], snap['pane_pid'], snap['session'],
            tuple(runner[k] for k in IDENTITY),
            sorted((p['pid'], tuple(p[k] for k in IDENTITY)) for p in runner['process_group_members']))


def boundary(first, second, *, frozen_from=None):
    """Require the whole rule twice and preserve identities/disk state across SIGSTOP."""
    if frozen_from is not None and boundary(*frozen_from) != 'READY':
        return 'WAIT_RACE'
    for snap in (first, second):
        status = observation_status(snap, stopped=frozen_from is not None)
        if status != 'READY':
            return status
    if second['observed_monotonic'] - first['observed_monotonic'] < OBSERVATION_INTERVAL:
        return 'WAIT_OBSERVATION_INTERVAL'
    observations = [*(frozen_from or ()), first, second]
    if any(identity(snap) != identity(first) for snap in observations):
        return 'WAIT_RUNNER_IDENTITY'
    if any(any(snap[k] != first[k] for k in ('latest_update', 'files', 'leases', 'lease_files'))
           for snap in observations):
        return 'WAIT_DISK_CHANGED'
    return 'READY'


def observe(key, work, probe, sleep):
    first = deepcopy(probe(key, work))
    sleep(OBSERVATION_INTERVAL)
    return first, deepcopy(probe(key, work))


def boundary_probe(admission, *, trajectory=None, work=WORK, probe=snapshot, sleep=time.sleep):
    """Read-only probes may inspect any declared v3 run; pause authority stays single-run."""
    from admission import check_admission
    record = check_admission(admission, require_launch=True)
    designated = selection(admitted_config(record))
    if trajectory is not None and trajectory not in TRAJECTORIES:
        raise ValueError('unknown v3 trajectory')
    report = {}
    for key in ((trajectory,) if trajectory else designated):
        observations = observe(key, work, probe, sleep)
        report[key] = {'status': boundary(*observations), 'snapshot': observations[-1],
                       'observations': observations, 'read_only': True,
                       'designated_for_pause': key in designated}
    return report


def verify_identity(runner, inspect):
    for original in runner['process_group_members']:
        current = inspect(original['pid'])
        if any(current[k] != original[k] for k in IDENTITY):
            raise ValueError('PID reused or process identity changed')


def pause(admission, *, trajectory=None, work=WORK, veto_not_issued=False, probe=snapshot,
          kill=os.killpg, inspect=proc, now=None, sleep=time.sleep):
    from admission import check_admission
    now = time.time() if now is None else now
    if now < VETO_END or not veto_not_issued:
        raise ValueError('V4-A3 veto window/absence of veto not satisfied')
    record = check_admission(admission, require_launch=True)
    designated = selection(admitted_config(record), trajectory)
    work = Path(work)
    path = work / 'phase2/autoresume_paused.json'
    # Same lock as watchdog prevents a relaunch between stop and durable pause state.
    with (work / 'phase2/autoresume.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {key: 'WAIT_WATCHDOG_LOCK' for key in designated}
        state = json.loads(path.read_text()) if path.exists() else {'amendment': 'V4-A3', 'trajectories': {}}
        if not isinstance(state.get('trajectories'), dict) or set(state['trajectories']) - set(designated):
            raise ValueError('pause list contains non-designated trajectories')
        report = {}
        for key in designated:
            if key in state['trajectories']:
                report[key] = 'ALREADY_PAUSED'
                continue
            observations = observe(key, work, probe, sleep)
            snap = observations[-1]
            status = boundary(*observations)
            if status != 'READY':
                report[key] = status
                continue
            runner = next(p for p in snap['processes'] if p['kind'] == 'runner')
            verify_identity(runner, inspect)
            kill(runner['pgid'], signal.SIGSTOP)
            try:
                # Group-stop delivery is asynchronous.
                sleep(0.05)
                frozen = observe(key, work, probe, sleep)
                verify_identity(runner, inspect)
                if boundary(*frozen, frozen_from=observations) != 'READY':
                    report[key] = 'WAIT_RACE'
                    continue
                receipt = {**snap, 'operational_record': record['operational_pause'],
                           'boundary_rule': 'pilot-process-disk-v1',
                           'observations': observations, 'stopped_observations': frozen,
                           'paused_unix': time.time(), 'pid': runner['pid'],
                           'start_ticks': runner['start_ticks'], 'start_unix': runner['start_unix'],
                           'pgid': runner['pgid']}
                state['trajectories'][key] = receipt
                tmp = path.with_name('.autoresume_paused.tmp')
                with tmp.open('w') as f:
                    json.dump(state, f, sort_keys=True)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, path)
                directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
                kill(runner['pgid'], signal.SIGTERM)
                report[key] = 'PAUSED'
            finally:
                try:
                    verify_identity(runner, inspect)
                    kill(runner['pgid'], signal.SIGCONT)
                except (FileNotFoundError, ProcessLookupError, ValueError):
                    pass
        return report


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--admission', required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--probe', action='store_true')
    p.add_argument('--trajectory')
    p.add_argument('--veto-not-issued', action='store_true')
    a = p.parse_args()
    if a.probe:
        print(json.dumps(boundary_probe(a.admission, trajectory=a.trajectory)))
    elif a.execute:
        print(json.dumps(pause(a.admission, trajectory=a.trajectory,
            veto_not_issued=a.veto_not_issued or os.environ.get('E13V4_A3_NO_VETO') == '1')))
    else:
        raise SystemExit('No action; use --probe for read-only inspection or --execute after the veto window.')
