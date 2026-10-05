"""Inventory frozen VeriBench factor and historical replay artifacts without new model calls."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

CORE = {'easy_set', 'cs_set', 'humaneval_set', 'realcode_set', 'security_set'}
FACTORS = ('IC_tests', 'IC_proofs', 'FSC')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_inputs(root):
    manifest = json.loads((root / 'input_manifest.json').read_text())
    data = {}
    for item in manifest['inputs']:
        path = root / item['snapshot']
        if sha(path) != item['sha256']:
            raise ValueError(f"Input hash mismatch: {item['snapshot']}")
        if path.suffix == '.json':
            data[item['name']] = json.loads(path.read_text())
        else:
            with path.open(newline='') as stream:
                data[item['name']] = list(csv.DictReader(stream))
    return manifest, data


def condition(row, manifest):
    return row.get('condition') or (manifest['condition'] if row['benchmark'] == 'vbv1_896' else 'unspecified')


def panel(row):
    if row['benchmark'] != 'vbv1_896':
        return row['benchmark']
    return 'core_614' if row['task'].split('__')[0] in CORE else 'industry_282'


def summarize(rows, declared):
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        key = (row['benchmark'], condition(row, declared), row['model'], row['task'])
        if key in seen:
            raise ValueError(f'Duplicate cell: {key}')
        seen.add(key)
        for metric in (*FACTORS, 'SCSC'):
            value = row.get(metric)
            if value is not None and (not isinstance(value, (int, float)) or not 0 <= value <= 1):
                raise ValueError(f'Invalid {metric} for {key}')
        groups[(row['benchmark'], condition(row, declared), row['model'], panel(row))].append(row)
    # Explicitly include configurations absent from the saved snapshot.
    for model in declared['models']:
        for p in ('core_614', 'industry_282'):
            groups[('vbv1_896', declared['condition'], model, p)]
    result = []
    for (bench, cond, model, p), rs in sorted(groups.items()):
        expected = None
        if bench == 'vbv1_896' and cond == declared['condition'] and model in declared['models']:
            expected = 614 if p == 'core_614' else 282
            if len(rs) > expected:
                raise ValueError('More V1 original cells than declared')
        complete = sum(all(r.get(f) is not None for f in FACTORS) for r in rs)
        zero = sum(any(r.get(f) == 0 for f in FACTORS) for r in rs)
        supplied = [r['SCSC'] for r in rs if r.get('SCSC') is not None]
        result.append(dict(benchmark=bench, condition=cond, model=model, panel=p,
            declared_original_cells=expected, saved_rows=len(rs),
            absent_from_snapshot=None if expected is None else expected-len(rs),
            status_counts=dict(sorted(Counter(r['cell_status'] for r in rs).items())),
            all_factors_present=complete,
            factor_present={f:sum(r.get(f) is not None for r in rs) for f in FACTORS},
            known_zero_per_artifact_product=zero,
            supplied_scsc_present=len(supplied), supplied_scsc_distinct=len(set(supplied)),
            candidate_hash_present=sum(bool(r.get('solution_sha256')) for r in rs)))
    return result


def build_report(result):
    lines = ['# Retained artifact feasibility audit', '',
        '**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2/expt_v1/results/RESULTS_existing_artifacts.md>', '',
        '**TLDR:** The frozen factor snapshot has no independently measured fixed-reference pass@1 endpoint. Historical adapter and proof-replay labels are available, but do not establish strict kernel correctness or an intervention effect.', '',
        f"Audit host: `{result['host']}`. Source snapshot time: `{result['source_written_utc']}` (machine timestamp).", '',
        f"Saved rows: {result['saved_rows']}; complete factor rows: {result['all_factors_present']}. These are finite-file counts; intervals and p-val=n/a.", '',
        f"Original V1 snapshot coverage: {result['v1_saved_original']}/{result['v1_declared_original']} declared cells; {result['v1_absent_from_snapshot']} absent. This is snapshot coverage, not a claim that live jobs were unattempted.", '',
        'SCSC means Smooth Conjunctive Score for Code verification. Core and IndustrySet panels are separate. Other conditions have saved-row counts only; this audit has not independently reconstructed their declared task manifests.', '',
        '| Benchmark / panel | Condition | Model | Saved / declared original | All factors | Known zero artifact product | Supplied SCSC |',
        '|---|---|---|---:|---:|---:|---:|']
    for g in result['groups']:
        denom = g['declared_original_cells'] if g['declared_original_cells'] is not None else 'not reconstructed'
        lines.append(f"| {g['panel']} | {g['condition']} | {g['model']} | {g['saved_rows']} / {denom} | {g['all_factors_present']} | {g['known_zero_per_artifact_product']} | {g['supplied_scsc_present']} |")
    lines += ['', '## Historical adapter and replay inventory', '',
        'All labels below are historical ordinary Lean outcomes. No proof was rerun, and transitive axiom trust was not revalidated.', '',
        f"Adapter rows: {result['historical']['adapter_rows']}; recorded labels: `{json.dumps(result['historical']['adapter_status_counts'], sort_keys=True)}`.", '',
        f"Replay pair rows: {result['historical']['replay_pair_rows']}; recorded decisions: `{json.dumps(result['historical']['replay_decision_counts'], sort_keys=True)}`.", '',
        '## Decision and limitations', '',
        '**Independent-outcome correlation: NOT IDENTIFIABLE from these inputs.** The audit found no fields for the specified reference-test or strict reference-obligation outcomes. This is a schema/construct conclusion, not a negative correlation result.', '',
        'The V1 task list is represented by a hash in the upstream manifest, not copied here as a reconstructed full task manifest. Missing counts are reconciled at model/panel level. Recovery and multifile conditions remain separate. A valid zero factor identifies a zero per-artifact product even when another factor is absent; it does not supply the missing factor or a complete official aggregate.', '',
        'The frozen inputs already existed and selected prior outcomes were known when this audit was designed. No prospective prediction, intervention gain, population estimate or proof certificate is claimed. Statistical intervals, repeated-run variation and hypothesis-test p-values are unavailable/not applicable to this descriptive inventory.', '',
        '**[p 9/10] Validate fixed-reference endpoints on screened external tasks**, because trusted independent outcomes are missing; then freeze a cost-matched component-versus-scalar feedback comparison.', '',
        '**TLDR-end:** [rl-4-code-verification: 04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2] Retained inputs support an availability audit, not a new correctness correlation. Endpoint validation is the next dependency.', '',
        '**Snapshot:**', '```text', f"saved_rows={result['saved_rows']}", f"complete_factor_rows={result['all_factors_present']}", f"v1_snapshot_cells={result['v1_saved_original']}/{result['v1_declared_original']}", 'independent_reference_outcome=unavailable', 'new_model_calls=0', '```', '']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    args = ap.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    manifest, data = read_inputs(args.root)
    rows = data['factor_summary']['rows']
    declared = data['v1_manifest']
    groups = summarize(rows, declared)
    v1 = [g for g in groups if g['benchmark']=='vbv1_896' and g['condition']==declared['condition'] and g['model'] in declared['models']]
    expected = sum(g['declared_original_cells'] for g in v1)
    if expected != declared['expected_cells']:
        raise ValueError('Declared matrix does not match expected cell count')
    result = dict(audit_version=1, host=platform.node(), python=sys.version.split()[0],
        started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
        source_written_utc=data['factor_summary'].get('written_utc'),
        script_sha256=sha(__file__), input_manifest_sha256=sha(args.root/'input_manifest.json'),
        protocol_sha256=sha(args.root.parent/'PROTOCOL.md'),
        saved_rows=len(rows), all_factors_present=sum(g['all_factors_present'] for g in groups),
        v1_declared_original=expected, v1_saved_original=sum(g['saved_rows'] for g in v1),
        v1_absent_from_snapshot=sum(g['absent_from_snapshot'] for g in v1),
        groups=groups, independent_reference_outcome='unavailable in selected input schemas',
        historical=dict(adapter_rows=len(data['adapters']),
          adapter_status_counts=dict(Counter(r['adapter_status'] for r in data['adapters'])),
          replay_pair_rows=len(data['replay_pairs']),
          replay_decision_counts=dict(Counter(r['kernel_decision'] for r in data['replay_pairs']))),
        new_model_calls=0, new_gpu_hours=0, incremental_provider_charges_usd=0)
    out=args.root/'results';out.mkdir(exist_ok=True)
    (out/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (out/'RESULTS_existing_artifacts.md').write_text(build_report(result))
    print(json.dumps({k:result[k] for k in ('host','saved_rows','all_factors_present','v1_saved_original','v1_declared_original','v1_absent_from_snapshot','new_model_calls')}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
