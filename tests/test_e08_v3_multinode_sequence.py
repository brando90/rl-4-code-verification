"""The replay sequencer requires verified native completion and never replays a dispatch."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
import multinode_sequence as seq


def ready():
    ident = {'pid': 123, 'boot_id': 'boot', 'start_ticks': '456'}
    config = {'deadline_unix': 100, 'e_root': '/owned/E', 'e_identity': ident}
    snapshot = {'deadline_unix': 100, 'r_admission': {},
        'e_admission': {'root': '/owned/E', 'identity': ident},
        'e_receipt': {'identity': ident, 'exit_code': 0}, 'e_alive': False,
        'e_result': {'root': '/owned/E', 'status': 'PASS',
            'transport_exits': {host: 0 for host in seq.multi.DEVICE_PLAN},
            'cleanup': {host: {'status': 'STOPPED', 'remaining_children': [], 'watchdog_exit_code': -15}
                        for host in seq.multi.DEVICE_PLAN}},
        'e_coordinator_alive': False,
        'participants': [{'root': '/owned/E', 'status': 'RELEASED'} for _ in range(3)],
        'local_lease_released': True, 'scheduler_alive': True,
        'jobs': {'verify_E_14b': {'status': 'DONE', 'identity': ident, 'exit_code': 0},
                 'train_R_14b': {'status': 'RUNNING'}},
        'verify_receipt': {'identity': ident, 'exit_code': 0}, 'r_controller_alive': True}
    return deepcopy(config), deepcopy(snapshot)


def test_exact_verified_expansion_and_live_replay_controller_allow_capacity_check():
    config, snap = ready()
    assert seq.transition(config, snap, 10) == 'CHECK_CAPACITY'


@pytest.mark.parametrize('mutation', [
    lambda s: s['e_receipt'].update(exit_code=1),
    lambda s: s['e_receipt']['identity'].update(start_ticks='reused'),
    lambda s: s['e_result'].update(status='FAIL'),
    lambda s: s['e_result']['cleanup']['skampere1'].update(remaining_children=[{'pid': 1}]),
    lambda s: s.update(local_lease_released=False),
    lambda s: s.update(scheduler_alive=False),
    lambda s: s['jobs']['verify_E_14b'].update(status='FAILED'),
    lambda s: s.update(r_controller_alive=False),
])
def test_native_failure_reused_pid_or_incomplete_cleanup_never_admits(mutation):
    config, snap = ready(); mutation(snap)
    with pytest.raises(AssertionError):
        seq.transition(config, snap, 10)


def test_existing_replay_is_preserved_without_duplicate_even_if_expansion_failed():
    config, snap = ready(); snap['r_admission'] = {'identity': {'pid': 999}}
    snap['e_receipt']['exit_code'] = 1
    assert seq.transition(config, snap, 10) == 'PRESERVE_R_ADMISSION'


def test_dead_native_process_without_terminal_receipt_is_not_success():
    config, snap = ready(); snap['e_receipt'].pop('exit_code')
    with pytest.raises(AssertionError, match='disappeared'):
        seq.transition(config, snap, 10)
    snap['e_alive'] = True
    assert seq.transition(config, snap, 10) == 'WAIT_EXPANSION'


def test_waits_for_cleanup_verification_and_scheduler_created_replay():
    config, snap = ready(); snap['e_result'] = {}; snap['e_coordinator_alive'] = True
    assert seq.transition(config, snap, 10) == 'WAIT_EXPANSION_CLEANUP'
    config, snap = ready(); snap['jobs']['verify_E_14b']['status'] = 'RUNNING'
    assert seq.transition(config, snap, 10) == 'WAIT_EXPANSION_VERIFICATION'
    config, snap = ready(); snap['jobs'].pop('train_R_14b')
    assert seq.transition(config, snap, 10) == 'WAIT_REPLAY_CONTROLLER'


def test_expired_or_changed_deadline_cannot_admit():
    config, snap = ready()
    with pytest.raises(AssertionError, match='deadline reached'):
        seq.transition(config, snap, 100)
    snap['deadline_unix'] = 101
    with pytest.raises(AssertionError, match='deadline changed'):
        seq.transition(config, snap, 10)


def test_source_change_is_a_hard_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(seq, 'HERE', tmp_path)
    p = tmp_path / 'source.py'; p.write_text('original')
    config = {'source_sha256': {'source.py': hashlib.sha256(p.read_bytes()).hexdigest()}}
    seq.checked_sources(config); p.write_text('changed')
    with pytest.raises(AssertionError):
        seq.checked_sources(config)


def test_dispatch_claim_is_durable_before_spawn_and_prevents_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(seq, 'ROOT', tmp_path)
    monkeypatch.setattr(seq.multi, 'RUNTIME', tmp_path)
    monkeypatch.setattr(seq.time, 'time', lambda: 1)
    path = tmp_path / 'state.json'; state = {}
    def crash(*args, **kwargs):
        assert seq.read(path)['status'] == 'DISPATCH_CLAIMED'
        raise RuntimeError('interruption after durable claim')
    monkeypatch.setattr(seq.subprocess, 'Popen', crash)
    with pytest.raises(RuntimeError, match='interruption'):
        seq.dispatch_once({'deadline_unix': 100}, state, path)
    with pytest.raises(AssertionError, match='Prior dispatch'):
        seq.dispatch_once({'deadline_unix': 100}, seq.read(path), path)


def test_canonical_admission_appearing_before_spawn_is_adopted(tmp_path, monkeypatch):
    monkeypatch.setattr(seq, 'ROOT', tmp_path); monkeypatch.setattr(seq.multi, 'RUNTIME', tmp_path)
    monkeypatch.setattr(seq.time, 'time', lambda: 1)
    (tmp_path / 'remote_R_14b.json').write_text('{}')
    monkeypatch.setattr(seq.subprocess, 'Popen', lambda *a, **k: pytest.fail('duplicate launch'))
    state = {}; assert seq.dispatch_once({'deadline_unix': 100}, state, tmp_path / 'state.json') is None
    assert state['status'] == 'PRESERVE_R_ADMISSION'
