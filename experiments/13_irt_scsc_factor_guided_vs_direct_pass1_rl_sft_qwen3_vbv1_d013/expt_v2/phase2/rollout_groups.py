"""Join declared rollout and scorer receipts into complete reward groups without replacement or missing-as-zero."""
from __future__ import annotations

from collections import defaultdict

from arm_rewards import rewards
from generation_core import validate_cells
from training_data import validate_groups
from panel import validate_generation

IDENTITY = ('cell_id', 'task_id', 'split', 'sample', 'seed', 'group_index', 'arm', 'run_seed', 'update')


def index_rows(rows, cells, kind, *, allow_missing=False):
    expected = {c['cell_id']: c for c in cells}
    table = {}
    for row in rows:
        key = row['cell_id']
        if key not in expected or key in table:
            raise ValueError(kind+' contains an unknown or duplicate slot')
        # Scorers do not repeat rollout RNG seeds; generation must preserve them.
        fields = IDENTITY if kind == 'generation' else tuple(k for k in IDENTITY if k != 'seed')
        if any(row.get(k) != expected[key].get(k) for k in fields):
            raise ValueError(kind+' identity differs from the declared group')
        table[key] = row
    if not allow_missing and set(table) != set(expected):
        raise ValueError(kind+' does not account for every declared slot')
    return table


def assemble(cells, generations, scores, *, train_ids, plans=None, technical=False):
    """All generations are required; unmeasured scorer receipts stay explicit reward None."""
    validate_cells(cells, train_ids)
    if len(cells) % 8:
        raise ValueError('only complete eight-response groups may enter an update')
    generated = index_rows(generations, cells, 'generation')
    scored = index_rows(scores, cells, 'score')
    for cell in cells:
        validate_generation(cell, generated[cell['cell_id']],
                            {'max_model_len': 15945, 'terminal_token_ids': [151643, 151645]})
    buckets = defaultdict(list)
    run = {(c['arm'], c['run_seed'], c['update']) for c in cells}
    if len(run) != 1:
        raise ValueError('one arm/seed/update per complete batch is required')
    arm, seed, update = next(iter(run))
    if type(seed) is not int or type(update) is not int or update < 1:
        raise ValueError('invalid run identity')
    if technical != (arm == 'technical'):
        raise ValueError('technical and learning reward paths cannot be interchanged')
    for cell in cells: buckets[cell['group_index']].append(cell)
    if technical:
        if plans is not None or len(buckets) != 32:
            raise ValueError('technical update requires exactly 32 declared groups and strict reward')
    else:
        if plans is None or len(plans) != len(buckets):
            raise ValueError('one pre-generation reward plan per group is required')
        plan_map = {p['group_index']: p for p in plans}
        if len(plan_map) != len(plans) or set(plan_map) != set(buckets):
            raise ValueError('reward group-plan identity changed')
    groups = []
    for key in sorted(buckets):
        group = sorted(buckets[key], key=lambda c: c['sample'])
        if len(group) != 8 or [c['sample'] for c in group] != list(range(8)) or len({c['task_id'] for c in group}) != 1:
            raise ValueError('eight slots of the same declared task are required')
        outcomes = [scored[c['cell_id']] for c in group]
        if technical:
            values = []
            for row in outcomes:
                if row['status'] != 'measured': values.append(None)
                elif type(row.get('strict')) not in (bool, int, float) or row['strict'] not in (0, 1):
                    raise ValueError('invalid measured strict reward')
                else: values.append(float(row['strict']))
        else:
            plan = plan_map[key]
            if (plan['arm'], plan['run_seed'], plan['update'], plan['task_id']) != (arm, seed, update, group[0]['task_id']):
                raise ValueError('pre-generation reward plan differs from this run')
            for expected, actual in zip(plan['cells'], group):
                if any(expected[k] != actual[k] for k in ('cell_id', 'task_id', 'split', 'sample', 'seed')):
                    raise ValueError('rollout differs from pre-generation reward plan')
            values = rewards(plan, outcomes)
        rows = [{**generated[c['cell_id']], 'slot': c['sample'], 'reward': value,
                 'score_status': score['status']} for c, value, score in zip(group, values, outcomes)]
        groups.append({'group_index': key, 'task_id': group[0]['task_id'], 'rows': rows})
    validate_groups(groups, terminal_token_ids=[151643, 151645])
    return groups
