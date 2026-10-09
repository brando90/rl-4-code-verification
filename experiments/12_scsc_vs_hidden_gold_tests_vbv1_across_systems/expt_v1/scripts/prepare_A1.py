"""Build the prospective A1 input manifest, preserving prior receipts and binding gold and candidate bytes."""
import collections
import csv
import io
import json
import subprocess
import tarfile
from pathlib import Path

from audit_inputs_e12 import FACTORS, sha, resolve_candidate
from rl4cv.forecast import verify_forecast

PHASE = Path(__file__).resolve().parents[1]
RESULTS = PHASE / 'results'
VB = Path('/lfs/skampere1/0/brando9/veribench_vb103')
E103 = next((VB / 'experiments').glob('103_single_call_baselines*'))
GOLD_REPO = Path('/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench')


def main():
    for name in ('e12_phase_a_forecast', 'e12_phase_a_forecast_amendment_A1'):
        assert verify_forecast(PHASE / 'forecasts' / (name + '.json'))
    manifest = json.loads((RESULTS / 'input_manifest.json').read_text())
    audit = json.loads((RESULTS / 'aggregation_preflight.json').read_text())
    for source in manifest['sources']:
        assert sha(Path(source['path'])) == source['sha256'], source['path']
    sources = list(manifest['sources'])
    maps, scorers, summaries = {}, {}, {}
    for system in [r['system'] for r in audit['systems'] if r['source_experiment'] == 103]:
        for condition, dirname, score_dir in [('original', 'jobs', 'scsc_vbv1'), ('recovery_1', 'jobs_recovery_1', 'scsc_vbv1_recovery_1')]:
            f = E103 / f'private/{dirname}/{system}_summary.json'
            summaries[system, condition] = json.loads(f.read_text())
            sources.append({'path': str(f), 'sha256': sha(f)})
            f = next((E103 / f'private/{score_dir}/{system}').glob('*_per_task.csv'))
            sources.append({'path': str(f), 'sha256': sha(f)})
            scorers[system, condition] = {r['task']: r for r in csv.DictReader(f.open())}
            for task, r in scorers[system, condition].items():
                if not r['gold_key']:
                    continue
                assert task not in maps or maps[task] == r['gold_key']
                maps[task] = r['gold_key']
    assert len(maps) == len(set(maps.values())) == 896
    reverse = {v: k for k, v in maps.items()}
    for r in manifest['cells']:
        r['panel'] = 'primary'
        if r['source_experiment'] == 102:
            r['gold_key'] = r['task_id']
            r['task_id'] = reverse[r['gold_key']]
            r['condition'] = 'original'
        else:
            system, task = r['system'], r['task_id']
            original = summaries[system, 'original']['cells'][task]
            condition = 'original'
            if not r.get('expected_sha256'):
                # A1.4 explicitly permits only the existing infrastructure-recovery condition.
                if original['status'] == 'unmeasured_infra' and task in summaries[system, 'recovery_1']['cells']:
                    condition = 'recovery_1'
                dirname = 'jobs_recovery_1' if condition == 'recovery_1' else 'jobs'
                cell = summaries[system, condition]['cells'][task]
                binding = resolve_candidate([E103 / f'private/{dirname}/{system}/{task}/verifier/solution.lean'], cell.get('solution_sha256'))
                for key in ('path', 'sha256', 'bytes', 'searched_paths', 'copies', 'matching_copies', 'expected_sha256'):
                    r.pop(key, None)
                r.update(binding)
                r['join_basis'] = 'A1.4 run/condition path; original factors preserved'
            elif '/jobs_recovery_1/' in r['path']:
                condition = 'recovery_1'
            r['condition'] = condition
            r['recorded_run_id'] = summaries[system, condition].get('run_id')
            r['gold_key'] = maps[task]
            score = scorers[system, condition].get(task)
            r['recorded_compiles'] = {'True': True, 'False': False}.get(score['agent_compiles']) if score else None
            if all(r[k] is not None for k in FACTORS):
                assert condition == 'original', 'Measured original factors must bind original condition'
                assert abs(float(score['IC_ap']) - r['IC_tests']) < 1e-9
                assert abs(float(score['IC_pp']) - r['IC_proofs']) < 1e-9
        if r['join_status'] == 'ambiguous':
            r['join_status'] = 'join_ambiguous'
        r['split'] = r['gold_key'].split('/')[0]
        r['subset'] = 'Core614' if r['split'] in {'easy_set', 'cs_set', 'humaneval_set', 'realcode_set', 'security_set'} else 'IndustrySet282'
        r['common_measured'] = all(r.get(k) is not None for k in FACTORS)
    pin = json.loads((PHASE.parents[2] / 'external/deps.lock.json').read_text())['veribench']['commit']
    prefix = 'veribench_dataset/lean_src/veribench/'
    archive = subprocess.check_output(['git', '-C', str(GOLD_REPO), 'archive', pin, prefix])
    gold = []
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for task, key in sorted(maps.items()):
            relative = prefix + key + '.lean'
            data = tar.extractfile(relative).read()
            path = GOLD_REPO / relative
            assert path.read_bytes() == data, str(path)
            gold.append({'task_id': task, 'gold_key': key, 'path': str(path), 'sha256': sha(path), 'bytes': len(data)})
    joins = collections.Counter(r['join_status'] for r in manifest['cells'])
    unavailable = joins['file_missing'] + joins['join_ambiguous']
    checks = []
    for s in audit['systems']:
        checks.append({'system': s['system'], 'source_experiment': s['source_experiment'],
                       'published_convention': 'mean_per_cell' if s['source_experiment'] == 103 else 'geometric_of_means',
                       'published_value': s['published_scsc'],
                       'recomputed': s['mean_per_cell_scsc_measured'] if s['source_experiment'] == 103 else s['geometric_mean_of_factor_means_measured'],
                       'passes': s['mean_per_cell_matches_published_three_decimals'] if s['source_experiment'] == 103 else s['matches_published_three_decimals'],
                       'system_score_A1': s['geometric_mean_of_factor_means_measured'], 'n_common_measured': s['n_common_measured']})
    report = {'amendment': 'A1', 'forecast_hashes_verified': True, 'checks': checks,
              'candidate_joins': dict(joins), 'n_declared': 9856, 'unavailable_joins': unavailable,
              'unavailable_fraction': unavailable / 9856, 'join_gate_passes': unavailable / 9856 <= .05,
              'n_gold': len(gold), 'gold_pin': pin, 'compile_reproduction': 'PENDING', 'sources': sources}
    manifest.update(status='A1_INPUT_GATES_PASS_COMPILE_PENDING', sources=sources, gold=gold, gold_pin=pin,
                    scope='A1 primary manifest; immutable original factor values; recovery may resolve unmeasured joins only')
    manifest['systems'] = checks
    manifest['file_missing'] = [{'system': r['system'], 'task_id': r['task_id']} for r in manifest['cells'] if r['join_status'] in ('file_missing', 'join_ambiguous')]
    for filename, data in [('input_manifest_A1.json', manifest), ('aggregation_preflight_A1.json', report)]:
        (RESULTS / filename).write_text(json.dumps(data, separators=(',', ':')) + '\n')
    print(json.dumps({k: report[k] for k in ('candidate_joins', 'unavailable_joins', 'join_gate_passes', 'n_gold')}))
    assert all(r['passes'] for r in checks) and report['join_gate_passes']


if __name__ == '__main__':
    main()
