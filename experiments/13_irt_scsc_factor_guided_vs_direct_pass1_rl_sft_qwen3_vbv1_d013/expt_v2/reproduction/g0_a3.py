#!/usr/bin/env python3
"""Bound G0 over A3 exclusions with frozen evaluate, hash preflight and a single-run receipt."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import subprocess

import numpy as np

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
REPO = V2.parents[2]
MAX_CONFIGURATIONS = 2**20
EXCLUSION_HASH = 'c00b35abaecda874820d4b1b29015655e248c19f319fa574fefa3d0804124128'
SIZES = ('1p7B', '4B', '8B')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_evaluator():
    # Import definitions only. In particular, never invoke frozen g0.main.
    spec = importlib.util.spec_from_file_location('e13_a3_frozen_g0', HERE / 'g0.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate, module.auc


def verify_lock(lock_path, repo, work_root):
    """Verify every binding before importing the evaluator or opening validation rows."""
    lock = json.loads(Path(lock_path).read_text())
    required = {'g0', 'wrapper', 'tests', 'exclusions', 'admission', 'ordinary_manifest',
                'ordinary_results', 'evaluation', 'opaque_public'}
    if set(lock['bindings']) != required:
        raise ValueError('lock binding set mismatch')
    paths = {}
    for name, item in lock['bindings'].items():
        root = {'repo': Path(repo), 'work': Path(work_root)}[item['root']]
        path = (root / item['path']).resolve()
        if not path.is_relative_to(root.resolve()) or sha(path) != item['sha256']:
            raise ValueError('hash mismatch: ' + name)
        paths[name] = path
    if lock['bindings']['exclusions']['sha256'] != EXCLUSION_HASH:
        raise ValueError('hash mismatch: admission exclusion identity')
    return lock, paths


def validate_exclusions(exclusions, manifest, public_class_c):
    """Check metadata only; no outcome or factor enters this verification."""
    ids = [r['cell_id'] for r in exclusions]
    if len(ids) != 217 or len(set(ids)) != 217:
        raise ValueError('exclusion count or uniqueness')
    rows = {r['cell_id']: r for r in manifest}
    if len(rows) != len(manifest) or len(rows) != 33456:
        raise ValueError('ordinary manifest denominator')
    from collections import Counter
    composition = Counter()
    for row in exclusions:
        source = rows.get(row['cell_id'])
        if source is None or row['split'] not in ('train', 'validation') or source['split'] != row['split']:
            raise ValueError('nonordinary exclusion')
        composition['typed_limit' if row['recorded_status'] == 'deterministic_resource_limit'
                    else row['a3_class']] += 1
    if composition != {'typed_limit': 168, 'a': 2, 'c': 4, 'd': 43}:
        raise ValueError('exclusion composition')
    if len(public_class_c) != 4 or not set(public_class_c) <= set(ids):
        raise ValueError('public class c exclusion missing')
    if {r['cell_id'] for r in exclusions if r['a3_class'] == 'c'} != set(public_class_c):
        raise ValueError('public class c identity mismatch')
    return set(ids)


def retained_rows(rows, excluded):
    """Discard excluded receipts before inspecting any of their measured fields."""
    for row in rows:
        if row['split'] == 'test':
            raise ValueError('test is sealed')
        if row['cell_id'] in excluded:
            continue
        yield row


def load_arrays(manifest, rows, excluded, *,task_count=135):
    """Use the declared manifest for masks; only explicitly excluded cells become free."""
    groups = {}
    slots = {}
    for row in manifest:
        if row['split'] == 'test':
            raise ValueError('test is sealed')
        if row['split'] != 'validation':
            continue
        task = row['task_id']
        if task in groups and groups[task] != row['group_id']:
            raise ValueError('group identity mismatch')
        groups[task] = row['group_id']
        for expectation in row['expectations']:
            if expectation['family'] == 'ladder':
                key = (expectation['policy'], task, row['sample_idx'])
                if key in slots:
                    raise ValueError('duplicate manifest slot')
                slots[key] = row['cell_id']
    if len(groups) != task_count:
        raise ValueError('validation denominator changed')
    measured = {}
    seen = set()
    for row in retained_rows(rows, excluded):
        if row['cell_id'] in seen:
            raise ValueError('duplicate receipt')
        seen.add(row['cell_id'])
        if row['split'] != 'validation' or row['status'] != 'measured':
            continue
        for readback in row['readbacks']:
            if readback['family'] != 'ladder':
                continue
            key = (readback['policy'], row['task_id'], row['sample_idx'])
            if slots.get(key) != row['cell_id'] or key in measured:
                raise ValueError('receipt identity mismatch')
            if not readback['equal']:
                raise ValueError('unexcluded oracle inequality')
            measured[key] = (readback['value'], readback['factored_reward'])
    tasks = sorted(groups)
    strata = {}
    for size in SIZES:
        arrays = []
        missing = 0
        for rung in ('f0p5', 'f1p0'):
            array = np.full((task_count, 8, 2), np.nan)
            for i, task in enumerate(tasks):
                for sample in range(8):
                    key = (f'sft_{size}_{rung}', task, sample)
                    cell = slots.get(key)
                    if cell in excluded:
                        continue
                    value = measured.get(key)
                    if cell is None or value is None or value[0] is None or value[1] is None:
                        missing += 1
                    else:
                        array[i, sample] = value
            arrays.append(array)
        strata[size] = {'missing_unexcluded_cells': missing, 'arrays': arrays}
    return strata, [groups[t] for t in tasks]


def check_array(array):
    array = np.asarray(array, float)
    if array.ndim != 3 or array.shape[1:] != (8, 2):
        raise ValueError('eight samples with strict/B required')
    mask = np.isnan(array).all(axis=2)
    if np.any(np.isnan(array).any(axis=2) != mask):
        raise ValueError('partially missing cell')
    known = array[~mask]
    if not np.isfinite(known).all() or not np.isin(known[:, 0], [0, 1]).all():
        raise ValueError('invalid strict')
    if np.any((known[:, 1] < 0) | (known[:, 1] > 1)) or np.any(known[known[:, 0] == 1, 1] != 1):
        raise ValueError('invalid reward or strict-success reward')
    return array.copy(), mask


def fill_zero(array):
    return np.nan_to_num(array, nan=0.)


def dense_flag(row):
    return bool(np.ptp(row[:, 0]) == 0 and np.ptp(row[:, 1]) > 0)


def dense_extremes(later):
    """Exact taskwise extrema: constant filling, endpoints, and one unequal slot suffice."""
    minima, maxima = [], []
    for row in later:
        missing = np.isnan(row[:, 0])
        base = fill_zero(row)
        candidates = [base]
        if missing.any():
            for strict, reward in ((0, 1), (1, 1)):
                candidate = base.copy(); candidate[missing] = (strict, reward)
                candidates.append(candidate)
            for reward in np.unique(row[~missing, 1]):
                candidate = base.copy(); candidate[missing] = (0, reward)
                candidates.append(candidate)
            candidate = base.copy(); candidate[np.flatnonzero(missing)[0]] = (0, 1)
            candidates.append(candidate)
        minima.append(min(candidates, key=dense_flag))
        maxima.append(max(candidates, key=dense_flag))
    return np.array(minima), np.array(maxima)


def task_states(earlier, later):
    """(included, later-positive) states, collapsing irrelevant labels outside the subset."""
    e_missing = np.isnan(earlier[:, 0])
    l_missing = np.isnan(later[:, 0])
    if np.any(earlier[~e_missing, 0] == 1):
        return [(False, None)]
    labels = [True] if np.any(later[~l_missing, 0] == 1) else ([False, True] if l_missing.any() else [False])
    states = [(True, label) for label in labels]
    if e_missing.any():
        states.append((False, None))
    return states


def completion(earlier, later, states, maximize):
    """Realize each membership/label state and its monotone AUC score endpoint."""
    e, l = fill_zero(earlier), fill_zero(later)
    for i, (included, positive) in enumerate(states):
        em = np.isnan(earlier[i, :, 0]); lm = np.isnan(later[i, :, 0])
        if included:
            e[i, em, 1] = float(positive == maximize)
            if positive and not np.any(l[i, :, 0] == 1):
                l[i, np.flatnonzero(lm)[0]] = (1, 1)
        elif not np.any(e[i, :, 0] == 1):
            e[i, np.flatnonzero(em)[0]] = (1, 1)
    return e, l


def auc_extremes(earlier, later, auc, *,limit=MAX_CONFIGURATIONS):
    choices = [task_states(e, l) for e, l in zip(earlier, later)]
    count = math.prod(map(len, choices))
    # A one-class (or empty) completion exists iff either class need not be present.
    undefined = any(not any(all(included and positive == label for included, positive in options)
                            for options in choices) for label in (False, True))
    variable = [i for i, options in enumerate(choices) if len(options) > 1]
    base = [options[0] for options in choices]
    best = [None, None]
    witnesses = [None, None]
    undefined_witness = None
    if count > limit:
        # Valid outer bounds: never call interior feasible witnesses certified extrema.
        configs = [tuple(base)]
        for label in (False, True):
            configs.append(tuple(next((s for s in opts if not s[0] or s[1] == label), opts[0]) for opts in choices))
    else:
        def configurations():
            for selected in itertools.product(*(choices[i] for i in variable)):
                states = base.copy()
                for i, state in zip(variable, selected): states[i] = state
                yield states
        configs = configurations()
    # Compute score endpoints with the same NumPy mean as evaluate, preserving exact ties.
    score_low = fill_zero(earlier)[:, :, 1].mean(axis=1)
    score_high_array = fill_zero(earlier)
    score_high_array[np.isnan(earlier[:, :, 0]), 1] = 1.
    score_high = score_high_array[:, :, 1].mean(axis=1)
    for states in configs:
        included = np.array([s[0] for s in states], bool)
        labels = np.array([bool(s[1]) for s in states], bool)
        if not labels[included].any() or labels[included].all():
            if undefined_witness is None: undefined_witness = states
            continue
        for direction in (0, 1):
            scores = np.where(labels == bool(direction), score_high, score_low)
            value = auc(labels[included], scores[included])
            if best[direction] is None or (value > best[direction] if direction else value < best[direction]):
                best[direction] = value; witnesses[direction] = states
    if count > limit:
        bounds = [0., 1.]
    else:
        bounds = best
    return {'minimum': bounds[0], 'maximum': bounds[1], 'exact': count <= limit,
            'configurations': count, 'enumeration_limit': limit, 'undefined_possible': undefined,
            'witness_values': best}, witnesses, undefined_witness


def verdict(dense_min, dense_max, auc_result, *,dense_threshold=21, auc_threshold=.65):
    if dense_max < dense_threshold or (auc_result['maximum'] is not None and auc_result['maximum'] < auc_threshold):
        return 'FAIL'
    if auc_result['exact'] and auc_result['maximum'] is None:
        return 'FAIL'  # Every completion has undefined discrimination.
    if (dense_min >= dense_threshold and not auc_result['undefined_possible']
            and auc_result['minimum'] is not None and auc_result['minimum'] >= auc_threshold):
        return 'PASS'
    return 'INCONCLUSIVE'


def bound_stratum(earlier, later, groups, *,draws=10000, limit=MAX_CONFIGURATIONS):
    e, em = check_array(earlier); l, lm = check_array(later)
    if e.shape != l.shape or len(groups) != len(e): raise ValueError('unpaired tasks')
    evaluate, auc = frozen_evaluator()
    dense_low, dense_high = dense_extremes(l)
    dense = {'minimum': sum(map(dense_flag, dense_low)), 'maximum': sum(map(dense_flag, dense_high)), 'exact': True}
    extrema, witnesses, undefined = auc_extremes(e, l, auc, limit=limit)
    outputs = {'dense_minimum': evaluate(fill_zero(e), dense_low, groups, draws=draws),
               'dense_maximum': evaluate(fill_zero(e), dense_high, groups, draws=draws)}
    private = {'dense_minimum': (fill_zero(e), dense_low), 'dense_maximum': (fill_zero(e), dense_high)}
    for direction, states in enumerate(witnesses):
        label = 'auc_' + ('maximum' if direction else 'minimum')
        if states is None:
            outputs[label] = None
        else:
            completed = completion(e, l, states, bool(direction))
            outputs[label] = evaluate(*completed, groups, draws=draws)
            assert outputs[label]['auc'] == extrema['witness_values'][direction]
            private[label] = completed
    if undefined is not None:
        completed = completion(e, l, undefined, False)
        outputs['auc_undefined'] = evaluate(*completed, groups, draws=draws)
        private['auc_undefined'] = completed
    result = {'status': verdict(dense['minimum'], dense['maximum'], extrema), 'tasks': len(groups),
              'affected_tasks': int((em.any(axis=1) | lm.any(axis=1)).sum()),
              'excluded_cells': int(em.sum()+lm.sum()), 'dense_only': dense, 'auc': extrema,
              'evaluate_outputs': outputs,
              'witness_interpretation': 'certified extrema' if extrema['exact'] else
              'dense extrema exact; AUC [0,1] outer bound, displayed AUC witnesses are feasible only, not certified extrema'}
    return result, private


def run(lock_path, repo, work_root, output_dir, publication):
    lock, paths = verify_lock(lock_path, repo, work_root)
    # Require the precise lock to be on fetched origin/main before any validation read.
    subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', publication, 'origin/main'], check=True)
    for name in ('g0', 'wrapper', 'tests', 'admission', 'evaluation'):
        item = lock['bindings'][name]
        data = subprocess.check_output(['git', '-C', str(repo), 'show', publication + ':' + item['path']])
        if hashlib.sha256(data).hexdigest() != item['sha256']: raise ValueError('unpublished binding: '+name)
    committed = subprocess.check_output(['git', '-C', str(repo), 'show', publication + ':' + str(Path(lock_path).resolve().relative_to(Path(repo).resolve()))])
    if committed != Path(lock_path).read_bytes(): raise ValueError('unpublished lock')
    output_dir = Path(output_dir)
    if output_dir.resolve() != (Path(work_root) / 'G0_A3').resolve():
        raise ValueError('single-run output path must be work-root/G0_A3')
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / 'attempt.json').open('x') as handle:
        json.dump({'publication': publication, 'lock_sha256': sha(lock_path), 'attempt': 1}, handle)
    opaque = json.loads(paths['opaque_public'].read_text())
    if opaque['equality_among_measured'] != 'PASS': raise ValueError('opaque admission missing')
    exclusions = json.loads(paths['exclusions'].read_text())
    manifest = [json.loads(line) for line in paths['ordinary_manifest'].open()]
    excluded = validate_exclusions(exclusions, manifest, lock['public_class_c'])
    with paths['ordinary_results'].open() as handle:
        strata, groups = load_arrays(manifest, (json.loads(line) for line in handle), excluded)
    result = {'gate': 'G0_A3', 'status': 'FAIL', 'publication': publication, 'lock_sha256': sha(lock_path),
              'threshold_source': 'PROTOCOL section 3; PLAN section 4; R2_A3_ADMISSION_10-14-2026.md',
              'dense_only_minimum': 21, 'dense_only_denominator': 135, 'auc_minimum': .65, 'strata': {}}
    private = {}
    for size, data in strata.items():
        if data['missing_unexcluded_cells']:
            result['strata'][size] = {'status': 'INCOMPLETE', 'tasks': 135,
                                     'missing_unexcluded_cells': data['missing_unexcluded_cells']}
            continue
        result['strata'][size], completions = bound_stratum(*data['arrays'], groups)
        private[size] = {key: [a.tolist() for a in pair] for key, pair in completions.items()}
    primary = result['strata']['4B']['status']
    result['status'] = 'FAIL' if primary == 'INCOMPLETE' else primary
    with (output_dir / 'completions_private.json').open('x') as handle:
        json.dump(private, handle)
    result['private_completions_sha256'] = sha(output_dir / 'completions_private.json')
    with (output_dir / 'result.json').open('x') as handle:
        json.dump(result, handle, indent=2); handle.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-root', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--publication', required=True)
    args = parser.parse_args()
    result = run(V2/'locks/G0_A3.json', REPO, args.work_root, args.output_dir, args.publication)
    print(json.dumps(result, indent=2))
    return {'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[result['status']]


if __name__ == '__main__':
    raise SystemExit(main())
