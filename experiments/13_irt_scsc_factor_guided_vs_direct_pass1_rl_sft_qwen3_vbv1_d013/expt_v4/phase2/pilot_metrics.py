"""TLDR: Apply conservative A/1301 feasibility, extend every pilot arm, and freeze T from both A seeds."""
import math
from fractions import Fraction

TRAJECTORIES = {(arm,seed) for arm in ('A','B','P') for seed in (1301,1302)}


def update_table(rows, arm, seed, end):
    selected = [r for r in rows if r['arm'] == arm and r['seed'] == seed and 1 <= r['update'] <= end]
    if len(selected) != end or {r['update'] for r in selected} != set(range(1,end+1)):
        raise ValueError('all completed updates required')
    for r in selected:
        if r.get('completed') is not True or len(r['strict']) != 256:
            raise ValueError('256 declared slots per completed update required')
        if any(v not in (None,0,1) for v in r['strict']): raise ValueError('invalid strict outcome')
    return {r['update']:r for r in selected}


def t5(rows, horizon=30, seed=1301):
    if horizon not in (30,60) or seed not in (1301,1302): raise ValueError('invalid pilot gate')
    table = update_table(rows, 'A', seed, horizon)
    early = [v for u in range(1,11) for v in table[u]['strict']]
    late = [v for u in range(horizon-9,horizon+1) for v in table[u]['strict']]
    early_count = sum(1 if v is None else v for v in early)
    late_count = sum(0 if v is None else v for v in late)
    gain = Fraction(late_count-early_count,2560)
    passed = gain >= Fraction(2,100)
    return {'gate':'V4-T5','arm':'A','seed':seed,'horizon':horizon,
            'status':'PASS' if passed else 'FAIL','conservative_gain':float(gain),
            'early_successes_upper':early_count,'late_successes_lower':late_count,'window_slots':2560,
            'missing_early':early.count(None),'missing_late':late.count(None),
            'role':'gating' if seed == 1301 else 'replication_only'}


def extension_plan(rows, horizon=30):
    for arm,seed in TRAJECTORIES: update_table(rows,arm,seed,horizon)
    gate=t5(rows,horizon)
    if gate['status']=='PASS': return {'action':'MAIN_RESOURCE_CHECK','horizon':horizon,'gate':gate}
    if horizon==60:return {'action':'STOP_PUBLISH','horizon':60,'gate':gate}
    return {'action':'EXTEND_ALL_SIX','from_update':31,'through_update':60,
            'trajectories':[list(x) for x in sorted(TRAJECTORIES)],'gate':gate}


def token_budget(rows):
    counts=[]
    for seed in (1301,1302):
        for r in update_table(rows,'A',seed,30).values():
            values=r['generated_tokens']
            if len(values)!=256 or any(type(v) is not int or not 0 <= v <= 12288 for v in values):
                raise ValueError('every generated slot requires a bounded token count')
            counts.extend(values)
    total=sum(counts)
    if total==0:raise ValueError('no generated tokens')
    mean_ceiling=(total+len(counts)-1)//len(counts)
    return {'T':25600*mean_ceiling,'generated_tokens':total,'slots':len(counts),
            'mean_generated_tokens':total/len(counts),'ceil_mean':mean_ceiling,
            'source':'A/1301 and A/1302 updates 1-30 only'}


def token_matching(a_tokens,b_tokens,target,group_size):
    if group_size not in (8,16) or target<=0:raise ValueError('invalid token target')
    if min(a_tokens,b_tokens)<target or max(a_tokens,b_tokens)-target>group_size*12288:
        raise ValueError('crossing-group bound violated')
    return abs(a_tokens-b_tokens)*100 <= target
