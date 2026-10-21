"""TLDR: Silent live-state fixtures require stable process identities and pre-allocation disk evidence."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

from pause_v3 import boundary, disk_state, references


def touch(root, *names):
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{}\n')


def observation(tmp_path, key='B_1302', *, update=12, phase='optimize', pid=1291595,
                children=(), wchan='hrtimer_nanosleep'):
    """Use the dispatch's observed runner fields, with explicitly synthetic shell identities."""
    arm, seed = key.split('_')
    pilot = tmp_path / 'phase2/pilot' / key
    directory = pilot / f'update_{update:05d}'
    touch(directory, 'plans.json', 'cells.json')
    if phase != 'generate':
        touch(directory, 'generate_lease.json', 'generate_lease_end.json')
    if phase in ('optimize', 'updating'):
        touch(directory, 'score/groups.json')
    if phase == 'updating':
        touch(directory, 'update_lease.json')
    shell = {'pid': pid - 1, 'ppid': 1, 'pgid': pid - 1, 'uid': 1000,
             'arguments': ['sh', '-c', 'synthetic runner command'], 'start_ticks': '11',
             'state': 'S', 'wchan': 'do_wait'}
    runner = {'kind': 'runner', 'pid': pid, 'ppid': shell['pid'], 'pgid': shell['pid'],
              'uid': 1000, 'arguments': ['python', '/synthetic/pilot_run.py', '--arm', arm,
                                      '--seed', seed], 'start_ticks': '12', 'start_unix': 1,
              'state': 'S', 'wchan': wchan, 'children': list(children)}
    runner['process_group_members'] = [shell, deepcopy(runner)]
    return {'trajectory': key, 'pane': '%123', 'pane_pid': shell['pid'],
            'session': f'rl4cv-e13v3-pilot-{arm}-{seed}', 'pane_text': '\n' * 30,
            'processes': [runner], 'observation_errors': [], 'observed_monotonic': 10.0,
            **disk_state(pilot)}


def pair(first):
    second = deepcopy(first)
    second['observed_monotonic'] += 1.0
    return first, second


def frozen_pair(first):
    stopped = deepcopy(first)
    stopped['observed_monotonic'] += 2.0
    runner = stopped['processes'][0]
    for process in [runner, *runner['process_group_members']]:
        process['state'] = 'T'
        process['wchan'] = 'do_signal_stop'
    return pair(stopped)


@pytest.mark.parametrize('key,pid,update,phase,children,wchan,expected', [
    ('B_1302', 1291595, 12, 'optimize', (), 'hrtimer_nanosleep', 'READY'),
    ('P_1301', 1246693, 21, 'generate', (), 'hrtimer_nanosleep', 'READY'),
    ('P_1302', 3171723, 17, 'scoring', tuple(range(400001, 400022)),
     'futex_wait_queue', 'WAIT_STAGE_RUNNING'),
    ('P_1302', 3171723, 17, 'scoring', tuple(range(400001, 400033)),
     'futex_wait_queue', 'WAIT_STAGE_RUNNING'),
    ('A_1302', 692011, 17, 'updating', (692012,), 'hrtimer_nanosleep', 'WAIT_STAGE_RUNNING'),
])
def test_observed_silent_runner_states(tmp_path, key, pid, update, phase, children, wchan, expected):
    # The dispatch supplied update numbers only for B_1302 and P_1301; 17 is a fixture choice.
    snap = observation(tmp_path, key, pid=pid, update=update, phase=phase,
                       children=children, wchan=wchan)
    assert not snap['pane_text'].strip()
    assert boundary(*pair(snap)) == expected


@pytest.mark.parametrize('sample', [0, 1])
def test_child_without_trajectory_in_argv_refuses_boundary(tmp_path, sample):
    observations = pair(observation(tmp_path))
    observations[sample]['processes'][0]['children'] = [400000]
    assert boundary(*observations) == 'WAIT_STAGE_RUNNING'


@pytest.mark.parametrize('sample', [0, 1])
def test_other_process_referencing_pilot_refuses_boundary(tmp_path, sample):
    observations = pair(observation(tmp_path))
    observations[sample]['processes'].append({'kind': 'stage', 'pid': 400000, 'references': ['cwd']})
    assert boundary(*observations) == 'WAIT_STAGE_RUNNING'


def test_unreleased_lease_blocks_even_without_child(tmp_path):
    snap = observation(tmp_path)
    latest = Path(snap['latest_update'])
    touch(latest, 'nested/export_lease.json')
    snap.update(disk_state(latest.parent))
    assert snap['leases'] == [str(latest / 'nested/export_lease.json')]
    assert boundary(*pair(snap)) == 'WAIT_LEASE_HELD'
    touch(latest, 'nested/export_lease_end.json')
    snap.update(disk_state(latest.parent))
    assert boundary(*pair(snap)) == 'READY'


