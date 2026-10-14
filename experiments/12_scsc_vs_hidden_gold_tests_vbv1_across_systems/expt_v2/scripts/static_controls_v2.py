"""Zero-Lean static controls for adapter_v2 over all 882 gold suites: gold as its own candidate must map every symbol to itself at step 1, and renamed gold must never resolve to a helper or a wrong symbol statically."""
import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adapter_v2 as v2  # noqa: E402
from adapter_e12 import renamed_control  # noqa: E402  (frozen version-1 helper, read-only)

E12 = HERE.parents[1]
V1_RESULTS = E12 / 'expt_v1' / 'results'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(E12 / 'expt_v2' / 'results' / 'static_controls_v2.json'))
    args = ap.parse_args()
    started = time.time()
    suites = json.loads((V1_RESULTS / 'hidden_tests_manifest.json').read_text())['tasks']
    c1 = Counter()
    c2 = Counter()
    c1_failures, c2_notes = [], []
    for t in suites:
        if not t['n_tests']:
            continue
        source = Path(t['path']).read_text()
        assert hashlib.sha256(source.encode()).hexdigest() == t['sha256'], t['task_id']
        # C1-static: gold as candidate.
        mapping, diag, _ = v2.map_symbols(t['symbols'], source, t['tests'], None)
        ok = all(mapping.get(s['full_name']) == s['full_name'] for s in t['symbols']) and all(d['step'] == 1 for d in diag)
        c1['tasks'] += 1
        c1['pass'] += ok
        if not ok:
            c1_failures.append({'task_id': t['task_id'], 'diagnostics': [{k: d[k] for k in ('gold_symbol', 'step', 'status', 'chosen', 'reason')} for d in diag]})
        # C2-static: renamed gold; the static stage may map (2a/2b) or defer to the probe, but must never choose a wrong or helper symbol.
        renamed, subs = renamed_control(source, t['symbols'])
        mapping2, diag2, _ = v2.map_symbols(t['symbols'], renamed, t['tests'], None)
        expected = {s['full_name']: '.'.join(subs.get(p, p) for p in s['full_name'].split('.')) for s in t['symbols']}
        c2['tasks'] += 1
        statuses = Counter(d['status'] for d in diag2)
        wrong = [d['gold_symbol'] for d in diag2 if d['status'] == 'mapped' and mapping2[d['gold_symbol']] != expected[d['gold_symbol']]]
        if wrong:
            c2['wrong_static_mapping'] += 1
            c2_notes.append({'task_id': t['task_id'], 'wrong': wrong, 'mapping': mapping2, 'expected': expected})
        elif statuses.get('mapped', 0) == len(diag2):
            c2['resolved_static_correct'] += 1
        elif statuses.get('needs_probe'):
            c2['deferred_to_probe'] += 1
        else:
            c2['not_applicable_static'] += 1
        for d in diag2:
            c2['step_' + str(d['step'])] += 1
    report = {'created': time.strftime('%m-%d-%Y %H:%M %Z'), 'seconds': round(time.time() - started, 1),
              'adapter_v2_sha256': hashlib.sha256((HERE / 'adapter_v2.py').read_bytes()).hexdigest(),
              'hidden_tests_manifest_sha256': hashlib.sha256((V1_RESULTS / 'hidden_tests_manifest.json').read_bytes()).hexdigest(),
              'C1_static_gold_self_mapping': dict(c1), 'C1_failures': c1_failures,
              'C2_static_renamed_gold': dict(c2), 'C2_wrong_mappings': c2_notes[:50],
              'note': 'static stage only (steps 1, 2a, 2b); no Lean, no hidden outcome; the Lean controls C1-C4 of PROTOCOL section 3 still gate the evaluation'}
    Path(args.out).write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({k: report[k] for k in ('seconds', 'C1_static_gold_self_mapping', 'C2_static_renamed_gold')}, indent=1))
    print('C1 failures:', len(c1_failures), 'C2 wrong:', len(c2_notes))


if __name__ == '__main__':
    main()
