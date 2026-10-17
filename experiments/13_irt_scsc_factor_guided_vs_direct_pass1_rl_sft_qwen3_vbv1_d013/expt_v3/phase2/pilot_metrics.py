"""Measure both paired pilot seeds and apply the inherited A6 feasibility gate to B seed 1301."""
from __future__ import annotations

from decimal import Decimal
import math


def t5(rows, *, horizon):
    """Keep the inherited gating seed; seed 1302 is a paired replication, never a selection opportunity."""
    if horizon not in (30, 60):
        raise ValueError('only the frozen 30/60-update horizons are permitted')
    table = {}
    for row in rows:
        key = (row['seed'], row['update'])
        if (key in table or row['seed'] not in (1301, 1302) or row['arm'] != 'B'
                or row['split'] != 'train' or type(row['update']) is not int
                or not 1 <= row['update'] <= horizon or len(row['rewards']) != 256):
            raise ValueError('complete paired B train opportunities required')
        if any(v is not None and (type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1)
               for v in row['rewards']):
            raise ValueError('invalid factored reward')
        table[key] = row['rewards']
    if set(table) != {(seed, i) for seed in (1301, 1302) for i in range(1, horizon + 1)}:
        raise ValueError('missing paired pilot opportunity')

    def window(seed, updates):
        values = [v for i in updates for v in table[seed, i]]
        total = sum((Decimal(str(v)) for v in values if v is not None), Decimal(0))
        missing = sum(v is None for v in values)
        n = Decimal(len(values))
        return (total / n, (total + missing) / n), {'declared': len(values),
            'measured': len(values) - missing, 'reward_sum': float(total),
            'mean_bounds': [float(total / n), float((total + missing) / n)]}

    seeds = {}
    for seed in (1301, 1302):
        initial, first = window(seed, range(1, 11))
        final, last = window(seed, range(horizon - 9, horizon + 1))
        lo, hi = final[0] - initial[1], final[1] - initial[0]
        status = ('PASS' if lo >= Decimal('.02') else 'EXTEND_TO_60' if horizon == 30
                  else 'FAIL' if hi < Decimal('.02') else 'INCONCLUSIVE')
        seeds[str(seed)] = {'initial': first, 'final': last, 'status': status,
                            'improvement_bounds': [float(lo), float(hi)]}
    return {'condition': 'v3-A7', 'gate': 'T5', 'arm': 'B', 'horizon': horizon,
            'status': seeds['1301']['status'], 'gating_seed': 1301, 'paired_seeds': [1301, 1302],
            'seeds': seeds, 'threshold': .02, 'extension_used': horizon == 60,
            'threshold_source': 'A6 rule 3 and inherited a6_t5_measurement.py gating seed',
            'interpretation': 'feasibility selection, not evidence of held-out efficacy; p-val=n/a',
            'missing_outcomes_assigned_zero': False}
