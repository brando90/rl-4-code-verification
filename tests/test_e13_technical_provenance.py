"""Reproduce the T2 missing-provenance failure and check technical and learning metadata before device work."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

PHASE = Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0, str(PHASE))
import technical_driver
import a6_technical_driver
import technical_runtime as runtime
import trainer_core


def materialized(tmp_path, module, key):
    cells = tmp_path/'probe.json'; cells.write_text('[]')
    policy = tmp_path/'policy.json'; policy.write_text('{}')
    root = tmp_path/'T2/attempt_2'
    (root/'score').mkdir(parents=True)
    (root/'score/groups.json').write_text('[]')
    config = {'runtime': {'condition': 'v2-S2', 'run_seed': 1302201,
                         'terminal_token_ids': [151643, 151645], 'loss_config': {'frozen': True},
                         'bindings': [module.reference(policy)]},
              'probability_probe': module.reference(cells)}
    original = copy.deepcopy(config)
    path = module.dynamic_config(config, 'T2', key, root, {'id': 'authored-lease'})
    assert config == original
    return json.loads(path.read_text()), root


@pytest.mark.parametrize('module', [technical_driver, a6_technical_driver])
def test_generated_metadata_reaches_update_and_missing_legacy_field_reproduces_keyerror(tmp_path, monkeypatch, module):
    config, root = materialized(tmp_path, module, 'update')
    calls = []
    @contextmanager
    def session(*args, **kwargs):
        yield object(), SimpleNamespace(pad_token_id=151643)
    monkeypatch.setattr(trainer_core, 'policy_session', session)
    monkeypatch.setattr(trainer_core, 'update', lambda *args, **kwargs: calls.append(kwargs) or {'authored': True})
    # Isolate the original failing invocation after model construction. The
    # historical configuration had every same field except provenance.
    monkeypatch.setattr(runtime, 'verify', lambda *args: None)
    legacy = {k: v for k, v in config.items() if k != 'provenance'}
    with pytest.raises(KeyError, match='provenance'):
        runtime.run(legacy, 'update')
    assert calls == []
    assert runtime.run(config, 'update') == {'authored': True}
    assert len(calls) == 1 and calls[0]['provenance'] == {
        'condition': 'v2-S2', 'gate': 'T2', 'stage': 'update',
        'attempt_root': str(root), 'run_seed': 1302201}
    assert calls[0]['loss_config'] == {'frozen': True} and calls[0]['replay'] is False


@pytest.mark.parametrize('module', [technical_driver, a6_technical_driver])
def test_nonprobe_materialization_covers_the_same_metadata_requirement(tmp_path, module):
    config, root = materialized(tmp_path, module, 'preflight')
    result = runtime.provenance_preflight(config)
    assert result['status'] == 'PASS' and result['model_calls'] == result['optimizer_updates'] == 0
    assert result['admission_statistics_computed'] is False
    assert result['provenance']['stage'] == 'preflight'


@pytest.mark.parametrize('stage', ['preflight', 'evaluation_preflight', 'update'])
@pytest.mark.parametrize('value', [None, {}, {'condition': 'v2-S2', 'run_seed': 2},
                                 {'condition': 'v2-S2', 'run_seed': True}])
def test_bad_metadata_rejected_before_binding_reads_or_model_construction(stage, value):
    config = {'condition': 'v2-S2', 'stage': stage, 'run_seed': 1, 'provenance': value}
    with pytest.raises(ValueError, match='runtime provenance'):
        runtime.verify(config, stage)


def test_existing_pilot_and_main_metadata_remains_compatible():
    for phase in ('pilot', 'main'):
        provenance = {'condition': 'v2-S2', 'phase': phase, 'arm': 'B', 'run_seed': 1301,
                      'update': 1, 'execution_sha256': 'authored'}
        result = runtime.provenance_preflight({'provenance': provenance, 'run_seed': 1301})
        assert result['provenance'] == provenance and result['status'] == 'PASS'
