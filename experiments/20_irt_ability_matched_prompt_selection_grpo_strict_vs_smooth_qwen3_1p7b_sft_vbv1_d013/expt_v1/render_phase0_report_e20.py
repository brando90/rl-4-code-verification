"""Render saved E20 CPU Phase 0 analysis evidence to one Markdown report without modifying inputs or running fits."""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import json
import math
from pathlib import Path

EXPERIMENT = '20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013'
MODELS = ('random_intercept', 'explanatory', 'random_intercept_1pl', 'explanatory_1pl', 'features_only', 'baseline', 'panel_strict_rate')
LABELS = dict(random_intercept='Random-intercept 2PL', explanatory='Explanatory 2PL',
              random_intercept_1pl='Random-intercept 1PL', explanatory_1pl='Explanatory 1PL',
              features_only='Features only', baseline='Population Beta(1,1)', panel_strict_rate='Panel strict rate (ranking only)')


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def num(value, digits=4):
    return f'{value:.{digits}g}' if finite(value) else 'unavailable'


def cell(value):
    return str(value if value is not None else 'unavailable').replace('|', '\\|').replace('\n', ' ')


def integer(value):
    return str(int(value)) if finite(value) and int(value) == value else 'unavailable'


def estimate(interval, point=None, pvalue=False):
    interval = interval if isinstance(interval, dict) else {}
    value = interval.get('point', point)
    text = f"{num(value)} [{num(interval.get('lo'))}, {num(interval.get('hi'))}]"
    if pvalue:
        text += ' p-val=' + (num(interval['p_two_sided']) if finite(interval.get('p_two_sided')) else 'n/a')
    return text


def truth(v):
    return v is True or isinstance(v, str) and v.lower() == 'true'


class Evidence:
    def __init__(self, root):
        self.root = root
        self.problems = []
        self.cache = {}

    def read(self, name, csv_file=False):
        if name in self.cache:
            return self.cache[name]
        path = self.root / name
        try:
            with path.open(newline='' if csv_file else None) as fh:
                result = list(csv.DictReader(fh)) if csv_file else json.load(fh)
            if not csv_file and not isinstance(result, dict):
                raise ValueError('expected a JSON object')
        except (OSError, ValueError, csv.Error) as exc:
            self.problems.append(f'{name}: {type(exc).__name__}: {exc}')
            result = None
        self.cache[name] = result
        return result


def native_verify(repo, results, final, pins):
    receipt = final.get('freeze', {}) if isinstance(final.get('freeze'), dict) else {}
    raw = receipt.get('file')
    if not raw:
        return {'status': 'unavailable', 'reason': receipt.get('status', 'no freeze receipt/file')}
    path = Path(raw)
    if not path.is_absolute():
        # An explicit relative --freeze-dir is relative to the analysis launch checkout.
        candidates = [repo/path, results/path]
        path = next((p for p in candidates if p.is_file()), candidates[0])
    try:
        sys.path.insert(0, str(repo/'src'))
        from rl4cv.forecast import verify_forecast
        valid = verify_forecast(path)
        payload = json.loads(path.read_text())
        ids = payload.get('task_ids', [])
        arrays = ('a', 'd', 'p_strict', 'p_active', 'p_strict_at_theta0', 'p_active_at_theta0')
        lengths_match = isinstance(ids, list) and len(ids) == 539 and len(set(ids)) == 539 and all(
            isinstance(payload.get(k), list) and len(payload[k]) == 539 and all(finite(x) for x in payload[k]) for k in arrays)
        identity_match = bool(pins and pins.get('identity') and payload.get('input_identity') == pins['identity'])
        return {'status': 'verified' if valid and lengths_match and identity_match else 'FAILED verification',
                'native_hash_verified': valid, 'task_count': len(ids), 'all_parameter_lengths_539': lengths_match,
                'input_identity_matches': identity_match, 'file': str(path), 'theta0': payload.get('theta0'),
                'theta0_sd': payload.get('theta0_sd'), 'model': payload.get('model')}
    except (OSError, ValueError, TypeError, ImportError, KeyError) as exc:
        return {'status': 'unavailable', 'file': str(path), 'reason': f'{type(exc).__name__}: {exc}'}


def safe_float(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError):
        return None


def max_gradient(rows, key):
    values = [safe_float(r.get(key)) for r in rows]
    return max(values) if values and all(v is not None for v in values) else None


