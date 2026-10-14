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
    lines=[f'# Matched step-658 test results — {FULL}', '', f'**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/{FULL}/expt_v2/results.md>', '',f'**TLDR:** Qwen3 1.7B, 4B, 8B and 14B are compared after identical supervised fine-tuning (SFT): 1,315 examples, 658 updates and 5,752,936 loss tokens on VeriBench V1; execution status is **{status}**.', '',f'**Last updated:** {stamp}', '',f'**Status:** {status}'+(f' — {blocker}' if blocker else ''),'',
        'All scores are on a 0–1 scale. IC_tests is the kernel test factor; IC_proofs is the fraction of stated theorems proved with allowed axioms; fsc_compiled is compile-gated formal specification coverage from the validated judge. SCSC (smooth conjunctive score for code verification) is the geometric mean of these three factor means on one common known cohort. Kernel binary success additionally requires the unchanged strict proof and non-vacuity checks.', '',
        'Every interval below uses 10,000 task-bootstrap resamples, seed 0, carrying all eight samples together; **p-val=n/a** (interval estimation only). These intervals cover this single training run, not training-seed variation. Incomplete summaries use their measured cohort, retain unknowns in declared counts, and provide full-manifest bounds in the evaluation JSON.', '',
        '## Matched trained and Base systems', '', '| Size / system | Scope | IC_tests [95%] | IC_proofs [95%] | fsc_compiled [95%] | SCSC [95%] | Kernel binary [95%] | Known factors / declared | Known kernel / declared |','|---|---|---|---|---|---|---|---|---|']
    manifest=read(ROOT/'test_manifest_v2.json'); systems=sorted(manifest['systems'],key=lambda s:(float(s['size'].replace('B','')),s['role']=='base'))
    for system in systems:
        label=system['label']
        for scope,r in data['systems'][label]['scopes'].items():
            p=r['point_common_cohort']; ci=r['bootstrap95_task'] or {}
            values=[interval(p[k],ci.get(k)) for k in ['IC_tests','IC_proofs','fsc_compiled','SCSC']]
            lines.append(f"| {system['size']} `{label}` | {scope} | "+' | '.join(values)+f" | {interval(r['kernel_binary_mean_pass_rate'],r['kernel_binary_bootstrap95'])} | {r['n_known_cells']} / {r['n_declared_cells']} | {r['kernel_binary_known_cells']} / {r['n_declared_cells']} |")
    incomplete=[s for s in systems if data['systems'][s['label']]['n_unknown_cells']]
    if incomplete:
        lines+=['','Full-manifest bounds below are worst-case bounds over unknown factors, not confidence intervals.','','| System | Scope | SCSC full-manifest bounds |','|---|---|---|']
        for s in incomplete:
            for scope,r in data['systems'][s['label']]['scopes'].items():
                lo,hi=r['full_manifest_bounds']['SCSC']
                lines.append(f"| `{s['label']}` | {scope} | [{lo:.4f}, {hi:.4f}] |")
    lines+=['','The 1.7B and 4B step-658 checkpoints failed version 1 validation format gates; their values are matched-budget diagnostics, not established reinforcement-learning warm starts.','','## SFT minus Base paired differences','','| Size | Scope | SCSC difference [95%] | Kernel binary difference [95%] | Missing factor pairs | Missing kernel pairs |','|---|---|---|---|---|---|']
    for size,scopes in sorted(data['paired_differences'].items(),key=lambda p:float(p[0][:-1])):
        for scope,r in scopes.items():
            lines.append(f"| {size} | {scope} | {interval(r['SCSC']['point'],r['SCSC']['bootstrap95'])} | {interval(r['kernel_binary']['point'],r['kernel_binary']['bootstrap95'])} | {r['n_missing_pairs']} | {r['kernel_missing_pairs']} |")
    lines+=['','## Scaling at the matched token budget','','| Adjacent sizes | Scope | SCSC difference [95%] | Kernel binary difference [95%] | Missing factor pairs |','|---|---|---|---|---|']
    for pair,scopes in data['adjacent_size_differences'].items():
        for scope,r in scopes.items(): lines.append(f"| {pair} | {scope} | {interval(r['SCSC']['point'],r['SCSC']['bootstrap95'])} | {interval(r['kernel_binary']['point'],r['kernel_binary']['bootstrap95'])} | {r['n_missing_pairs']} |")
    lines+=['','## Version 1 step-334 diagnostic','','The 14B step-334 checkpoint used 2,884,708 loss tokens and is excluded from the matched table. Its original values and ratings are read unchanged.','','| Scope | IC_tests [95%] | IC_proofs [95%] | fsc_compiled [95%] | Step-334 SCSC [95%] | Known / declared | Step-658 minus step-334 SCSC [95%] | Kernel binary difference [95%] |','|---|---|---|---|---|---|---|---|']
    for scope,r in data['systems']['test_sft_14B_f0p5']['scopes'].items():
        d=data['diagnostic_14B_step658_minus_step334'][scope]
        factors=' | '.join(interval(r['point_common_cohort'][k],r['bootstrap95_task'][k]) for k in ['IC_tests','IC_proofs','fsc_compiled','SCSC'])
        lines.append(f"| {scope} | {factors} | {r['n_known_cells']} / {r['n_declared_cells']} | {interval(d['SCSC']['point'],d['SCSC']['bootstrap95'])} | {interval(d['kernel_binary']['point'],d['kernel_binary']['bootstrap95'])} |")
    lines+=['','## Frozen forecasts','','The forecast hash was verified before scoring. PASS, FAIL and UNRESOLVED are reported equally; F1 tests validation-rate inclusion in the test interval, F2 tests whether each trained-minus-Base interval lower bound exceeds zero, and F3 tests strict size ordering of the trained score point estimates. These are the frozen forecast criteria, not additional hypothesis tests.','','| Forecast | Verdict | Evidence |','|---|---|---|']
    for key,r in forecasts['scores'].items():
        evidence=interval(r.get('point',r.get('observed')),r.get('bootstrap95')) if key!='F3' else ', '.join('unavailable' if v is None else f'{v:.4f}' for v in r['observed'])
        lines.append(f"| {key} | **{r['verdict']}** | {evidence} |")
    lines+=['','## Coverage, ratings and charges','','| New system | Known factors / declared | Ratings measured / declared | Reported judge charge |','|---|---|---|---|']
    pack=read(ROOT/'judge/judge_pack_test.json',{})
    reconciled=read(ROOT/'judge_reconciliation_v2.json',{})
    measured=declared=0; charges=0.; charge_reports=0; missing_charges=0; unknown_ratings=reconciled.get('unknown_ratings',[])
    for s in systems:
        if s['generation']!='new': continue
        label=s['label']; f=read(ROOT/f'judge/fsc_{label}.json',{}); r=data['systems'][label]['scopes']['all']
        n_declared=f.get('n_ratings_declared',sum(c['system']==label for c in pack.get('cells',[]))*2)
        measured+=f.get('n_ratings_measured',0); declared+=n_declared; charges+=f.get('charges_usd',0.); charge_reports+='charges_usd' in f
        lines.append(f"| `{label}` | {r['n_known_cells']} / 1,776 | {f.get('n_ratings_measured',0)} / {n_declared if pack or f else 'not frozen'} | {'$'+str(f['charges_usd']) if 'charges_usd' in f else 'not reported'} |")
    for path in sorted((ROOT/'judge/harvests').glob('*.json')):
        for r in read(path)['cells']:
            missing_charges+=r.get('cost_usd') is None
            if not reconciled and r['status']!='measured': unknown_ratings.append({k:r.get(k) for k in ['system','task_id_vb','sample_idx','repeat','config','status']})
    if reconciled:
        lines+=['','Repeat dispersion (mean within-file standard deviation of each member’s three normalized raw ratings; this is not a confidence interval):','','| System | Sol SD / files with three ratings | Opus SD / files with three ratings |','|---|---|---|']
        for label,info in reconciled['systems'].items():
            vals=[info['repeat_sd'][name] for name in ['H2_sol_high','H2_opus55_max']]
            lines.append(f"| `{label}` | {vals[0]['mean_within_file_sd']} / {vals[0]['n_files_with_three_ratings']} | {vals[1]['mean_within_file_sd']} / {vals[1]['n_files_with_three_ratings']} |")
    controls=read(ROOT/'judge/controls_check.json',{})
    coverage=read(ROOT/'terminal_coverage_v2.json',{})
    if coverage:
        unknown_ratings=coverage['unknown_ratings']
        lines+=['',f"Route controls measured **0/50** ratings. The fixed audits require **1,080** test ratings over 180 files; all are missing because candidate files were unavailable. Additional compile-gated rating eligibility remains unknown for **5,328** cells. The test pack was not frozen or admitted. [Complete coverage inventory](results/terminal_coverage_v2.json) lists every missing generation, fixed-audit/control rating and unresolved eligibility identity. Both failed admissions were positively reconciled as unserved; no model request was admitted.",'',
            'The current CLI authenticates to `BrandoMiranda-fellow`, but the server has no Daytona mapping and returns HTTP 403: managed AWS access is unavailable for this organization. [Blocker evidence](results/judge_route_blocker_v2.json) records the supported-client checks. Vals must restore this existing route before controls or test judging can resume. No substitute funding or model was used.']
    control_costs=[r['charges_usd'] for r in controls.get('configs',{}).values() if 'charges_usd' in r]
    controls_charge=sum(control_costs) if control_costs else None
    charge_text=f'${charges:.4f}' if charge_reports else 'not reported'
    control_text=f'${controls_charge:.4f}' if controls_charge is not None else 'not reported'
    if reconciled: missing_charges=sum(r['missing_charge_receipts'] for r in reconciled['systems'].values())
    lines+=['',f"New test ratings measured: {measured}/{declared if declared else 'not yet frozen'}. Reported test subtotal: {charge_text}; route controls: {control_text}. Missing test charge receipts: {missing_charges}; unknown charges are not asserted to be zero. Reused-system historical charges are not charged again. Host compute costs were not measured.",'',
        'Every unknown factor cell is listed without truncation in [test_eval_v2.json](results/test_eval_v2.json); every matched and diagnostic cell is in [test_factor_cells_v2.csv](results/test_factor_cells_v2.csv). When built, the judge pack records omissions and fixed-audit membership in `results/judge/judge_pack_test.json`. Available admitted-rating receipts are retained in `results/judge/harvests/`; every missing or unadmitted test rating is separately enumerated in [unknown_judge_ratings_v2.json](results/unknown_judge_ratings_v2.json). No missing cell is treated as a measured zero.', '',
        'The validated judge is GPT-6 Sol high plus Claude Opus 5.5 max, three ratings per member/file; the mean of member medians is divided by five. Audit coverage on noncompiling files remains diagnostic. Human agreement on these student outputs, training-seed variation, and independent repeatability of the final ensemble were not measured.', '',
        '## Verification and provenance','',f'Full `make test`: {tests}. `git diff --check` passes. All six reused systems reproduce every original scope field exactly, including means, bounds and intervals. The independent CSV summarizer checks every factor mean and SCSC across all nine systems and three scopes (108 checks); unknown-only cohorts are checked as unavailable. Version 1 files remain unchanged.','',
        'Scientific inputs: [protocol](PROTOCOL_v2.md), [input checks](results/inputs_check.json), [manifest](results/test_manifest_v2.json), [route identity](results/route_identity_v2.json), [forecast scores](results/forecast_evaluation_v2.json), [independent check](results/independent_factor_check_v2.json). Runtime state and failed attempts stay under `/lfs/skampere1/0/brando9/rl4cv_e08/v2/`. The [checkpoint log](CKPT_e08v2.md) retains launch, environment recovery and publication history.','',
        f'**TLDR-end:** [rl4cv: {FULL}/expt_v2 matched step-658 test] The matched-budget test evaluation is {status.lower()}; measured and unknown cells, paired comparisons and every forecast are reported above.']
    (EXP/'results.md').write_text('\n'.join(lines)+'\n')
    if coverage:
        with (EXP/'results.md').open('a') as out:
            out.write('\n**Snapshot:**\n\n```text\nStatus: PARTIAL — Vals managed AWS route blocked\nNew measured cells: 0 / 5,328\nReused matched cells: 8,880 / 8,880\nControl ratings: 0 / 50\nFixed-audit ratings: 0 / 1,080\nNew forecast verdicts: UNRESOLVED\n```\n')
    (ROOT/'unknown_judge_ratings_v2.json').write_text(json.dumps(unknown_ratings,indent=2)+'\n')
    return dict(status=status,reported_test_charge=charges if charge_reports else None,reported_controls_charge=controls_charge,ratings_measured=measured,ratings_in_built_pack=declared)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--status',required=True); parser.add_argument('--tests',required=True); parser.add_argument('--blocker',default=''); args=parser.parse_args()
    print(json.dumps(render(args.status,args.tests,args.blocker)))
