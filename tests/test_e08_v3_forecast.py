"""Keep incomplete forecasts unresolved and assess both frozen fractions in order."""
import importlib.util
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parents[1] / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'
spec = importlib.util.spec_from_file_location('e08_forecast_assessment', HERE / 'assess_forecast.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_incomplete_never_becomes_neither():
    assert m.outcome({'f0p5': {'status': 'COMPLETE', 'selected': None},
                      'f1p0': {'status': 'INCOMPLETE'}})['status'] == 'INCOMPLETE'


def test_earliest_selected_fraction_and_neither():
    d = {'f0p5': {'status': 'COMPLETE', 'selected': None}, 'f1p0': {'status': 'COMPLETE', 'selected': 'E'}}
    assert m.outcome(d) == {'status': 'COMPLETE', 'condition': 'E', 'fraction': 'f1p0'}
    d['f0p5']['selected'] = 'R'
    assert m.outcome(d)['fraction'] == 'f0p5'
    d['f0p5']['selected'] = d['f1p0']['selected'] = None
    assert m.outcome(d)['condition'] == 'neither'


def test_modified_forecast_cannot_be_assessed(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'HERE', tmp_path)
    (tmp_path / 'forecasts').mkdir()
    (tmp_path / 'forecasts/e08_v3_forecast.json').write_text('{"edited": true}')
    with pytest.raises(AssertionError, match='Prospective forecast was modified'):
        m.assess({})


def test_existing_frozen_forecast_checks_file_and_canonical_hashes():
    decisions = {'f0p5': {'status': 'INCOMPLETE'}, 'f1p0': {'status': 'INCOMPLETE'}}
    result = m.assess({'primary': decisions, 'sensitivity': decisions})
    assert result['forecast_sha256'] == m.FROZEN_SHA256
    assert result['forecast_canonical_sha256'] == m.FROZEN_CANONICAL_SHA256
    assert result['primary']['hit'] is None and result['sensitivity']['hit'] is None


def test_both_condition_fractions_remain_visible():
    d = {'f0p5': {'status': 'COMPLETE', 'selected': 'R', 'common_checkpoint': {'R': True, 'E': False}},
         'f1p0': {'status': 'COMPLETE', 'selected': 'E', 'common_checkpoint': {'R': False, 'E': True}}}
    assert m.outcome(d)['condition'] == 'R'
    common = m.common_checkpoints(d, {'condition': 'E', 'fraction': 'f1p0'})
    assert common['earliest_fraction_per_condition'] == {'R': 'f0p5', 'E': 'f1p0'}
    assert common['predicted_common_checkpoint_reached'] and common['both_conditions_qualify']
