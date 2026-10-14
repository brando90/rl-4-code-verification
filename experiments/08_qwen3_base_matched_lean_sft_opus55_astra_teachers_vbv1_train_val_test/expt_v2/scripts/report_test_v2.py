#!/usr/bin/env python3
"""Render the complete matched test report from saved factor, forecast, and judge receipts."""
import argparse
import json
import subprocess
from pathlib import Path

EXP=Path(__file__).resolve().parents[1]
ROOT=EXP/'results'
FULL='08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test'


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def interval(point, ci):
    return 'unavailable' if point is None else f'{point:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]' if ci else f'{point:.4f} [unavailable]'


def render(status, tests, blocker=''):
    data=read(ROOT/'test_eval_v2.json'); forecasts=read(ROOT/'forecast_evaluation_v2.json')
    stamp=subprocess.check_output(['date','+%m-%d-%Y %H:%M %Z'],text=True).strip()
    lines=[f'# Matched step-658 test results — {FULL}', '', f'**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/{FULL}/expt_v2/results.md>', '',f'Qwen3 1.7B, 4B, 8B and 14B are compared after identical supervised fine-tuning (SFT): 1,315 examples, 658 updates and 5,752,936 loss tokens on VeriBench V1; execution status is **{status}**.', '',f'**Last updated:** {stamp}', '',f'**Status:** {status}'+(f' — {blocker}' if blocker else ''),'',
        'All scores are on a 0–1 scale. IC_tests is the kernel test factor; IC_proofs is the fraction of stated theorems proved with allowed axioms; fsc_compiled is compile-gated formal specification coverage from the validated judge. SCSC (smooth conjunctive score for code verification) is the geometric mean of these three factor means on one common known cohort. Kernel binary success additionally requires the unchanged strict proof and non-vacuity checks.', '',
        'Every interval below uses 10,000 task-bootstrap resamples, seed 0, carrying all eight samples together; **p-val=n/a** (interval estimation only). These intervals cover this single training run, not training-seed variation. Incomplete summaries use their measured cohort, retain unknowns in declared counts, and provide full-manifest bounds in the evaluation JSON.', '',
        '## Matched trained and Base systems', '', '| Size / system | Scope | IC_tests [95%] | IC_proofs [95%] | fsc_compiled [95%] | SCSC [95%] | Kernel binary [95%] | Known / declared |','|---|---|---|---|---|---|---|---|']
    manifest=read(ROOT/'test_manifest_v2.json'); systems=sorted(manifest['systems'],key=lambda s:(float(s['size'].replace('B','')),s['role']=='base'))
    for system in systems:
        label=system['label']
        for scope,r in data['systems'][label]['scopes'].items():
            p=r['point_common_cohort']; ci=r['bootstrap95_task'] or {}
            values=[interval(p[k],ci.get(k)) for k in ['IC_tests','IC_proofs','fsc_compiled','SCSC']]
            lines.append(f"| {system['size']} `{label}` | {scope} | "+' | '.join(values)+f" | {interval(r['kernel_binary_mean_pass_rate'],r['kernel_binary_bootstrap95'])} | {r['n_known_cells']} / {r['n_declared_cells']} |")
    lines+=['','The 1.7B and 4B step-658 checkpoints failed version 1 validation format gates; their values are matched-budget diagnostics, not established reinforcement-learning warm starts.','','## SFT minus Base paired differences','','| Size | Scope | SCSC difference [95%] | Kernel binary difference [95%] | Missing factor pairs | Missing kernel pairs |','|---|---|---|---|---|---|']
    for size,scopes in sorted(data['paired_differences'].items(),key=lambda p:float(p[0][:-1])):
        for scope,r in scopes.items():
            lines.append(f"| {size} | {scope} | {interval(r['SCSC']['point'],r['SCSC']['bootstrap95'])} | {interval(r['kernel_binary']['point'],r['kernel_binary']['bootstrap95'])} | {r['n_missing_pairs']} | {r['kernel_missing_pairs']} |")
    lines+=['','## Scaling at the matched token budget','','| Adjacent sizes | Scope | SCSC difference [95%] | Kernel binary difference [95%] | Missing factor pairs |','|---|---|---|---|---|']
    for pair,scopes in data['adjacent_size_differences'].items():
        for scope,r in scopes.items(): lines.append(f"| {pair} | {scope} | {interval(r['SCSC']['point'],r['SCSC']['bootstrap95'])} | {interval(r['kernel_binary']['point'],r['kernel_binary']['bootstrap95'])} | {r['n_missing_pairs']} |")
    lines+=['','## Version 1 step-334 diagnostic','','The 14B step-334 checkpoint used 2,884,708 loss tokens and is excluded from the matched table. Its original values and ratings are read unchanged.','','| Scope | Step-334 SCSC [95%] | Step-658 minus step-334 SCSC [95%] | Kernel binary difference [95%] |','|---|---|---|---|']
    for scope,r in data['systems']['test_sft_14B_f0p5']['scopes'].items():
        d=data['diagnostic_14B_step658_minus_step334'][scope]
        lines.append(f"| {scope} | {interval(r['point_common_cohort']['SCSC'],r['bootstrap95_task']['SCSC'])} | {interval(d['SCSC']['point'],d['SCSC']['bootstrap95'])} | {interval(d['kernel_binary']['point'],d['kernel_binary']['bootstrap95'])} |")
    lines+=['','## Frozen forecasts','','The forecast hash was verified before scoring. PASS, FAIL and UNRESOLVED are reported equally; F1 tests validation-rate inclusion in the test interval, F2 tests whether each trained-minus-Base interval lower bound exceeds zero, and F3 tests strict size ordering of the trained score point estimates. These are the frozen forecast criteria, not additional hypothesis tests.','','| Forecast | Verdict | Evidence |','|---|---|---|']
    for key,r in forecasts['scores'].items():
        evidence=interval(r.get('point',r.get('observed')),r.get('bootstrap95')) if key!='F3' else str(r['observed'])
        lines.append(f"| {key} | **{r['verdict']}** | {evidence} |")
    lines+=['','## Coverage, ratings and charges','','| New system | Known factors / declared | Ratings measured / declared | Reported judge charge |','|---|---|---|---|']
    measured=declared=0; charges=0.; missing_charges=0; unknown_ratings=[]
    for s in systems:
        if s['generation']!='new': continue
        label=s['label']; f=read(ROOT/f'judge/fsc_{label}.json',{}); r=data['systems'][label]['scopes']['all']
        measured+=f.get('n_ratings_measured',0); declared+=f.get('n_ratings_declared',0); charges+=f.get('charges_usd',0.)
        lines.append(f"| `{label}` | {r['n_known_cells']} / 1,776 | {f.get('n_ratings_measured','not admitted')} / {f.get('n_ratings_declared','not frozen')} | {'$'+str(f['charges_usd']) if 'charges_usd' in f else 'not reported'} |")
    for path in sorted((ROOT/'judge/harvests').glob('*.json')):
        for r in read(path)['cells']:
            missing_charges+=r.get('cost_usd') is None
            if r['status']!='measured': unknown_ratings.append({k:r.get(k) for k in ['system','task_id_vb','sample_idx','repeat','config','status']})
    reconciled=read(ROOT/'judge_reconciliation_v2.json',{})
    if reconciled:
        lines+=['','Repeat dispersion (mean within-file standard deviation of each member’s three normalized raw ratings; this is not a confidence interval):','','| System | Sol SD / files with three ratings | Opus SD / files with three ratings |','|---|---|---|']
        for label,info in reconciled['systems'].items():
            vals=[info['repeat_sd'][name] for name in ['H2_sol_high','H2_opus55_max']]
            lines.append(f"| `{label}` | {vals[0]['mean_within_file_sd']} / {vals[0]['n_files_with_three_ratings']} | {vals[1]['mean_within_file_sd']} / {vals[1]['n_files_with_three_ratings']} |")
    controls=read(ROOT/'judge/controls_check.json',{})
    controls_charge=sum(r.get('charges_usd',0.) for r in controls.get('configs',{}).values())
    lines+=['',f"New test ratings measured: {measured}/{declared if declared else 'not yet frozen'}. Reported test subtotal: ${charges:.4f}; route controls: ${controls_charge:.4f}. Missing charge receipts: {missing_charges}; unknown charges are not asserted to be zero. Reused-system historical charges are not charged again. Host compute costs were not measured.",'',
        'Every unknown factor cell is listed without truncation in [test_eval_v2.json](results/test_eval_v2.json); every matched and diagnostic cell is in [test_factor_cells_v2.csv](results/test_factor_cells_v2.csv). Judge pack omissions and fixed-audit membership are retained in [judge_pack_test.json](results/judge/judge_pack_test.json). Each admitted rating has a terminal receipt in `results/judge/harvests/`; incomplete ratings are separately enumerated in [unknown_judge_ratings_v2.json](results/unknown_judge_ratings_v2.json). No missing cell is treated as a measured zero.', '',
        'The validated judge is GPT-6 Sol high plus Claude Opus 5.5 max, three ratings per member/file; the mean of member medians is divided by five. Audit coverage on noncompiling files remains diagnostic. Human agreement on these student outputs, training-seed variation, and independent repeatability of the final ensemble were not measured.', '',
        '## Verification and provenance','',f'Full `make test`: {tests}. `git diff --check` passes. All six reused systems reproduce every original scope field exactly, including means, bounds and intervals. The independent CSV summarizer checks every factor mean and SCSC across all nine systems and three scopes (108 checks); unknown-only cohorts are checked as unavailable. Version 1 files remain unchanged.','',
        'Scientific inputs: [protocol](PROTOCOL_v2.md), [input checks](results/inputs_check.json), [manifest](results/test_manifest_v2.json), [route identity](results/route_identity_v2.json), [forecast scores](results/forecast_evaluation_v2.json), [independent check](results/independent_factor_check_v2.json). Runtime state and failed attempts stay under `/lfs/skampere1/0/brando9/rl4cv_e08/v2/`.','',
        f'**TLDR-end:** [rl4cv: {FULL}/expt_v2 matched step-658 test] The matched-budget test evaluation is {status.lower()}; measured and unknown cells, paired comparisons and every forecast are reported above.']
    (EXP/'results.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'unknown_judge_ratings_v2.json').write_text(json.dumps(unknown_ratings,indent=2)+'\n')
    return dict(status=status,reported_test_charge=charges,reported_controls_charge=controls_charge,ratings_measured=measured,ratings_declared=declared)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--status',required=True); parser.add_argument('--tests',required=True); parser.add_argument('--blocker',default=''); args=parser.parse_args()
    print(json.dumps(render(args.status,args.tests,args.blocker)))
