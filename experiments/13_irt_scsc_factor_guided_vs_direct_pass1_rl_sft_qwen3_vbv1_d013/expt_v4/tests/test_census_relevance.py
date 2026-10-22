"""TLDR: Only relevant incomplete process reads block ordinary and stopped pause observations."""
from copy import deepcopy
from pathlib import Path
import os

import pytest
import pause_v3 as module
from test_pause_boundary import observation, pair, frozen_pair


@pytest.fixture
def census(tmp_path, monkeypatch):
    observation(tmp_path, key='A_1302', pid=50002)
    root = tmp_path / 'proc'
    root.mkdir()
    (root / 'stat').write_text('btime 1000\n')
    real_path = Path
    monkeypatch.setattr(module, 'Path', lambda *args: root if args == ('/proc',) else
                        root / 'stat' if args == ('/proc/stat',) else real_path(*args))
    monkeypatch.setattr(module.subprocess, 'check_output', lambda argv, **kw:
                        'rl4cv-e13v3-pilot-A-1302\t%123\t50001\n' if 'list-panes' in argv else '')
    pilot = tmp_path / 'phase2/pilot/A_1302'
    def add(pid, *, ppid=1, pgid=None, argv=('worker',), children=(), tid=None):
        path = root / str(pid)
        path.mkdir()
        fields = ['S', str(ppid), str(pgid or pid)] + ['0'] * 17
        fields[19] = str(pid)
        (path / 'stat').write_text(f'{pid} (fixture) ' + ' '.join(fields))
        (path / 'cmdline').write_bytes(b'\0'.join(arg.encode() for arg in argv))
        (path / 'wchan').write_text('do_wait' if pid == 50001 else 'hrtimer_nanosleep')
        task = path / 'task' / str(tid or pid)
        task.mkdir(parents=True)
        (task / 'children').write_text(' '.join(map(str, children)))
        (path / 'fd').mkdir()
        (path / 'cwd').symlink_to(tmp_path)
        return path
    add(50001, argv=('sh', '-c', 'fixture'))
    add(50002, ppid=50001, pgid=50001,
        argv=('python', '/synthetic/pilot_run.py', '--arm', 'A', '--seed', '1302'))
    # /proc order is intentionally unrelated-process first: classification must
    # wait for the runner's own thread/child evidence, independent of scan order.
    original_iterdir = Path.iterdir
    def iterdir(path):
        values = list(original_iterdir(path))
        return iter(sorted(values, key=lambda p: p.name, reverse=True)) if path == root else iter(values)
    monkeypatch.setattr(Path, 'iterdir', iterdir)
    return root, pilot, add


