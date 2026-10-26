"""Verify frozen v2 inputs and write atomic receipts without modifying version 1."""
import hashlib
import json
import os
from pathlib import Path
from rl4cv.forecast import verify_forecast

PHASE = Path(__file__).resolve().parents[1]
V1 = PHASE.parent / 'expt_v1'
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e12/v2')
V1_WORK = WORK.parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n')
    tmp.replace(path)


def verify_inputs():
    for name in ('e12_v2_forecast', 'e12_v2_forecast_amendment_A1'):
        assert verify_forecast(PHASE / 'forecasts' / (name + '.json'))
    for name in ('e12_phase_a_forecast', 'e12_phase_a_forecast_amendment_A1', 'e12_phase_a_forecast_amendment_A2'):
        assert verify_forecast(V1 / 'forecasts' / (name + '.json'))
    frozen = json.loads((PHASE / 'forecasts/e12_v2_forecast_amendment_A1.json').read_text())['inputs']
    paths = [PHASE/'scripts/adapter_v2.py', PHASE/'results/mapping_census_v2.json',
             PHASE/'results/static_controls_v2.json', V1/'results/hidden_tests_manifest.json',
             V1/'results/input_manifest_A1.json']
    for path in paths:
        assert digest(path) == frozen[path.name + '_sha256'], str(path)
    assert '**Lock line:** `LOCKED ' in (PHASE/'PROTOCOL.md').read_text()
    reproduction = json.loads((V1/'results/compile_reproduction_A1.json').read_text())
    assert reproduction['passes'] and reproduction['n_matches'] >= 99
    for row in reproduction['rows']:
        # Reuse the compile reproduction only for the unchanged sampled candidates.
        original = next(r for r in json.loads((V1/'results/compile_selection_A1.json').read_text())['cells']
                        if (r['system'], r['task_id']) == (row['system'], row['task_id']))
        assert digest(original['path']) == row['sha256']
    return {p.name: digest(p) for p in paths}


def workers_allowed(workers):
    if workers not in (2, 3, 4):
        raise ValueError('Use 2 workers, or up to 4 only when the one-minute load is below 20')
    if workers > 2 and os.getloadavg()[0] >= 20:
        raise ValueError('One-minute load is at least 20; use 2 workers')
    return workers
