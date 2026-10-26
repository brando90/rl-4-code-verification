"""Verify Experiment 20's missing-smooth analysis without numerical fits, compilers, GPUs, or model calls."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import tempfile

import numpy as np
from scipy.special import expit

E20_NAME = '20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013'
HERE = Path(__file__).resolve().parent
# Intended installed location: experiments/<E20_NAME>/expt_v1/verification/verify_missing_smooth_analysis.py
DEFAULT_REPO = HERE.parents[3] if len(HERE.parents) > 3 else None
C = None


def load_analysis(repo: Path):
    source = repo / 'experiments' / E20_NAME / 'expt_v1/analyze_phase0_e20.py'
    if not source.is_file():
        raise FileNotFoundError(f'analysis driver not found: {source}')
    spec = importlib.util.spec_from_file_location('analyze_phase0_e20_under_verification', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def write_scores(generation_manifest: Path, path: Path, *, smooth_missing: int | None = None,
                 strict_missing: int | None = None) -> None:
    generation = list(csv.DictReader(generation_manifest.open(newline='')))
    fields = ['task_id', 'sample_idx', 'status', 'strict', 'factored_reward', 'partial_status', 'partial_note', 'IC_tests',
              'IC_proofs', 'FSC', 'generated_tokens', 'capped', 'lean_sha256', 'seed']
    with path.open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(generation):
            sample = int(row['sample_idx'])
            strict = int((i * 7 + sample) % 11 == 0)
            reward = [0.0, 0.25, 0.6, 0.9, 1.0][(i + sample) % 5]
            out = dict(task_id=row['task_id'], sample_idx=sample, status='measured', strict=strict,
                       factored_reward=reward, partial_status='measured', partial_note='', IC_tests=strict,
                       IC_proofs=strict, FSC='unmeasured', generated_tokens=row['generated_tokens'],
                       capped=row['capped'], lean_sha256=row['lean_sha256'], seed=row['seed'])
            if i == smooth_missing:
                out.update(factored_reward='', partial_status='unresolved',
                           partial_note='duplicate fully qualified declaration identity')
            if i == strict_missing:
                out.update(status='unresolved_measurement', strict='')
            writer.writerow(out)


def legacy_joint_log_score(fit, ys, ms, cat, mc, target, pseudo):
    """Frozen pre-candidate implementation, used only to check the all-complete path."""
    grid = C.I.Grid(*fit['grid'])
    par = C.I.two_skill_params(fit['x'], fit['n_items'], 5, fit['tied'])
    oh = C.I.onehot_categories(cat, mc, 5)
    ls, lf = C.I.two_skill_node_logliks(par, ys, ms, oh, grid.nodes)
    _, joint, post_s, _, _ = C.I.two_skill_posterior(par, ls, lf, grid)
    ac = expit(par['a'][target, None] * grid.nodes + par['d'][target, None])
    pc, _ = C.I.grm_cat_probs(par['b'][target], par['cuts'][target], grid.nodes)
    total = 0.0
    for r in pseudo:
        prob_s = np.where(ys[r, target, None] == 1, ac, 1 - ac)
        prob_c = np.take_along_axis(
            pc, np.broadcast_to(cat[r, target, None, None].astype(int), (len(target), grid.count, 1)), axis=2
        )[:, :, 0]
        weighted = prob_s * post_s[r] if joint is None else prob_s @ joint[r]
        total += float(np.log(np.clip(np.sum(weighted * prob_c, axis=1), 1e-300, 1)).sum())
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=DEFAULT_REPO,
                        help='repository root; defaults from the script installed under expt_v1/verification')
    args = parser.parse_args()
    if args.repo is None:
        parser.error('--repo is required when the script is not installed under expt_v1/verification')
    repo = args.repo.resolve()
    generation_manifest = repo / 'experiments' / E20_NAME / 'expt_v1/results/phase0_cells_unscored.csv'
    global C
    C, source = load_analysis(repo)

    with tempfile.TemporaryDirectory(prefix='e20_missing_smooth_verify_') as tmp_name:
        tmp = Path(tmp_name)
        complete_scores, partial_scores, strict_missing_scores = (
            tmp / n for n in ('complete.csv', 'partial.csv', 'strict_missing.csv')
        )
        write_scores(generation_manifest, complete_scores)
        write_scores(generation_manifest, partial_scores, smooth_missing=17)
        write_scores(generation_manifest, strict_missing_scores, strict_missing=11)

        complete = C.load_inputs(repo, complete_scores, generation_manifest, tmp / 'complete_out')
        partial = C.load_inputs(repo, partial_scores, generation_manifest, tmp / 'partial_out')
        assert np.array_equal(complete['strict'], partial['strict'])
        assert np.array_equal(complete['k_sp'], partial['k_sp'])
        assert np.array_equal(complete['n_sp'], partial['n_sp'])
        assert complete['reward_mask'].all() and partial['reward_mask'].sum() == 4311
        audit = json.loads((tmp / 'partial_out/input_audit.json').read_text())
        assert audit['strict_measured_cells'] == 4312 and audit['strict_missing_cells'] == 0
        assert audit['smooth_measured_cells'] == 4311 and audit['smooth_missing_cells'] == 1
        assert audit['smooth_missing_status_counts'] == {'unresolved': 1}
        assert audit['smooth_missing_reason_counts'] == {
            'unresolved: duplicate fully qualified declaration identity': 1
        }
        assert audit['measured_joint_cells'] == 4311

        try:
            C.load_inputs(repo, strict_missing_scores, generation_manifest, tmp / 'strict_missing_out')
        except ValueError as exc:
            assert 'strict scoring incomplete' in str(exc)
        else:
            raise AssertionError('a missing strict cell must reject the analysis')

        v = np.array([0.0, 0.25, 0.6, 0.9, 1.0, 0.25, 0.6, 0.9])
        all_complete = C.smooth_task_summary(v, np.ones(8, bool))
        assert all_complete['smooth_mean'] == float(v.mean())
        assert all_complete['smooth_sd'] == float(v.std(ddof=1))
        assert all_complete['smooth_nonconstant'] == int(np.ptp(v) > 0)
        assert all_complete['smooth_summary_scope'] == 'complete_case'
        partial_summary = C.smooth_task_summary(v, np.array([1, 1, 0, 0, 0, 0, 0, 0], bool))
        assert partial_summary['smooth_measured'] == 2
        assert partial_summary['smooth_nonconstant'] is None
        assert (partial_summary['smooth_nonconstant_lower'], partial_summary['smooth_nonconstant_upper']) == (1, 1)

        # A masked category never enters the one-hot likelihood representation or objective.
        ys = np.array([[0., 1., 0.], [1., 0., 1.]])
        ms = np.ones_like(ys)
        cat0 = np.array([[0, 1, 2], [3, 4, 0]])
        mc = np.ones_like(ys)
        mc[0, 1] = 0
        cat1 = cat0.copy()
        cat1[0, 1] = 4
        oh0, oh1 = C.I.onehot_categories(cat0, mc, 5), C.I.onehot_categories(cat1, mc, 5)
        assert np.array_equal(oh0, oh1)
        layout = C.I._layout(3, 5, True)
        x = np.zeros(layout['size'])
        grid = C.I.Grid(-3, 3, 61)
        obj0 = C.I.objective_two_skill(x, ys, ms, oh0, 5, True, grid, .5, 1.0)[0]
        obj1 = C.I.objective_two_skill(x, ys, ms, oh1, 5, True, grid, .5, 1.0)[0]
        assert obj0 == obj1

        pseudo, target = np.array([0, 1]), np.array([0, 1, 2])
        assert C.paired_cell_count(ms, mc, pseudo, target) == 5
        for tied in (True, False):
            layout = C.I._layout(3, 5, tied)
            x = np.zeros(layout['size'])
            if not tied:
                x[layout['r']] = 0.4
            fit = dict(x=x, n_items=3, n_cats=5, tied=tied, grid=(-3, 3, 61))
            complete_mask = np.ones_like(ms, bool)
            new_complete = C.joint_log_score(fit, ys, ms, cat0, np.ones_like(mc), target, pseudo, complete_mask)
            old_complete = legacy_joint_log_score(fit, ys, ms, cat0, np.ones_like(mc), target, pseudo)
            assert new_complete == old_complete
            score0 = C.joint_log_score(fit, ys, ms, cat0, mc, target, pseudo, (ms > 0) & (mc > 0))
            score1 = C.joint_log_score(fit, ys, ms, cat1, mc, target, pseudo, (ms > 0) & (mc > 0))
            assert score0 == score1

        print(json.dumps({
            'status': 'PASS',
            'analysis_source': str(source.relative_to(repo)),
            'strict_counts_unchanged_with_missing_smooth': True,
            'missing_strict_rejected': True,
            'masked_category_likelihood_invariant': True,
            'paired_cells_scored': C.paired_cell_count(ms, mc, pseudo, target),
            'paired_cells_declared': int(ms.size),
            'all_complete_joint_score_exactly_unchanged': True,
            'tied_and_correlated_untied_checked': True,
            'fixture_smooth_measured_declared': [audit['smooth_measured_cells'], audit['smooth_declared_cells']],
            'numerical_fits': 0,
            'compiler_calls': 0,
        }, sort_keys=True))


if __name__ == '__main__':
    main()
