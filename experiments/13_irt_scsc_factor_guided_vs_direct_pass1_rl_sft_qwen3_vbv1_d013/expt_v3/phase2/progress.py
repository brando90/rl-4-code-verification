"""Refresh human-readable progress from durable receipts; never infer success from process exit."""
from __future__ import annotations

import csv
from datetime import datetime
import io
import json
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from technical import ROOT, V3, T2, T3


def read(path):
    if not path.is_file(): return None
    for attempt in range(3):
        try: return json.loads(path.read_text())
        except json.JSONDecodeError:
            if attempt == 2: raise
            time.sleep(.1)


def refresh():
    t2 = read(T2 / 'result.json'); t3 = read(T3 / 'result.json')
    t4 = read(ROOT / 'phase2/technical/T4/attempt_1/gate.json')
    probe = read(ROOT / 'phase2/technical/T4/attempt_1/result.json')
    dispatch = read(ROOT / 'phase2/pilot_dispatch/result.json')
    errors = read(ROOT / 'phase2/pilot_dispatch/error.json')
    runs = []
    curve = io.StringIO()
    writer = csv.DictWriter(curve, lineterminator='\n', fieldnames=['arm', 'seed', 'update', 'measured', 'reward_mean_observed',
        'active_groups', 'usable_groups', 'active_group_fraction', 'grad_norm', 'nonzero_advantage_slots',
        'strict_successes', 'generated_tokens', 'parameter_change'])
    writer.writeheader()
    for seed in (1301, 1302):
        for arm in ('B', 'A', 'P'):
            rows = [read(p) for p in sorted((ROOT / 'phase2/pilot' / f'{arm}_{seed}').glob('update_*/summary.json'))]
            for row in rows: writer.writerow({k: row[k] for k in writer.fieldnames})
            evaluations = []
            for boundary in (30, 60):
                r = read(ROOT / 'phase2/validation' / f'{arm}_{seed}_{boundary}/result.json')
                if r: evaluations.append(r)
            runs.append({'arm': arm, 'seed': seed, 'completed': len(rows),
                         'latest': rows[-1] if rows else None, 'evaluations': evaluations})
    status = errors['status'] if errors else dispatch['status'] if dispatch else 'PILOT_RUNNING' if (ROOT / 'phase2/pilot_admission.json').is_file() else 'TECHNICAL_GATES_RUNNING'
    for gate in (t2, t3, t4):
        if gate and gate['status'] not in ('PASS',): status = 'STOPPED_AT_' + gate['gate'] + '_' + gate['status']; break
    machine = {'condition': 'v3-A7', 'status': status, 'T2': t2, 'T3': t3, 'T4': t4 or probe,
               'runs': runs, 'dispatcher_error': errors, 'api_spend_usd': 0}
    path = V3 / 'results/live_progress.json'
    if read(path) == machine: return False
    path.write_text(json.dumps(machine, sort_keys=True, indent=2) + '\n')
    (V3 / 'results/pilot_trajectory.csv').write_text(curve.getvalue())
    stamp = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%m-%d-%Y %H:%M %Z')
    lines = ['<!-- LIVE START -->', f'Live receipt status ({stamp}): **{status}**. API spend: **$0**.', '',
             '| Arm / seed | Completed updates | Latest observed train reward | Active / usable groups | Gradient norm |',
             '|---|---:|---:|---:|---:|']
    for run in runs:
        row = run['latest']
        values = [f"{row['reward_mean_observed']:.6f}", f"{row['active_groups']}/{row['usable_groups']}", f"{row['grad_norm']:.6g}"] if row else ['unmeasured'] * 3
        lines.append(f"| {run['arm']} / {run['seed']} | {run['completed']} | " + ' | '.join(values) + ' |')
    evaluations = [value for run in runs for value in run['evaluations']]
    if evaluations:
        lines += ['', '| Validation arm / seed / update | Strict successes / declared | pass@1 bounds | SCSC mean bounds | Known SCSC cells |',
                  '|---|---:|---|---|---:|']
        for value in evaluations:
            scsc = value['official_SCSC_evidence']
            lines.append(f"| {value['arm']} / {value['seed']} / {value['boundary']} | {value['successes']}/{value['declared']} | {value['strict_mean_bounds']} | {scsc['mean_bounds']} | {scsc['known_composites']}/{scsc['declared']} |")
    lines += ['', '[Every completed training step](results/pilot_trajectory.csv); [machine-readable gate and validation results](results/live_progress.json).',
              'Training rows are fixed-run diagnostics (p-val=n/a), not an efficacy claim. Validation receipts retain grouped-task bootstrap intervals and missingness bounds. Coverage requiring a judge remains unmeasured; a known zero local factor can determine a zero composite.', '<!-- LIVE END -->']
    document = V3 / 'results.md'; text = document.read_text()
    if '<!-- LIVE START -->' in text:
        begin = text.index('<!-- LIVE START -->'); end = text.index('<!-- LIVE END -->') + len('<!-- LIVE END -->')
        text = text[:begin] + '\n'.join(lines) + text[end:]
    else:
        text = text.replace('**TLDR-end:**', '\n'.join(lines) + '\n\n**TLDR-end:**')
    text = text.replace(next(line for line in text.splitlines() if line.startswith('**Status:**')), '**Status:** ' + status)
    for label, gate in [('T2: one update and eight-response refit', t2), ('T3: saved-batch replay', t3),
                        ('T4: eight-cell train evaluation cost', t4 or probe)]:
        if gate:
            old = next(line for line in text.splitlines() if line.startswith('| ' + label + ' |'))
            link = '[Measured result](RESULTS_T2_v3.md)' if label.startswith('T2') else '[Receipt](results/live_progress.json)'
            text = text.replace(old, f"| {label} | {gate['status']} | {link} |")
    if any(r['completed'] for r in runs):
        old = next(line for line in text.splitlines() if line.startswith('| T5 and paired B/A/P pilot |'))
        text = text.replace(old, '| T5 and paired B/A/P pilot | ' + status + ' | See live table below. |')
    document.write_text(text)
    checkpoint = V3 / 'CKPT_factored_pilot.md'
    state = checkpoint.read_text()
    old = next(line for line in state.splitlines() if line.startswith('**TLDR:**'))
    state = state.replace(old, f'**TLDR:** {status}; exact receipts and completed update counts are in results.md. No official SCSC result without validated coverage.')
    old = next(line for line in state.splitlines() if line.startswith('Last updated:'))
    state = state.replace(old, 'Last updated: ' + stamp)
    checkpoint.write_text(state)
    with checkpoint.open('a') as stream:
        stream.write(f"- {stamp} — Receipt event: {status}; completed updates " + ', '.join(f"{r['arm']}/{r['seed']}={r['completed']}" for r in runs) + '.\n')
    return True


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    while True:
        refresh()
        if not args.watch: break
        if (ROOT / 'phase2/pilot_dispatch/result.json').is_file() or (ROOT / 'phase2/pilot_dispatch/error.json').is_file(): break
        time.sleep(30)
