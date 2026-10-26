"""Run hash-bound local NeMo/vLLM primitives with v3 resource ownership and unchanged numerics."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
V2 = HERE.parent.parent / 'expt_v2'
sys.path.extend([str(V2 / 'phase2'), str(V2 / 'phase1')])
from cohort import digest
from device_guard import check, install
install()
from training_checkpoint import export, write_new


def run(config):
    for binding in config['bindings']:
        if digest(binding['path']) != binding['sha256']:
            raise ValueError('changed runtime input: ' + binding['path'])
    for package, version in config['runtime_versions'].items():
        if importlib.metadata.version(package) != version:
            raise ValueError('runtime version mismatch: ' + package)
    stage = config['stage']
    check(config)
    if stage == 'update':
        from trainer_core import policy_session, update
        # Restore v2's exact before-update state, including empty optimizer and RNG.
        with policy_session(config, checkpoint=config.get('checkpoint')) as (policy, tokenizer):
            return update(policy, json.loads(Path(config['groups_path']).read_text()),
                          pad_token_id=tokenizer.pad_token_id,
                          terminal_token_ids=config['terminal_token_ids'],
                          loss_config=config['loss_config'], root=config['stage_root'],
                          provenance=config['provenance'], lease_check=lambda: check(config))
    if stage == 'export':
        return export(config['checkpoint'], config['stage_root'],
                      model_config=config['initial_model'], tokenizer=config['tokenizer'])
    if stage == 'generate':
        from generation_core import generate
        return generate(config, json.loads(Path(config['cells_path']).read_text()), root=config['stage_root'])
    if stage == 'probabilities':
        from technical_runtime import probabilities
        return probabilities(config, json.loads(Path(config['cells_path']).read_text()))
    if stage == 'replay':
        from trainer_core import policy_session, replay_saved
        with policy_session(config) as (policy, _):
            return replay_saved(policy, config['source_update'], root=config['stage_root'],
                                loss_config=config['loss_config'], lease_check=lambda: check(config))
    if stage == 'evaluation_generate':
        from evaluation_generation import generate
        manifest = json.loads(Path(config['manifest']).read_text())
        return generate(config, manifest, list(range(8)), root=config['stage_root'])
    raise ValueError('unknown stage')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    run(config)
