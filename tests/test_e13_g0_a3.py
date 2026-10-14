"""Verify A3 bounds against exhaustive synthetic completions and enforce pre-read integrity."""
import importlib.util
import itertools
import json
from pathlib import Path
import re

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
V2 = REPO / 'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2'
SPEC = importlib.util.spec_from_file_location('test_e13_g0_a3', V2/'reproduction/g0_a3.py')
A3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A3)


def arrays():
    e = np.zeros((4, 8, 2)); l = np.zeros_like(e)
    e[:, :, 1] = np.array([.2, .4, .6, .8])[:, None]
    l[:, :, 1] = .3
    l[0, 0] = (1, 1)
    return e, l


def exhaustive(e, l):
    evaluate, _ = A3.frozen_evaluator()
    holes = [(rung, i, k) for rung, a in enumerate((e, l)) for i, k in zip(*np.where(np.isnan(a[:, :, 0])))]
    values = []
    # Interior .3 is needed to witness a constant reward in dense-only cases.
    for assigned in itertools.product(((0, 0), (0, .3), (0, 1), (1, 1)), repeat=len(holes)):
        completed = [e.copy(), l.copy()]
        for (rung, i, k), value in zip(holes, assigned): completed[rung][i, k] = value
        values.append(evaluate(*completed, ['a', 'b', 'c', 'd'], draws=1))
    return values


@pytest.mark.parametrize('holes', [[], [(0, 0, 0)], [(1, 1, 0)],
                                   [(0, 0, 0), (0, 1, 0), (1, 1, 1)],
                                   [(0, 2, 0), (1, 0, 0), (1, 2, 1)],
                                   [(1, 0, 0), (1, 1, 0), (1, 3, 0)]])
def test_bounds_match_exhaustive_synthetic_completions(holes):
    e, l = arrays()
    for rung, i, k in holes: (e, l)[rung][i, k] = np.nan
    values = exhaustive(e, l)
    result, witnesses = A3.bound_stratum(e, l, ['a', 'b', 'c', 'd'], draws=3)
    assert result['dense_only']['minimum'] == min(v['dense_only'] for v in values)
    assert result['dense_only']['maximum'] == max(v['dense_only'] for v in values)
    valid = [v['auc'] for v in values if v['auc'] is not None]
    assert result['auc']['minimum'] == (min(valid) if valid else None)
    assert result['auc']['maximum'] == (max(valid) if valid else None)
    assert result['auc']['undefined_possible'] == any(v['auc'] is None for v in values)
    for earlier, later in witnesses.values():
        for original, completed in ((e, earlier), (l, later)):
            known = ~np.isnan(original[:, :, 0])
            np.testing.assert_array_equal(original[known], completed[known])
            A3.check_array(completed)


def test_dense_extrema_with_all_missing_and_constant_interior():
    _, l = arrays(); l[1] = np.nan; l[2, 0] = np.nan
    low, high = A3.dense_extremes(l)
    assert not A3.dense_flag(low[1]) and A3.dense_flag(high[1])
    assert not A3.dense_flag(low[2]) and A3.dense_flag(high[2])
    # Either constant B or mixed strict labels can realize the same minimum.
    np.testing.assert_array_equal(low[2, 1:], l[2, 1:])


def test_one_class_completion_and_all_undefined_never_pass():
    e, l = arrays(); l[0, 0] = np.nan
    result, _ = A3.bound_stratum(e, l, list('abcd'), draws=3)
    assert result['auc']['undefined_possible']
    assert result['evaluate_outputs']['auc_undefined']['auc'] is None
    assert A3.verdict(30, 40, result['auc']) != 'PASS'
    l[0, 0] = (0, .3)
    result, _ = A3.bound_stratum(e, l, list('abcd'), draws=3)
    assert result['auc']['maximum'] is None
    assert A3.verdict(30, 40, result['auc']) == 'FAIL'


def test_auc_monotonicity_with_average_rank_ties():
    _, auc = A3.frozen_evaluator()
    labels = np.array([0, 1, 0, 1, 1, 0], bool)
    for scores in itertools.product((0., .5, 1.), repeat=6):
        scores = np.array(scores); original = auc(labels, scores)
        for i in range(len(scores)):
            improved = scores.copy(); improved[i] = 1. if labels[i] else 0.
            assert auc(labels, improved) >= original


def test_outer_bound_is_conservative_and_cannot_create_pass_or_fail():
    e, l = arrays(); e[0, 0] = np.nan; l[2, 0] = np.nan
    exact, _ = A3.bound_stratum(e, l, list('abcd'), draws=2)
    outer, _ = A3.bound_stratum(e, l, list('abcd'), draws=2, limit=1)
    assert not outer['auc']['exact']
    assert outer['auc']['minimum'] <= exact['auc']['minimum'] <= exact['auc']['maximum'] <= outer['auc']['maximum']
    assert A3.verdict(30, 40, outer['auc']) == 'INCONCLUSIVE'
    assert A3.verdict(0, 20, outer['auc']) == 'FAIL'


