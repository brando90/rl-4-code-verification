"""TLDR: Exercise tmux auto-continue, vanished processes and every stopped cleanup boundary on CPU."""
from copy import deepcopy
import json
import os
from pathlib import Path
import signal
import time

import pytest
import pause_v3 as module
from dry_run import stop_fixture
from test_single_pause import setup_pause
from test_pause_boundary import observation, pair, frozen_pair


def test_fake_tmux_auto_continues_group_but_runner_stop_holds(tmp_path):
    admission, work, runner, snap, _, _, kw = setup_pause(tmp_path)
    calls = []
    def pid_signal(pid, sig):
        calls.append(('pid', pid, sig))
        assert pid == runner['pid']
        if sig == signal.SIGSTOP:
            stop_fixture(snap)
        if sig == signal.SIGCONT:
            runner.update(state='S', wchan='hrtimer_nanosleep')
    def group_signal(pgid, sig):
        calls.append(('group', pgid, sig))
        assert pgid == runner['pgid']
        if sig == signal.SIGSTOP:
            # tmux receives SIGCHLD for its direct shell child and resumes the group.
            for p in [runner, *runner['process_group_members']]:
                p.update(state='S', wchan='do_wait' if p['pid'] == pgid else 'hrtimer_nanosleep')
    group_signal(runner['pgid'], signal.SIGSTOP)
    assert module.observation_status(snap, stopped=True) == 'WAIT_NOT_STOPPED'
    calls.clear()
    assert module.pause(admission, **{**kw, 'kill': pid_signal, 'kill_group': group_signal}) == {'A_1302': 'PAUSED'}
    assert calls == [('pid', runner['pid'], signal.SIGSTOP),
                     ('group', runner['pgid'], signal.SIGTERM),
                     ('pid', runner['pid'], signal.SIGCONT)]
    receipt = json.loads((work / 'phase2/autoresume_paused.json').read_text())['trajectories']['A_1302']
    for frozen in receipt['stopped_observations']:
        shell, child = frozen['processes'][0]['process_group_members']
        assert (shell['state'], shell['wchan']) == ('S', 'do_wait')
        assert (child['state'], child['wchan']) == ('T', 'do_signal_stop')


@pytest.mark.parametrize('change', ['shell_stopped', 'shell_wchan', 'shell_identity', 'member_children'])
def test_frozen_shell_and_runner_requirements(tmp_path, change):
    before = pair(observation(tmp_path))
    frozen = frozen_pair(before[1])
    shell, runner = frozen[1]['processes'][0]['process_group_members']
    if change == 'shell_stopped': shell['state'] = 'T'
    elif change == 'shell_wchan': shell['wchan'] = 'hrtimer_nanosleep'
    elif change == 'shell_identity': shell['start_ticks'] = 'changed'
    else: runner['children'] = [999]
    assert module.boundary(*frozen, frozen_from=before).startswith('WAIT_')


@pytest.mark.parametrize('site', ['census_shell', 'census_runner', 'census_stage',
                                  'fresh_runner', 'group_shell', 'group_runner'])
