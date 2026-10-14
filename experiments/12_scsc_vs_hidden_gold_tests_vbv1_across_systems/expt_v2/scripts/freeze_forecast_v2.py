"""Freeze the experiment 12 version 2 forecast after the mapping census and before any version-2 hidden-test outcome, refusing to run if an outcome file exists."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
E12 = V2.parent
sys.path.insert(0, str(E12.parents[1] / 'src'))
from rl4cv.forecast import freeze_forecast, verify_forecast  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    for name in ('e12_phase_a_forecast', 'e12_phase_a_forecast_amendment_A1', 'e12_phase_a_forecast_amendment_A2'):
        assert verify_forecast(E12 / 'expt_v1' / 'forecasts' / (name + '.json')), name
    outcome_files = list((V2 / 'results').glob('cells_v2*')) + list((V2 / 'results').glob('analysis_v2*')) + list((V2 / 'results').glob('evaluation_*'))
    assert not outcome_files, f'version-2 outcome files exist; a forecast cannot be frozen now: {outcome_files}'
    census = json.loads((V2 / 'results' / 'mapping_census_v2.json').read_text())
    assert not any(k.startswith('hidden') or 'pass' in k for k in census['totals']), 'census must not carry outcomes'
    forecast = {
        'experiment': '12_scsc_vs_hidden_gold_tests_vbv1_across_systems', 'version': 'expt_v2',
        'frozen_by': 'Claude Code worker (claude-fable-5-1) for Brando, 10-14-2026, after the zero-call mapping census and before any version-2 evaluation',
        'outcomes_seen_before_freeze': 'version-1 outcomes published 10-10-2026 (P1 0.891, P2 0.640, P3 0.151, applicability 3224/4674) and the version-2 static mapping census; no version-2 hidden-test outcome exists',
        'inputs': {'adapter_v2.py_sha256': sha(HERE / 'adapter_v2.py'),
                   'mapping_census_v2.json_sha256': sha(V2 / 'results' / 'mapping_census_v2.json'),
                   'hidden_tests_manifest.json_sha256': sha(E12 / 'expt_v1' / 'results' / 'hidden_tests_manifest.json'),
                   'input_manifest_A1.json_sha256': sha(E12 / 'expt_v1' / 'results' / 'input_manifest_A1.json'),
                   'protocol': 'expt_v2/PROTOCOL.md (locked 10-14-2026)'},
        'thresholds_source': 'carried unchanged from e12_phase_a_forecast.json (frozen 10-09-2026, agent-suggested); the applicability gate number is unchanged but applied to the stricter fully-applicable cohort, decided before the run',
        'analysis': 'PROTOCOL.md section 5: seed 20261009, 10,000 task-cluster bootstrap draws, system-stratified ranks; p-val=n/a',
        'predictions': {
            'P1': {'statistic': 'Spearman(system S-tilde SCSC, system hidden all-pass rate), 11 systems', 'threshold': '>= 0.80',
                   'point': 0.89, 'plausible_range': [0.80, 0.95], 'direction_vs_v1': 'about unchanged (v1 0.891)'},
            'P2': {'statistic': 'system-stratified AUC of per-cell SCSC for hidden_all_pass, fully applicable compiling primary cells', 'threshold': '>= 0.60 and 95% task-cluster interval excludes 0.50',
                   'point': 0.68, 'plausible_range': [0.62, 0.74], 'direction_vs_v1': 'up (v1 0.640): helper mappings and partial-applicability false failures at SCSC = 1.0 are removed'},
            'P3': {'statistic': 'pooled within-system Spearman(per-cell SCSC, hidden_pass_rate), same cohort', 'threshold': '> 0 and interval excludes 0',
                   'point': 0.20, 'plausible_range': [0.12, 0.30], 'direction_vs_v1': 'up (v1 0.151)'},
            'G-A': {'statistic': 'fully applicable / compiling cells with tests (4,626)', 'threshold': '>= 0.50',
                    'point': 0.62, 'plausible_range': [0.55, 0.70], 'basis': 'census static upper bound 3129/4626 = 0.676 before probes, <= 3381/4626 = 0.731 after; 272 result-type and 266 argument-type mismatch cells are the expected losses'},
            'applicability_any_evaluable': {'statistic': '>= 1 evaluable test / 4,626', 'point': 0.72, 'plausible_range': [0.66, 0.78], 'direction_vs_v1': 'unchanged or up (v1 3224/4674 = 0.690; 3224/4626 = 0.697)'},
            'failing_share': {'statistic': 'cells with hidden_all_pass = 0 / fully applicable compiling score-measured cells', 'plausible_range': [0.02, 0.06], 'direction_vs_v1': 'down from 200/3199 = 0.0625'},
            'inspected_rows': 'of the 6 version-1 helper-mapping rows (hazard pointer, LWW pick-left, interrupt route, bump alloc, power transition, dose interval), at least 5 become hidden_all_pass = 1 or missing, and none remains a helper-mapped failure; the 4 partial-applicability rows become missing for hidden_all_pass with every evaluable test passing; the 10 low-score Leanstral rows keep hidden_all_pass = 1',
            'census_consistency': 'evaluated cells mapped at steps 1-2b equal the census counts exactly (4,626 cells, 3,129 fully mapped, 252 probe, 927 none) because the inputs and adapter are hash-pinned',
        },
        'reading': 'P1 and P2 hold with P2 > 0.640: the version-1 claim stands and was conservative. P2 < 0.640 on a cohort of similar size: version-1 agreement partly reflected helper mappings; report both. G-A < 0.50: LIMITED COVERAGE with bounds.',
        'failure_reporting': 'every prediction is reported with its measured value, interval, denominators and verdict, failed or not (D-004)',
    }
    entry = freeze_forecast(forecast, V2 / 'forecasts', 'e12_v2_forecast', outcomes_observed=False)
    print(json.dumps(entry, indent=1))


if __name__ == '__main__':
    main()
