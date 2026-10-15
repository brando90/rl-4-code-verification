"""Exercise technical chronology, idle-device resumption, interrupted-stage refusal and finality."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PHASE = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
spec = importlib.util.spec_from_file_location('e13_technical_driver', PHASE/'technical_driver.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return path


def fixture(tmp_path, monkeypatch):
    calls = []; config_path = put(tmp_path/'config.json', {'authored': True})
    config = {'work_root': str(tmp_path/'work'), 'stage_seconds': {'T1': {k: 600 for k in
               ('preflight', 'generate', 'probabilities')}}, 'environment': {}}
    lock = {'configuration': {'technical_ledger': str(tmp_path/'ledger')}}
    plan = {'LP': {'sha256': 'lp-sha'}, 'configuration': str(config_path), 'gate': 'T1', 'attempt': 1,
            'repository': str(tmp_path), 'resource_plan': {'lease_root': str(tmp_path/'leases')}, 'prerequisites': {}}
    monkeypatch.setattr(m, 'authorize', lambda p: (lock, config, 'science-sha'))
    def reserve(p, **kw):
        key = kw['stage_key']; calls.append('claim:'+key)
        lease = {'id': key, 'status': 'ACTIVE'}
        put(tmp_path/'leases'/(key+'.json'), lease)
        return {'status': 'RESERVED', 'lease': lease}
    monkeypatch.setattr(m, 'reserve', reserve)
    def dynamic(c, gate, key, root, lease):
        return put(root/key/'runtime.json', {'stage_key': key})
    monkeypatch.setattr(m, 'dynamic_config', dynamic)
    def prepare(**kw):
        key = kw['stage_key']; calls.append('prepare:'+key)
        if key == 'preflight': assert kw['attempt_path'] is None
        else: assert Path(kw['attempt_path']).exists() and kw['preflight']
        return Path(kw['config_path'])
    monkeypatch.setattr(m, 'prepare', prepare)
    def launch(path, **kw):
        key = path.parent.name; calls.append('run:'+key)
        put(tmp_path/'leases'/(key+'.json'), {'id': key, 'status': 'RELEASED'})
        if key == 'preflight':
            put(path.parent/'health/preflight.json', {'status': 'PASS', 'scope': 'non-probe infrastructure only',
                'admission_statistics_computed': False, 'generated_tokens': 1, 'visible_index': '2'})
        return {'status': 'RUNTIME_FINISHED'}
    monkeypatch.setattr(m, 'launch_local', launch)
    def admit(root, gate, **kw):
        calls.append('admit'); assert 'run:preflight' in calls and 'run:generate' not in calls
        path = put(Path(root)/gate/'attempt_1/attempt.json', {'attempt': 1})
        return path.parent, {'attempt': 1}
    monkeypatch.setattr(m, 'admit', admit)
    monkeypatch.setattr(m, 'evaluate', lambda *a: calls.append('evaluate') or {'gate': 'T1', 'status': 'PASS'})
    return plan, calls, reserve


def test_full_gate_executes_health_before_attempt_and_each_stage_once(tmp_path, monkeypatch):
    plan, calls, reserve = fixture(tmp_path, monkeypatch)
    result = m.tick(plan)
    assert result['status'] == 'COMPLETE' and result['result']['status'] == 'PASS'
    assert calls == ['claim:preflight', 'prepare:preflight', 'run:preflight', 'admit',
                     'claim:generate', 'prepare:generate', 'run:generate',
                     'claim:probabilities', 'prepare:probabilities', 'run:probabilities', 'evaluate']
    count = len(calls)
    assert m.tick(plan) == result and len(calls) == count


def test_busy_device_is_resumable_without_counting_or_replaying_health(tmp_path, monkeypatch):
    plan, calls, reserve = fixture(tmp_path, monkeypatch)
    busy = {'value': True}
    def sometimes(p, **kw):
        if kw['stage_key'] == 'generate' and busy['value']:
            return {'status': 'WAIT_FOR_IDLE_DEVICE'}
        return reserve(p, **kw)
    monkeypatch.setattr(m, 'reserve', sometimes)
    assert m.tick(plan)['status'] == 'WAIT_FOR_IDLE_DEVICE'
    assert calls.count('admit') == 1 and 'run:generate' not in calls
    busy['value'] = False
    assert m.tick(plan)['status'] == 'COMPLETE'
    assert calls.count('run:preflight') == calls.count('admit') == 1


def test_existing_running_state_requires_reconciliation_not_automatic_execution(tmp_path, monkeypatch):
    plan, calls, reserve = fixture(tmp_path, monkeypatch)
    put(tmp_path/'work/T1/attempt_1/state.json', {'condition': 'v2-S2', 'gate': 'T1', 'status': 'RUNNING',
        'next_stage': 'generate', 'LP_sha256': 'lp-sha', 'configuration_sha256': m.digest(plan['configuration'])})
    assert m.tick(plan)['status'] == 'RECOVERY_REQUIRED' and calls == []


def test_preparation_exception_releases_claim_and_leaves_durable_unresolved_state(tmp_path, monkeypatch):
    plan, calls, reserve = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(m, 'dynamic_config', lambda *a: (_ for _ in ()).throw(ValueError('authored preparation defect')))
    import resource_lease, lp1
    monkeypatch.setattr(lp1, 'cleanup', lambda marker: calls.append('cleanup:'+marker) or {'verified': True})
    monkeypatch.setattr(resource_lease, 'release', lambda root, marker, cleanup_verified:
                        calls.append(('release', marker, cleanup_verified)))
    with pytest.raises(ValueError, match='authored preparation defect'): m.tick(plan)
    assert calls == ['claim:preflight', 'cleanup:preflight', ('release', 'preflight', True)]
    assert m.tick(plan)['status'] == 'RECOVERY_REQUIRED'


def test_materialization_preserves_static_hashes_and_binds_predecessor_receipts(tmp_path):
    static = tmp_path/'policy.json'; static.write_text('{}')
    cells = put(tmp_path/'cells.json', [{'cell_id': 'authored'}])
    config = {'runtime': {'bindings': [m.reference(static)]}, 'probability_probe': m.reference(cells)}
    root = tmp_path/'work'; put(root/'generate/output/result.json', {'status': 'COMPLETE'})
    result = m.dynamic_config(config, 'T1', 'probabilities', root, {'id': 'authored-lease'})
    rendered = json.loads(result.read_text())
    assert {r['path'] for r in rendered['bindings']} == {
        str(static), str(cells), str(root/'generate/output/result.json')}
    assert rendered['generation_root'] == str(root/'generate/output')
    static.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='immutable runtime input'):
        m.dynamic_config(config, 'T1', 'preflight', root, {'id': 'authored-lease'})
    assert not (root/'preflight').exists()


def test_actual_synthetic_T1_evaluation_is_exclusive_and_retains_raw_receipts(tmp_path):
    cell = {'cell_id': 'authored', 'task_id': 'train', 'split': 'train', 'seed': 1, 'prompt_token_ids': [12]}
    cells = put(tmp_path/'cells.json', [cell])
    root = tmp_path/'work'; out = root/'probabilities/output'
    put(out/'result.json', {'status': 'COMPLETE', 'completed': 1})
    put(out/'00000.probability.json', {**cell, 'output_token_ids': [151645], 'finish_reason': 'stop',
        'generation_logprobs': [-.1], 'trainer_input_ids': [12, 151645],
        'trainer_token_mask': [0, 1], 'trainer_logprobs': [0., -.1]})
    attempt = put(tmp_path/'admission/attempt.json', {'gate': 'T1', 'attempt': 1,
        'LP_sha256': 'authored-LP', 'science_sha256': 'authored-science'})
    config = {'probability_probe': m.reference(cells)}
    result = m.evaluate('T1', config, root, attempt)
    assert result['status'] == 'PASS' and result['responses'] == 1 and result['generated_tokens'] == 1
    assert (attempt.parent/'evaluation_attempt.json').exists() and len(result['inputs']) == 2
    with pytest.raises(RuntimeError, match='already closed'): m.evaluate('T1', config, root, attempt)


def test_T3_source_is_resolved_only_from_the_published_T2_inventory(tmp_path, monkeypatch):
    source = put(tmp_path/'work/T2/attempt_2/update/output/result.json', {'status': 'MEASURED'})
    probe = put(tmp_path/'probe.json', [{'cell_id': 'authored'}])
    config = {'condition': 'v2-S2', 'host': m.socket.gethostname().split('.')[0], 'runtime': {},
              'work_root': str(tmp_path/'work'), 'probability_probe': m.reference(probe), 'update_probe': m.reference(probe)}
    config_path = put(tmp_path/'configuration.json', config)
    gates = {'G0': {'gate': 'G0_A3', 'status': 'PASS'},
             'LP1': {'condition': 'v2-S2', 'status': 'PASS', 'numerical_dtype': 'float16', 'admission_statistics_computed': True},
             'calibration': {'condition': 'v2-S2', 'status': 'FROZEN', 'C_calibration_admitted': True},
             'G1': {'gate': 'G1', 'status': 'PASS'}, 'H2': {'gate': 'H2', 'status': 'PASS'}}
    paths = [config_path, PHASE/'technical_driver.py', PHASE/'technical_resources.py',
             PHASE/'technical_stage.py', PHASE/'technical_measurements.py', PHASE/'rollout_groups.py']
    lock = {'bindings': m.bindings(paths), 'science': {k: config[k] for k in ('probability_probe', 'update_probe')},
            'phase1_results': gates, 'eligible_arms': ['A', 'B', 'C', 'P']}
    t2 = {'gate': 'T2', 'condition': 'v2-S2', 'status': 'PASS', 'science_sha256': 'science-sha',
          'admission_statistics_computed': True, 'attempt': 2, 'inputs': [m.reference(source)]}
    plan = {'LP': {}, 'repository': str(tmp_path), 'configuration': str(config_path), 'gate': 'T3',
            'resource_plan': {'allocation_plan': {}}, 'prerequisites': {'T2': t2}}
    monkeypatch.setattr(m, 'pilot_lock', lambda *a: (lock, 'science-sha'))
    monkeypatch.setattr(m, 'published', lambda reference, repository: reference)
    import resource_lease
    monkeypatch.setattr(resource_lease, 'verify_allocation', lambda p: ({'routes': {config['host']: {}}}, 'allocation-sha'))
    _, resolved, _ = m.authorize(plan)
    assert resolved['source_update'] == {'path': str(source.parent), 'result_sha256': m.digest(source)}
    assert 'source_update' not in json.loads(config_path.read_text())
    t2['inputs'] = []
    with pytest.raises(ValueError, match='actual source update'): m.authorize(plan)
    t2['status'] = 'FAIL'
    with pytest.raises(ValueError, match='same-science PASS'): m.authorize(plan)
