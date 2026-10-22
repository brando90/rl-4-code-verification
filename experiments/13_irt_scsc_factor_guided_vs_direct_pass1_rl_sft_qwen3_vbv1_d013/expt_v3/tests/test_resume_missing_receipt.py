"""Regress missing checkpoint receipts using isolated files and mocked training/launch boundaries."""
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

from test_autoresume_watchdog import FakeOwner, FakeRun, load, ok

PHASE = Path(__file__).resolve().parents[1] / 'phase2'


def incomplete_update(tmp_path, update=23):
    root = tmp_path / 'phase2/pilot/B_1301'
    previous = root / f'update_{update-1:05d}'
    after = previous / 'update/output/after'
    after.mkdir(parents=True)
    (after / 'receipt.json').write_text('{}')
    (previous / 'summary.json').write_text(json.dumps({'model': str(previous / 'export'),
                                                      'checkpoint': str(after)}))
    work = root / f'update_{update:05d}'
    generated = work / 'generate/output'
    generated.mkdir(parents=True)
    for i in range(256):
        (generated / f'{i:05d}.generation.json').write_text('{}')
    (work / 'score').mkdir()
    (work / 'score/groups.json').write_text('[{"rows": [{"reward": 1}]}]')
    (work / 'update/output').mkdir(parents=True)
    (work / 'update/output/result.json').write_text('{"status":"UNMEASURED","optimizer_updates":0}')
    (work / 'update_lease.json').write_text('{}')
    (work / 'update_lease_end.json').write_text('{}')
    return work, after


@pytest.mark.parametrize("result", [{"status": "UNMEASURED", "optimizer_updates": 0},
                                  {"status": "MEASURED", "optimizer_updates": 1}])
def test_missing_receipt_retries_once_per_tick_and_stops_at_existing_limit(tmp_path, result):
    w = load(tmp_path)
    work, _ = incomplete_update(tmp_path)
    (work / 'update/output/result.json').write_text(json.dumps(result))
    w.ARMS, w.SEEDS = ('B',), (1301,)
    owner = FakeOwner(tmp_path)
    for attempt in range(1, 4):
        report = w.tick(run=FakeRun([ok('')]), R=owner)
        assert report['trajectories']['B_1301']['action'] == 'retry'
        assert json.loads(w.STATE.read_text()) == {'B_1301': {'23': attempt}}
    for _ in range(2):
        report = w.tick(run=FakeRun([ok('')]), R=owner)
        assert report['trajectories']['B_1301']['action'] == 'diagnose'
    assert [c for c in owner.calls if c[0] == 'retry'] == [('retry', 'B', 1301, 23)] * 3
    assert not any(c[0] in ('account', 'launch', 'archive') for c in owner.calls)
    assert not (work / 'summary.json').exists()


def load_helper(monkeypatch):
    # Import only the owner orchestration; never import or construct a real training engine.
    pilot = ModuleType('pilot_run')
    for name in ('PILOT PREPARATION SOURCE allocation check_admission digest execute export '
                 'load_inputs retire_previous score_batch write_new').split():
        setattr(pilot, name, None)
    gates = ModuleType('gates')
    gates.single_rank_gradient = None
    monkeypatch.setitem(sys.modules, 'pilot_run', pilot)
    monkeypatch.setitem(sys.modules, 'gates', gates)
    monkeypatch.syspath_prepend(str(PHASE))
    spec = importlib.util.spec_from_file_location('isolated_resume', PHASE / 'resume_pilot_after_foreign_gpu.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


def test_retry_restores_previous_complete_state_preserves_samples_and_failed_attempt(tmp_path, monkeypatch):
    from contextlib import contextmanager
    h = load_helper(monkeypatch)
    work, previous = incomplete_update(tmp_path)
    h.PILOT = tmp_path / 'phase2/pilot'
    h.log = lambda message: None
    h.digest = lambda path: 'admission-digest'
    (work / 'export').mkdir()
    (work / 'export/stale').write_text('old incomplete export')
    calls = []

    @contextmanager
    def allocation(stage, admission):
        calls.append(('allocation', stage))
        yield 'mock-lease'

    def execute(stage, target, lease, **kwargs):
        assert kwargs['checkpoint'] == str(previous)
        assert kwargs['model'] == str(work.parent / 'update_00022/export')
        assert kwargs['groups_path'] == str(work / 'score/groups.json')
        assert not target.exists()
        after = target / 'output/after'
        after.mkdir(parents=True)
        (after / 'receipt.json').write_text('{}')
        (target / 'output/result.json').write_text('{"optimizer_updates":1}')
        calls.append(('execute', stage))

    def account(*args):
        assert h.optimizer_complete(work)
        calls.append(('account',))

    h.allocation, h.execute, h.account = allocation, execute, account
    h.retry_optimizer('B', 1301, 23, {})
    assert [c[0] for c in calls] == ['allocation', 'execute', 'account']
    assert len(list((work / 'generate/output').glob('*.generation.json'))) == 256
    assert json.loads((work / 'update_failed_permission_10-19-2026/output/result.json').read_text())['status'] == 'UNMEASURED'
    assert (work / 'update_attempt1_lease.json').exists()
    assert (work / 'update_attempt1_lease_end.json').exists()
    assert (work / 'export_failed_optimizer/stale').read_text() == 'old incomplete export'
    assert (previous / 'receipt.json').exists()


def test_account_rejects_result_without_receipt_before_export(tmp_path, monkeypatch):
    h = load_helper(monkeypatch)
    work, _ = incomplete_update(tmp_path)
    h.PILOT = tmp_path / 'phase2/pilot'
    with pytest.raises(RuntimeError, match='no complete optimizer checkpoint'):
        h.account('B', 1301, 23, tmp_path / 'admission.json')
    assert not (work / 'summary.json').exists()


def test_complete_receipt_still_accounts_without_replaying_optimizer(tmp_path, monkeypatch):
    h = load_helper(monkeypatch)
    work, _ = incomplete_update(tmp_path)
    after = work / 'update/output/after'
    after.mkdir(); (after / 'receipt.json').write_text('{}')
    h.PILOT = tmp_path / 'phase2/pilot'
    calls = []
    h.account = lambda *args: calls.append(args)
    h.retry_optimizer('B', 1301, 23, {})
    assert len(calls) == 1
    assert (work / 'update/output/result.json').exists()
    w = load(tmp_path)
    info = w.trajectory_state('B', 1301)
    assert w.decide(live=False, complete=False, partials=info['partials'], restarts={},
                    next_update=24)[0] == 'account_then_launch'


def test_missing_previous_receipt_stops_before_parking_failed_files(tmp_path, monkeypatch):
    h = load_helper(monkeypatch)
    work, _ = incomplete_update(tmp_path)
    h.PILOT = tmp_path / 'phase2/pilot'
    summary = work.parent / 'update_00022/summary.json'
    summary.write_text(json.dumps({'model': 'previous-model', 'checkpoint': str(tmp_path / 'missing')}))
    with pytest.raises(RuntimeError, match='previous completed update'):
        h.retry_optimizer('B', 1301, 23, {})
    assert (work / 'update/output/result.json').exists()
    assert not (work / 'update_failed_permission_10-19-2026').exists()
