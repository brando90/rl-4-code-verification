"""Keep learning waits uncounted and preserve every closed or unresolved per-run device charge."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_learning_resources', PHASE/'learning_resources.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def allocation():
    return {'phase': 'v2-S2-learning-pilot', 'cumulative_device_hours': 10.,
            'routes': {'skampere1': {}, 'skampere2': {}},
            'run_caps_device_hours': {'A/1301':2.,'A/1302':2.,'B/1301':2.,'C/1301':2.,'P/1301':2.}}


def lease(key, hours, status='RELEASED'):
    return {'phase': 'v2-S2-learning-pilot', 'allocation_sha256': 'allocation-sha', 'run_key': key,
            'status': status, 'device_hours': hours, 'reserved_device_hours': hours}


def test_allocation_and_per_run_costs_cannot_reset():
    rows=[lease('B/1301/0/health',.1),lease('B/1301/1/generate',.5),
          lease('B/1301/1/update',.7,'CLEANUP_REQUIRED'),lease('A/1301/1/generate',1.)]
    r=m.remaining({'leases':rows},allocation(),'allocation-sha','B',1301)
    assert r['allocation_hours']==pytest.approx(7.7) and r['run_hours']==pytest.approx(.7)
    with pytest.raises(ValueError,match='budget cannot reset'):m.remaining({'leases':rows},allocation(),'changed','B',1301)
    with pytest.raises(ValueError,match='duplicate'):m.remaining({'leases':rows+[rows[0]]},allocation(),'allocation-sha','B',1301)
    with pytest.raises(ValueError,match='missing'):m.remaining({'leases':[]},allocation(),'allocation-sha','B',1302)


def fixture(tmp_path, monkeypatch, rows=()):
    leases = tmp_path/'leases'; leases.mkdir(); (leases/'registry.json').write_text(json.dumps({'leases': list(rows)}))
    plan = {'run':{'phase':'pilot','arm':'B','run_seed':1301,'execution_lock':{'sha256':'lock-sha'}}, 'allocation_plan': {}, 'lease_root': str(leases),
            'resource_poll_root': str(tmp_path/'poll')}
    lock = {'allocation_sha256':'allocation-sha',
            'configuration': {k: plan[k] for k in ('lease_root', 'resource_poll_root')},
            'bindings': [{'path': str(p), 'sha256': m.digest(p)} for p in
                         (PHASE/'learning_resources.py', PHASE/'resource_lease.py', PHASE.parent/'phase1/device_watch.py')]}
    monkeypatch.setattr(m, 'verify_learning', lambda *a: ({},lock,'science-sha'))
    monkeypatch.setattr(m, 'verify_allocation', lambda p: (allocation(), 'allocation-sha'))
    return plan


def inventory(host, idle=True):
    return {'host': host, 'inventory_complete': True, 'idle_device_indices': [2] if idle else [],
            'devices': [{'index': 2, 'uuid': 'GPU-authored', 'processes': [] if idle else [{'pid': 1}]}]}


def test_busy_poll_makes_no_claim_or_learning_dispatch_and_retains_each_observation(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'observe', lambda host: inventory(host, False))
    monkeypatch.setattr(m, 'claim', lambda *a, **k: pytest.fail('busy device was claimed'))
    for i in range(2):
        result = m.reserve(plan, update=1, stage_key='health', seconds=300)
        assert result['status'] == 'WAIT_FOR_IDLE_DEVICE' and result['device_claims'] == 0
        assert result['run_seed']==1301 and len(result['observations'])==2
    assert len(list(Path(plan['resource_poll_root']).glob('poll_*.json'))) == 2
    assert not list(tmp_path.rglob('attempt.json'))


def test_fresh_census_releases_unused_claim_when_foreign_process_arrives(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch); seen = []; calls = []
    def observe(host):
        seen.append(host)
        return inventory(host, len(seen) == 1)
    monkeypatch.setattr(m, 'observe', observe)
    monkeypatch.setattr(m, 'claim', lambda *a, **k: {'id': 'owned-reservation', 'uuid': 'GPU-authored'})
    monkeypatch.setattr(m, 'release', lambda root, marker, cleanup_verified:
                        calls.append((marker, cleanup_verified)) or {'status': 'RELEASED'})
    result = m.reserve(plan, update=1, stage_key='health', seconds=300)
    assert result['status'] == 'DEVICE_CHANGED_BEFORE_LAUNCH'
    assert calls == [('owned-reservation', True)] and len(seen) == 2
    assert not list(tmp_path.rglob('attempt.json'))


def test_run_budget_is_enforced_before_device_census_and_duplicate_claim_refused(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch, [lease('B/1301/1/health', 1.99)])
    monkeypatch.setattr(m, 'observe', lambda host: pytest.fail('exhausted budget polled a device'))
    result = m.reserve(plan, update=1, stage_key='generate', seconds=300)
    assert result['status'] == 'RESOURCE_EXHAUSTED' and result['device_claims'] == 0
    with pytest.raises(RuntimeError, match='already claimed'):
        m.reserve(plan, update=1, stage_key='health', seconds=300)


def test_successful_reservation_checks_uuid_twice_and_refuses_moved_ledger(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'observe', inventory)
    monkeypatch.setattr(m, 'claim', lambda *a, **k: {'id': 'owned', 'uuid': 'GPU-authored', 'status': 'ACTIVE'})
    result = m.reserve(plan, update=2, stage_key='update', seconds=600)
    assert result['status'] == 'RESERVED' and len(result['observations']) == 2
    moved = copy.deepcopy(plan); moved['resource_poll_root'] = str(tmp_path/'new-root')
    with pytest.raises(ValueError, match='moved'):
        m.reserve(moved, update=2, stage_key='update', seconds=600)
