"""Generate one fixed diagnostic monitor snapshot under the unchanged S2 sampler and current bound checkpoint."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from technical_runtime import bound,verify,run as technical_run
from generation_core import generate
from training_checkpoint import write_new

HERE=Path(__file__).resolve().parent


def validate(snapshot,config):
    if (snapshot.get('condition')!='v2-S2' or snapshot.get('stage')!='PILOT_MONITOR_SNAPSHOT'
            or snapshot.get('declared')!=32 or snapshot.get('frozen_before_generation') is not True):
        raise ValueError('fixed pre-response monitor snapshot required')
    if config['arm'] not in ('B','C') or config['run_seed']!=1301 or config['update'] not in (0,10,20,30):
        raise ValueError('undeclared monitor arm, seed or checkpoint')
    if any(snapshot.get(k)!=config[k] for k in ('arm','run_seed','update')):
        raise ValueError('monitor snapshot belongs to another run or checkpoint')
    cells=snapshot['cells']
    if (len(cells)!=32 or len({c['audit_id'] for c in cells})!=32 or len({c['task_id'] for c in cells})!=32
            or len({c['group_id'] for c in cells})!=32):raise ValueError('monitor population changed')
    for cell in cells:
        if any(cell.get(k)!=config[k] for k in ('arm','run_seed','update')) or cell['split']!='train' or cell['sample']!=0:
            raise ValueError('monitor cell identity changed')
    return cells


def run(config,stage):
    if stage not in ('monitor_preflight','monitor_generate') or config['stage']!=stage:
        raise ValueError('undeclared monitor runtime stage')
    for name in ('monitor_runtime.py','monitor_preparation.py','generation_core.py'):
        bound(config,HERE/name)
    snapshot=json.loads(bound(config,config['snapshot']).read_text());cells=validate(snapshot,config)
    if json.loads(bound(config,config['cells_path']).read_text())!=cells:
        raise ValueError('monitor generator inputs differ from the pre-response freeze')
    base_stage='preflight' if stage=='monitor_preflight' else 'generate'
    runtime={**config,'stage':base_stage};verify(runtime,base_stage)
    if stage=='monitor_preflight':return technical_run(runtime,'preflight')
    result=generate(runtime,cells,root=config['stage_root'])
    receipt={**result,'stage':'PILOT_MONITOR_GENERATION','learning_rollout_tokens':0,'diagnostic_generated_tokens':result['generated_tokens']}
    write_new(Path(config['stage_root'])/'monitor_result.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',required=True,type=Path)
    p.add_argument('--stage',required=True,choices=['monitor_preflight','monitor_generate'])
    a=p.parse_args();print(json.dumps(run(json.loads(a.config.read_text()),a.stage),sort_keys=True))
