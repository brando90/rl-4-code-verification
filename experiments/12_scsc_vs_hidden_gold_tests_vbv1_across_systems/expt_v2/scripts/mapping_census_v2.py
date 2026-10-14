"""Zero-compilation, zero-model-call mapping census: compare version-1 recorded mappings with adapter_v2's static mapping over the 11 primary systems' saved compiling cells, reading no hidden-test pass/fail field."""
import argparse
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adapter_v2 as v2  # noqa: E402
from extract_hidden_tests import IDENT as IDENT_V1  # noqa: E402  (frozen version-1 lexer, read-only)

E12 = HERE.parents[1]
V1_RESULTS = E12 / 'expt_v1' / 'results'
RECEIPT_KEYS = ('mapping', 'diagnostics', 'all_symbols_mapped')  # the only receipt fields this census reads


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def v1_receipt_mapping(receipt_dir, task_id, sha):
    """Return the version-1 mapping of a (task, file) group from its evaluation receipt, dropping every outcome field."""
    key = hashlib.sha256((task_id + ':' + sha).encode()).hexdigest()
    path = Path(receipt_dir) / (key + '.json')
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    kept = {k: raw.get(k) for k in RECEIPT_KEYS}
    kept['compile_status'] = (raw.get('compile') or {}).get('status')
    kept['steps'] = [d.get('step') for d in (kept['diagnostics'] or []) if d.get('status') == 'mapped']
    del raw
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--receipts', default='/lfs/skampere1/0/brando9/rl4cv_e12/evaluation_A2')
    ap.add_argument('--out', default=str(E12 / 'expt_v2' / 'results' / 'mapping_census_v2.json'))
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()
    started = time.time()
    manifest = json.loads((V1_RESULTS / 'input_manifest_A1.json').read_text())
    suites = {t['task_id']: t for t in json.loads((V1_RESULTS / 'hidden_tests_manifest.json').read_text())['tasks']}
    cells = [c for c in manifest['cells'] if c['panel'] == 'primary']
    if args.limit:
        cells = cells[:args.limit]
    groups = defaultdict(list)
    skipped = Counter()
    eligible = []
    for c in cells:
        if c['join_status'] in ('file_missing', 'join_ambiguous'):
            skipped['join_' + c['join_status']] += 1
            continue
        if c['recorded_compiles'] is not True:
            skipped['noncompiling' if c['recorded_compiles'] is False else 'unmeasured_compile'] += 1
            continue
        if not suites[c['task_id']]['n_tests']:
            skipped['no_tests'] += 1
            continue
        groups[(c['task_id'], c['sha256'])].append(c)
        eligible.append(c)
    group_results = {}
    source_hash_mismatch = []
    for (task_id, sha), members in groups.items():
        path = Path(members[0]['path'])
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            source_hash_mismatch.append({'task_id': task_id, 'path': str(path)})
            continue
        suite = suites[task_id]
        mapping, diag, summary = v2.map_symbols(suite['symbols'], raw.decode(errors='replace'), suite['tests'], None)
        plan = v2.per_test_plan(suite['tests'], mapping)
        n_mapped_tests = sum(r['status'] == 'mapped' for r in plan)
        statuses = Counter(d['status'] for d in diag)
        v1 = v1_receipt_mapping(args.receipts, task_id, sha)
        group_results[(task_id, sha)] = {
            'v2_mapping': mapping, 'v2_steps': [d['step'] for d in diag if d['status'] == 'mapped'],
            'v2_status': ('mapped_all' if statuses.get('mapped', 0) == len(diag) else
                          'needs_probe' if statuses.get('needs_probe') else
                          'mapped_partial' if statuses.get('mapped') else 'not_applicable'),
            'v2_helpers_excluded': sum(bool(d['helpers_excluded']) for d in diag),
            'v2_reasons': [d['reason'] for d in diag if d['status'] != 'mapped'],
            'v2_result_type_mismatch': sum(d['result_type_compatible'] is False for d in diag),
            'v2_argument_type_mismatch': sum(d['argument_types_compatible'] is False for d in diag),
            'n_tests': suite['n_tests'], 'n_mapped_tests': n_mapped_tests,
            'candidate_n_examples': summary['n_examples'], 'candidate_n_eval_commands': summary['n_eval_commands'],
            'v1': v1}
    per_system = {}
    hist_all = Counter()
    step_counter_v2 = Counter()
    step_counter_v1 = Counter()
    reason_counter = Counter()
    for c in eligible:
        g = group_results.get((c['task_id'], c.get('sha256')))
        if g is None:
            continue
        reason_counter.update(str(r) for r in g['v2_reasons'])
        s = per_system.setdefault(c['system'], Counter())
        s['compiling_with_tests'] += 1
        v1 = g['v1']
        v1_all = bool(v1 and v1['all_symbols_mapped'])
        v1_any = bool(v1 and v1['mapping'])
        s['v1_receipt_found'] += v1 is not None
        s['v1_mapped_all'] += v1_all
        s['v1_mapped_any'] += v1_any
        s['v2_' + g['v2_status']] += 1
        v2_all = g['v2_status'] == 'mapped_all'
        v2_any = bool(g['v2_mapping'])
        s['newly_mapped_all'] += (not v1_all) and v2_all
        s['newly_unmapped_all'] += v1_all and (not v2_all)
        s['newly_needs_probe_after_v1_mapped'] += v1_all and g['v2_status'] == 'needs_probe'
        if v1_any and v2_any:
            shared = [k for k in g['v2_mapping'] if k in (v1['mapping'] or {})]
            changed = any(g['v2_mapping'][k] != v1['mapping'][k] for k in shared)
            s['both_mapped_some_symbol'] += 1
            s['changed_entry_point'] += changed
        s['helper_excluded_cells'] += g['v2_helpers_excluded'] > 0
        s['result_type_mismatch_cells'] += g['v2_result_type_mismatch'] > 0
        s['argument_type_mismatch_cells'] += g['v2_argument_type_mismatch'] > 0
        s['zero_self_test_cells'] += (g['candidate_n_examples'] == 0 and g['candidate_n_eval_commands'] == 0)
        s['tests_total'] += g['n_tests']
        s['tests_mapped_v2'] += g['n_mapped_tests']
        s['all_tests_mapped_v2'] += g['n_mapped_tests'] == g['n_tests']
        share = g['n_mapped_tests'] / g['n_tests']
        bucket = '1.0' if share == 1 else '0' if share == 0 else f'({(int(share * 4) * 25)}%, {(int(share * 4) + 1) * 25}%]'
        s['hist_' + bucket] += 1
        hist_all[bucket] += 1
        for st in g['v2_steps']:
            step_counter_v2[str(st)] += 1
        for st in (v1['steps'] if v1 else []):
            step_counter_v1[str(st)] += 1
    totals = Counter()
    for s in per_system.values():
        totals.update(s)
    # Gold-side lexer impact: do any gold declarations or extracted test statements tokenize differently under the corrected lexer?
    gold_impact = {'tasks_with_suffixed_identifiers': 0, 'tests_tokenizing_differently': 0, 'examples': []}
    for g in manifest['gold']:
        text = Path(g['path']).read_text(errors='replace')
        if hashlib.sha256(text.encode()).hexdigest() != g['sha256']:
            source_hash_mismatch.append({'task_id': g['task_id'], 'path': g['path'], 'kind': 'gold'})
        clean = v2.strip_comments(text)
        suffixed = sorted({t for t in v2.IDENT.findall(clean) if re.search(r'[?!]', t)})
        if suffixed:
            gold_impact['tasks_with_suffixed_identifiers'] += 1
            if len(gold_impact['examples']) < 10:
                gold_impact['examples'].append({'task_id': g['task_id'], 'identifiers': suffixed[:6]})
        for t in suites[g['task_id']]['tests']:
            st = v2.STRING.sub('""', t['statement'])
            if IDENT_V1.findall(st) != [x for x in v2.IDENT.findall(st) if not x.isdigit()] and \
               [x for x in IDENT_V1.findall(st)] != v2.IDENT.findall(st):
                gold_impact['tests_tokenizing_differently'] += 1
    report = {
        'created': time.strftime('%m-%d-%Y %H:%M %Z'), 'seconds': round(time.time() - started, 1),
        'scope': 'primary panel, 11 systems, compiling cells with extracted tests; static mapping only (steps 1, 2a, 2b); no Lean, no model calls; no hidden pass/fail field read',
        'receipt_fields_read': list(RECEIPT_KEYS) + ['compile.status'],
        'input_hashes': {'input_manifest_A1.json': sha256_file(V1_RESULTS / 'input_manifest_A1.json'),
                         'hidden_tests_manifest.json': sha256_file(V1_RESULTS / 'hidden_tests_manifest.json'),
                         'adapter_v2.py': sha256_file(HERE / 'adapter_v2.py'),
                         'adapter_e12.py (version 1)': sha256_file(E12 / 'expt_v1' / 'scripts' / 'adapter_e12.py')},
        'n_primary_cells': len(cells), 'skipped': dict(skipped), 'n_unique_groups': len(groups),
        'source_hash_mismatch': source_hash_mismatch,
        'totals': dict(totals), 'per_system': {k: dict(v) for k, v in sorted(per_system.items())},
        'tests_mapped_histogram': dict(hist_all),
        'v2_static_steps': dict(step_counter_v2), 'v1_recorded_steps': dict(step_counter_v1),
        'v2_unmapped_symbol_reasons': dict(reason_counter),
        'gold_lexer_impact': gold_impact,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: report[k] for k in ('n_primary_cells', 'skipped', 'n_unique_groups', 'totals', 'tests_mapped_histogram', 'v2_static_steps', 'v1_recorded_steps', 'gold_lexer_impact', 'seconds')}, indent=1))


if __name__ == '__main__':
    main()
