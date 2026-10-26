"""Check that the v3 auto-resume supervisor never touches a live trajectory and picks the owner's step for each dead state."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

PATH = Path(__file__).resolve().parents[1] / 'phase2/autoresume_watchdog.py'


def load(tmp_path):
    os.environ['E13V3_WORK'] = str(tmp_path)
    spec = importlib.util.spec_from_file_location('v3_autoresume', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def partial(update, generations=0, scored=False, optimizer_result=False):
    return {'update': update, 'generations': generations, 'scored': scored, 'optimizer_result': optimizer_result}


def test_live_trajectory_is_never_touched(tmp_path):
    w = load(tmp_path)
    for p in ([], [partial(7, 0)], [partial(7, 256, True)], [partial(7, 256, True, True)]):
        assert w.decide(live=True, complete=False, partials=p, restarts={}, next_update=8)[0] == 'skip'


def test_complete_trajectory_is_skipped(tmp_path):
    w = load(tmp_path)
    assert w.decide(live=False, complete=True, partials=[], restarts={}, next_update=31)[0] == 'skip'


def test_dead_states_map_to_owner_steps(tmp_path):
    w = load(tmp_path)
    d = lambda p: w.decide(live=False, complete=False, partials=p, restarts={}, next_update=18)
    assert d([]) == ('launch', 18, 'no partial update')
    assert d([partial(17, 256, True, True)])[:2] == ('account_then_launch', 17)
    assert d([partial(2, 0)])[:2] == ('archive_then_launch', 2)
    assert d([partial(12, 256, True)])[:2] == ('retry', 12)


def test_partial_or_unscored_generation_is_reported_not_resampled(tmp_path):
    w = load(tmp_path)
    for p in ([partial(5, 100)], [partial(5, 256, False)]):
        action, update, detail = w.decide(live=False, complete=False, partials=p, restarts={}, next_update=6)
        assert action == 'diagnose' and update == 5 and 'resampling' in detail
    assert w.decide(live=False, complete=False, partials=[partial(3), partial(4)], restarts={},
                    next_update=5)[0] == 'diagnose'


def test_restart_limit_stops_a_crash_loop(tmp_path):
    w = load(tmp_path)
    limit = {str(12): w.MAX_RESTARTS_PER_UPDATE}
    assert w.decide(live=False, complete=False, partials=[partial(12, 256, True)], restarts=limit,
                    next_update=13)[0] == 'diagnose'
    below = {str(12): w.MAX_RESTARTS_PER_UPDATE - 1}
    assert w.decide(live=False, complete=False, partials=[partial(12, 256, True)], restarts=below,
                    next_update=13)[0] == 'retry'


def test_trajectory_state_reads_only_live_numbered_updates(tmp_path):
    w = load(tmp_path)
    root = tmp_path / 'phase2/pilot/B_1301'
    for name in ('update_00016', 'update_00017', 'update_00011_permission_19h_10-18-2026'):
        (root / name).mkdir(parents=True)
    (root / 'update_00016/summary.json').write_text('{}')
    out = root / 'update_00017/generate/output'; out.mkdir(parents=True)
    for i in range(256):
        (out / f'{i:05d}.generation.json').write_text('{}')
    (root / 'update_00017/score').mkdir(); (root / 'update_00017/score/groups.json').write_text('[]')
    (root / 'update_00017/update/output').mkdir(parents=True)
    (root / 'update_00017/update/output/result.json').write_text('{}')
    state = w.trajectory_state('B', 1301, pilot=tmp_path / 'phase2/pilot')
    assert state['partials'] == [partial(17, 256, True, True)]
    assert state['next_update'] == 18 and state['completed_updates'] == 1 and not state['complete']


def test_session_table_and_trajectory_filter(tmp_path):
    w = load(tmp_path)
    fake = lambda *a, **k: SimpleNamespace(returncode=0, stdout=(
        'rl4cv-e13v3-pilot-B-1301\t0\nrl4cv-e13v3-retry-A-1301-u12\t1\n'
        'rl4cv-e13v3-pilot-B-13010\t0\nother-session\t0\n'))
    table = w.sessions(run=fake)
    assert w.trajectory_sessions('B', 1301, table) == {'rl4cv-e13v3-pilot-B-1301': False}
    assert w.trajectory_sessions('A', 1301, table) == {'rl4cv-e13v3-retry-A-1301-u12': True}


def test_full_resume_guard_ignores_retry_sessions(tmp_path):
    w = load(tmp_path)
    fake = lambda out: (lambda *a, **k: SimpleNamespace(returncode=0, stdout=out))
    retry = '11 python /x/resume_pilot_after_foreign_gpu.py retry A 1301 12\n'
    assert not w.full_resume_running(run=fake(retry))
    assert w.full_resume_running(run=fake('12 python /x/resume_pilot_after_foreign_gpu.py\n'))
    assert w.full_resume_running(run=fake('13 sh -c python /x/e13v3_targeted_resume_10-20.py; sleep 1800\n'))


def test_update_one_retry_is_diagnosed_not_retried(tmp_path):
    w = load(tmp_path)
    action, update, detail = w.decide(live=False, complete=False, partials=[partial(1, 256, True)],
                                      restarts={}, next_update=2)
    assert action == 'diagnose' and update == 1 and 'update_00000' in detail


def test_probes_fail_closed(tmp_path):
    w = load(tmp_path)
    err = lambda code, out='', errtext='': (lambda *a, **k: SimpleNamespace(returncode=code, stdout=out, stderr=errtext))
    import pytest
    with pytest.raises(w.ProbeError):
        w.sessions(run=err(1, errtext='server exited unexpectedly'))
    assert w.sessions(run=err(1, errtext='no server running on /tmp/tmux-1/default')) == {}
    with pytest.raises(w.ProbeError):
        w.sessions(run=err(0, out='garbled-row-without-tab\n'))
    assert w.trajectory_processes('A', 1301, run=err(1)) == []
    with pytest.raises(w.ProbeError):
        w.trajectory_processes('A', 1301, run=err(3))


class FakeRun:
    """Scripted tmux/pgrep: list-sessions answers are consumed in order; pgrep finds nothing."""
    def __init__(self, session_answers):
        self.session_answers = list(session_answers)
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append(argv)
        if argv[:2] == ['tmux', 'list-sessions']:
            answer = self.session_answers.pop(0) if len(self.session_answers) > 1 else self.session_answers[0]
            return answer
        if argv[0] == 'pgrep':
            return SimpleNamespace(returncode=1, stdout='', stderr='')
        return SimpleNamespace(returncode=0, stdout='', stderr='')


class FakeOwner:
    WRAPPER = '#!/bin/sh\nexit 0\n'

    def __init__(self, tmp_path, fail_launch=False):
        self.BIN = tmp_path / 'bin'
        self.ADMISSION = tmp_path / 'admission.json'
        self.calls = []
        self.fail_launch = fail_launch

    def check_admission(self, path):
        self.calls.append(('check_admission',))

    def launch(self, arm, seed):
        self.calls.append(('launch', arm, seed))
        if self.fail_launch:
            raise RuntimeError('launch failed')

    def spawn_retry(self, arm, seed, update):
        self.calls.append(('retry', arm, seed, update))

    def account(self, arm, seed, update, admission):
        self.calls.append(('account', arm, seed, update))

    def archive_without_generations(self, arm, seed, update):
        self.calls.append(('archive', arm, seed, update))


def finished_trajectory(tmp_path, arm='B', seed=1301, updates=3):
    root = tmp_path / 'phase2/pilot' / f'{arm}_{seed}'
    for u in range(1, updates + 1):
        (root / f'update_{u:05d}').mkdir(parents=True)
        (root / f'update_{u:05d}/summary.json').write_text('{}')
    return root


def ok(stdout=''):
    return SimpleNamespace(returncode=0, stdout=stdout, stderr='')


def test_tick_fails_closed_on_tmux_error(tmp_path):
    w = load(tmp_path)
    owner = FakeOwner(tmp_path)
    run = FakeRun([SimpleNamespace(returncode=1, stdout='', stderr='lost server')])
    assert w.tick(run=run, R=owner)['status'] == 'SKIPPED_PROBE_ERROR'
    assert owner.calls == []


def test_tick_rechecks_liveness_before_acting(tmp_path):
    w = load(tmp_path)
    finished_trajectory(tmp_path)
    owner = FakeOwner(tmp_path)
    live_row = ok('rl4cv-e13v3-pilot-B-1301\t0\n')
    # Call order: gate, then (probe, recheck) for A_1301 and A_1302, then B_1301's probe (6th call, dead)
    # and its recheck (7th call, live): the session appeared between snapshot and action.
    answers = [ok('')] * 6 + [live_row] * 20
    run = FakeRun(answers)
    result = w.tick(run=run, R=owner)
    assert result['trajectories']['B_1301']['action'] == 'skip'
    assert result['trajectories']['B_1301']['detail'] == 'became live before action'
    assert not [c for c in owner.calls if c[0] == 'launch' and c[1:] == ('B', 1301)]


def test_tick_reserves_attempt_even_when_action_fails(tmp_path):
    w = load(tmp_path)
    finished_trajectory(tmp_path)
    owner = FakeOwner(tmp_path, fail_launch=True)
    result = w.tick(run=FakeRun([ok('')]), R=owner)
    assert 'launch failed' in result['trajectories']['B_1301']['error']
    state = json.loads((tmp_path / 'phase2/autoresume_state.json').read_text())
    assert state['B_1301'] == {'4': 1}
    assert (tmp_path / 'bin/nvidia-smi').read_text() == FakeOwner.WRAPPER


def test_tick_restart_limit_holds_across_ticks(tmp_path):
    w = load(tmp_path)
    finished_trajectory(tmp_path)
    owner = FakeOwner(tmp_path, fail_launch=True)
    for _ in range(w.MAX_RESTARTS_PER_UPDATE + 2):
        w.tick(run=FakeRun([ok('')]), R=owner)
    launches = [c for c in owner.calls if c == ('launch', 'B', 1301)]
    assert len(launches) == w.MAX_RESTARTS_PER_UPDATE


def test_pause_list_skips_only_listed_trajectories(tmp_path):
    w=load(tmp_path);owner=FakeOwner(tmp_path)
    w.PAUSED.parent.mkdir(parents=True,exist_ok=True)
    w.PAUSED.write_text(json.dumps({'trajectories':['A_1301','P_1302']}))
    result=w.tick(run=FakeRun([ok('')]),R=owner)
    for key in ('A_1301','P_1302'):
        assert result['trajectories'][key]['detail']=='paused (V4-A3)'
    assert result['trajectories']['B_1301']['detail']!='paused (V4-A3)'
    assert not [c for c in owner.calls if c==('launch','A',1301)]


def test_absent_pause_list_preserves_default_and_rejects_b1301(tmp_path):
    import pytest
    w=load(tmp_path)
    assert w.paused_trajectories()==set()
    w.PAUSED.parent.mkdir(parents=True,exist_ok=True)
    w.PAUSED.write_text('{"trajectories":["B_1301"]}')
    with pytest.raises(w.ProbeError):w.paused_trajectories()
    w.PAUSED.write_text('broken')
    with pytest.raises(w.ProbeError):w.paused_trajectories()
