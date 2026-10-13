#!/usr/bin/env python3
"""Apply frozen R1 acceptance rules and report rejection causes over the rejected train cohort."""
from collections import Counter
import json
import math
from pathlib import Path
import sys
import numpy as np

# Branch coverage is defined from source and authored fixtures before any train result.
COVERAGE = {
    'vacuity_unparseable_type': ['unparseable_compiling', 'unparseable_noncompiling'],
    'vacuity_count_overflow': ['vacuous'],
    'parser_parse_error': ['truncated_syntax'],
    'identity_duplicate': ['duplicate_obligation'],
    'identity_kernel_disagreement': ['failed_then_valid', 'unresolved_type'],
}
TYPED = {'deterministic_resource_limit', 'transient_infrastructure'}


def wilson(k, n):
    z = 1.959963984540054
    if not n:
        return [None, None]
    p = k / n
    divisor = 1 + z*z/n
    middle = (p + z*z/(2*n)) / divisor
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / divisor
    return [max(0., middle-half), min(1., middle+half)]


def summarize(root):
    root = Path(root)
    sample = json.loads((root/'sample.json').read_text())
    rows = [json.loads(line) for line in (root/'results.jsonl').read_text().splitlines()]
    expected = {r['cell_id'] for r in sample}
    actual = [r['cell_id'] for r in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('R1 receipt denominator incomplete or replaced')
    rejected = [r for r in rows if r['original_category'] == 'rejected']
    causes = Counter(r.get('v1_cause', 'unresolved_v1_path') for r in rejected)
    table = [{'cause': c, 'count': k, 'denominator': len(rejected), 'share': k/len(rejected),
              'wilson_95': wilson(k, len(rejected)), 'fixtures': COVERAGE.get(c, [])}
             for c,k in sorted(causes.items())]
    measured = [r for r in rows if r['status'] == 'measured']
    untyped = [r['cell_id'] for r in rows if r['status'] not in TYPED | {'measured'}]
    unequal = [r['cell_id'] for r in measured if not r['oracle_equal']]
    inconsistencies = [r['cell_id'] for r in measured if r['v2']['consistency'].startswith('untyped_')]
    uncovered = [r['cause'] for r in table if r['share'] > .01 and not r['fixtures']]
    peaks = [max(r.get('peak_tree_rss_bytes',0),r.get('child_max_rss_bytes',0)) for r in rows]
    walls = [r['wall_seconds'] for r in rows if 'wall_seconds' in r]
    result = {'stage': 'R1_attempt_1', 'development_attempt': 1, 'attempt_limit': 5,
        'status': 'FAIL' if untyped or unequal or inconsistencies or uncovered else 'PASS',
        'declared': len(sample), 'measured': len(measured), 'typed_classes': dict(Counter(r['status'] for r in rows)),
        'oracle_matches': sum(r['oracle_equal'] for r in measured), 'untyped_measurements': untyped,
        'oracle_disagreements': unequal, 'untyped_consistency_cells': inconsistencies,
        'uncovered_cause_branches_above_one_percent': uncovered, 'rejected_cause_table': table,
        'consistency_counts': dict(Counter(r['v2']['consistency'] for r in measured)),
        'memory_cells': len(peaks), 'memory_p99_bytes': float(np.percentile(peaks,99)),
        'memory_max_bytes': max(peaks), 'mean_complete_cell_seconds': float(np.mean(walls)),
        'total_cell_seconds': sum(walls), 'split': 'train',
        'interval_note': 'Wilson 95% per requested rejected-cell denominator; descriptive binomial intervals do not adjust within-task correlation; p-val=n/a.'}
    with (root/'receipt.json').open('x') as handle:
        json.dump(result,handle,indent=2);handle.write('\n')
    return result


if __name__ == '__main__':
    r=summarize(sys.argv[1]);print(json.dumps({k:r[k] for k in ('stage','status','declared','measured','oracle_matches')}))
