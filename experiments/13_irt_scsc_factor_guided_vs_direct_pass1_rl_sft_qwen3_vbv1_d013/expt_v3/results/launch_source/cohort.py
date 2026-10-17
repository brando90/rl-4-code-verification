"""Assemble the immutable v2 cohort with v3 factored rewards and explicit missing groups."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

SOURCE = Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/phase2/technical/T2/attempt_3')
SCORE_SHA256 = 'e9f4e62094e766663acd8e7f29b343e6742dcc41899cccc88a14cd08813dce45'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def factored_groups(groups, scores):
    table = {row['cell_id']: row for row in scores}
    ids = [r['cell_id'] for g in groups for r in g['rows']]
    if len(table) != len(scores) or len(set(ids)) != len(ids) or set(ids) != set(table):
        raise ValueError('score/generation identities are not a bijection')
    result = copy.deepcopy(groups)
    active = usable = nonzero = measured = positive = 0
    summary = []
    for group in result:
        if len(group['rows']) != 8:
            raise ValueError('eight retained slots required')
        for slot, row in enumerate(group['rows']):
            score = table[row['cell_id']]
            if row['slot'] != slot or row['split'] != 'train':
                raise ValueError('nontrain or reordered slot')
            for key in ('task_id', 'split', 'sample', 'group_index', 'arm', 'run_seed', 'update'):
                if row[key] != score[key]:
                    raise ValueError('scoring identity changed: ' + key)
            if score['status'] != 'measured':
                value = None
            else:
                value = score.get('factored_reward')
                if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError('invalid measured factored reward')
                measured += 1
                positive += int(value > 0)
            row['reward'] = value
            row['score_status'] = score['status']
        values = [r['reward'] for r in group['rows']]
        complete = all(v is not None for v in values)
        varied = complete and len(set(values)) > 1
        slots = sum(v != sum(values) / 8 for v in values) if varied else 0
        usable += int(complete)
        active += int(varied)
        nonzero += slots
        summary.append({'group_index': group['group_index'], 'task_id': group['task_id'],
                        'rewards': values, 'complete': complete, 'active': bool(varied),
                        'nonzero_advantage_slots': slots})
    return result, {'declared_slots': len(ids), 'measured_rewards': measured,
                    'positive_rewards': positive, 'usable_groups': usable,
                    'active_groups': active, 'nonzero_advantage_slots': nonzero,
                    'groups': summary}


def retained():
    score_path = SOURCE / 'score/cells/result.json'
    if digest(score_path) != SCORE_SHA256:
        raise ValueError('frozen scoring receipt changed')
    groups = json.loads((SOURCE / 'score/groups.json').read_text())
    cells = json.loads((SOURCE / 'generate_update/output/cells.json').read_text())
    rows = [row for group in groups for row in group['rows']]
    if len(cells) != 256 or len(rows) != 256:
        raise ValueError('the exact 256-rollout cohort is required')
    bindings = []
    for index, (cell, row) in enumerate(zip(cells, rows)):
        path = SOURCE / f'generate_update/output/{index:05d}.generation.json'
        generation = json.loads(path.read_text())
        if row['cell_id'] != cell['cell_id'] or any(row[k] != v for k, v in generation.items()):
            raise ValueError('retained group differs from original generation')
        bindings.append({'path': str(path), 'sha256': digest(path)})
    result, summary = factored_groups(groups, json.loads(score_path.read_text())['rows'])
    expected = {'declared_slots': 256, 'measured_rewards': 255, 'positive_rewards': 21,
                'usable_groups': 31, 'active_groups': 14, 'nonzero_advantage_slots': 112}
    if any(summary[k] != v for k, v in expected.items()):
        raise ValueError('retained signal-density finding did not reproduce')
    summary.update(source_score_sha256=SCORE_SHA256, generation_bindings=bindings,
                   source_groups_sha256=digest(SOURCE / 'score/groups.json'),
                   api_spend_usd=0, reward='factored_reward')
    return result, summary