def test_summary_precludes_preallocation_boundary(tmp_path):
    snap = observation(tmp_path)
    touch(Path(snap['latest_update']), 'summary.json')
    snap.update(disk_state(Path(snap['latest_update']).parent))
    assert boundary(*pair(snap)) == 'WAIT_SUMMARY_PRESENT'


@pytest.mark.parametrize('new_wchan', ['futex_wait_queue', '0', 'do_wait'])
def test_wchan_changes_between_observations(tmp_path, new_wchan):
    first, second = pair(observation(tmp_path))
    second['processes'][0]['wchan'] = new_wchan
    assert boundary(first, second) == 'WAIT_WCHAN'


@pytest.mark.parametrize('state', ['R', 'T', 'Z'])
def test_sleep_wchan_requires_sleeping_process(tmp_path, state):
    snap = observation(tmp_path)
    snap['processes'][0]['state'] = state
    assert boundary(*pair(snap)) == 'WAIT_WCHAN'


@pytest.mark.parametrize('count', [0, 2])
def test_exactly_one_runner_required(tmp_path, count):
    snap = observation(tmp_path)
    snap['processes'] = [deepcopy(snap['processes'][0]) for _ in range(count)]
    assert boundary(*pair(snap)) == 'WAIT_RUNNER_IDENTITY'


@pytest.mark.parametrize('member', ['runner', 'shell'])
def test_pid_reuse_between_samples(tmp_path, member):
    first, second = pair(observation(tmp_path))
    runner = second['processes'][0]
    target = runner if member == 'runner' else runner['process_group_members'][0]
    target['start_ticks'] = 'reused'
    assert boundary(first, second) == 'WAIT_RUNNER_IDENTITY'


@pytest.mark.parametrize('missing', ['plans.json', 'cells.json'])
def test_generate_requires_both_input_files(tmp_path, missing):
    snap = observation(tmp_path, phase='generate')
    (Path(snap['latest_update']) / missing).unlink()
    snap.update(disk_state(Path(snap['latest_update']).parent))
    assert boundary(*pair(snap)) == 'WAIT_PREALLOCATION'


@pytest.mark.parametrize('phase,lease', [('generate', 'generate_lease'), ('optimize', 'update_lease')])
def test_completed_stage_lease_is_not_a_preallocation_state(tmp_path, phase, lease):
    snap = observation(tmp_path, phase=phase)
    touch(Path(snap['latest_update']), f'{lease}.json', f'{lease}_end.json')
    snap.update(disk_state(Path(snap['latest_update']).parent))
    assert not snap['leases']
    assert boundary(*pair(snap)) == 'WAIT_PREALLOCATION'


def test_missing_update_is_not_ready(tmp_path):
    snap = observation(tmp_path)
    empty = tmp_path / 'empty'
    empty.mkdir()
    snap.update(disk_state(empty))
    assert snap['latest_update'] is None
    assert boundary(*pair(snap)) == 'WAIT_PREALLOCATION'


def test_disk_state_uses_latest_numbered_update_only(tmp_path):
    snap = observation(tmp_path)
    pilot = Path(snap['latest_update']).parent
    touch(pilot / 'update_00011', 'old_lease.json')
    touch(pilot / 'update_00013', 'plans.json', 'cells.json')
    touch(pilot / 'update_99999_partial', 'summary.json', 'busy_lease.json')
    state = disk_state(pilot)
    assert state['latest_update'] == str(pilot / 'update_00013')
    assert not state['leases'] and not state['lease_files']
    snap.update(state)
    assert boundary(*pair(snap)) == 'READY'


@pytest.mark.parametrize('change', ['latest_update', 'files', 'lease_files'])
def test_mixed_disk_states_across_samples_refuse(tmp_path, change):
    first, second = pair(observation(tmp_path))
    if change == 'latest_update':
        second[change] = str(Path(second[change]).with_name('update_00013'))
    elif change == 'files':
        second[change]['cells.json'] = False  # Optimize evidence still independently passes.
    else:
        second[change].append('/synthetic/completed_lease.json')
    assert boundary(first, second) == 'WAIT_DISK_CHANGED'


