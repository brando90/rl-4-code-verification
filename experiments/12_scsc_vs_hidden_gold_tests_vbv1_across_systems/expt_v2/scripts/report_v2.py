"""Render the completed, frozen-analysis receipt without recomputing or selecting outcomes."""
from collections import Counter
from datetime import datetime
import json
from zoneinfo import ZoneInfo
from support_v2 import PHASE


def number(value):
    return 'unavailable' if value is None else f'{value:.4f}'


def ci(value, limits):
    return f"{number(value)} [{number(limits['low'])}, {number(limits['high'])}]"


def verdict(value):
    return 'HOLDS' if value else 'DOES NOT HOLD'


def table(headers, rows):
    def line(row):
        return '| ' + ' | '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in row) + ' |'
    return '\n'.join([line(headers), line(['---'] * len(headers)), *(line(r) for r in rows)])


def render(a, cells, controls, complete):
    p = a['P1']; q = a['P2_P3']; v = a['verdicts']; g = a['G_A']
    observed = [r for r in cells if r['hidden_all_pass'] is not None]
    passing = sum(r['hidden_all_pass'] == 1 for r in cells)
    unknown = len(cells) - len(observed)
    no_tests = sum(r['status'] == 'no_tests' for r in cells)
    measured_unknown = unknown - no_tests
    status = Counter(r['status'] for r in cells)
    paragraphs = [
        '# 12_scsc_vs_hidden_gold_tests_vbv1_across_systems — version-2 completed analysis',
        '**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/RESULTS_analysis_v2.md>',
        f"**Updated:** {datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%m-%d-%Y %H:%M %Z')}",
        f"All 4,626 eligible groups and all 9,856 declared cells are accounted for. P1 {verdict(v['P1_holds'])}: "
        f"system Spearman {ci(p['spearman'], p['task_bootstrap_95']['spearman'])}; P2 {verdict(v['P2_holds'])}: "
        f"area under the receiver operating characteristic curve (AUC) {ci(q['auc'], q['auc_bootstrap_95'])}; "
        f"P3 {verdict(v['P3_holds'])}: within-system Spearman {ci(q['spearman_within_system'], q['spearman_bootstrap_95'])}. "
        f"Fully applicable coverage is {g['n']}/{g['denominator']} = {number(g['fraction'])}: {v['coverage_verdict']}.",
        'Smooth conjunctive score for code verification (SCSC) combines internal consistency of tests (IC_tests), '
        'internal consistency of proofs (IC_proofs), and formal specification coverage (FSC). '
        'These results measure agreement with hidden computational gold-reference tests on saved VeriBench V1 (VBV1) candidates; '
        'they do not establish human acceptance or complete semantic correctness. Zero new model calls, zero judge calls, zero graphics processing units, and $0 Vals spend.',
        '## Scope, denominators and missing outcomes',
        f"The fixed panel has 11 systems × 896 tasks = 9,856 cells, including {no_tests} cells on 14 tasks without extracted tests. "
        f"Exactly 4,626 compiling, joined, test-bearing cells were evaluated. There are {len(observed)} observed binary outcomes "
        f"({passing} passing) and {measured_unknown} missing test-bearing outcomes. No-test cells are excluded consistently from protocol statistics. "
        'The additional all-declared bounds below retain them as unknown, preserving the literal 9,856-cell denominator.',
        table(['Status', 'Cells'], sorted(status.items())),
        table(['Accounting', 'Passes / observed', 'Missing', 'All missing fail / all missing pass'], [
            ['Protocol: tasks with tests', f'{passing}/{len(observed)}', measured_unknown,
             f'{number(passing/(len(cells)-no_tests))} / {number((passing+measured_unknown)/(len(cells)-no_tests))}'],
            ['All declared cells', f'{passing}/{len(observed)}', unknown,
             f'{number(passing/len(cells))} / {number((passing+unknown)/len(cells))}']]),
        'A non-compiling test-bearing candidate is a failure. A compiling candidate with any unevaluable test has a missing binary all-pass outcome, '
        'even when every evaluable test passes. The graded rate uses evaluable tests only. Missing outcomes are never silently converted to successes.',
        '## Dynamic controls',
        table(['Control', 'Count', 'Rate', 'Frozen gate', 'Verdict'], [
            [label, f"{controls[key][num]}/{controls[key][den]}", number(controls[key]['fraction']),
             f"≥{number(controls[key]['threshold'])}" + (' and ≥50 mutants' if key == 'C3' else ''),
             'PASS' if controls[key]['passes'] else 'FAIL']
            for label,key,num,den in [('C1 gold self-tests','C1','n_pass','n_tests'),
                                     ('C2 renamed gold recovery','C2','n_recovered','n_C1_passing_tasks'),
                                     ('C3 compiling mutant detection','C3','n_killed','n_compiling_mutants'),
                                     ('C4 wrong-task rejection or failure','C4','n_rejected','n_pairs')]]),
        'All 50 prescribed tasks completed before primary evaluation. [Per-task controls](results/controls_v2.json). '
        'The frozen adapter, forecasts, references and version-1 files remain unchanged.',
        '## Frozen hypotheses and coverage gate',
        table(['Hypothesis', 'Estimate [95% task-cluster interval]', 'Denominator', 'Frozen threshold', 'Verdict'], [
            ['P1: system ranking', ci(p['spearman'], p['task_bootstrap_95']['spearman']),
             f"{p['n_systems']} systems; {p['n_tasks']} task clusters", 'Spearman ≥0.80', verdict(v['P1_holds'])],
            ['P2: discriminate passing candidates', ci(q['auc'], q['auc_bootstrap_95']),
             f"{q['n_cells']} cells; {q['n_pass']} pass / {q['n_fail']} fail; {q['n_observed_tasks']} observed tasks", 'AUC ≥0.60 and lower 95% bound >0.50', verdict(v['P2_holds'])],
            ['P3: within-system graded ranking', ci(q['spearman_within_system'], q['spearman_bootstrap_95']),
             f"same {q['n_cells']} cells", 'Spearman >0 and lower 95% bound >0', verdict(v['P3_holds'])],
            ['G-A: fully applicable coverage', ci(g['fraction'], g['task_bootstrap_95']),
             f"{g['n']}/{g['denominator']}", '≥0.50', v['coverage_verdict']],
            ['At least one evaluable test', ci(a['applicability_any_evaluable']['fraction'], a['applicability_any_evaluable']['task_bootstrap_95']),
             f"{a['applicability_any_evaluable']['n']}/{a['applicability_any_evaluable']['denominator']}", 'Descriptive', 'No gate']]),
        'Thresholds come from the original frozen experiment forecast, carried into [version-2 protocol §5](PROTOCOL.md). '
        'They were agent-suggested before evaluation. Version 2 applies the unchanged coverage threshold to the stricter fully applicable cohort. '
        'All intervals use 10,000 paired task-cluster bootstrap draws, seed 20261009, retaining all systems in each sampled task. '
        'The P2/P3 resampling frame is all 896 tasks; within-system normalized midranks are recomputed in every draw. p-val=n/a: no p-value gate was specified.',
        '## System-level agreement and calibration',
        'P1 uses the common three-factor score cohort within each system, with the hidden mean over its non-missing test-bearing subset. '
        'This preserves the version-1 definition; it is not an identical cell denominator for score and hidden outcome. '
        'The per-system factor and hidden denominators are shown below. Positive bias means SCSC is higher than hidden all-pass rate.',
        table(['Statistic', 'Estimate [95% task interval]', '95% system-bootstrap sensitivity'], [
            [name, ci(p[key], p['task_bootstrap_95'][key]),
             f"[{number(p['system_bootstrap_95'][key]['low'])}, {number(p['system_bootstrap_95'][key]['high'])}]"]
            for name, key in [('Spearman ρ', 'spearman'), ('Pearson r', 'pearson'), ('Kendall τ-b', 'kendall_tau_b'),
                              ('Mean SCSC', 'mean_score'), ('Mean hidden outcome', 'mean_hidden'),
                              ('Bias: SCSC − hidden', 'bias_score_minus_hidden'), ('Mean absolute difference', 'mean_absolute_difference')]]),
        table(['Descriptive score/outcome', 'Systems', 'Spearman', 'Pearson', 'Kendall', 'Mean score', 'Mean hidden', 'Bias', 'Mean absolute difference'], [
            [label, obj['n_systems'], *(number(obj[k]) for k in ('spearman','pearson','kendall_tau_b','mean_score','mean_hidden','bias_score_minus_hidden','mean_absolute_difference'))]
            for label,obj in [('SCSC / graded hidden', p['graded_outcome']), *p['factor_correlations'].items()]]),
        'The graded and individual-factor rows are descriptive point estimates; their intervals were not specified. '
        'A single saved scoring run exists per cell. Raw-repeat standard deviation and aggregate test–retest variability are unavailable; '
        'task resampling measures task-sample uncertainty, not generation, scorer-repeat, reference or adapter uncertainty.',
        '## Per-system factors and outcomes',
        table(['System', 'Declared', 'Factor cohort', 'IC_tests', 'IC_proofs', 'FSC', 'System SCSC', 'Compiles', 'Compile rate', 'P1 hidden n', 'P1 hidden mean'], [
            [r['system'], r['n_declared'], r['n_common_measured'], *(number(r['factor_means_common'][f]) for f in ('IC_tests','IC_proofs','FSC')),
             number(r['system_score']), r['n_compiling'], number(r['compile_rate']), r['P1_n_hidden'], number(r['P1_hidden_mean'])] for r in a['systems']]),
        table(['System', 'Compiling with tests', 'Fully applicable', 'Any evaluable', 'Observed hidden', 'Pass / observed', 'Graded mean', 'Protocol bounds', 'All-declared bounds'], [
            [r['system'], r['n_compiling_with_tests'], f"{r['n_fully_applicable']} ({number(r['fully_applicable_share'])})",
             f"{r['n_any_evaluable']} ({number(r['any_evaluable_share'])})", r['n_hidden_observed'],
             f"{r['hidden_all_pass_count']}/{r['n_hidden_observed']} ({number(r['hidden_all_pass_mean'])})", number(r['hidden_pass_rate_mean']),
             ' / '.join(map(number,r['hidden_bounds'])), ' / '.join(map(number,r['hidden_bounds_all_declared']))] for r in a['systems']]),
        'Each system has 896 declared cells and 14 no-test cells. Protocol bounds use 882 tasks; all-declared bounds use 896. '
        'The graded mean in this table is over binary-observed rows, preserving the version-1 table definition. '
        '[Machine-readable system table](results/systems_v2.json) also retains available-factor means and kernel-verification descriptives.',
        '## Prespecified sensitivities',
        table(['Cohort', 'Cells', 'Pass / fail', 'P2 AUC [95% interval]', 'P3 Spearman [95% interval]'], [
            [label, r['n_cells'], f"{r['n_pass']} / {r['n_fail']}", ci(r['auc'],r['auc_bootstrap_95']), ci(r['spearman_within_system'],r['spearman_bootstrap_95'])]
            for label,r in [('Primary fully applicable',q),('S-V2a: at least one evaluable',a['S_V2a']),
                            ('S-V2b: fully applicable, static steps 1–2b',a['S_V2b']),
                            ('S-V2d: common fully applicable, v1',a['S_V2d']['v1']['P2_P3']),
                            ('S-V2d: common fully applicable, v2',a['S_V2d']['v2']['P2_P3'])]]),
        table(['P1 sensitivity', 'Systems', 'Spearman [95% interval]', 'Pearson', 'Kendall', 'Bias', 'Mean absolute difference'], [
            [label,r['n_systems'],ci(r['spearman'],r['task_bootstrap_95']['spearman']),*(number(r[k]) for k in ('pearson','kendall_tau_b','bias_score_minus_hidden','mean_absolute_difference'))]
            for label,r in [('S-V2c: model_error/incomplete as failure',a['S_V2c']),('S-V2d common cohort, v1',a['S_V2d']['v1']['P1']),('S-V2d common cohort, v2',a['S_V2d']['v2']['P1'])]]),
        f"S-V2d contains {a['S_V2d']['n_common_cells']} cells fully applicable in both versions. "
        'The same task resampling seed is used for the two versions. These are sensitivity estimates, never replacements for the primary verdicts.',
        '## Core and industry subsets',
        table(['Subset', 'Declared tasks', 'P1 Spearman [95% interval]', 'Fully applicable score cells', 'Pass / fail', 'P2 AUC [95% interval]', 'P3 Spearman [95% interval]'], [
            [name, r['P1']['n_tasks'],ci(r['P1']['spearman'],r['P1']['task_bootstrap_95']['spearman']),r['P2_P3']['n_cells'],
             f"{r['P2_P3']['n_pass']} / {r['P2_P3']['n_fail']}",ci(r['P2_P3']['auc'],r['P2_P3']['auc_bootstrap_95']),
             ci(r['P2_P3']['spearman_within_system'],r['P2_P3']['spearman_bootstrap_95'])] for name,r in a['subsets'].items()]),
        'Per-system tables for each subset, individual-factor P2/P3 descriptives and every interval’s defined-draw count are retained in '
        '[the complete analysis receipt](results/analysis_e12_v2.json). Optional secondary panels were not evaluated in this primary-only dispatch.',
        '## Every frozen forecast',
        table(['Forecast', 'Point forecast', 'Plausible range', 'Measured', 'Inside range?', 'Directional prediction'], [
            [key,number(r['forecast'].get('point')), '–'.join(map(number,r['forecast']['plausible_range'])),number(r['measured']),
             verdict(r['within_plausible_range']),verdict(r['direction_holds']) if 'direction_holds' in r else r['forecast'].get('direction_vs_v1','No separate directional rule')]
            for key,r in a['forecast_checks'].items()]),
        f"Failing share: {a['failing_share']['n']}/{a['failing_share']['denominator']} = "
        f"{ci(a['failing_share']['fraction'],a['failing_share']['task_bootstrap_95'])}; version-1 comparator 200/3,199. "
        'A forecast plausible range is a frozen prediction range, not a confidence interval. P1 “about unchanged” has no separate numerical tolerance; '
        'its point, range and frozen ≥0.80 hypothesis are reported without inventing another gate.',
        f"Amended static-census consistency: {verdict(a['census_consistency']['holds'])}; "
        f"observed {a['census_consistency']['observed']}, expected {a['census_consistency']['expected']}. "
        'The V2-A1 amendment supersedes the original forecast’s pre-amendment mapping counts. '
        'Both frozen forecast files and hashes are preserved.',
        '## Mapping and paired version comparison',
        table(['Mapping step', 'Mapped symbols', 'Share of mapped symbols'], [
            [step,count,number(count/sum(a['mapping_steps'].values()))] for step,count in sorted(a['mapping_steps'].items())]),
        'Mapping counts describe symbols, so multiple symbols can belong to one cell. Static coverage is a mapping property; '
        'fully applicable coverage additionally requires every test to elaborate and yield a Boolean outcome.',
    ]
    pairs = a['S_V2d']['changed_entry_points']
    transitions = Counter((str(r['v1_hidden_all_pass']),str(r['v2_hidden_all_pass'])) for r in pairs)
    paragraphs += [
        table(['v1 all-pass', 'v2 all-pass', 'Changed-entry-point cells'], [(x,y,n) for (x,y),n in sorted(transitions.items())]),
        f"All {len(pairs)} post-amendment changed-entry-point rows are retained in [the paired table](results/paired_changed_entry_points_v2.json). "
        'None means missing. Version 1’s binary field treated partial applicability differently, so an outcome transition alone is not proof of a semantic correction.',
        table(['System', 'Originally inspected task', 'v1 category', 'v1 all-pass', 'v2 all-pass', 'v2 tests pass/evaluable', 'v2 fully applicable'], [
            [r['system'],r['task_id'],r['v1_category'],r['v1_hidden_all_pass'],r['v2_hidden_all_pass'],f"{r['v2_n_pass']}/{r['v2_n_evaluable']}",r['v2_fully_applicable']]
            for r in a['S_V2d']['inspected_v1_rows']]),
        f"Frozen original-20-row prediction: {verdict(a['inspected_prediction']['holds'])}. Details: `{json.dumps(a['inspected_prediction'],sort_keys=True)}`. "
        '[Original 20 rows and mappings](results/paired_inspected_v1_rows_v2.json).',
        '## Twenty newly selected disagreements',
        'Selection is the frozen version-1 rule applied to version 2’s fully applicable, compiling, score-measured cohort: '
        '10 highest-SCSC failures and 10 lowest-SCSC successes, with system/task tie breakers. '
        'The selected rows and per-test evidence are inspected in [the disagreement report](DISAGREEMENTS_v2.md).',
        table(['Group', 'System', 'Task', 'SCSC', 'Tests pass / total', 'Mapping steps'], [
            [r['group'],r['system'],r['task_id'],number(r['scsc']),f"{r['n_pass']}/{r['n_tests']}",', '.join(map(str,r['mapping_steps']))]
            for r in a['disagreement_selection']]),
        '## Reproducibility and limitations',
        f"Outcome ledger SHA-256: `{complete['outcomes_sha256']}`. [All 9,856 per-cell records](results/cells_v2.jsonl); "
        '[analysis JSON](results/analysis_e12_v2.json); [completion receipt](results/evaluation_complete_v2.json); '
        '[frozen runtime manifest](results/evaluation_launch_v2.json); [preflight](results/preflight_v2.json).',
        'The run used Lean v4.22.0 with pinned Mathlib on skampere1, two low-priority CPU workers, the inherited 600-second Lean timeout, '
        'and at most one identical infrastructure retry per group. The complete receipt audit records module reuse and retries. '
        'No adapter tuning, candidate modification, gold-reference modification, new model scoring, or outcome-based sample selection occurred.',
        'Task-bootstrap intervals reflect resampling the existing 896 task clusters for one saved run. '
        'The system-bootstrap sensitivity has only 11 systems. Missing adapter coverage can select an easier measured cohort; '
        'full-denominator bounds and the prespecified sensitivities expose, but do not eliminate, that limitation. '
        'Passing finite computational tests does not prove the full intended specification. No human labels or repeated model runs were collected.',
    ]
    assert len(cells) == 9856 and controls['all_controls_pass'] and complete['complete']
    return '\n\n'.join(paragraphs) + '\n'


def main():
    root = PHASE / 'results'
    a = json.loads((root/'analysis_e12_v2.json').read_text())
    cells = [json.loads(line) for line in (root/'cells_v2.jsonl').read_text().splitlines()]
    controls = json.loads((root/'controls_v2.json').read_text())
    complete = json.loads((root/'evaluation_complete_v2.json').read_text())
    (PHASE/'RESULTS_analysis_v2.md').write_text(render(a,cells,controls,complete))


if __name__ == '__main__':
    main()
