"""Freeze the fixed train monitor's paired responses and current C weights before any snapshot generation."""
from __future__ import annotations

from a6_monitor_points import valid_checkpoint

import hashlib
from pathlib import Path
import numpy as np

from arm_rewards import marginal_arrays,gradient_weights,family_reward,weighted_reward
from training_checkpoint import write_new,digest


def prepare(cohort,prompts,train_ids,*,arm,run_seed,update,models=None,abilities=None):
    if not valid_checkpoint(arm,run_seed,update):raise ValueError('undeclared pilot monitor snapshot')
    allowed=set(train_ids);tasks=sorted(allowed);cells=cohort['cells']
    if (cohort.get('condition')!='v2-S2' or len(cells)!=32 or len({c['audit_id'] for c in cells})!=32
            or len({c['task_id'] for c in cells})!=32 or len({c['group_id'] for c in cells})!=32):
        raise ValueError('frozen 32-group monitor cohort required')
    if set(prompts)!=allowed:raise ValueError('monitor templates must retain the complete train allowlist')
    weights=None
    if arm=='C':
        theta=np.asarray(abilities,dtype=float)
        if theta.shape!=(3,) or not np.isfinite(theta).all():raise ValueError('current pre-response C abilities required')
        arrays=marginal_arrays(models,tasks);weights=gradient_weights(arrays,theta)
    rows=[]
    for index,entry in enumerate(cells):
        task=entry['task_id']
        if entry['split']!='train' or task not in allowed:raise ValueError('monitor cohort crossed the train split')
        template=prompts[task]
        if template['task_id']!=task or template['split']!='train':raise ValueError('monitor prompt identity changed')
        # Separate from all learning random streams; the same fixed task uses
        # the same monitoring randomness at each own-run checkpoint and arm.
        payload=f'rl4cv-e13-v2-S2-pilot-monitor-1302271/{run_seed}/{task}/0'.encode()
        seed=int.from_bytes(hashlib.sha256(payload).digest()[:8],'big')%(2**63)
        row={**template,'cell_id':f'v2-S2-monitor/{arm}/{run_seed}/{update}/{entry["audit_id"]}/0',
             'condition':'v2-S2','audit_id':entry['audit_id'],'group_id':entry['group_id'],
             'sample':0,'seed':seed,'arm':arm,'run_seed':run_seed,'update':update,'group_index':index,
             'weights':weights[tasks.index(task)].tolist() if arm=='C' else None,
             'abilities':theta.tolist() if arm=='C' else None}
        rows.append(row)
    return {'condition':'v2-S2','stage':'PILOT_MONITOR_SNAPSHOT','arm':arm,'run_seed':run_seed,'update':update,
            'declared':32,'split':'train','cells':rows,'frozen_before_generation':True,
            'sampling':'unchanged training sampler, one separate diagnostic response per fixed audit task',
            'seed_rule':'SHA256 domain 1302271, run seed, task and sample 0; paired across arms and snapshots',
            'C_weight_timing':'current abilities at the completed checkpoint, before the next ten-update refit',
            'learning_rollout_tokens':0,'model_calls':0}


def reward_rows(snapshot,scored):
    """Join current monitor strict/components to the weights fixed before those responses."""
    if not snapshot.get('frozen_before_generation') or snapshot.get('declared')!=32:raise ValueError('pre-response snapshot required')
    cells=snapshot['cells'];table={r['cell_id']:r for r in scored}
    if len(table)!=len(scored) or set(table)!={c['cell_id'] for c in cells}:raise ValueError('monitor score denominator changed')
    rows=[]
    for cell in cells:
        measured=table[cell['cell_id']]
        if any(measured.get(k)!=cell[k] for k in ('task_id','sample','split','arm','run_seed','update','group_index')):
            raise ValueError('monitor scored identity changed')
        if measured.get('cleanup_verified') is not True:raise ValueError('monitor scorer cleanup unresolved')
        value=None;theorems=None
        if measured['status']=='measured':
            strict=measured['strict']
            if type(strict) not in (int,bool) or strict not in (0,1):raise ValueError('invalid monitor strict label')
            value=family_reward(measured,strict) if snapshot['arm']=='B' else weighted_reward(measured,cell['weights'],strict)
            theorems=measured['p']['denominator']
        rows.append({**{k:cell[k] for k in ('cell_id','audit_id','task_id','group_id','split','arm','run_seed','update')},
                     'reward':value,'theorem_count':theorems,'strict':measured.get('strict') if value is not None else None,
                     'formal_specification_coverage':None,'hidden_test_coverage':None})
    return rows
