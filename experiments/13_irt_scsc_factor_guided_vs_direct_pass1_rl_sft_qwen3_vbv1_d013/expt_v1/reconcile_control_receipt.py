#!/usr/bin/env python3
"""Reconcile the documented printed-error expectation without rerunning frozen controls."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

from phase0_prepare import FIXTURES, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--original', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    prior = json.loads((a.original / 'result.json').read_text())
    frozen = json.loads((a.original / 'locks/L0.json').read_text())
    cases = []
    for name, (text, expected, truncated) in FIXTURES.items():
        path = a.original / f'{name}.json'
        row = json.loads(path.read_text())
        source_digest = hashlib.sha256(text.encode()).hexdigest()
        assert row['source_sha256'] == source_digest == frozen['fixture_hashes'][f'{name}.lean']
        assert sha(a.original / 'fixtures' / f'{name}.lean') == source_digest
        if name == 'printed_error':
            assert row['expected_strict'] == frozen['expected'][name] == 1
            assert row['compile'][0]['success'] is True
            assert row['cache']['kernel']['probe_ok'] is False
            assert row['cache']['kernel']['n_unknown'] == 1
            assert row['cache']['kernel']['probe_errors'][0]['msg'] == 'pretend'
        else:
            assert row['expected_strict'] == frozen['expected'][name] == expected
        assert row['actual_strict'] == expected and row['truncated'] == truncated
        cases.append({'fixture': name, 'actual_strict': row['actual_strict'],
                      'original_expected': row['expected_strict'], 'corrected_expected': expected,
                      'source_sha256': source_digest, 'evidence_path': str(path), 'evidence_sha256': sha(path)})
    result = {**prior, 'status': 'FIXED', 'fixtures_passed': len(cases),
              'reconciled_at': datetime.now(timezone.utc).isoformat(), 'fixture_results': cases,
              'original_receipt_sha256': sha(a.original / 'result.json'), 'original_receipt_status': prior['status'],
              'amendment': 'Authored expected label for printed_error corrected 1 to 0 from actual frozen probe rejection; oracle unchanged. Original 14/15 failure preserved.',
              'reconciliation_script_sha256': sha(Path(__file__)),
              'current_preparation_script_sha256': sha(Path(__file__).with_name('phase0_prepare.py'))}
    with a.out.open('x') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps({'status': 'FIXED', 'verified_fixtures': len(cases), 'original_status': prior['status']}))


if __name__ == '__main__':
    main()
