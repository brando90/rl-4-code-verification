"""Freeze task selection, C weights and independent placebo draws before each complete rollout group."""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
from scipy.special import expit

HERE=Path(__file__).resolve().parent
for directory in (HERE.parent/'prediction',HERE.parent/'reproduction'):
    if str(directory) not in sys.path:sys.path.insert(0,str(directory))
from marginal_v2 import gradient_weights,weighted_reward
from cell_worker import family_reward
from rl4cv.e13 import placebo_reward
from schedule import uniform_task,information_task,rollout_seed


def marginal_arrays(models,tasks):
    result={}
    for component in ('d','t','p'):
        model=models[component];a=np.asarray(model['a'],float);b=np.asarray(model['b'],float)
        if a.shape!=(len(tasks),) or b.shape!=a.shape or not np.isfinite(a+b).all() or np.any(a<.1) or np.any(a>5.):
            raise ValueError('frozen marginal item dimensions or bounds changed')
        result[component]={**model,'a':a,'b':b}
    return result


def plan_group(arm,*,seed,update,group_index,tasks,models=None,abilities=None,placebo_distribution=None):
    """This interface accepts no response, scorer outcome, length or held-out data."""
    tasks=list(tasks)
    if tasks!=sorted(set(tasks)) or not tasks:raise ValueError('fixed sorted train item order is required')
    if arm not in ('A','B','C','P') or type(update) is not int or update<1:
        raise ValueError('unregistered arm or scheduled update')
    weights=None;information=None
    if arm=='C':
        arrays=marginal_arrays(models,tasks);theta=np.asarray(abilities,float)
        if theta.shape!=(3,) or not np.isfinite(theta).all():raise ValueError('three fixed pre-group abilities required')
        a=np.column_stack([arrays[k]['a'] for k in ('d','t','p')]);b=np.column_stack([arrays[k]['b'] for k in ('d','t','p')])
        q=expit(a*(theta[None,:]-b));information=dict(zip(tasks,np.sum(a*a*q*(1-q),axis=1).tolist()))
        task=information_task(tasks,information,seed,group_index)
        weights=gradient_weights(arrays,theta)[tasks.index(task)].tolist()
    else:task=uniform_task(tasks,seed,group_index)
    draws=None
    if arm=='P':
        draws=[placebo_reward(placebo_distribution,seed=seed,update=update,group=group_index,slot=s) for s in range(8)]
    cells=[{'cell_id':f'v2-S2/{arm}/{seed}/{update}/{group_index}/{s}','task_id':task,'split':'train','sample':s,
            'seed':rollout_seed(seed,group_index,s)} for s in range(8)]
    return {'condition':'v2-S2','arm':arm,'run_seed':seed,'update':update,'group_index':group_index,
            'task_id':task,'weights':weights,'abilities':list(abilities) if arm=='C' else None,
            'placebo_draws':draws,'cells':cells,'frozen_before_generation':True}


def rewards(plan,rows):
    """Use exact frozen reward functions; an independent P draw never depends on scorer availability."""
    if plan.get('condition')!='v2-S2' or not plan.get('frozen_before_generation') or len(rows)!=8:
        raise ValueError('a complete predeclared S2 group is required')
    expected=plan['cells'];table={r['cell_id']:r for r in rows}
    if len(table)!=8 or set(table)!={c['cell_id'] for c in expected}:raise ValueError('group identity changed')
    result=[]
    for slot,cell in enumerate(expected):
        row=table[cell['cell_id']]
        if row['split']!='train' or row['task_id']!=plan['task_id']:raise ValueError('group task or split changed')
        if plan['arm']=='P':
            # Its reward was observed before generation and is independent of the
            # present strict/component diagnostic, including a missing diagnostic.
            value=plan['placebo_draws'][slot]
        elif row['status']!='measured':value=None
        else:
            strict=row['strict']
            if strict not in (0,1):raise ValueError('invalid strict oracle value')
            if plan['arm']=='A':value=float(strict)
            elif plan['arm']=='B':value=family_reward(row,strict)
            elif plan['arm']=='C':value=weighted_reward(row,plan['weights'],strict)
            else:raise ValueError('unregistered reward arm')
        result.append(value)
    return result