def numerical_ok(f):
    return isinstance(f, dict) and truth(f.get('converged')) and all(
        finite(f.get(k)) and 0 <= f[k] <= 1e-4 for k in ('max_abs_grad', 'check_grid_max_abs_grad'))


def build_report(args):
    E = Evidence(args.results_dir)
    primary = E.read('primary_g0.json') or {}
    final = E.read('analysis_e20.json') or {}
    audit = E.read('input_audit.json') or {}
    pins = E.read('input_pins_e20.json') or {}
    boot = E.read('primary_g0_bootstrap.json') or {}
    finals = E.read('primary_final_fit_summary.json') or {}
    gate = primary.get('gate', {})
    selected = primary.get('selected_model')
    model = primary.get('models', {}).get(selected, {})
    intervals = primary.get('intervals', {}).get(selected, {})
    assessable = (gate.get('status') == 'evaluated' and finite(gate.get('auc')) and
                  finite(gate.get('log_loss')) and finite(gate.get('baseline_log_loss')))
    verdict = ('PASS' if gate.get('passed') is True else 'FAIL (IRT selection NULL)') if assessable else 'UNAVAILABLE'
    if assessable:
        literal = gate['auc'] >= .70 and gate['log_loss'] < gate['baseline_log_loss']
        if literal != (gate.get('passed') is True):
            E.problems.append('primary_g0.json: saved gate verdict disagrees with registered numeric criteria')
            verdict = 'UNAVAILABLE: inconsistent gate evidence'
    freeze = native_verify(args.repo, args.results_dir, final, pins)
    try:
        relative = args.out_md.resolve().relative_to(args.repo.resolve()).as_posix()
    except ValueError:
        relative = f'experiments/{EXPERIMENT}/RESULTS_phase0_calibration.md'
    link = f'https://github.com/brando90/rl-4-code-verification/blob/{args.branch}/{relative}'
    L = [f'# Experiment 20: CPU Phase 0 calibration', '', f'**Doc link:** <{link}>', '',
         '**TLDR:** '+f'Primary calibration gate G0: **{verdict}**. Frozen item parameters: **{freeze["status"]}**. '
         'Trainer **FAILED**, unchanged; this CPU follow-up does not authorize training.', '',
         f'Experiment: `{EXPERIMENT}`. The post-stop CPU dispatcher was authorized on **10-21-2026** to score saved generations, '
         'fit calibration models and freeze parameters. The link above is the intended branch publication location.', '',
         'Declared cohort: VeriBench V1 train **539 tasks / 400 task groups / 4,312 saved samples** (8 samples per task). '
         f'Strict scoring: **{integer(audit.get("strict_measured_cells"))}/{integer(audit.get("strict_declared_cells", audit.get("declared_cells")))}** measured; '
         f'smooth reward: **{integer(audit.get("smooth_measured_cells"))}/{integer(audit.get("smooth_declared_cells", audit.get("declared_cells")))}** measured, '
         f'**{integer(audit.get("smooth_missing_cells"))}** missing. '
         f'Joint strict/smooth observed cells **{integer(audit.get("measured_joint_cells"))}/{integer(audit.get("declared_cells"))}**. '
         f'Panel measured cells **{integer(audit.get("panel_measured_cells"))}/{integer(audit.get("panel_declared_cells"))}**; '
         'unmeasured entries remain missing and are never silently recoded as zero.', '',
         '## Primary held-out calibration', '',
         f'Selected model: **{cell(LABELS.get(selected, selected))}**. '
         f'Area under the receiver-operating-characteristic curve (AUC): **{estimate(intervals.get("auc"), model.get("auc"), True)}**; '
         f'log loss **{estimate(intervals.get("log_loss"), model.get("log_loss"), True)}** versus '
         f'population Beta(1,1) baseline **{estimate(primary.get("intervals",{}).get("baseline",{}).get("log_loss"), gate.get("baseline_log_loss"), True)}**. '
         f'Paired baseline-minus-model log-loss gain: **{estimate(intervals.get("log_loss_gain_vs_baseline"), pvalue=True)}**.', '',
         'G0 requires AUC ≥ 0.70 and lower log loss than the in-fold population Beta(1,1) forecast '
         '(registered E20 protocol §3; AUC threshold from E13 F2). These are point-estimate gates; calibration error and alternatives are descriptive. '
         'No training gate is reopened by a calibration PASS.', '',
         f'Expected calibration error (ECE; 10 equal-width bins): **{estimate(intervals.get("ece"), model.get("ece"), True)}**. '
         f'Predicted active share **{estimate(intervals.get("predicted_active_share"), model.get("predicted_active_share"), True)}** versus observed '
         f'**{estimate(intervals.get("observed_active_share"), model.get("observed_active_share"), True)}**. '
         f'Mean absolute error **{estimate(intervals.get("mean_absolute_error"), model.get("mean_absolute_error"), True)}**; '
         f'mean bias **{estimate(intervals.get("mean_bias"), model.get("mean_bias"), True)}** '
         '(prediction minus observation; positive means overprediction).', '',
         '## Alternatives on the same task folds', '',
         '| Model | Status | AUC [95% interval] | Log loss [95% interval] | ECE [95% interval] | Predicted / observed active share |',
         '|---|---|---|---|---|---|']
    for name in MODELS:
        r = primary.get('models', {}).get(name, {})
        ci = primary.get('intervals', {}).get(name, {})
        ranking = name == 'panel_strict_rate'
        L.append('| '+ ' | '.join([LABELS[name],cell(r.get('status','unavailable')),
            estimate(ci.get('auc'),r.get('auc')), 'not a probability forecast' if ranking else estimate(ci.get('log_loss'),r.get('log_loss')),
            'not applicable' if ranking else estimate(ci.get('ece'),r.get('ece')),
            'not applicable' if ranking else f'{num(r.get("predicted_active_share"))} / {num(r.get("observed_active_share"))}'])+' |')
    L += ['', '2PL = two-parameter logistic item response model; 1PL fixes every discrimination slope to one. '
          'Panel-rate comparison uses the original 11-system strict pass rates for ranking only. '
          f'Selected-minus-panel AUC difference: **{estimate(intervals.get("auc_minus_panel"), pvalue=True)}**.', '',
          f'Intervals use **{integer(boot.get("draws"))}** paired train-task-group bootstrap draws '
          f'(registered 10,000; seed **{integer(boot.get("seed"))}**). Resampling unit: **{cell(boot.get("unit"))}**. '
          f'Limits: {cell(boot.get("limits"))}. '
          'AUC p-values above compare with 0.70; paired difference p-values use the two-sided percentile test of zero, floored at 1/draws. '
          'Other level statistics and descriptive table entries have p-val=n/a. '
          f'Selected AUC finite bootstrap draws: **{integer(intervals.get("auc",{}).get("valid_draws"))}/'
          f'{integer(intervals.get("auc",{}).get("requested_draws"))}**. Eight generated samples are not repeated rescoring trials; rescoring variability was not measured.', '',
          '## Priors and numerical convergence', '',
          'Each 2PL family has 20 prior pairs × 5 grouped cell folds; each descriptive 1PL family has 5 residual scales × 5 folds. '
          'Every accepted count fit must satisfy maximum absolute gradient ≤ 1e-4 on both the 1,201-node fitting grid and the 4,801-node check grid. '
          'The table separates observed counts from the registered required counts.', '',
          '| Dataset / model | Chosen slope SD / residual SD | Eligible priors / observed / required | Converged CV fits / observed / required | Converged G0 fits / observed / required | Final fit status; fitting / check gradient |',
          '|---|---|---|---|---|---|']
    for tag,label in [('primary','Primary'),('with_e05','With E05')]:
        priors=E.read(f'{tag}_priors.json') or {}
        grid=E.read(f'{tag}_cv_grid.csv',True)
        cv=E.read(f'{tag}_cv_folds.csv',True)
        g=primary if tag=='primary' else E.read(f'{tag}_g0.json') or {}
        fs=finals if tag=='primary' else E.read(f'{tag}_final_fit_summary.json') or {}
        for name in MODELS[:4]:
            fixed=name.endswith('_1pl');family=name.removesuffix('_1pl');required=5 if fixed else 20
            rows=None if grid is None else [r for r in grid if r.get('family')==family and truth(r.get('fixed_slope'))==fixed]
            folds=None if cv is None else [r for r in cv if r.get('family')==family and truth(r.get('fixed_slope'))==fixed]
            gfits=[r for r in g.get('convergence',[]) if r.get('model')==name]
            eligible=None if rows is None else sum(safe_float(r.get('converged_folds'))==5 and safe_float(r.get('folds'))==5 and safe_float(r.get('log_loss')) is not None for r in rows)
            converged=None if folds is None else sum(truth(r.get('converged')) and all(safe_float(r.get(k)) is not None and 0<=float(r[k])<=1e-4 for k in ('max_abs_grad','check_grid_max_abs_grad')) for r in folds)
            pr=priors.get(name) or {};f=fs.get(name) or {}
            final_status='converged' if numerical_ok(f) else 'failed/unavailable'
            L.append('| '+ ' | '.join([f'{label} / {LABELS[name]}',f'{num(pr.get("slope_sd"))} / {num(pr.get("sigma_e"))}',
                f'{integer(eligible)} / {integer(len(rows) if rows is not None else None)} / {required}',
                f'{integer(converged)} / {integer(len(folds) if folds is not None else None)} / {required*5}',
                f'{sum(numerical_ok(r) for r in gfits)} / {len(gfits)} / 5' if g else 'unavailable / unavailable / 5',
                f'{final_status}; {num(f.get("max_abs_grad"))} / {num(f.get("check_grid_max_abs_grad"))}'])+' |')
        feature_fits=[r for r in g.get('convergence',[]) if r.get('model')=='features_only']
        L += [f'', f'{label} features-only numerical fits: **{str(sum(numerical_ok(r) for r in feature_fits))+"/"+str(len(feature_fits))+" observed" if g else "unavailable"}**, 5 required; '
              f'max fitting/check gradients **{num(max_gradient(feature_fits,"max_abs_grad"))} / {num(max_gradient(feature_fits,"check_grid_max_abs_grad"))}**.']
    # Keep the main convergence table contiguous; feature summaries follow it.
    feature_notes=[line for line in L if line.startswith(('Primary features-only numerical fits:', 'With E05 features-only numerical fits:'))]
    L=[line for line in L if line not in feature_notes]
    # Blank lines inserted between the two datasets would split the Markdown table, so remove those only.
    start=next(i for i,v in enumerate(L) if v.startswith('| Dataset / model'))
    L=L[:start]+[v for v in L[start:] if v!='']
    L += ['',*feature_notes,'','## E05 Base-model sensitivity','']
    sensitivity=E.read('e05_sensitivity.json') or {}
    alt=E.read('with_e05_g0.json') or {}
    ag=alt.get('gate',{})
    altassessed=ag.get('status')=='evaluated' and finite(ag.get('auc'))
    altverdict=('PASS' if ag.get('passed') is True else 'NULL') if altassessed else 'unavailable'
    altci=alt.get('intervals',{}).get(alt.get('selected_model'),{})
    altbaseci=alt.get('intervals',{}).get('baseline',{})
    L += [f'Alternative including three E05 Base models: **{altverdict}**, selected **{cell(alt.get("selected_model"))}**, '
          f'AUC **{estimate(altci.get("auc"), ag.get("auc"), True)}**, log loss **{estimate(altci.get("log_loss"),ag.get("log_loss"),True)}** versus baseline **{estimate(altbaseci.get("log_loss"),ag.get("baseline_log_loss"),True)}**. '
          f'Primary-selection policy: {cell(sensitivity.get("selection_rule"))}', '',
          '| Model | Mean / maximum absolute slope change | Mean / maximum absolute intercept change | Mean absolute active-probability change | Ability change |',
          '|---|---|---|---|---|']
    comparisons=sensitivity.get('comparisons',{})
    for name in MODELS[:4]:
        r=comparisons.get(name,{})
        L.append(f'| {LABELS[name]} | {num(r.get("mean_abs_delta_a"))} / {num(r.get("max_abs_delta_a"))} | '
                 f'{num(r.get("mean_abs_delta_d"))} / {num(r.get("max_abs_delta_d"))} | {num(r.get("mean_abs_delta_p_active"))} | {num(r.get("theta_delta"))} |')
    L += ['', 'The registration says to add Base models if the fit changes but supplies no substantive-change threshold. '
          'Both fits must be reported, preserving the specified 11-system primary; no favorable-G0 substitution is made.', '',
          '## Smooth reward and dimensionality', '']
    smooth=E.read('smooth_analysis.json') or {}
    dim=E.read('dimensionality.json') or {}
    smooth_measured = smooth.get("smooth_measured_cells", audit.get("smooth_measured_cells"))
    smooth_declared = smooth.get("smooth_declared_cells", audit.get("smooth_declared_cells", audit.get("declared_cells")))
    smooth_missing = smooth.get("smooth_missing_cells", audit.get("smooth_missing_cells"))
    smooth_reasons = smooth.get("smooth_missing_reason_counts", audit.get("smooth_missing_reason_counts", {}))
    cat_lo = smooth.get("observed_category_nonconstant_share_lower", smooth.get("observed_category_nonconstant_share"))
    cat_hi = smooth.get("observed_category_nonconstant_share_upper", smooth.get("observed_category_nonconstant_share"))
    exact_lo = smooth.get("observed_exact_nonconstant_share_lower", smooth.get("observed_exact_nonconstant_share"))
    exact_hi = smooth.get("observed_exact_nonconstant_share_upper", smooth.get("observed_exact_nonconstant_share"))
    likelihood = smooth.get("smooth_missingness_likelihood", audit.get("smooth_missingness_likelihood", "unavailable"))
    L += [f'Graded smooth-reward model: **{cell(smooth.get("status",final.get("smooth_status")))}**; '
          f'measured/declared smooth cells **{integer(smooth_measured)}/{integer(smooth_declared)}**, missing **{integer(smooth_missing)}**. '
          f'fitting/check maximum gradients **{num(smooth.get("fit",{}).get("max_abs_grad"))} / {num(smooth.get("fit",{}).get("check_grid_max_abs_grad"))}** (gate ≤ 1e-4). '
          f'Predicted nonconstant-category share **{num(smooth.get("predicted_category_nonconstant_share"))}** across all 539 items. '
          f'Observed category-nonconstant share sharp bounds **[{num(cat_lo)}, {num(cat_hi)}]** and exact-reward-nonconstant share sharp bounds **[{num(exact_lo)}, {num(exact_hi)}]**; '
          'these deterministic bounds include all missing smooth cells and are not confidence intervals. '
          'Smooth summaries are conditional on observed smooth cells: missing-at-random is not established. '
          'The ordinal forecast is a lower bound on exact smooth-reward nonconstancy because within-bin differences are unidentifiable. '
          'These are posterior replications, not prospective predictions of the already observed Phase 0 outcomes.',
          f'Smooth missingness reasons: **{cell(smooth_reasons)}**. Likelihood handling: **{cell(likelihood)}**. Registered malformed-source zeroes are observed zero rewards; duplicate fully qualified declaration identities remain missing.', '',
          '| Strict difficulty versus graded threshold | Pearson [95% interval] | Spearman [95% interval] | Kendall [95% interval] |',
          '|---|---|---|---|']
    corr=smooth.get('difficulty_correlations',{})
    for name,label in [('first_threshold_ability_scale','First ability threshold −cut₁/b'),('first_cut_logit_parameter','Literal first logit cut (sensitivity)')]:
        r=corr.get(name,{})
        L.append('| '+ ' | '.join([label]+[estimate(r.get(k)) for k in ('pearson','spearman','kendall')])+' |')
    cb=smooth.get('correlation_bootstrap',{})
    L += ['', f'Correlation intervals: **{integer(cb.get("draws"))}** item-group bootstrap draws (registered 1,000), '
          f'**{integer(cb.get("groups"))}** groups; conditional on fitted parameters, no model refitting; all correlation p-val=n/a.', '',
          f'Tied versus untied skill comparison: **{cell(dim.get("status",final.get("dimensionality_status")))}**. '
          f'Joint held-out log likelihood: tied **{num((dim.get("joint_log_likelihood") or {}).get("tied"))}**, '
          f'untied **{num((dim.get("joint_log_likelihood") or {}).get("untied"))}**, difference **{num(dim.get("untied_minus_tied"))}**, '
          f'**{integer(dim.get("paired_cells_scored"))}** observed paired cells / **{integer(dim.get("paired_cells_declared", audit.get("declared_cells")))}** declared. '
          'The log score integrates the strict outcome and ordinal category jointly, preserving within-cell dependence. '
          f'Selection limitation: {cell(dim.get("selection_limitation", "paired comparison is conditional on observed smooth cells"))}. '
          'This descriptive partial-reward analysis does not gate strict G0; a failed full-fit or held-out numerical check makes the dimensional comparison unavailable.', '',
          '| Dimensional model | Full-fit convergence | Fitting / finer-check gradient | Converged held-out fits / observed / required |',
          '|---|---|---|---|']
    for name in ('tied','untied'):
        r=dim.get('full_fits',{}).get(name,{})
        folds=[f for f in dim.get('fold_fits',[]) if f.get('model')==name]
        L.append(f'| {name} | {"yes" if numerical_ok(r) else "failed/unavailable"} | '
                 f'{num(r.get("max_abs_grad"))} / {num(r.get("check_grid_max_abs_grad"))} | '
                 f'{str(sum(numerical_ok(f) for f in folds))+" / "+str(len(folds)) if dim else "unavailable / unavailable"} / 5 |')
    L += ['', '## Frozen parameters and completeness', '',
          f'Native `rl4cv.forecast.verify_forecast`: **{cell(freeze.get("native_hash_verified","unavailable"))}**; '
          f'freeze status **{freeze["status"]}**; task count **{integer(freeze.get("task_count"))}**; '
          f'all parameter arrays have 539 finite entries **{cell(freeze.get("all_parameter_lengths_539","unavailable"))}**; '
          f'input identity matches **{cell(freeze.get("input_identity_matches","unavailable"))}**. '
          f'Start-policy ability **{num(freeze.get("theta0"))}**, posterior standard deviation **{num(freeze.get("theta0_sd"))}**. '
          f'File: `{cell(freeze.get("file"))}`. '+(f'Reason: {cell(freeze["reason"])}.' if freeze.get('reason') else ''), '',
          'The frozen forecasts target future draws and retain both posterior-integrated and ability-mean probabilities. '
          'The payload does not invent numeric H1–H4 training-effect forecasts; those would require a separate pretraining registration if training were ever reauthorized. '
          'Input pins are read from `input_pins_e20.json` in the results directory; publish a byte-identical canonical `expt_v1/input_pins_e20.json` or explicitly link the actual location.', '']
    missing=audit.get('missing_smooth_cells', audit.get('missing_cells'))
    L += [f'Missing strict cells: **{integer(audit.get("strict_missing_cells"))}**; missing smooth cells: **{len(missing) if isinstance(missing,list) else integer(audit.get("smooth_missing_cells"))}** '
          '(full list in `input_audit.json`; all panel statuses in `panel_train_cells.csv`). '
          f'Scorer-versus-adapter strict disagreements: **{cell(audit.get("scorer_adapter_strict_disagreements"))}**; '
          'the pinned scorer remains authoritative. Strict G0 uses its full strict cohort independently of descriptive partial-reward missingness. No validation/test outcomes or new generations are used in this analysis.']
    if isinstance(missing,list) and missing:
        L += ['', 'First missing-cell receipts:']+[f'- `{cell(r.get("task_id"))}` sample {cell(r.get("sample_idx"))}: '
               f'strict {cell(r.get("strict_status", "measured"))}; smooth {cell(r.get("status", r.get("partial_status")))}: {cell(r.get("note", r.get("partial_note", "")))}.' for r in missing[:5]]
    if E.problems:
        L += ['', '**Missing or invalid evidence:**']+[f'- {cell(x)}' for x in E.problems]
    if selected and not numerical_ok(finals.get(selected)):
        L += ['', '**Final selected fit is not numerically verified; a passing held-out G0 alone does not complete parameter freezing.**']
    L += ['', '**Copy-ready message:** '+('I evaluated the saved calibration outputs under the registered task-group checks. ' if assessable else 'The saved calibration evidence is incomplete or numerically unavailable. ') +
          f'The calibration gate is {verdict}, and the parameter freeze is {freeze["status"]}; the trainer remains failed and no training has resumed.', '',
          '**TLDR-end:** [rl4cv: E20 CPU calibration] '
          f'`{EXPERIMENT}`: G0 **{verdict}**, parameter freeze **{freeze["status"]}**; trainer **FAILED**, unchanged.', '',
          '**Snapshot:**', '```text', f'Primary model: {selected or "unavailable"}', f'G0: {verdict}',
          f'Tasks/groups observed: {integer(primary.get("tasks"))}/{integer(primary.get("groups"))}',
          f'Native freeze hash verification: {freeze.get("native_hash_verified", "unavailable")}',
          'Trainer: FAILED; no training authorized', '```', '']
    return '\n'.join(L), {'gate':verdict,'freeze':freeze['status'],'missing_or_invalid_files':len(E.problems)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--results-dir',type=Path,required=True)
    ap.add_argument('--out-md',type=Path,required=True)
    ap.add_argument('--repo',type=Path,default=Path.cwd())
    ap.add_argument('--branch',default='e20-irt-prompt-selection',help='intended GitHub publication branch; does not publish')
    args=ap.parse_args()
    if args.out_md.suffix.lower()!='.md':ap.error('--out-md must name a Markdown file')
    content,status=build_report(args)
    args.out_md.parent.mkdir(parents=True,exist_ok=True)
    args.out_md.write_text(content,encoding='utf-8')
    print(json.dumps({'report':str(args.out_md),**status}))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
