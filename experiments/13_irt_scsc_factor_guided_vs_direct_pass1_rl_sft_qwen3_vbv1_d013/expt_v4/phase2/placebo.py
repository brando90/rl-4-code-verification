"""TLDR: Freeze G0's measured B distribution and precompute domain-separated placebo draws."""
import hashlib
import math
import numpy as np
from common import object_digest, write_new
from group_selection import validate_batch


def reference(rows):
    if len(rows) != 1024 or len({(r['task_id'],r['sample_idx']) for r in rows}) != 1024:
        raise ValueError('complete G0 slot inventory required')
    validate_batch(rows, sorted({r['task_id'] for r in rows}))
    values = [float(r['factored_reward']) for r in rows if r['factored_reward'] is not None]
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in values):
        raise ValueError('invalid B reference reward')
    values.sort()
    # Numeric sort, one 17-significant-digit decimal per line, final LF included.
    payload = ''.join(format(v, '.17g')+'\n' for v in values).encode('ascii')
    return {'status': 'ADMITTED' if len(values) >= math.ceil(.9*1024) else 'EXCLUDED',
            'declared': 1024, 'measured': len(values), 'missing': 1024-len(values),
            'values': values, 'distribution_sha256': hashlib.sha256(payload).hexdigest(),
            'encoding': 'numeric ascending; .17g ASCII; one per line including final LF'}


def draw(ref, seed, update, slot):
    if type(seed) is not int or type(update) is not int or type(slot) is not int or ref['status'] != 'ADMITTED' or seed not in (1301,1302,13011,13012,13013) or update < 1 or not 0 <= slot < 256:
        raise ValueError('unadmitted placebo draw')
    key = f'e13v4-placebo\0{seed}\0{update}\0{slot}'.encode('ascii')
    # SHA-256 keyed counter with rejection removes modulo bias exactly.
    n = len(ref['values']); limit = 2**256 - (2**256 % n)
    counter = 0
    while True:
        number = int.from_bytes(hashlib.sha256(hashlib.sha256(key).digest()+counter.to_bytes(8,'big')).digest(), 'big')
        if number < limit: return ref['values'][number % n]
        counter += 1


def precompute(ref, seeds, updates, output, *, first_response_exists):
    if first_response_exists:
        raise ValueError('placebo stream must be bound before first P response')
    expected = hashlib.sha256(''.join(format(v,'.17g')+'\n' for v in sorted(ref['values'])).encode('ascii')).hexdigest()
    if ref['values'] != sorted(ref['values']) or expected != ref['distribution_sha256']:
        raise ValueError('reference distribution changed')
    if len(set(seeds)) != len(seeds) or type(updates) is not int or updates < 1:
        raise ValueError('invalid placebo schedule')
    draws = {f'{seed}/{update}': [draw(ref,seed,update,slot) for slot in range(256)]
             for seed in seeds for update in range(1,updates+1)}
    result = {'distribution_sha256': expected, 'draws': draws, 'draws_sha256': object_digest(draws),
              'bound_before_first_response': True}
    write_new(output, result)
    return result


def density(groups):
    if not groups or len({len(g) for g in groups}) != 1:
        raise ValueError('equal declared groups required')
    measured = [v for g in groups for v in g if v is not None]
    complete = [g for g in groups if all(v is not None for v in g)]
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in measured):
        raise ValueError('invalid reward')
    variances = [float(np.var(g, ddof=0)) for g in complete]
    return {'declared_slots': sum(map(len,groups)), 'measured_slots': len(measured),
            'mean_reward': float(np.mean(measured)) if measured else None,
            'declared_groups': len(groups), 'complete_groups': len(complete),
            'nonzero_variance_group_fraction': sum(v>0 for v in variances)/len(variances) if variances else None,
            'mean_within_group_variance': float(np.mean(variances)) if variances else None,
            'incomplete_groups': len(groups)-len(complete)}


def density_report(b_groups, p_groups):
    return {'B': density(b_groups), 'P': density(p_groups),
            'interpretation': 'P matches only start-policy marginal B reward density'}
