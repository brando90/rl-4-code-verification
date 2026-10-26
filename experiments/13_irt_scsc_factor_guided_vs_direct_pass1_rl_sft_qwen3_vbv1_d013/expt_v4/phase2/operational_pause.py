"""TLDR: Read the admission-bound single-pause decision and reject every other trajectory."""
import json
from pathlib import Path

RECORD='OPERATIONAL_V4-A3_single_pause_10-21-2026.md'
CONFIG=Path(__file__).with_suffix('.json')


def selection(path=CONFIG,trajectory=None):
    config=json.loads(Path(path).read_text())
    if config.get('record')!=RECORD or config.get('mode')!='single':
        raise ValueError('single-pause operational record required')
    # This is the frozen decision, not a user-configurable expansion of pause authority.
    if config.get('trajectories')!=['A_1302']:
        raise ValueError('operational record designates only A_1302; never B_1301')
    if trajectory is not None and trajectory not in config['trajectories']:
        raise ValueError('non-designated trajectory refused: '+trajectory)
    return tuple(config['trajectories'])


def admitted_config(admission):
    return Path(admission['root'])/'phase2/operational_pause.json'
