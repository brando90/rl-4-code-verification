"""TLDR: Select G with paired whole-task bootstraps and retain the deterministic T2 subset."""
from math import comb
import numpy as np


def select_tasks(train_ids):
    ids = sorted(train_ids)
    if len(ids) != 539 or len(set(ids)) != 539:
        raise ValueError('complete 539-task train manifest required')
    return np.random.default_rng(1304001).choice(ids, size=32, replace=False).tolist()


def qhat(successes, group_size):
    if type(successes) is not int or not 0 <= successes <= 32 or group_size not in (8, 16):
        raise ValueError('invalid G0 counts')
    choose = lambda n: comb(n, group_size) if n >= group_size else 0
    return 1 - (choose(successes) + choose(32-successes)) / comb(32, group_size)


def validate_batch(rows, task_order):
    if len(task_order) != 32 or len(set(task_order)) != 32 or len(rows) != 1024:
        raise ValueError('G0 requires 32 declared tasks x 32 slots')
    table = {}
    for r in rows:
        key = (r['task_id'], r['sample_idx'])
        if key in table or r.get('split') != 'train':
            raise ValueError('duplicate or held-out G0 slot')
        if r['strict'] not in (None, 0, 1) or (r['factored_reward'] is not None and
                not 0 <= r['factored_reward'] <= 1):
            raise ValueError('invalid G0 reward')
        table[key] = r
    if set(table) != {(t, s) for t in task_order for s in range(32)}:
        raise ValueError('G0 cell inventory changed')
    return table


def choose_group_size(rows, task_order):
    table = validate_batch(rows, task_order)
    # Identical whole-task resamples for both completions and both statistics.
    draws = np.random.default_rng(1304002).integers(0, 32, size=(10000, 32))
    completions = []
    for missing_value in (0, 1):
        successes = [sum(table[t, s]['strict'] if table[t, s]['strict'] is not None else missing_value
                         for s in range(32)) for t in task_order]
        q8 = np.array([qhat(int(s), 8) for s in successes])
        q16 = np.array([qhat(int(s), 16) for s in successes])
        differences = np.column_stack((256 * (q16 - 1.2*q8), 16*q16 - 3))
        bounds = np.quantile(differences[draws].mean(1), .05, axis=0, method='linear')
        completions.append({'missing_as': missing_value, 'N8': float(256*q8.mean()),
                            'N16': float(256*q16.mean()), 'M8': float(32*q8.mean()),
                            'M16': float(16*q16.mean()), 'lower95_N16_minus_1p2_N8': float(bounds[0]),
                            'lower95_M16_minus_3': float(bounds[1]), 'choose16': bool((bounds > 0).all())})
    return {'gate': 'V4-G0', 'G': 16 if all(c['choose16'] for c in completions) else 8,
            'completions': completions, 'draws': 10000, 'bootstrap_seed': 1304002,
            'unit': 'paired whole task', 'missing': sum(r['strict'] is None for r in rows)}


def t2_subset(rows, task_order, group_size):
    if group_size not in (8, 16):
        raise ValueError('unregistered group size')
    table = validate_batch(rows, task_order)
    return [[table[t, s] for s in range(group_size)] for t in task_order[:256//group_size]]
