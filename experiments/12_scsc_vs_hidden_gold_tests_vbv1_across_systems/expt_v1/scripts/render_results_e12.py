"""Render the completed frozen analysis and inspected disagreements into the live experiment result record."""
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from extract_hidden_tests import PHASE
from rl4cv.forecast import verify_forecast


def num(x):return 'unavailable' if x is None else f'{x:.3f}'


def ci(x):return f"[{num(x['low'])}, {num(x['high'])}] ({x['n_defined']}/{x['n_requested']} defined)"


def main():
    for name in ('e12_phase_a_forecast','e12_phase_a_forecast_amendment_A1','e12_phase_a_forecast_amendment_A2'):
        assert verify_forecast(PHASE/'forecasts'/(name+'.json'))
    result=json.loads((PHASE/'results/analysis_e12.json').read_text())
    controls=json.loads((PHASE/'results/controls_e12.json').read_text());assert controls['all_controls_pass']
    inspections=json.loads((PHASE/'results/disagreements_e12.json').read_text())
    selected=result['disagreement_selection'];assert len(inspections['rows'])==len(selected)
    assert {(r['system'],r['task_id']) for r in inspections['rows']}=={(r['system'],r['task_id']) for r in selected}
    now=datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%m-%d-%Y %H:%M %Z')
    verdicts=result['verdicts'];p1=result['P1'];p23=result['P2_P3'];ga=result['G_A']
    verdict=('SCSC tracks system hidden-test success and discriminates beyond compilation' if verdicts['P1_holds'] and verdicts['P2_holds'] else
             'system agreement holds, but discrimination beyond compilation is not established' if verdicts['P1_holds'] else
             'the frozen system-ranking prediction fails')
    if not ga['passes']:verdict='LIMITED COVERAGE; '+verdict
    lines=['# Experiment 12 results — hidden gold-reference tests on VeriBench V1','',
      '**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/results.md>','',
      f'Experiment `12_scsc_vs_hidden_gold_tests_vbv1_across_systems` compared saved code from 11 primary systems using hidden gold-reference tests with zero experiment model calls: **{verdict}**.','',
      '**Status:** DONE',f'**Last updated:** {now}','',
      'SCSC means smooth conjunctive score for code verification. It combines internal consistency of tests (IC_tests), internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). A2 changes only mechanical symbol mapping; P1–P3 thresholds remain frozen.','',
      '## Frozen predictions','',
      '| Prediction | Estimate | 95% task-cluster bootstrap | Threshold and verdict |',
      '|---|---:|---|---|',
      f"| P1 system Spearman | {num(p1['spearman'])} | {ci(p1['task_bootstrap_95']['spearman'])} | ≥0.80: {'HOLDS' if verdicts['P1_holds'] else 'FAILS'} |",
      f"| P2 area under the receiver operating characteristic curve | {num(p23['auc'])} | {ci(p23['auc_bootstrap_95'])} | ≥0.60 and interval excludes 0.50: {'HOLDS' if verdicts['P2_holds'] else 'FAILS'} |",
      f"| P3 pooled within-system Spearman | {num(p23['spearman_within_system'])} | {ci(p23['spearman_bootstrap_95'])} | >0 and interval excludes 0: {'HOLDS' if verdicts['P3_holds'] else 'FAILS'} |",
      f"| G-A applicability | {num(ga['fraction'])} ({ga['n_applicable']}/{ga['n_compiling']}) | Deterministic census | ≥0.50: {verdicts['coverage_verdict']} |",'',
      f"P1 contains {p1['n_systems']} systems and resamples {p1['n_tasks']} tasks. P2/P3 contain {p23['n_cells']} compiling, applicable, score-measured cells ({p23['n_pass']} passing / {p23['n_fail']} failing), on {p23['n_observed_tasks']} observed tasks. Intervals use 10,000 paired task-cluster draws, seed 20261009; systems are retained together within each sampled task. Undefined draws are reported, not replaced. Thresholds are master-suggested and frozen in the original forecast; p-val=n/a. Single saved run per cell; repeated scoring variability is unavailable.",'',
      'P2 pools within-system normalized score midranks before computing the binary-outcome area. P3 correlates pooled within-system normalized score and graded-outcome midranks. Ranks are recomputed in every bootstrap draw.','',
      '## System-level agreement and absolute differences','',
      '| Statistic | Estimate | 95% task bootstrap | 95% system bootstrap sensitivity |','|---|---:|---|---|']
    for metric in ['pearson','spearman','kendall_tau_b','mean_score','mean_hidden','bias_score_minus_hidden','mean_absolute_difference']:
        lines.append(f"| {metric} | {num(p1[metric])} | {ci(p1['task_bootstrap_95'][metric])} | {ci(p1['system_bootstrap_95'][metric])} |")
    lines+=['','Positive bias means SCSC exceeds the hidden all-tests-pass rate. A1 computes the geometric mean of factor means over each system’s common measured factor cohort; hidden means use that cohort minus unavailable hidden outcomes and no-test tasks. These denominators are reported separately.','',
      '## Primary systems','',
      '| System | Factors measured / declared | IC_tests | IC_proofs | FSC | SCSC | Compile | Applicable / compiling | P1 hidden mean (n) | Full hidden bounds |',
      '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in result['systems']:
        if r['panel']!='primary':continue
        f=r['factor_means_common'];bounds=r['hidden_bounds']
        lines.append(f"| {r['system']} | {r['n_common_measured']}/{r['n_declared']} | {num(f['IC_tests'])} | {num(f['IC_proofs'])} | {num(f['FSC'])} | {num(r['system_score'])} | {r['n_compiling']}/{r['n_declared']} | {r['n_applicable']}/{r['n_compiling']} | {num(r['P1_hidden_mean'])} ({r['P1_n_hidden']}) | [{num(bounds[0])}, {num(bounds[1])}] |")
    lines+=['','Bounds count every unavailable hidden outcome as failing versus passing over all declared cells with extracted tests. Noncompiling code is a hidden failure; compiling but unevaluable code stays missing. Detailed no-test, unmeasured and applicable counts are in [analysis_e12.json](expt_v1/results/analysis_e12.json).','',
      '## Amendment sensitivities and subsets','',
      '| Analysis | Spearman or area | 95% task-cluster interval |','|---|---:|---|']
    a1=result['sensitivity_A1'];a2=result['sensitivity_A2']
    lines += [f"| A1 P1: model_error/incomplete set to zero; infrastructure missing excluded | {num(a1['spearman'])} | {ci(a1['task_bootstrap_95']['spearman'])} |",
              f"| A2 P2: mapping steps 1–2 only ({a2['n_cells']} cells) | {num(a2['auc'])} | {ci(a2['auc_bootstrap_95'])} |",
              f"| A2 P3: mapping steps 1–2 only | {num(a2['spearman_within_system'])} | {ci(a2['spearman_bootstrap_95'])} |"]
    for subset,d in result['subsets'].items():
        for name,value,iv in [('P1',d['P1']['spearman'],d['P1']['task_bootstrap_95']['spearman']),('P2',d['P2_P3']['auc'],d['P2_P3']['auc_bootstrap_95']),('P3',d['P2_P3']['spearman_within_system'],d['P2_P3']['spearman_bootstrap_95'])]:
            lines.append(f'| {subset} {name} (descriptive) | {num(value)} | {ci(iv)} |')
    lines+=['','Mapping steps: 1 normalized name; 2 unique compatible type; 3 candidate definitions agree on hidden argument tuples; 4 candidate example/theorem reference counts resolve disagreement or undecidability. Hidden expected values never decide a mapping.','',
      '| Mapping step | Symbols | Share of mapped symbols |','|---|---:|---:|']
    for step,count in result['mapping_steps']['counts'].items():lines.append(f"| {step} | {count} | {num(result['mapping_steps']['shares'][step])} |")
    lines+=['','## Secondary panels','',
      'These are descriptive saved-output panels. Experiment 08 uses validation only; its test split and sealed experiments 107/109 were not accessed.','',
      '| Panel / system | Declared | IC_tests | IC_proofs | Kernel rate (n) | Hidden all-pass (observed n) | Hidden among kernel-verified (observed n / verified) |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for r in result['systems']:
        if r['panel']=='primary':continue
        f=r['factor_means_available']
        lines.append(f"| {r['panel']} / {r['system']} | {r['n_declared']} | {num(f['IC_tests'])} | {num(f['IC_proofs'])} | {num(r['kernel_binary_mean'])} ({r['kernel_binary_n']}) | {num(r['hidden_all_pass_mean'])} ({r['n_hidden_observed']}) | {num(r['hidden_all_pass_given_kernel'])} ({r['n_kernel_verified_hidden_observed']}/{r['n_kernel_verified']}) |")
    lines+=['','Full bounds, missing counts and kernel-conditioned bounds for every secondary system are in the analysis artifact. The 5,400 unavailable factor cells remain explicit in the frozen manifest.','',
      '## Inspected disagreements','',
      '| Group | System / task | SCSC | Hidden result | Inspection |','|---|---|---:|---|---|']
    for r in inspections['rows']:
        lines.append(f"| {r['group']} | {r['system']} / {r['task_id']} | {num(r['scsc'])} | {r['hidden_all_pass']} | {r['reason'].replace('|','/')} |")
    lines+=['','## Validation, provenance and limitations','',
      'A1 reproduced all 11 published source aggregates under their own conventions and all 100 sampled compile statuses. Primary joins retain 9,678 hash-bound cells, 176 flagged unique paths, and two missing files. The extraction contains 10,534 tests on 882/896 gold tasks; 14 tasks have no extractable tests.','',
      f"Final controls: C1 {controls['C1']['n_pass']}/{controls['C1']['n_tests']} tests; C2 {controls['C2']['n_recovered']}/{controls['C2']['n_C1_passing_tasks']} recovered tasks; C3 {controls['C3']['n_killed']}/{controls['C3']['n_compiling_mutants']} compiling mutants detected; C4 {controls['C4']['n_rejected']}/{controls['C4']['n_pairs']} wrong-task pairs rejected. Thresholds remain 98%, 95%, 60%, 95% respectively. These are deterministic checks on the fixed 50-task sample, p-val=n/a.",'',
      'Historical failures and implementation corrections remain in [the checkpoint](expt_v1/CKPT_e12.md), with round-1/2 and partial round-3 receipts. A1 resolved aggregation conventions; A2 resolved identical-type alternatives before the protocol lock or any real-candidate hidden outcome. Candidate and gold source files and factors were never edited. All three forecasts remain frozen.','',
      'The outcome is finite-test success, not a proof of full program correctness or a human acceptance rating. Missing applicability is bounded rather than silently scored zero. Core and IndustrySet results, missing-factor sensitivity and unambiguous-mapping sensitivity are descriptive and do not replace the frozen verdicts. Next versions cover hidden proofs and the agent-spec v8 panel.','',
      '**TLDR-end:** [rl4cv: 12_scsc_vs_hidden_gold_tests_vbv1_across_systems] Hidden gold-test agreement is fully measured under the frozen protocol and amendments; '+verdict+'.','']
    (PHASE.parent/'results.md').write_text('\n'.join(lines))


if __name__=='__main__':main()
