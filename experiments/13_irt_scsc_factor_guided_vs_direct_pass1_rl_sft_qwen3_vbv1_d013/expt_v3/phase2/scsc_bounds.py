"""Determine composite-score zeros from frozen local factors; retain unknown coverage as bounds."""
from __future__ import annotations

import json
import math

from cohort import digest


def bounds(tests, proofs, coverage=None):
    for value in (tests, proofs, coverage):
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError('SCSC factor outside [0,1]')
    known = [v for v in (tests, proofs, coverage) if v is not None]
    upper = math.prod(known) ** (1 / 3)
    lower = upper if len(known) == 3 else 0.
    return [lower, upper]


def attach(scores, root):
    rows = []
    for index, row in enumerate(scores['rows']):
        factors = {'IC_tests': None, 'IC_proofs': None, 'FSC': None}
        evidence = None
        if row['status'] == 'measured':
            attempt = root / f"{index:05d}/attempt_{row['attempts']}"
            oracle_path = attempt / 'evidence/oracle/oracle.json'
            mechanical_path = attempt / 'evidence/oracle/ladder/train/scored/scored_fixture_g8.jsonl'
            oracle = json.loads(oracle_path.read_text())
            mechanical = json.loads(mechanical_path.read_text())
            if (oracle['source_sha256'] != row['source_sha256']
                    or digest(attempt / 'solution.lean') != row['source_sha256']
                    or oracle['compile'] is not row['compile'] or mechanical['status'] != 'scored'):
                raise ValueError('local composite-score evidence differs from official strict receipt')
            factors.update(IC_tests=mechanical['IC_tests'], IC_proofs=mechanical['IC_proofs'])
            # This is the inherited compile-gated coverage rule, not a judge prediction.
            if oracle['compile'] is False: factors['FSC'] = 0.
            evidence = {'oracle_sha256': digest(oracle_path), 'mechanical_sha256': digest(mechanical_path)}
        interval = bounds(factors['IC_tests'], factors['IC_proofs'], factors['FSC'])
        rows.append({**row, 'official_factors': factors, 'official_SCSC_bounds': interval,
                     'official_SCSC': interval[0] if interval[0] == interval[1] else None,
                     'official_factor_evidence': evidence})
    n = len(rows)
    interval = [sum(r['official_SCSC_bounds'][i] for r in rows) / n for i in (0, 1)]
    return {**scores, 'rows': rows, 'official_SCSC_summary': {
        'declared': n, 'known_composites': sum(r['official_SCSC'] is not None for r in rows),
        'coverage_measured_or_compile_gated': sum(r['official_factors']['FSC'] is not None for r in rows),
        'mean_bounds': interval, 'mean': interval[0] if interval[0] == interval[1] else None,
        'rule': 'unchanged cube-root product; known zero factor determines zero; every unknown factor ranges over [0,1]',
        'unknown_coverage_imputed': False, 'api_spend_usd': 0}}
