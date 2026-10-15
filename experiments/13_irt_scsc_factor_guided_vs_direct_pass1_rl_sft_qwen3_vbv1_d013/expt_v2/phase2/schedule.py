"""Define paired prompt streams and complete-group token boundaries before Phase 2 outcomes."""
from __future__ import annotations

import hashlib
import json
import math
import random

SLOTS=8
GROUPS_PER_UPDATE=32
TOKEN_CAP=8192


def seed_for(domain,*parts):
    payload=json.dumps(['e13v2-S2',domain,*parts],separators=(',',':'),ensure_ascii=False)
    return int.from_bytes(hashlib.sha256(payload.encode()).digest(),'big')


def uniform_task(tasks,seed,group_index):
    """A/B/P consume the same without-replacement epoch by cumulative group index."""
    tasks=sorted(tasks)
    if not tasks or len(tasks)!=len(set(tasks)) or type(group_index) is not int or group_index<0:
        raise ValueError('invalid prompt stream')
    epoch,offset=divmod(group_index,len(tasks))
    random.Random(seed_for('uniform-prompts',seed,epoch)).shuffle(tasks)
    return tasks[offset]


def information_task(tasks,information,seed,group_index):
    """C mixes the paired uniform stream with frozen pre-group train information equally."""
    tasks=sorted(tasks)
    if set(information)!=set(tasks):raise ValueError('information must cover exactly the train allowlist')
    weights=[float(information[t]) for t in tasks]
    if any(not math.isfinite(v) or v<0 for v in weights):raise ValueError('invalid train information')
    uniform=uniform_task(tasks,seed,group_index)
    total=sum(weights)
    if total==0:return uniform
    rng=random.Random(seed_for('information-prompts',seed,group_index))
    if rng.random()<.5:return uniform
    point=rng.random()*total;running=0.
    for task,weight in zip(tasks,weights):
        running+=weight
        if point<running:return task
    return tasks[-1]


def rollout_seed(seed,group_index,slot):
    if type(slot) is not int or not 0<=slot<SLOTS or group_index<0:raise ValueError('invalid rollout slot')
    return seed_for('rollout',seed,group_index,slot)%(2**63)


def pilot_token_budget(lengths):
    """Use every fixed A-pilot slot; missing lengths cannot be imputed or dropped."""
    values=list(lengths)
    if not values or any(type(v) is not int or not 1<=v<=TOKEN_CAP for v in values):
        raise ValueError('all declared A-pilot token lengths are required')
    mean_ceiling=(sum(values)+len(values)-1)//len(values)
    total=25600*mean_ceiling;targets=[total*k//4 for k in (1,2,3,4)]
    return {'pilot_slots':len(values),'pilot_generated_tokens':sum(values),
        'mean_length':sum(values)/len(values),'ceiling_mean_length':mean_ceiling,
        'T':total,'targets':targets,'maximum_group_overshoot':SLOTS*TOKEN_CAP,
        'one_percent_matching_feasible':100*SLOTS*TOKEN_CAP<=targets[0]}


def advance_group(state,lengths):
    """Account for every slot before deciding to stop; never truncate the crossing group."""
    state=dict(state);values=list(lengths)
    if len(values)!=SLOTS or any(type(v) is not int or not 1<=v<=TOKEN_CAP for v in values):
        raise ValueError('one complete eight-response group is required')
    if state['generated_tokens']>=state['next_target'] or state['update_groups']>=GROUPS_PER_UPDATE:
        raise ValueError('update or boundary already closed')
    state['generated_tokens']+=sum(values);state['update_groups']+=1;state['group_index']+=1
    state['boundary_crossed']=state['generated_tokens']>=state['next_target']
    state['update_due']=state['boundary_crossed'] or state['update_groups']==GROUPS_PER_UPDATE
    state['overshoot']=max(0,state['generated_tokens']-state['next_target'])
    return state


def boundary_agreement(target,arm_tokens):
    """Actual paired prefix mismatch, with every arm's crossing group retained."""
    counts=list(arm_tokens.values())
    if target<=0 or len(counts)<2 or any(type(n) is not int or n<target or n-target>SLOTS*TOKEN_CAP for n in counts):
        raise ValueError('incomplete or invalid paired token boundary')
    difference=max(counts)-min(counts)
    return {'target':target,'arm_tokens':dict(arm_tokens),'difference':difference,
            'fraction_of_target':difference/target,'matched':100*difference<=target}
