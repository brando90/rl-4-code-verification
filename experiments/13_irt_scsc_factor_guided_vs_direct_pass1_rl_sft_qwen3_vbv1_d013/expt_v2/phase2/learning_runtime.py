"""Execute one bound learning stage using the same admitted S2 policy and complete-group generation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
from technical_runtime import verify, bound, run as technical_run
from learning_generation import generate

STAGES = ('preflight', 'generate', 'update', 'export')


def run(config, stage):
    if stage not in STAGES: raise ValueError('unregistered learning stage')
    for name in ('learning_runtime.py', 'learning_generation.py', 'schedule.py'):
        bound(config, HERE/name)
    if config.get('learning_phase') not in ('pilot', 'main') or config.get('arm') not in ('A', 'B', 'C', 'P'):
        raise ValueError('learning condition and arm must be explicit')
    verify(config, stage)
    if stage == 'generate':
        cells = json.loads(bound(config, config['cells_path']).read_text())
        if any(c['arm'] != config['arm'] or c['run_seed'] != config['run_seed'] or c['update'] != config['update'] for c in cells):
            raise ValueError('generation prefix belongs to another learning opportunity')
        state = None
        if config['learning_phase'] == 'main':
            state = json.loads(bound(config, config['budget_state']).read_text())
        elif config.get('budget_state') is not None:
            raise ValueError('fixed-update pilot has no token boundary')
        return generate(config, cells, root=config['stage_root'], budget_state=state)
    if stage == 'update':
        groups = json.loads(bound(config, config['groups_path']).read_text())
        # The group producer binds identities; the installed trainer still
        # normalizes the actual complete groups, including a boundary batch.
        if not 1 <= len(groups) <= 32: raise ValueError('learning update has no complete prompt groups')
    return technical_run(config, stage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--stage', choices=STAGES, required=True)
    args = parser.parse_args(); run(json.loads(args.config.read_text()), args.stage)
