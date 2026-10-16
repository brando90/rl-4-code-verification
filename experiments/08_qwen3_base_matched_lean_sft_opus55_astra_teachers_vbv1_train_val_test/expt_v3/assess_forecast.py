"""Assess the immutable prospective forecast against complete primary gate decisions."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def outcome(decisions):
    if any(decisions[f]['status'] != 'COMPLETE' for f in ('f0p5', 'f1p0')):
        return {'status': 'INCOMPLETE', 'condition': None, 'fraction': None}
    for fraction in ('f0p5', 'f1p0'):
        selected = decisions[fraction]['selected']
        if selected:
            return {'status': 'COMPLETE', 'condition': selected, 'fraction': fraction}
    return {'status': 'COMPLETE', 'condition': 'neither', 'fraction': None}


def assess(summary):
    path = HERE / 'forecasts/e08_v3_forecast.json'
    forecast = json.loads(path.read_text())
    result = {'forecast_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'rule': 'Earliest fraction with a selected condition; both fractions retained in the full decision table'}
    for key, pred in [('primary', 'primary_prediction'), ('sensitivity', 'three_size_sensitivity_prediction')]:
        actual = outcome(summary[key])
        expected = forecast[pred]
        hit = None if actual['status'] != 'COMPLETE' else all(actual[k] == expected[k] for k in ('condition', 'fraction'))
        result[key] = {'prediction': expected, 'outcome': actual, 'hit': hit}
    return result


if __name__ == '__main__':
    summary = json.loads((HERE / 'results/validation_summary_v3.json').read_text())
    result = assess(summary)
    (HERE / 'results/forecast_assessment_v3.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