@pytest.mark.parametrize('error', [FileNotFoundError, ProcessLookupError, module.ProcessChanged])
def test_snapshot_proc_failure_blocks_only_relevant_processes(tmp_path, monkeypatch, site, error):
    snap = observation(tmp_path, key='A_1302', pid=50002)
    runner = snap['processes'][0]
    shell = runner['process_group_members'][0]
    stage = dict(shell, pid=50003, pgid=50003, arguments=['unrelated'])
    rows = {p['pid']: dict(p, command=' '.join(p['arguments']), children=p.get('children', []))
            for p in (shell, runner, stage)}
    fake = tmp_path / 'proc'; fake.mkdir()
    for pid, row in rows.items():
        directory = fake / str(pid); directory.mkdir()
        fields = ['S', str(row['ppid']), str(row['pgid'])] + ['0'] * 20
        (directory / 'stat').write_text(f'{pid} (fixture) ' + ' '.join(fields))
    original_iterdir = Path.iterdir
    monkeypatch.setattr(Path, 'iterdir', lambda path: original_iterdir(fake if path == Path('/proc') else path))
    monkeypatch.setattr(module.subprocess, 'check_output', lambda argv, **kw:
                        'rl4cv-e13v3-pilot-A-1302\t%123\t50001\n' if 'list-panes' in argv else '')
    monkeypatch.setattr(module, 'references', lambda *a: [])
    counter = 0
    target = ['census_shell', 'census_runner', 'census_stage', 'fresh_runner', 'group_shell', 'group_runner'].index(site)
    # Preserve deterministic census order regardless of filesystem directory order.
    monkeypatch.setattr(Path, 'iterdir', lambda path: iter([fake / str(p) for p in rows])
                        if path == Path('/proc') else original_iterdir(path))
    def inspect(pid, evidence=None):
        nonlocal counter
        current = counter; counter += 1
        if current == target: raise error('process vanished')
        return deepcopy(rows[int(pid)])
    monkeypatch.setattr(module, 'proc', inspect)
    actual = module.snapshot('A_1302', tmp_path)
    if site == 'census_stage':
        assert not actual['observation_errors']
        assert actual['ignored_vanished'] == 1
        assert module.observation_status(actual) == 'READY'
    else:
        assert actual['observation_errors']
        assert module.observation_status(actual) == 'WAIT_OBSERVATION'


@pytest.mark.parametrize('site', ['stat_before', 'cmdline', 'task', 'children', 'wchan', 'stat_after', 'uid'])
@pytest.mark.parametrize('error', [FileNotFoundError, ProcessLookupError])
def test_proc_component_vanish_is_wait_at_observation_boundary(monkeypatch, site, error):
    pid = os.getpid(); root = Path('/proc') / str(pid)
    original_text, original_bytes = Path.read_text, Path.read_bytes
    original_iterdir, original_stat = Path.iterdir, Path.stat
    stat_reads = 0
    def text(path, *a, **kw):
        nonlocal stat_reads
        if path == root / 'stat':
            stat_reads += 1
            if (site == 'stat_before' and stat_reads == 1 or site == 'stat_after' and stat_reads == 2):
                raise error('vanished stat')
        if site in ('children', 'wchan') and str(path).startswith(str(root) + '/') and path.name == site:
            raise error('vanished field')
        return original_text(path, *a, **kw)
    def read_bytes(path, *a, **kw):
        if site == 'cmdline' and path == root / 'cmdline': raise error('vanished cmdline')
        return original_bytes(path, *a, **kw)
    def iterdir(path):
        if site == 'task' and path == root / 'task': raise error('vanished task')
        return original_iterdir(path)
    def stat(path, *a, **kw):
        if site == 'uid' and path == root: raise error('vanished uid')
        return original_stat(path, *a, **kw)
    monkeypatch.setattr(Path, 'read_text', text)
    monkeypatch.setattr(Path, 'read_bytes', read_bytes)
    monkeypatch.setattr(Path, 'iterdir', iterdir)
    monkeypatch.setattr(Path, 'stat', stat)
    def probe(*_):
        nonlocal stat_reads
        stat_reads = 0
        module.proc(pid)
        raise AssertionError('expected incomplete process read')
    samples = module.observe('A_1302', None, probe, lambda _: None)
    assert module.boundary(*samples) == 'WAIT_OBSERVATION'