@pytest.mark.parametrize('change', ['extra_member', 'missing_shell', 'foreign_uid', 'wrong_parent'])
def test_nonisolated_group_refuses(tmp_path, change):
    snap = observation(tmp_path)
    runner = snap['processes'][0]
    group = runner['process_group_members']
    if change == 'extra_member':
        group.append({'pid': 400000})
    elif change == 'missing_shell':
        group.pop(0)
    elif change == 'foreign_uid':
        group[0]['uid'] += 1
    else:
        runner['ppid'] = 400000
    assert boundary(*pair(snap)) == 'WAIT_RUNNER_IDENTITY'


@pytest.mark.parametrize('elapsed,expected', [(0, 'WAIT_OBSERVATION_INTERVAL'),
                                            (0.999, 'WAIT_OBSERVATION_INTERVAL'),
                                            (1.0, 'READY'), (1.2, 'READY')])
def test_observation_interval(tmp_path, elapsed, expected):
    first, second = pair(observation(tmp_path))
    second['observed_monotonic'] = first['observed_monotonic'] + elapsed
    assert boundary(first, second) == expected


def test_old_pane_text_rule_never_passed_on_observed_blank_panes(tmp_path):
    snap = observation(tmp_path)
    old_pane_text_condition = 'waiting for an idle GPU' in snap['pane_text']
    assert old_pane_text_condition is False
    assert boundary(*pair(snap)) == 'READY'
    snap['pane_text'] = 'waiting for an idle GPU'
    snap['processes'][0]['children'] = [400000]
    assert boundary(*pair(snap)) == 'WAIT_STAGE_RUNNING'


def test_stopped_rule_retains_pre_stop_sleep_evidence(tmp_path):
    before = pair(observation(tmp_path))
    stopped = frozen_pair(before[1])
    assert boundary(*stopped) == 'WAIT_WCHAN'
    assert boundary(*stopped, frozen_from=before) == 'READY'


@pytest.mark.parametrize('change,expected', [
    ('child', 'WAIT_STAGE_RUNNING'), ('lease', 'WAIT_LEASE_HELD'),
    ('summary', 'WAIT_SUMMARY_PRESENT'), ('disk', 'WAIT_DISK_CHANGED'),
    ('pid_reuse', 'WAIT_RUNNER_IDENTITY'), ('running_shell', 'WAIT_NOT_STOPPED'),
])
def test_stop_recheck_applies_whole_rule(tmp_path, change, expected):
    before = pair(observation(tmp_path))
    first, second = frozen_pair(before[1])
    runner = second['processes'][0]
    if change == 'child':
        runner['children'] = [400000]
    elif change == 'lease':
        second['leases'] = ['/synthetic/new_lease.json']
    elif change == 'summary':
        second['files']['summary.json'] = True
    elif change == 'disk':
        second['latest_update'] = '/synthetic/update_00013'
    elif change == 'pid_reuse':
        runner['start_ticks'] = 'reused'
    else:
        runner['process_group_members'][0]['state'] = 'R'
    assert boundary(first, second, frozen_from=before) == expected


def test_invalid_pre_stop_pair_cannot_authorize_stopped_pair(tmp_path):
    before = pair(observation(tmp_path))
    stopped = frozen_pair(before[1])
    before[0]['processes'][0]['wchan'] = 'futex_wait_queue'
    assert boundary(*stopped, frozen_from=before) == 'WAIT_RACE'


@pytest.mark.parametrize('suffix,expected', [('', True), ('/plans.json', True), ('_other', False)])
def test_argv_reference_matching_respects_directory_boundary(tmp_path, suffix, expected):
    pilot = tmp_path / 'A_1302'
    pilot.mkdir()
    refs = references({'pid': os.getpid(), 'command': f'worker --input {pilot}{suffix}'}, pilot)
    assert ('argv' in refs) is expected


def test_open_file_reference_detected_without_argv_reference(tmp_path):
    pilot = tmp_path / 'A_1302'
    pilot.mkdir()
    with (pilot / 'input.json').open('w') as opened:
        refs = references({'pid': os.getpid(), 'command': 'synthetic unrelated command'}, pilot)
        assert f'fd/{opened.fileno()}' in refs
        assert 'argv' not in refs


def test_cwd_reference_detected_in_owned_cpu_child(tmp_path):
    pilot = tmp_path / 'A_1302'
    pilot.mkdir()
    child = subprocess.Popen([sys.executable, '-c',
                              'import sys; print("ready", flush=True); sys.stdin.read()'],
                             cwd=pilot, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline() == 'ready\n'
        refs = references({'pid': child.pid, 'command': 'synthetic unrelated command'}, pilot)
        assert 'cwd' in refs and 'argv' not in refs
    finally:
        child.communicate(timeout=10)
    assert child.returncode == 0
