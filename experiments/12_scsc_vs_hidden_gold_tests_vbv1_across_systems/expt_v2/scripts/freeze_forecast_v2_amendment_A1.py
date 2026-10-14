"""Freeze forecast amendment A1 for experiment 12 version 2: adapter amendment V2-A1 hashes, predictions unchanged, still before any evaluation."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
sys.path.insert(0, str(V2.parents[2] / 'src'))
from rl4cv.forecast import freeze_forecast, verify_forecast  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert verify_forecast(V2 / 'forecasts' / 'e12_v2_forecast.json')
    outcome_files = list((V2 / 'results').glob('cells_v2*')) + list((V2 / 'results').glob('analysis_v2*')) + list((V2 / 'results').glob('evaluation_*')) + list((V2 / 'results').glob('controls_v2*'))
    assert not outcome_files, outcome_files
    original = json.loads((V2 / 'forecasts' / 'e12_v2_forecast.json').read_text())
    amendment = {
        'experiment': original['experiment'], 'version': 'expt_v2', 'amends': 'e12_v2_forecast.json sha256 ' + sha(V2 / 'forecasts' / 'e12_v2_forecast.json'),
        'reason': 'PROTOCOL.md section 8, amendment V2-A1: the static renamed-gold control found 7/882 wrong step-2b picks; name affinity is now a word-boundary suffix with a reference veto',
        'outcomes_seen_before_freeze': 'as the original forecast plus the rerun static census and static controls; no version-2 hidden-test outcome or Lean control exists',
        'predictions': 'unchanged from e12_v2_forecast.json (P1 >= 0.80, point 0.89; P2 >= 0.60, point 0.68; P3 > 0, point 0.20; G-A fully applicable >= 0.50, point 0.62)',
        'updated_basis': {'G-A static upper bound': '3121/4626 = 0.675 before probes, <= 3384/4626 = 0.732 after',
                          'census_consistency': '4,626 cells; 3,121 fully mapped; 263 probe; 927 none'},
        'inputs': {'adapter_v2.py_sha256': sha(HERE / 'adapter_v2.py'),
                   'mapping_census_v2.json_sha256': sha(V2 / 'results' / 'mapping_census_v2.json'),
                   'static_controls_v2.json_sha256': sha(V2 / 'results' / 'static_controls_v2.json'),
                   'hidden_tests_manifest.json_sha256': original['inputs']['hidden_tests_manifest.json_sha256'],
                   'input_manifest_A1.json_sha256': original['inputs']['input_manifest_A1.json_sha256']},
        'frozen_by': 'Claude Code worker (claude-fable-5-1) for Brando, 10-14-2026',
    }
    print(json.dumps(freeze_forecast(amendment, V2 / 'forecasts', 'e12_v2_forecast_amendment_A1', outcomes_observed=False), indent=1))


if __name__ == '__main__':
    main()
