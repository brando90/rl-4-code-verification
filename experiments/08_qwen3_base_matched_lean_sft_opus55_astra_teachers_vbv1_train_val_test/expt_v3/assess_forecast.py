"""Assess the immutable prospective forecast against complete primary gate decisions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN_SHA256 = '7e4ebbe567792d6509bbac2b78b3c5acd782591fea959c0f3a44ff07744efd5f'
FROZEN_CANONICAL_SHA256 = 'dc0db39bb62527d24d26c44a128103182afb9e4d28c575c0528eacc773269684'


def outcome(decisions):
    if any(decisions[f]['status'] != 'COMPLETE' for f in ('f0p5', 'f1p0')):
        return {'status': 'INCOMPLETE', 'condition': None, 'fraction': None}
    for fraction in ('f0p5', 'f1p0'):
        selected = decisions[fraction]['selected']
        if selected:
            return {'status': 'COMPLETE', 'condition': selected, 'fraction': fraction}
    return {'status': 'COMPLETE', 'condition': 'neither', 'fraction': None}


def common_checkpoints(decisions, expected):
    """Expose forecast reachability separately from the earliest selected winner."""
    if any(decisions[f]['status'] != 'COMPLETE' for f in ('f0p5', 'f1p0')):
        return {'status': 'INCOMPLETE', 'earliest_fraction_per_condition': None,
                'predicted_common_checkpoint_reached': None}
    earliest = {c: next((f for f in ('f0p5', 'f1p0')
                         if decisions[f]['common_checkpoint'][c]), None) for c in ('R', 'E')}
    reached = (all(f is None for f in earliest.values()) if expected['condition'] == 'neither'
               else earliest[expected['condition']] == expected['fraction'])
    return {'status': 'COMPLETE', 'earliest_fraction_per_condition': earliest,
            'predicted_common_checkpoint_reached': reached,
            'both_conditions_qualify': all(f is not None for f in earliest.values())}


def assess(summary):
    path = HERE / 'forecasts/e08_v3_forecast.json'
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual_hash == FROZEN_SHA256, 'Prospective forecast was modified'
    forecast = json.loads(path.read_text())
    canonical = json.dumps(forecast, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    assert hashlib.sha256(canonical.encode()).hexdigest() == FROZEN_CANONICAL_SHA256
    assert (HERE / 'forecasts/e08_v3_forecast.sha256').read_text().split()[0] == FROZEN_CANONICAL_SHA256
    ledger = [json.loads(line) for line in (HERE / 'forecasts/forecast_ledger.jsonl').read_text().splitlines()]
    assert any(row['file'] == path.name and row['sha256'] == FROZEN_CANONICAL_SHA256 for row in ledger)
    result = {'forecast_sha256': actual_hash,
              'forecast_canonical_sha256': FROZEN_CANONICAL_SHA256,
              'rule': 'Earliest fraction with a selected condition; both fractions retained in the full decision table',
              'interpretation_note': 'The original operational hit compares the earliest selected winner. The frozen question asks which condition reaches a common checkpoint; common_checkpoint_assessment separately reports the earliest fraction within each condition. These can disagree when both conditions qualify at different fractions; neither verdict replaces the other.'}
    for key, pred in [('primary', 'primary_prediction'), ('sensitivity', 'three_size_sensitivity_prediction')]:
        actual = outcome(summary[key])
        expected = forecast[pred]
        hit = None if actual['status'] != 'COMPLETE' else all(actual[k] == expected[k] for k in ('condition', 'fraction'))
        result[key] = {'prediction': expected, 'outcome': actual, 'hit': hit,
                       'common_checkpoint_assessment': common_checkpoints(summary[key], expected)}
    return result


if __name__ == '__main__':
    summary = json.loads((HERE / 'results/validation_summary_v3.json').read_text())
    result = assess(summary)
    (HERE / 'results/forecast_assessment_v3.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
