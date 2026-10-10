#!/usr/bin/env python3
"""Verify existing phase-0 receipts for handoff without rescoring historical sources."""
import argparse
import hashlib
import json
from pathlib import Path

from rl4cv.forecast import verify_forecast


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--controls', type=Path, required=True)
    a = ap.parse_args()
    receipt_path = a.controls / 'result_reconciled.json'
    result = json.loads(receipt_path.read_text())
    require(result['status'] == 'FIXED' and result['fixtures_passed'] == result['fixtures_total'] == 15,
            'authored controls unresolved')
    require(sha(a.controls / 'result.json') == result['original_receipt_sha256'], 'original receipt changed')
    require(verify_forecast(a.controls / 'locks/L0.json'), 'L0 hash changed')
    require(sha(a.controls / 'locks/L0.json') == result['L0_sha256'], 'L0 identity mismatch')
    manifest = a.controls / 'validation_source_manifest.jsonl'
    require(sha(manifest) == result['inventory']['cell_manifest_sha256'], 'manifest changed')
    for row in result['fixture_results']:
        require(sha(Path(row['evidence_path'])) == row['evidence_sha256'], 'fixture evidence changed')
    require(result['inventory']['source_hash_matches'] == 20520, 'source inventory incomplete')
    print(json.dumps({'status': 'READY_FOR_DECLARATION_ADAPTER', 'verified_receipt_sha256': sha(receipt_path),
                      'source_manifest': str(manifest), 'source_manifest_sha256': sha(manifest),
                      'available_validation_cells': 20520, 'declared_parent_cells': 25920,
                      'historical_reproduction_passed': False, 'training_admitted': False,
                      'next': 'Implement declaration adapter and sealed audit, then freeze L1 before historical factors.'}, sort_keys=True))


if __name__ == '__main__':
    main()
