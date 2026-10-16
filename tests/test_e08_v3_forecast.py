"""Keep incomplete forecasts unresolved and assess both frozen fractions in order."""
import importlib.util
from pathlib import Path

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
