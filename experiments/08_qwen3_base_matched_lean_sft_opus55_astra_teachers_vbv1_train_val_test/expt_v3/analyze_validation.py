"""Publish complete validation rungs, failure categories and paired task-bootstrap comparisons."""
from __future__ import annotations
import csv
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo
import numpy as np
from assess_forecast import assess

HERE = Path(__file__).resolve().parent
WORK = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')
sys.path.insert(0, str(HERE.parent / 'expt_v1/scripts'))
import analyze_ladder as base
base.WORK = WORK
base.EXP = HERE


def estimate(values, draws):
    values = np.asarray(values, dtype=float)
    low, high = np.quantile(values[draws].mean(axis=1), [.025, .975])
    return {'mean': float(values.mean()), 'ci95': [float(low), float(high)], 'p_value': None,
            'draws': len(draws), 'seed': 0, 'unit': 'task with eight attempts together'}


def coverage_rows(rows, ids):
    """Retain one status for every declared cell, including failed and absent rows."""
    want = {(t, k) for t in ids for k in range(8)}
    keys = [(r['task_id'], r['sample_idx']) for r in rows]
    if len(keys) != len(set(keys)) or set(keys) - want:
        raise ValueError('Duplicate or extra scored cells')
    indexed = dict(zip(keys, rows))
    return [{'task_id': t, 'sample_idx': k,
             'known': indexed.get((t, k), {}).get('status') == 'scored',
             'status': indexed.get((t, k), {}).get('status', 'missing'),
             'error': indexed.get((t, k), {}).get('error', '')}
            for t in ids for k in range(8)]


def decision(systems, sizes, paired):
    by_fraction = {}
    for fraction in ('f0p5', 'f1p0'):
        labels = {c: [f'v3_{c}_{s}_{fraction}' for s in sizes] for c in ('R', 'E')}
        if any(label not in systems for labs in labels.values() for label in labs):
            by_fraction[fraction] = {'status': 'INCOMPLETE', 'selected': None}
            continue
        passing = {c: all(systems[label]['gates']['pass'] for label in labs) for c, labs in labels.items()}
        selected = None
        if passing['E'] and passing['R']:
            floors = {c: min(systems[label]['task_bootstrap']['pass_rate']['mean'] for label in labs) for c, labs in labels.items()}
            no_harm = all(paired[f'{s}_{fraction}']['ci95'][1] >= 0 for s in sizes)
            selected = 'E' if floors['E'] > floors['R'] and no_harm else 'R'
        elif passing['E']:
            selected = 'E'
        elif passing['R']:
            selected = 'R'
        by_fraction[fraction] = {'status': 'COMPLETE', 'common_checkpoint': passing, 'selected': selected,
                                'selection_rule': 'E only with a higher minimum success rate and no wholly negative paired interval; otherwise retain R when both pass'}
    return by_fraction


