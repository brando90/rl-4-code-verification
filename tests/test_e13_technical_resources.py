"""Keep busy-device polls outside gate attempts and account health, failed and reserved device time."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_technical_resources', PHASE/'technical_resources.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def allocation():
    return {'phase': 'v2-S2-technical', 'cumulative_device_hours': 10.,
            'routes': {'skampere1': {}, 'skampere2': {}},
            'technical_gate_caps': {k: {'per_attempt_device_hours': 2., 'cumulative_device_hours': 4.}
                                    for k in ('T1', 'T2', 'T3', 'T4')}}


def lease(key, hours, status='RELEASED'):
    return {'phase': 'v2-S2-technical', 'allocation_sha256': 'allocation-sha', 'run_key': key,
            'status': status, 'device_hours': hours, 'reserved_device_hours': hours}


def test_allocation_gate_attempt_and_health_costs_cannot_reset():
    rows = [lease('T1/1/health', .1), lease('T1/1/generate', .5), lease('T1/2/health', .2),
            lease('T1/2/generate', .7, 'CLEANUP_REQUIRED'), lease('T2/1/update', 1.)]
    r = m.remaining({'leases': rows}, allocation(), 'allocation-sha', 'T1', 2)
    assert r['allocation_hours'] == pytest.approx(7.5)
    assert r['gate_hours'] == pytest.approx(2.5)
    assert r['attempt_hours'] == pytest.approx(1.1)
    with pytest.raises(ValueError, match='budget cannot reset'):
        m.remaining({'leases': rows}, allocation(), 'different-allocation', 'T1', 2)
    with pytest.raises(ValueError, match='duplicate'):
        m.remaining({'leases': rows+[rows[0]]}, allocation(), 'allocation-sha', 'T1', 2)
    with pytest.raises(ValueError, match='allowance'):
        m.remaining({'leases': []}, allocation(), 'allocation-sha', 'T1', 4)


def fixture(tmp_path, monkeypatch, rows=()):
    leases = tmp_path/'leases'; leases.mkdir(); (leases/'registry.json').write_text(json.dumps({'leases': list(rows)}))
    plan = {'LP': {}, 'repository': str(ROOT), 'allocation_plan': {}, 'lease_root': str(leases),
            'resource_poll_root': str(tmp_path/'poll')}
    lock = {'science': {'resource_caps': {'technical_allocation_sha256': 'allocation-sha'}},
            'configuration': {k: plan[k] for k in ('lease_root', 'resource_poll_root')},
            'bindings': [{'path': str(p), 'sha256': m.digest(p)} for p in
                         (PHASE/'technical_resources.py', PHASE/'resource_lease.py', PHASE.parent/'phase1/device_watch.py')]}
    monkeypatch.setattr(m, 'pilot_lock', lambda *a: (lock, 'science-sha'))
    monkeypatch.setattr(m, 'verify_allocation', lambda p: (allocation(), 'allocation-sha'))
    return plan


def inventory(host, idle=True):
    return {'host': host, 'inventory_complete': True, 'idle_device_indices': [2] if idle else [],
            'devices': [{'index': 2, 'uuid': 'GPU-authored', 'processes': [] if idle else [{'pid': 1}]}]}


def test_busy_poll_makes_no_claim_or_gate_attempt_and_retains_each_observation(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'observe', lambda host: inventory(host, False))
    monkeypatch.setattr(m, 'claim', lambda *a, **k: pytest.fail('busy device was claimed'))
    for i in range(2):
        result = m.reserve(plan, gate='T1', attempt=1, stage_key='health', seconds=300)
        assert result['status'] == 'WAIT_FOR_IDLE_DEVICE' and result['device_claims'] == 0
        assert not result['admission_statistics_computed'] and len(result['observations']) == 2
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
    result = m.reserve(plan, gate='T1', attempt=1, stage_key='health', seconds=300)
    assert result['status'] == 'DEVICE_CHANGED_BEFORE_LAUNCH'
    assert calls == [('owned-reservation', True)] and len(seen) == 2
    assert not list(tmp_path.rglob('attempt.json'))


def test_attempt_budget_is_enforced_before_device_census_and_duplicate_claim_refused(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch, [lease('T1/1/health', 1.99)])
    monkeypatch.setattr(m, 'observe', lambda host: pytest.fail('exhausted budget polled a device'))
    result = m.reserve(plan, gate='T1', attempt=1, stage_key='generate', seconds=300)
    assert result['status'] == 'RESOURCE_EXHAUSTED' and result['device_claims'] == 0
    with pytest.raises(RuntimeError, match='already claimed'):
        m.reserve(plan, gate='T1', attempt=1, stage_key='health', seconds=300)


def test_successful_reservation_checks_uuid_twice_and_refuses_moved_ledger(tmp_path, monkeypatch):
    plan = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'observe', inventory)
    monkeypatch.setattr(m, 'claim', lambda *a, **k: {'id': 'owned', 'uuid': 'GPU-authored', 'status': 'ACTIVE'})
    result = m.reserve(plan, gate='T2', attempt=1, stage_key='update', seconds=600)
    assert result['status'] == 'RESERVED' and len(result['observations']) == 2
    moved = copy.deepcopy(plan); moved['resource_poll_root'] = str(tmp_path/'new-root')
    with pytest.raises(ValueError, match='moved'):
        m.reserve(moved, gate='T2', attempt=1, stage_key='update', seconds=600)