def exclusion_fixture():
    public = set(re.findall(r'`(sft_[^`]+/\d+)`', (V2/'RESULTS_R2_diagnosis.md').read_text()))
    assert len(public) == 4
    ids = sorted(public) + [f'fixture/task_{i}/0' for i in range(213)]
    exclusions = []
    for i, cell in enumerate(ids):
        cls = 'c' if i < 4 else 'd' if i < 47 else 'a' if i < 50 else None
        status = 'deterministic_resource_limit' if i >= 49 else 'unresolved_measurement'
        exclusions.append({'cell_id': cell, 'split': 'validation', 'recorded_status': status, 'a3_class': cls})
    manifest = [{'cell_id': c, 'split': 'validation'} for c in ids]
    manifest += [{'cell_id': f'other/{i}/0', 'split': 'train'} for i in range(33456-len(ids))]
    return exclusions, manifest, public


def test_every_listed_exclusion_including_four_public_cells_is_discarded():
    exclusions, manifest, public = exclusion_fixture()
    ids = A3.validate_exclusions(exclusions, manifest, public)
    # Poison receipts deliberately omit all measured fields. Exclusion must happen first.
    poison = [{'cell_id': r['cell_id'], 'split': r['split']} for r in exclusions]
    assert list(A3.retained_rows(poison, ids)) == []
    actual = Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/R2_diagnosis_10-14-2026/a3_ordinary_exclusions_private.json')
    if actual.exists():
        assert A3.sha(actual) == A3.EXCLUSION_HASH
        listed = json.loads(actual.read_text())
        actual_ids = {r['cell_id'] for r in listed}
        assert len(actual_ids) == 217 and public <= actual_ids
        assert list(A3.retained_rows(listed, actual_ids)) == []
    exclusions[0]['split'] = 'test'
    with pytest.raises(ValueError, match='nonordinary'): A3.validate_exclusions(exclusions, manifest, public)


def test_loader_masks_exclusions_and_retains_other_missing_as_incomplete():
    manifest = []; rows = []; excluded = set()
    for size in A3.SIZES:
        for rung in ('f0p5', 'f1p0'):
            policy = f'sft_{size}_{rung}'
            for k in range(8):
                cell = f'{policy}/task/{k}'
                base = {'cell_id': cell, 'split': 'validation', 'task_id': 'task', 'group_id': 'group', 'sample_idx': k}
                manifest.append({**base, 'expectations': [{'family': 'ladder', 'policy': policy}]})
                if k == 0:
                    excluded.add(cell); rows.append(base)  # Poison excluded measurement.
                elif k != 1:
                    rows.append({**base, 'status': 'measured', 'readbacks': [{'family': 'ladder', 'policy': policy, 'equal': True, 'value': 0, 'factored_reward': .5}]})
    strata, groups = A3.load_arrays(manifest, rows, excluded, task_count=1)
    assert groups == ['group']
    for data in strata.values():
        assert data['missing_unexcluded_cells'] == 2
        assert all(np.isnan(a[0, 0]).all() for a in data['arrays'])
    with pytest.raises(ValueError, match='sealed'):
        list(A3.retained_rows([{'split': 'test', 'cell_id': 'sealed'}], {'sealed'}))


@pytest.mark.parametrize('name', ['g0', 'wrapper', 'tests', 'exclusions', 'admission', 'ordinary_manifest', 'ordinary_results', 'evaluation', 'opaque_public'])
def test_hash_mismatch_refuses_before_any_validation_parse(tmp_path, monkeypatch, name):
    names = ['g0', 'wrapper', 'tests', 'exclusions', 'admission', 'ordinary_manifest', 'ordinary_results', 'evaluation', 'opaque_public']
    bindings = {}
    for key in names:
        path = tmp_path/key; path.write_text('not JSON: no validation parsing allowed')
        bindings[key] = {'root': 'repo', 'path': key, 'sha256': A3.sha(path)}
    (tmp_path/name).write_text('mutated')
    lock = tmp_path/'lock.json'; lock.write_text(json.dumps({'bindings': bindings}))
    def forbidden(*args, **kwargs): raise AssertionError('validation read before hash refusal')
    monkeypatch.setattr(A3, 'load_arrays', forbidden)
    monkeypatch.setattr(A3, 'frozen_evaluator', forbidden)
    with pytest.raises(ValueError, match='hash mismatch'):
        A3.run(lock, tmp_path, tmp_path, tmp_path/'output', 'unused')
    assert not (tmp_path/'output').exists()


def test_invalid_partial_missing_or_strict_success_reward_rejected():
    e, _ = arrays(); e[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match='partially'): A3.check_array(e)
    e[0, 0] = (1, .5)
    with pytest.raises(ValueError, match='reward'): A3.check_array(e)