def main():
    manifest = json.loads((HERE / 'results/ladder_manifest_v3.json').read_text())
    ids = manifest['task_ids']
    draws = np.random.default_rng(0).integers(0, len(ids), (10000, len(ids)))
    systems, vectors, coverage = {}, {}, {}
    coverage_dir = HERE / 'results/coverage'; coverage_dir.mkdir(exist_ok=True)
    for system in manifest['systems']:
        label = system['label']
        scored = WORK / f'ladder/validation/scored/scored_{label}_g8.jsonl'
        rows = [json.loads(l) for l in scored.read_text().splitlines()] if scored.exists() else []
        cells = coverage_rows(rows, ids)
        path = coverage_dir / f'{label}.csv'
        with path.open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(cells[0]), lineterminator='\n')
            writer.writeheader(); writer.writerows(cells)
        known = sum(c['known'] for c in cells)
        coverage[label] = {'known': known, 'declared': len(cells),
                           'missing': sum(c['status'] == 'missing' for c in cells),
                           'failed_or_unknown': sum(not c['known'] and c['status'] != 'missing' for c in cells),
                           'cells_csv': str(path.relative_to(HERE))}
        if known != len(cells):
            continue
        result = base.evaluate({**system, 'source': 'e08'}, ids, 'validation', HERE / 'results/ladder')
        assert result['status'] == 'COMPLETE'
        task_rows = list(csv.DictReader((HERE / result['per_task_csv']).open()))
        values = np.array([int(r['k_kernel_binary']) / 8 for r in task_rows])
        vectors[label] = values
        result['task_bootstrap'] = {'pass_rate': estimate(values, draws),
                                    'pass_at_8': estimate(values > 0, draws),
                                    'mixed_share': estimate((values > 0) & (values < 1), draws)}
        result['scored_sha256'] = base.sha(scored.read_bytes())
        cell_rows = list(csv.DictReader((HERE / result['cells_csv']).open()))
        raw = {(r['task_id'], int(r['sample_idx'])): r for r in rows}
        counts = Counter()
        taxonomy = []
        for cell in cell_rows:
            r = raw[cell['task_id'], int(cell['sample_idx'])]
            if cell['extracted'] != 'True': category = 'no_lean_extracted'
            elif not r.get('compiles'): category = 'compile_error'
            elif not r.get('n_theorems_proved'): category = 'compiles_zero_proved'
            elif (int(r.get('n_theorems_proved') or 0) < int(r.get('n_theorems_stated') or 0)
                  or int(cell['n_vacuous']) or cell['unparseable'] == 'True'): category = 'compiles_partially_proved_or_vacuous'
            elif float(cell['kernel_binary']) == 1: category = 'kernel_success'
            else: category = 'compiles_all_proved_not_kernel_success'
            counts[category] += 1
            taxonomy.append({'task_id': cell['task_id'], 'sample_idx': cell['sample_idx'], 'category': category,
                             'capped': cell['capped'], 'lean_sha256': cell['lean_sha256']})
        with (HERE / f'results/ladder/{label}_taxonomy.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=list(taxonomy[0]), lineterminator='\n')
            writer.writeheader(); writer.writerows(taxonomy)
        result['failure_taxonomy'] = dict(counts)
        systems[label] = result
    paired = {}
    for short in ('1p7b', '4b', '8b', '14b'):
        for fraction in ('f0p5', 'f1p0'):
            e, r = f'v3_E_{short}_{fraction}', f'v3_R_{short}_{fraction}'
            if e in vectors and r in vectors:
                paired[f'{short}_{fraction}'] = estimate(vectors[e] - vectors[r], draws)
    known_cells = sum(c['known'] for c in coverage.values())
    summary = {'systems': systems, 'paired_E_minus_R': paired, 'known_cells': known_cells, 'declared_cells': 17280,
               'complete_rung_cells': 1080 * len(systems), 'cell_coverage': coverage,
               'primary': decision(systems, ('1p7b', '4b', '8b', '14b'), paired),
               'sensitivity': decision(systems, ('4b', '8b', '14b'), paired),
               'uncertainty': '10000 percentile paired task-bootstrap draws, seed 0; eight attempts together; single training seed; p-val=n/a',
               'unknown_systems': [s['label'] for s in manifest['systems'] if s['label'] not in systems]}
    forecast = assess(summary)
    (HERE / 'results/forecast_assessment_v3.json').write_text(json.dumps(forecast, indent=2) + '\n')
    summary['forecast_assessment'] = forecast
    (HERE / 'results/validation_summary_v3.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    now = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%m-%d-%Y %H:%M %Z')
    phase_status = {phase: json.loads((WORK / f'phase_{phase}_state.json').read_text()).get('status')
                    if (WORK / f'phase_{phase}_state.json').exists() else 'NOT_STARTED' for phase in ('a', 'b')}
    lines = ['# Matched replay versus expansion continuation results', '',
             f'**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/{HERE.relative_to(HERE.parents[2])}/results.md>', '',
             f'**TLDR:** Phase A: {phase_status["a"]}; Phase B: {phase_status["b"]}. {known_cells:,}/17,280 validation cells known. [Execution events and verified training progress](results/runtime_progress.md).', '',
             f'**Status:** {"VALIDATION COMPLETE" if len(systems) == 16 else "RUNNING"}. **Last updated:** {now}.', '',
             f'Known validation cells: **{known_cells}/17,280**; {1080 * len(systems)} belong to complete rungs. [Every missing/failed cell](results/coverage) remains in the declared denominator; no paid model calls.', '',
             '| System | Known / declared | Extracted | Capped | Mixed /135 | Gates | Pass rate [95% interval] |',
             '|---|---:|---:|---:|---:|---|---|']
    for s in manifest['systems']:
        label = s['label']
        if label not in systems:
            lines.append(f'| {label} | {coverage[label]["known"]}/1,080 | — | — | — | INCOMPLETE | — |')
            continue
        r = systems[label]; g = r['gates']; rate = r['task_bootstrap']['pass_rate']
        lines.append(f'| {label} | 1,080/1,080 | {g["a_extraction"]["n"]} | {g["b_capped"]["n"]} | {g["c_mixed"]["n"]} | {"PASS" if g["pass"] else "FAIL"} | {rate["mean"]:.4f} [{rate["ci95"][0]:.4f}, {rate["ci95"][1]:.4f}] |')
    lines += ['', 'Gates are protocol-defined: ≥972 extracted, ≤108 capped, ≥7 mixed tasks, with every input known. Intervals resample 135 tasks with all eight attempts, 10,000 draws, seed 0; p-val=n/a. Training-seed variation is unmeasured. Mixed-share Wilson intervals, failure taxonomy, diversity and paired comparisons are in [the full summary](results/validation_summary_v3.json) and [per-cell/per-task tables](results/ladder).', '',
              'Primary four-size decision: `' + json.dumps(summary['primary']) + '`.', '',
              'Three-size sensitivity (4B/8B/14B): `' + json.dumps(summary['sensitivity']) + '`.', '',
              'Hosted Smooth Conjunctive Score for Code verification judging remains deferred at $0 spend. Namespace escaping is a separate diagnostic and never changes primary scores; [diagnostic tables](results/namespace_diagnostic). The test split remains unopened.', '',
              'Frozen forecast assessment: [prediction and measured outcome](results/forecast_assessment_v3.json). Incomplete outcomes have no hit/miss verdict. The report retains the original earliest-selected-winner interpretation alongside earliest common checkpoint within each condition; both are disclosed if they disagree.', '',
              'Execution and recovery events: [runtime ledger](results/runtime_progress.md).', '',
              '**TLDR-end:** [rl4cv: matched replay versus expansion] 08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v3 validation coverage is ' + str(known_cells) + '/17,280; incomplete comparisons remain unresolved.']
    comparison = ['', '| Size and fraction | Expansion minus replay success rate [95% interval] |',
                  '|---|---:|']
    for key, value in paired.items():
        comparison.append(f'| {key} | {value["mean"]:.4f} [{value["ci95"][0]:.4f}, {value["ci95"][1]:.4f}] |')
    if paired:
        lines[-1:-1] = comparison + ['']
    (HERE / 'results.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'complete_systems': len(systems), 'known_cells': known_cells}))


if __name__ == '__main__':
    main()
