"""Freeze paired train-only prompt streams and independent placebo rewards before pilot generation."""
from __future__ import annotations

import json
from pathlib import Path

from technical import SOURCE, V3
from cohort import digest
from arm_rewards import plan_group
from training_checkpoint import write_new

PREPARATION = SOURCE.parents[2] / 'technical_preparation'
PLACEBO = SOURCE.parents[3] / 'phase1/calibration_S2/placebo_distribution.json'
PLACEBO_SHA256 = 'e26bcd6da4c670e3708a9671046dc686d8c81d9577ed16d357e03f0cf93e095b'


def prefix(arm, seed, update, templates, placebo):
    if arm not in ('A', 'B', 'P') or seed not in (1301, 1302) or not 1 <= update <= 60:
        raise ValueError('undeclared pilot condition')
    if arm != 'B' and update > 30:
        raise ValueError('only B has a prospective extension')
    if len(templates) != 539 or any(v['split'] != 'train' or k != v['task_id'] for k, v in templates.items()):
        raise ValueError('exact train prompt pool required')
    plans, cells = [], []
    for group in range(32 * (update - 1), 32 * update):
        plan = plan_group(arm, seed=seed, update=update, group_index=group,
                          tasks=sorted(templates), placebo_distribution=placebo if arm == 'P' else None)
        plans.append(plan)
        for cell in plan['cells']:
            cells.append({**templates[cell['task_id']], **cell, 'arm': arm, 'run_seed': seed,
                          'update': update, 'group_index': group})
    return plans, cells


def load_inputs():
    if digest(PLACEBO) != PLACEBO_SHA256:
        raise ValueError('frozen train-only placebo distribution changed')
    path = PREPARATION / 'inputs_v1/train_prompts.json'
    if digest(path) != '82524162ee09e0b1b2494a6f1c0bb85daa0243a43d76d1bf0fe777539c7221fe':
        raise ValueError('frozen training prompt bytes changed')
    templates = json.loads(path.read_text())
    allowed = set((SOURCE.parents[3] / 'phase1/train_ids.txt').read_text().splitlines())
    if set(templates) != allowed:
        raise ValueError('training prompt pool differs from original D-013 allowlist')
    placebo = json.loads(PLACEBO.read_text())
    if placebo['measured'] != len(placebo['values']) or placebo['measured'] != 4302:
        raise ValueError('frozen placebo sample count changed')
    return templates, placebo['values']
