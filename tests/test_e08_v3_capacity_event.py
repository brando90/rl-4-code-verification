"""Verify alternate capacity events are finite, explicit and free of polling churn."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location('e08_capacity_event', HERE / 'probe_capacity_event.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


@pytest.fixture
def armed(tmp_path):
    owner = {'pid': 123, 'boot_id': 'fixture', 'start_ticks': '456'}
    records = {
        'recovery_config.json': {'recovery_deadline_unix': 100},
        'recovery_state.json': {'attempts': [{'attempt': 'recovery-01', 'started_unix': 1}]},
        'owner_ack.json': {'owner': owner, 'attempt': 'recovery-01'},
        'owner_handoff.json': {'owner': owner, 'attempt': 'recovery-01', 'released': True, 'mode': 'EXTERNAL_RESOURCE_WAIT'},
        'external_resource_wait.json': {'schema': 1, 'status': 'EXTERNAL_RESOURCE_WAIT', 'owner': owner,
                                       'attempt': 'recovery-01', 'independent_work_complete': True,
                                       'admissions_absent_at_recording': True, 'deadline_unix': 100,
                                       'recorded_unix': 2, 'phase_snapshot': {'a': {}, 'b': {}},
                                       'expected_remote_admissions': ['remote_E_8b.json']}}
    for name, value in records.items(): (tmp_path / name).write_text(json.dumps(value))
    return tmp_path


def test_slurm_requires_authorized_account_exact_hardware_and_idle_node():
    nodes = '\n'.join(['NodeName=ampere1 State=IDLE Gres=gpu:a100:8(S:0-1)',
                       'NodeName=ampere2 State=MIXED Gres=gpu:a100:8',
                       'NodeName=ampere3 State=IDLE+DRAIN Gres=gpu:a100:8',
                       'NodeName=ampere4 State=IDLE Gres=gpu:a100:7',
                       'NodeName=ampere7 State=IDLE Gres=gpu:a100:7',
                       'NodeName=hyperturing2 State=IDLE Gres=gpu:rtx8000:10'])
    assert not m.parse_slurm('Cluster User Account\n', nodes)['eligible']
    result = m.parse_slurm(' il brando9 infolab\n', nodes)
    assert result['eligible'] and result['idle_eight_gpu_nodes'] == ['ampere1']
    assert not m.parse_slurm(' il another_user infolab\n', nodes)['eligible']
    with pytest.raises(ValueError): m.parse_slurm(' il brando9 infolab\n', 'malformed')


@pytest.mark.parametrize('change', ['unarmed', 'deadline', 'attempt', 'owner', 'not_released', 'work_remains'])
def test_no_probe_without_current_finite_release(armed, change):
    wait = m.read(armed / 'external_resource_wait.json')
    now = 10
    if change == 'unarmed': (armed / 'external_resource_wait.json').unlink()
    elif change == 'deadline': now = 100
    elif change == 'attempt': wait['attempt'] = 'recovery-00'
    elif change == 'owner': wait['owner'] = {'pid': 987}
    elif change == 'not_released':
        m.write(armed / 'owner_handoff.json', {'released': False})
    else: wait['independent_work_complete'] = False
    if change not in ('unarmed',): m.write(armed / 'external_resource_wait.json', wait)
    probe = lambda: pytest.fail('unarmed or expired probe')
    assert m.observe(armed, now, probe, probe)['status'] == 'UNARMED_OR_EXPIRED'


def test_only_actionable_changes_increment_event_sequence(armed):
    unavailable = lambda: {'eligible': False}
    a = m.observe(armed, 10, unavailable, unavailable, clock=lambda: 10)
    b = m.observe(armed, 20, unavailable, unavailable, clock=lambda: 20)
    assert a['sequence'] == b['sequence'] and a['fingerprint'] == b['fingerprint']
    local = lambda: {'eligible': True, 'available': [0, 1, 2, 3, 4]}
    c = m.observe(armed, 30, local, unavailable, clock=lambda: 30)
    assert c['sequence'] == b['sequence'] + 1 and c['route']['eligible']
    different_free_ids = lambda: {'eligible': True, 'available': [0, 2, 3, 4, 5]}
    d = m.observe(armed, 40, different_free_ids, unavailable, clock=lambda: 40)
    assert d['sequence'] == c['sequence'] and d['fingerprint'] == c['fingerprint']


def test_14b_wait_does_not_wake_for_four_device_local_route(armed):
    wait = m.read(armed / 'external_resource_wait.json')
    wait['expected_remote_admissions'] = ['remote_E_14b.json']
    m.write(armed / 'external_resource_wait.json', wait)
    result = m.observe(armed, 10, lambda: pytest.fail('8B already done'), lambda: {'eligible': False}, clock=lambda: 10)
    assert not result['route']['eligible']


def test_failed_probe_keeps_error_and_never_fabricates_eligibility(armed):
    def fail(): raise RuntimeError('inventory unavailable')
    event = m.observe(armed, 10, fail, fail, clock=lambda: 10)
    assert not event['route']['eligible']
    obs = m.read(armed / 'capacity_event_observation.json')
    assert set(obs['errors']) == {'local_four_devices', 'slurm'}


@pytest.mark.parametrize('field,value', [('expected_remote_admissions', []), ('expected_remote_admissions', ['remote_E_4b.json']),
                                         ('phase_snapshot', {}), ('recorded_unix', 'bad'), ('deadline_unix', 101)])
def test_malformed_wait_never_probes(armed, field, value):
    wait = m.read(armed / 'external_resource_wait.json'); wait[field] = value
    m.write(armed / 'external_resource_wait.json', wait)
    probe = lambda: pytest.fail('invalid wait probed')
    assert m.observe(armed, 10, probe, probe)['status'] == 'UNARMED_OR_EXPIRED'


@pytest.mark.parametrize('change', ['deadline_crossed', 'attempt_changed', 'corrupt_event'])
def test_final_fence_preserves_stale_or_malformed_event(armed, change):
    prior = armed / 'external_capacity_event.json'
    if change == 'corrupt_event': prior.write_text('{bad')
    def probe():
        if change == 'attempt_changed':
            m.write(armed / 'recovery_state.json', {'attempts': [{'attempt': 'recovery-02', 'started_unix': 12}]})
        return {'eligible': True}
    result = m.observe(armed, 10, probe, lambda: {'eligible': False}, clock=lambda: 100 if change == 'deadline_crossed' else 15)
    assert result['status'] == ('INVALID_PREVIOUS_EVENT' if change == 'corrupt_event' else 'STALE_BEFORE_WRITE')
    assert not (armed / 'capacity_event_observation.json').exists()
    assert not prior.exists() if change != 'corrupt_event' else prior.read_text() == '{bad'


def test_four_device_local_route_includes_large_model_inference(armed):
    wait = m.read(armed / "external_resource_wait.json")
    wait["expected_remote_admissions"] = ["remote_gen_v3_E_14b_f0p5.json"]
    m.write(armed / "external_resource_wait.json", wait)
    result = m.observe(armed, 10, lambda: {"eligible": True}, lambda: {"eligible": False}, clock=lambda: 10)
    assert result["route"]["alternates"]["local_four_devices"]["devices"] == 4
