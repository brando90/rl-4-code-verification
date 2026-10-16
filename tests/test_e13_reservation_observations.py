"""Reproduce cloned observation discovery while preserving live conflicts, immutable caps and ledger history."""
import copy
import json
from pathlib import Path
import sys
import pytest

PHASE = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
import reservation_observations as m
from test_e13_phase2_resource_lease import fixture as resource_fixture, claim, m as allocator


def fixture(tmp_path):
    root, inventory, allocation = resource_fixture(tmp_path)
    foreign = tmp_path/'foreign'; foreign.mkdir()
    original = tmp_path/'original.json'; duplicate = foreign/'foreign_reservations.json'
    original.write_text(json.dumps({'scope': 'Read-only foreign lease/reservation review, not an allocation', 'unreleased_records': 0}))
    duplicate.write_bytes(original.read_bytes())
    sha = m.digest(original)
    row = {'path': str(duplicate), 'reference_path': str(original), 'sha256': sha}
    lock = {'configuration': {'reservation_observation_duplicates': [row]},
            'bindings': [{'path': str(p), 'sha256': m.digest(p)} for p in (original, duplicate, Path(m.__file__))]}
    allocation['reservation_inventory']['roots'] = [str(foreign)]
    return root, inventory, allocation, lock, duplicate


def test_real_discovery_failure_then_reconciled_claim_preserves_allocation(tmp_path):
    root, inv, a, lock, duplicate = fixture(tmp_path)
    original = copy.deepcopy(a)
    with pytest.raises(RuntimeError, match='paths changed'):
        claim(root, inv, a)
    b = m.reconcile(a, lock)
    assert a == original
    assert {k:v for k,v in b.items() if k not in ('reservation_inventory','reservation_bindings')} == {k:v for k,v in a.items() if k not in ('reservation_inventory','reservation_bindings')}
    one = claim(root, inv, b)
    assert one['allocation_sha256'] == 'fixed'
    assert one['reservation_bindings'] == [{'path':str(duplicate),'sha256':m.digest(duplicate)}]
    allocator.release(root, one['id'], cleanup_verified=True, now=1900.)
    registry = json.loads((root/'registry.json').read_text())
    assert allocator.accounting(registry, a['phase'], 'fixed') == (.25, 0.)
    with pytest.raises(ValueError, match='cannot reset'):
        claim(root, inv, b, sha='new-allocation')


@pytest.mark.parametrize('which', ['reference_path','path'])
def test_any_changed_observation_fails_closed(tmp_path, which):
    _, _, a, lock, _ = fixture(tmp_path)
    Path(lock['configuration']['reservation_observation_duplicates'][0][which]).write_text('{}')
    with pytest.raises(RuntimeError, match='observation changed'):
        m.reconcile(a, lock)


def test_unreviewed_new_path_still_blocks(tmp_path):
    root, inv, a, lock, duplicate = fixture(tmp_path)
    (duplicate.parent/'new_lease.json').write_text('{}')
    with pytest.raises(RuntimeError, match='paths changed'):
        claim(root, inv, m.reconcile(a, lock))


def test_active_foreign_registry_still_blocks(tmp_path):
    root, inv, a, lock, _ = fixture(tmp_path)
    foreign = tmp_path/'live.json'
    foreign.write_text(json.dumps([{'owner':'another-user','host':'authored-host','devices':[0],'status':'ACTIVE'}]))
    a['foreign_registries'] = [{'path':str(foreign)}]
    with pytest.raises(RuntimeError, match='foreign lease'):
        claim(root, inv, m.reconcile(a, lock))


@pytest.mark.parametrize('change', ['unbound','active','allocation','outside','duplicate'])
def test_reconciliation_rejects_non_observations_or_unbound_inputs(tmp_path, change):
    _, _, a, lock, duplicate = fixture(tmp_path)
    row = lock['configuration']['reservation_observation_duplicates'][0]
    if change == 'unbound': lock['bindings'] = lock['bindings'][:-1]
    elif change == 'outside': a['reservation_inventory']['roots'] = []
    elif change == 'duplicate': lock['configuration']['reservation_observation_duplicates'].append(dict(row))
    else:
        value=json.loads(duplicate.read_text())
        if change == 'active': value['unreleased_records']=1
        else: value['scope']='allocation'
        duplicate.write_text(json.dumps(value));Path(row['reference_path']).write_bytes(duplicate.read_bytes())
        row['sha256']=m.digest(duplicate)
        for b in lock['bindings'][:2]: b['sha256']=row['sha256']
    with pytest.raises(ValueError): m.reconcile(a, lock)
