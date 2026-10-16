"""Check the prospective continuation manifest and loss-token boundaries independently."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3'


def test_budget_boundaries_and_examples_match_admitted_manifest():
    rows = list(csv.DictReader((V3 / 'results/admitted_corpus_manifest.csv').open()))
    for condition in ('R', 'E'):
        pool = [r for r in rows if r['admitted'] == '1' and (condition == 'E' or r['source'] == 'v1_selected')]
        pool.sort(key=lambda r: hashlib.sha256(('rl4cv-e08-v3-sft-order-v1:' + '|'.join(r[k] for k in ('source', 'task_id', 'teacher', 'sample'))).encode()).hexdigest())
        schedule = json.loads((V3 / f'results/sft_schedule_v3_{condition}.json').read_text())
        cumulative = 0
        for i, step in enumerate(schedule['steps']):
            batch = pool[2*i:2*i+2]
            cumulative += sum(int(r['n_assistant_tokens']) + 1 for r in batch)
            assert step['example_ids'] == [r['example_id'] for r in batch]
            assert step['cumulative_loss_tokens'] == cumulative
            assert step['padding_slots'] == 2 - len(batch)
        for fraction, target in [('f0p5', 2876468), ('f1p0', 5752936)]:
            checkpoint = schedule['checkpoints'][fraction]
            step = checkpoint['step']
            assert schedule['steps'][step - 2]['cumulative_loss_tokens'] < target
            assert schedule['steps'][step - 1]['cumulative_loss_tokens'] >= target
            assert checkpoint['overshoot_tokens'] == checkpoint['cumulative_loss_tokens'] - target
        assert schedule['planned_steps'] == schedule['checkpoints']['f1p0']['step']


def test_all_validation_cells_are_unique_and_heldout_test_is_absent():
    manifest = json.loads((V3 / 'results/ladder_manifest_v3.json').read_text())
    splits = list(csv.DictReader((V3.parent / 'expt_v1/results/split/vbv1_split_manifest.csv').open()))
    validation = {r['task_id'] for r in splits if r['split'] == 'validation'}
    systems = {s['label'] for s in manifest['systems']}
    expected = {(s, t, k) for s in systems for t in validation for k in range(8)}
    actual = [(c['system'], c['task_id'], c['sample_idx']) for c in manifest['cells']]
    assert len(systems) == 16 and len(validation) == 135
    assert len(actual) == len(set(actual)) == 17280
    assert set(actual) == expected


def test_forecast_is_frozen_and_has_no_observed_outcomes():
    from rl4cv.forecast import verify_forecast
    path = V3 / 'forecasts/e08_v3_forecast.json'
    assert verify_forecast(path)
    assert json.loads(path.read_text())['outcomes_observed'] is False
