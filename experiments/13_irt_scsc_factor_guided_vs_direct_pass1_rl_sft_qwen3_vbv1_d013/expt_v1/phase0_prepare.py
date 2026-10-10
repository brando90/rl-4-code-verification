#!/usr/bin/env python3
"""Freeze source-bound phase-0 controls and test the actual pinned strict scorer."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from rl4cv.forecast import freeze_forecast
from rl4cv.rewards import ScoredResponse, reward_kernel_binary

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
E08 = '08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test'
PIN = '59059a20d40adf3289869e58302169ad78102877'
FROZEN = {
    'scripts/scsc/run_real_eval.py': '6e82b3d1cd6d3686aaec3d45f273cd902b03b962c0c2eca48f2c2b4f25f41fa9',
    'scripts/scsc/kernel_axioms.py': '5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287',
    'experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py': 'b3713c48e0fdb24adec93b77be8785d20e48897ee8d1fd8ce31fdf37101e81d6',
}
GOOD = 'import Mathlib\nexample : 1 + 1 = 2 := by decide\ntheorem good : 1 + 1 = 2 := by decide\n'
FIXTURES = {
    'valid': (GOOD, 1, False),
    'valid_at_cap': (GOOD, 1, True),
    'no_example': ('import Mathlib\ntheorem good : 1 + 1 = 2 := by decide\n', 0, False),
    'no_theorem': ('import Mathlib\nexample : 1 + 1 = 2 := by decide\n', 0, False),
    'empty': ('', 0, False),
    'truncated_syntax': (GOOD + 'def broken : Nat := (', 0, True),
    'failed_then_valid': ('import Mathlib\nexample : 1 + 1 = 2 := by decide\ntheorem bad : False := by decide\ntheorem good : 1 + 1 = 2 := by decide\n', 0, False),
    'sorry': (GOOD.replace('theorem good : 1 + 1 = 2 := by decide', 'theorem good : 1 + 1 = 2 := by sorry'), 0, False),
    'helper_sorry': ('import Mathlib\nexample : 1 + 1 = 2 := by decide\nlemma helper : 1 + 1 = 2 := by sorry\ntheorem good : 1 + 1 = 2 := helper\n', 0, False),
    'native_theorem': (GOOD.replace('theorem good : 1 + 1 = 2 := by decide', 'theorem good : 1 + 1 = 2 := by native_decide'), 0, False),
    'native_example': (GOOD.replace('example : 1 + 1 = 2 := by decide', 'example : 1 + 1 = 2 := by native_decide'), 1, False),
    'declared_axiom': ('import Mathlib\naxiom foo : 1 + 1 = 2\nexample : 1 + 1 = 2 := by decide\ntheorem good : 1 + 1 = 2 := foo\n', 0, False),
    'vacuous': ('import Mathlib\nexample : 1 + 1 = 2 := by decide\ntheorem vac : True := by trivial\n', 0, False),
    'top_level_error': (GOOD + '#check unknown_e13_name\n', 0, False),
    'printed_error': (GOOD + '#eval IO.println "fixture.lean:1:1: error: pretend"\n', 0, False),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: object) -> None:
    with path.open('x') as out:
        json.dump(obj, out, indent=2, sort_keys=True, allow_nan=False)
        out.write('\n')


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def inventory(e08_root: Path, e05_root: Path, out: Path) -> dict:
    results = REPO / 'experiments' / E08 / 'expt_v1/results'
    split_path = results / 'split/vbv1_split_manifest.csv'
    with split_path.open() as f:
        split = {r['task_id']: r for r in csv.DictReader(f)}
    validation = {tid for tid, r in split.items() if r['split'] == 'validation'}
    if len(validation) != 135:
        raise ValueError('validation manifest changed')
    source_manifest = results / 'ladder_manifest.json'
    declared = json.loads(source_manifest.read_text())
    rows, missing, hashes = [], [], {}
    for system in declared['systems']:
        label = system['label']
        path = results / 'ladder' / f'{label}_validation_cells.csv'
        hashes[str(path.relative_to(REPO))] = sha(path)
        with path.open() as f:
            cells = list(csv.DictReader(f))
        if not cells:
            missing.append({'policy': label, 'cells': 1080, 'status': 'unavailable_parent_ladder_policy'})
            continue
        identities = {(c['task_id'], int(c['sample_idx'])) for c in cells}
        if identities != {(tid, k) for tid in validation for k in range(8)} or len(cells) != 1080:
            raise ValueError(f'incomplete/duplicate/unexpected validation cells: {label}')
        if label.endswith('_e05'):
            size = label.split('_')[1].replace('p', '.').replace('B', 'b')
            jobs, job_label = e05_root / 'out/jobs', f'qwen3-{size}-base'
        else:
            jobs, job_label = e08_root / 'ladder/validation/jobs', label
        for c in cells:
            source = jobs / f'{job_label}_g8_s{c["sample_idx"]}' / c['task_id'] / 'verifier/solution.lean'
            digest = sha(source) if source.is_file() else None
            # Empty extraction is a real zero cell; its empty source hash remains explicit.
            expected = c['lean_sha256'] or hashlib.sha256(b'').hexdigest()
            status = 'available' if digest == expected else 'missing_or_hash_mismatch'
            rows.append({'cell_id': f'{label}/{c["task_id"]}/{c["sample_idx"]}',
                         'policy': label, 'task_id': c['task_id'], 'sample_idx': int(c['sample_idx']),
                         'group_id': split[c['task_id']]['group_id'], 'split': 'validation',
                         'source_path': str(source), 'response_sha256': expected,
                         'actual_source_sha256': digest, 'source_status': status,
                         'kernel_binary': float(c['kernel_binary']) if c['known'] == 'True' else None})
    if len(rows) != 20520:
        raise ValueError(f'available cohort changed: {len(rows)}; freeze a new explicit inventory')
    with (out / 'validation_source_manifest.jsonl').open('x') as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + '\n')
    summary = {'declared_parent_cells': declared['n_declared_cells'], 'available_cohort_cells': len(rows),
               'source_hash_matches': sum(r['source_status'] == 'available' for r in rows),
               'known_strict_cells': sum(r['kernel_binary'] is not None for r in rows),
               'pending_parent_policies': missing, 'source_manifests_sha256': hashes,
               'split_sha256': sha(split_path), 'ladder_manifest_sha256': sha(source_manifest),
               'cell_manifest_sha256': sha(out / 'validation_source_manifest.jsonl'),
               'historical_full_base_cells': 21504, 'sealed_full_base_audit': 'NOT_RUN',
               'historical_factors_measured': 0}
    dump(out / 'inventory.json', summary)
    return summary


def run_fixtures(scorer_root: Path, lake: Path, out: Path) -> list[dict]:
    scorer = load_module('e13_pinned_scorer', scorer_root / 'scripts/scsc/run_real_eval.py')
    adapter = load_module('e13_historical_readback', REPO / 'experiments' / E08 / 'expt_v1/scripts/score_teacher_files.py')
    adapter.SCORER = scorer_root
    scorer.LAKE_DIR = str(lake)
    rows = []
    compile_records = []
    original_compile = scorer.compile_lean_file
    def observed_compile(*args, **kwargs):
        result = original_compile(*args, **kwargs)
        compile_records.append(asdict(result))
        return result
    scorer.compile_lean_file = observed_compile
    for name, (source, expected, truncated) in FIXTURES.items():
        path = out / 'fixtures' / f'{name}.lean'
        compile_records.clear()
        # Frozen scorer handles extraction/compile/proof, historical adapter handles vacuity.
        analysis, ic_test, ic_proof, cache = scorer._compute_agent_compile_scores(name, str(path), 'core', {}, False)
        vac = adapter.vacuity(source) if source else {'n_vacuous': 0, 'unparseable': []}
        kernel = analysis.kernel or {}
        stated = kernel.get('n_theorems', analysis.n_theorems)
        proved = kernel.get('n_honest', 0)
        old = ScoredResponse(bool(source.strip()), analysis.compiles, analysis.n_examples,
                             stated, proved, vacuous_theorems=vac['n_vacuous'], truncated=truncated)
        actual = None if vac['unparseable'] else reward_kernel_binary(old)
        evidence = {'fixture': name, 'source_sha256': sha(path), 'expected_strict': expected,
                    'actual_strict': actual, 'truncated': truncated, 'IC_tests': ic_test,
                    'IC_proofs': ic_proof, 'vacuity': vac, 'cache': cache,
                    'compile': list(compile_records), 'passed': actual == expected}
        dump(out / f'{name}.json', evidence)
        rows.append(evidence)
        print(json.dumps({'fixture': name, 'actual': actual, 'expected': expected, 'passed': actual == expected}), flush=True)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scorer-root', type=Path, required=True)
    parser.add_argument('--lake-dir', type=Path, required=True)
    parser.add_argument('--e08-root', type=Path, required=True)
    parser.add_argument('--e05-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    a = parser.parse_args()
    if subprocess.check_output(['git', '-C', str(a.scorer_root), 'rev-parse', 'HEAD'], text=True).strip() != PIN:
        raise ValueError('wrong scorer pin')
    for rel, expected in FROZEN.items():
        if sha(a.scorer_root / rel) != expected:
            raise ValueError(f'scorer hash mismatch: {rel}')
    if (a.lake_dir / 'lean-toolchain').read_text().strip() != 'leanprover/lean4:v4.22.0':
        raise ValueError('wrong Lean toolchain')
    a.out.mkdir(parents=True, exist_ok=False)
    (a.out / 'fixtures').mkdir()
    for name, (source, _, _) in FIXTURES.items():
        (a.out / 'fixtures' / f'{name}.lean').write_text(source)
    files = [HERE / 'phase0_prepare.py', HERE.parent / 'PROTOCOL.md', REPO / 'src/rl4cv/e13.py',
             REPO / 'src/rl4cv/rewards.py', REPO / 'experiments' / E08 / 'expt_v1/scripts/score_teacher_files.py']
    lock = {'kind': 'L0_authored_strict_controls', 'scorer_commit': PIN, 'scorer_hashes': FROZEN,
            'source_hashes': {str(p.relative_to(REPO)): sha(p) for p in files},
            'fixture_hashes': {p.name: sha(p) for p in sorted((a.out / 'fixtures').glob('*.lean'))},
            'expected': {k: v[1] for k, v in FIXTURES.items()},
            'toolchain': 'leanprover/lean4:v4.22.0', 'lake_manifest_sha256': sha(a.lake_dir / 'lake-manifest.json'),
            'historical_factors_observed': False}
    freeze_forecast(lock, a.out / 'locks', 'L0', outcomes_observed=False)
    inv = inventory(a.e08_root, a.e05_root, a.out)
    rows = run_fixtures(a.scorer_root, a.lake_dir, a.out)
    passed = all(r['passed'] for r in rows) and inv['source_hash_matches'] == 20520
    dump(a.out / 'result.json', {'created': datetime.now(timezone.utc).isoformat(),
         'status': 'PASS' if passed else 'FAIL', 'fixtures_passed': sum(r['passed'] for r in rows),
         'fixtures_total': len(rows), 'inventory': inv, 'L0_sha256': sha(a.out / 'locks/L0.json'),
         'scope': 'authored strict controls and validation source inventory only',
         'declaration_adapter_validated': False, 'historical_reproduction_passed': False,
         'G0_passed': False, 'training_admitted': False})
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