@pytest.mark.parametrize('site', ['fd_directory', 'cwd', 'fd_link'])
@pytest.mark.parametrize('error', [FileNotFoundError, ProcessLookupError])
def test_references_vanishing_process_is_not_ignored(tmp_path, monkeypatch, site, error):
    root = Path('/proc/123456789')
    monkeypatch.setattr(Path, 'iterdir', lambda path: iter([root / 'fd/3']))
    if site == 'fd_directory':
        monkeypatch.setattr(Path, 'iterdir', lambda path: (_ for _ in ()).throw(error('gone')))
    def readlink(path):
        if (site == 'cwd' and path.name == 'cwd' or site == 'fd_link' and path.name == '3'):
            raise error('gone')
        return '/unrelated'
    monkeypatch.setattr(module.os, 'readlink', readlink)
    monkeypatch.setattr(module, 'proc_identity', lambda pid: (_ for _ in ()).throw(error('gone')))
    samples = module.observe('A_1302', None, lambda *_: module.references(
        {'pid': 123456789, 'command': 'unrelated'}, tmp_path), lambda _: None)
    assert module.boundary(*samples) == 'WAIT_OBSERVATION'


@pytest.mark.parametrize('site', ['stop', 'delivery_wait', 'frozen_probe', 'frozen_identity',
                                  'boundary', 'temp_open', 'serialize', 'file_fsync',
                                  'replace', 'directory_open', 'directory_fsync', 'term'])
@pytest.mark.parametrize('error', [RuntimeError, KeyboardInterrupt])
def test_exception_paths_always_resume_runner(tmp_path, monkeypatch, site, error):
    admission, work, runner, snap, signals, _, kw = setup_pause(tmp_path)
    original_kill, original_probe, original_inspect = kw['kill'], kw['probe'], kw['inspect']
    fired = False
    def fail():
        nonlocal fired
        if not fired:
            fired = True
            raise error('injected failure')
    def kill(pid, sig):
        original_kill(pid, sig)
        if site == 'stop' and sig == signal.SIGSTOP: fail()
        if site == 'term' and sig == signal.SIGTERM: fail()
    def probe(*a):
        if site == 'frozen_probe' and signals: fail()
        return original_probe(*a)
    def inspect(pid):
        if site == 'frozen_identity' and signals: fail()
        return original_inspect(pid)
    def sleep(seconds):
        if site == 'delivery_wait' and signals: fail()
        snap['observed_monotonic'] += seconds + 1e-6
    kw.update(kill=kill, kill_group=kill, probe=probe, inspect=inspect, sleep=sleep)
    if site == 'boundary':
        original = module.boundary
        def check(*a, **k):
            if k.get('frozen_from'): fail()
            return original(*a, **k)
        monkeypatch.setattr(module, 'boundary', check)
    if site == 'temp_open':
        original = Path.open
        def opened(path, *a, **k):
            if path.name == '.autoresume_paused.tmp': fail()
            return original(path, *a, **k)
        monkeypatch.setattr(Path, 'open', opened)
    if site == 'serialize':
        monkeypatch.setattr(module.json, 'dump', lambda *a, **k: fail())
    if site in ('file_fsync', 'directory_fsync'):
        count = 0
        original = os.fsync
        def fsync(fd):
            nonlocal count
            count += 1
            if count == (1 if site == 'file_fsync' else 2): fail()
            return original(fd)
        monkeypatch.setattr(module.os, 'fsync', fsync)
    if site == 'replace': monkeypatch.setattr(module.os, 'replace', lambda *a: fail())
    if site == 'directory_open':
        original = os.open
        def opened(path, flags, *a, **k):
            if Path(path) == work / 'phase2': fail()
            return original(path, flags, *a, **k)
        monkeypatch.setattr(module.os, 'open', opened)
    with pytest.raises(error, match='injected failure'):
        module.pause(admission, **kw)
    assert fired and signals[0] == signal.SIGSTOP and signals[-1] == signal.SIGCONT


def test_alarm_interrupts_blocking_stopped_work_and_restores_handler(tmp_path, monkeypatch):
    admission, _, _, snap, signals, _, kw = setup_pause(tmp_path)
    monkeypatch.setattr(module, 'MAX_STOP_SECONDS', 0.03)
    before = signal.getsignal(signal.SIGALRM)
    def sleep(seconds):
        if signals: time.sleep(1)
        else: snap['observed_monotonic'] += seconds + 1e-6
    started = time.monotonic()
    assert module.pause(admission, **{**kw, 'sleep': sleep}) == {'A_1302': 'WAIT_STOP_TIMEOUT'}
    assert time.monotonic() - started < 0.5
    assert signals == [signal.SIGSTOP, signal.SIGCONT]
    assert signal.getitimer(signal.ITIMER_REAL) == (0, 0)
    assert signal.getsignal(signal.SIGALRM) == before