@pytest.mark.parametrize('error', [FileNotFoundError, ProcessLookupError, PermissionError, OSError])
@pytest.mark.parametrize('relation', ['unrelated', 'runner', 'group', 'child', 'thread_child', 'argv', 'cwd', 'fd'])
@pytest.mark.parametrize('stopped', [False, True])
def test_failure_relevance_and_stopped_recheck(census, tmp_path, monkeypatch, error, relation, stopped):
    root, pilot, add = census
    if stopped:
        stat = root / '50002/stat'
        stat.write_text(stat.read_text().replace('(fixture) S', '(fixture) T'))
        (root / '50002/wchan').write_text('do_signal_stop')
    target = root / '50003'
    if relation == 'runner':
        target = root / '50002'
    else:
        add(50003, ppid=50002 if relation == 'child' else 50004 if relation == 'thread_child' else 1,
            pgid=50001 if relation == 'group' else 50003,
            argv=('worker', str(pilot)) if relation == 'argv' else ('worker',))
    if relation == 'thread_child':
        task = root / '50002/task/50004'
        task.mkdir()
        (task / 'children').write_text('')
    if relation == 'cwd':
        (target / 'cwd').unlink()
        (target / 'cwd').symlink_to(pilot)
    if relation == 'fd':
        (target / 'fd/3').symlink_to(pilot / 'plans.json')
    original_text, original_link = Path.read_text, os.readlink
    if relation in ('cwd', 'fd'):
        (target / 'fd/9').symlink_to('/unrelated')
        def readlink(path):
            if path == target / 'fd/9': raise error('injected read failure')
            return original_link(path)
        monkeypatch.setattr(module.os, 'readlink', readlink)
        monkeypatch.setattr(module, 'proc_identity', lambda _: (_ for _ in ()).throw(error('gone')))
        # Explicit link order proves a match is retained before a later failure.
        original_iterdir = Path.iterdir
        monkeypatch.setattr(Path, 'iterdir', lambda p: iter(sorted(original_iterdir(p)))
                            if p == target / 'fd' else original_iterdir(p))
    else:
        def text(path, *a, **kw):
            if path == target / 'wchan': raise error('injected read failure')
            return original_text(path, *a, **kw)
        monkeypatch.setattr(Path, 'read_text', text)
    snap = module.snapshot('A_1302', tmp_path)
    expected = 'READY' if relation == 'unrelated' else 'WAIT_OBSERVATION'
    # A known live reference already takes precedence over its unreadable link.
    live_reference = relation in ('cwd', 'fd') and error is PermissionError
    assert module.observation_status(snap, stopped=stopped) == ('WAIT_STAGE_RUNNING' if live_reference else expected)
    assert snap['ignored_vanished'] == int(relation == 'unrelated')
    assert bool(snap['observation_errors']) == (relation != 'unrelated')
    before = pair(observation(tmp_path, key='A_1302', pid=50002))
    stopped = frozen_pair(before[1])
    # Use the census output in the same whole-rule stopped recheck; align the
    # synthetic clock/identity and stopped state while retaining error evidence.
    for sample in stopped:
        sample['observation_errors'] = deepcopy(snap['observation_errors'])
        sample['ignored_vanished'] = snap['ignored_vanished']
    assert module.boundary(*stopped, frozen_from=before) == expected


@pytest.mark.parametrize('thread', [50002, 50004])
@pytest.mark.parametrize('listed', [False, True])
def test_own_children_read_catches_midscan_vanishing_child(census, tmp_path, monkeypatch, thread, listed):
    root, _, add = census
    task = root / '50002/task' / str(thread)
    task.mkdir(exist_ok=True)
    (task / 'children').write_text('50003')
    if listed:
        path = add(50003)
        (path / 'stat').unlink()  # No argv, parent or group evidence survives.
    original = Path.read_text
    reads = 0
    def text(path, *a, **kw):
        nonlocal reads
        if path == task / 'children':
            reads += 1
            return '50003' if reads == 1 else ''
        return original(path, *a, **kw)
    monkeypatch.setattr(Path, 'read_text', text)
    snap = module.snapshot('A_1302', tmp_path)
    assert snap['processes'][0]['children'] == [50003]
    assert module.observation_status(snap) == ('WAIT_OBSERVATION' if listed else 'WAIT_STAGE_RUNNING')
    assert snap['ignored_vanished'] == 0
    if listed:
        assert snap['observation_errors'] == [{'pid': 50003, 'error': 'FileNotFoundError'}]


@pytest.mark.parametrize('relevant', [False, True])
def test_unreadable_reference_links_count_only_when_unrelated(census, tmp_path, monkeypatch, relevant):
    root, _, add = census
    target = root / '50002' if relevant else add(50003)
    original = Path.iterdir
    def iterdir(path):
        if path == target / 'fd': raise PermissionError('protected fd directory')
        return original(path)
    monkeypatch.setattr(Path, 'iterdir', iterdir)
    snap = module.snapshot('A_1302', tmp_path)
    assert module.observation_status(snap) == ('WAIT_OBSERVATION' if relevant else 'READY')
    assert snap['ignored_vanished'] == int(not relevant)
    if not relevant:
        assert snap['reference_inspection_unavailable'] == []
        assert snap['observation_errors'] == []