def test_shell_exiting_after_term_does_not_prevent_resume(tmp_path):
    admission, _, runner, _, signals, _, kw = setup_pause(tmp_path)
    original = kw['inspect']
    def inspect(pid):
        if signal.SIGTERM in signals and pid != runner['pid']:
            raise FileNotFoundError('shell already exited')
        return original(pid)
    assert module.pause(admission, **{**kw, 'inspect': inspect}) == {'A_1302': 'PAUSED'}
    assert signals == [signal.SIGSTOP, signal.SIGTERM, signal.SIGCONT]


@pytest.mark.parametrize('after_stop', [False, True])
@pytest.mark.parametrize('error', [FileNotFoundError, ProcessLookupError])
def test_identity_vanish_returns_wait(tmp_path, after_stop, error):
    admission, _, _, _, signals, _, kw = setup_pause(tmp_path)
    original = kw['inspect']
    def inspect(pid):
        if bool(signals) == after_stop: raise error('gone')
        return original(pid)
    assert module.pause(admission, **{**kw, 'inspect': inspect}) == {'A_1302': 'WAIT_PROCESS_CHANGED'}
    # An actually vanished/reused runner must never receive a fresh PID signal.
    assert signals == ([signal.SIGSTOP] if after_stop else [])


@pytest.mark.parametrize('error', [FileNotFoundError, ProcessLookupError, PermissionError,
                                  module.ProcessChanged, KeyboardInterrupt])
def test_pinned_runner_resumes_if_final_proc_identity_unavailable(tmp_path, monkeypatch, error):
    admission, _, runner, _, signals, _, kw = setup_pause(tmp_path)
    fd = os.open('/dev/null', os.O_RDONLY)
    original = kw['inspect']
    resumed = []
    monkeypatch.setattr(module.os, 'kill', kw['kill'])
    monkeypatch.setattr(module.os, 'pidfd_open', lambda pid: fd)
    monkeypatch.setattr(module.signal, 'pidfd_send_signal', lambda handle, sig: resumed.append((handle, sig)))
    def inspect(pid):
        if signal.SIGTERM in signals: raise error('cleanup /proc unavailable')
        return original(pid)
    assert module.pause(admission, **{**kw, 'inspect': inspect}) == {'A_1302': 'PAUSED'}
    assert resumed == [(fd, signal.SIGCONT)]
    assert signals == [signal.SIGSTOP, signal.SIGTERM]
    with pytest.raises(OSError): os.fstat(fd)


def test_group_term_requires_file_and_directory_durability(tmp_path, monkeypatch):
    admission, work, runner, _, signals, _, kw = setup_pause(tmp_path)
    events = []
    real_fsync, real_replace = os.fsync, os.replace
    def fsync(fd):
        real_fsync(fd)
        events.append('fsync')
    def replace(*args):
        real_replace(*args)
        events.append('replace')
    def terminate(pgid, sig):
        assert events == ['fsync', 'replace', 'fsync']
        assert pgid == runner['pgid'] and sig == signal.SIGTERM
        state = json.loads((work / 'phase2/autoresume_paused.json').read_text())
        assert set(state['trajectories']) == {'A_1302'}
        signals.append(sig)
    monkeypatch.setattr(module.os, 'fsync', fsync)
    monkeypatch.setattr(module.os, 'replace', replace)
    assert module.pause(admission, **{**kw, 'kill_group': terminate}) == {'A_1302': 'PAUSED'}
    assert signals == [signal.SIGSTOP, signal.SIGTERM, signal.SIGCONT]
