"""Evaluate complete technical receipts under the unchanged PROTOCOL thresholds; no model calls."""
from __future__ import annotations

from pathlib import Path
import sys
import re
import numpy as np

PHASE1=Path(__file__).resolve().parent.parent/'phase1'
if str(PHASE1) not in sys.path:sys.path.insert(0,str(PHASE1))
from probability import assess_probability


def complete_probe(rows,expected_cells):
    expected=list(expected_cells)
    if not expected or len(expected)!=len(set(expected)):
        raise ValueError('invalid declared technical probe')
    if len(rows)!=len(expected) or {r['cell_id'] for r in rows}!=set(expected):
        raise ValueError('technical probe is incomplete or its identity changed')
    if any(r['split']!='train' for r in rows):raise ValueError('technical admission is train-only')
    return rows


def t1(rows,*,expected_cells,eos_token_ids):
    result=assess_probability(complete_probe(rows,expected_cells),eos_token_ids=eos_token_ids)
    return {**result,'condition':'v2-S2','gate':'T1','admission_statistics_computed':True,
        'threshold_source':'PROTOCOL section 6 T1; unchanged LP-1 probability thresholds'}


def t2(update,refit_rows,*,expected_cells,eos_token_ids,expected_update_slots=256):
    if (update.get('condition')!='v2-S2' or update.get('status')!='MEASURED'
            or update.get('optimizer_updates')!=1 or update['counts']['declared_slots']!=expected_update_slots):
        raise ValueError('one complete declared technical update is required')
    # No admission comparison occurs in the runtime primitive. Both raw state
    # digests and the complete refitted probability probe precede this evaluation.
    probabilities=assess_probability(complete_probe(refit_rows,expected_cells),eos_token_ids=eos_token_ids)
    before=update['before_parameters'];after=update['after_parameters']
    if len(before)!=1 or len(after)!=1 or any(not re.fullmatch(r'[0-9a-f]{64}',p['sha256']) for p in before+after):
        raise ValueError('one-device actual parameter digests required')
    if any(before[0][key]!=after[0][key] for key in ('state_tensors','elements')):
        raise ValueError('technical update changed model state dimensions')
    changed=before[0]['sha256']!=after[0]['sha256']
    median=probabilities['median_absolute_logprob_error']
    passed=changed and probabilities['unsupported_tokens']==0 and median is not None and median<=.01
    return {'condition':'v2-S2','gate':'T2','status':'PASS' if passed else 'FAIL',
        'admission_statistics_computed':True,'parameter_change':changed,'optimizer_updates':1,
        'declared_update_slots':expected_update_slots,'refit_probability':probabilities,
        'threshold_source':'PROTOCOL section 6 T2: real weight change; finite exact-mask refit median error <=0.01',
        'additional_probability_statistics':'descriptive; T1 tail/truncation thresholds are not added to T2'}


def t3(original,replayed,*,source_result_sha256):
    if (original.get('condition')!='v2-S2' or original.get('status')!='MEASURED'
            or original.get('optimizer_updates')!=1 or replayed.get('condition')!='v2-S2'
            or replayed.get('status')!='MEASURED' or replayed.get('diagnostic_replay_updates')!=1
            or replayed.get('continued_learning_updates')!=0 or not replayed.get('pre_update_state_verified')
            or original['batch_sha256']!=replayed['batch_sha256']
            or replayed.get('source_result_sha256')!=source_result_sha256):
        raise ValueError('T3 exact saved batch and verified pre-update state are required')
    first=np.asarray(original['metrics']['loss'],dtype=float);second=np.asarray(replayed['metrics']['loss'],dtype=float)
    if not first.size or first.shape!=second.shape or not np.isfinite(first).all() or not np.isfinite(second).all():
        raise ValueError('T3 loss receipt is invalid or incomplete')
    error=float(np.max(np.abs(first-second)))
    return {'condition':'v2-S2','gate':'T3','status':'PASS' if error<=.001 else 'FAIL',
        'admission_statistics_computed':True,'maximum_loss_difference':error,
        'batch_sha256':original['batch_sha256'],'diagnostic_replay_updates':1,'continued_learning_updates':0,
        'post_replay_parameter_digest_equal':original['after_parameters']==replayed['parameters'],
        'post_replay_digest_interpretation':'descriptive; pre-update restoration is exact, replay loss tolerance is the gate',
        'threshold_source':'PROTOCOL section 6 T3: exact saved batch/RNG/optimizer/scheduler replay, loss difference <=1e-3'}


def t5(rows,*,horizon):
    """Use both fixed A seeds and all declared slots; missing outcomes retain worst-case bounds."""
    if horizon not in (30,60):raise ValueError('unregistered learning-pilot horizon')
    table={}
    for row in rows:
        key=(row['seed'],row['update'])
        if (key in table or row.get('split')!='train' or row['arm']!='A' or row['seed'] not in (1301,1302)
                or type(row['update']) is not int or not 1<=row['update']<=horizon
                or row['declared']!=256 or type(row['measured']) is not int
                or type(row['strict_successes']) is not int
                or not 0<=row['strict_successes']<=row['measured']<=256):
            raise ValueError('pilot opportunity accounting changed')
        table[key]=row
    if set(table)!={(seed,i) for seed in (1301,1302) for i in range(1,horizon+1)}:
        raise ValueError('every scheduled A opportunity from both fixed seeds must be accounted')
    def window(updates):
        subset=[table[seed,i] for seed in (1301,1302) for i in updates]
        declared=sum(r['declared'] for r in subset);measured=sum(r['measured'] for r in subset)
        successes=sum(r['strict_successes'] for r in subset)
        return {'declared':declared,'measured':measured,'strict_successes':successes,
                'rate_bounds':[successes/declared,(successes+declared-measured)/declared]}
    initial=window(range(1,11));final=window(range(horizon-9,horizon+1))
    lower=final['rate_bounds'][0]-initial['rate_bounds'][1]
    upper=final['rate_bounds'][1]-initial['rate_bounds'][0]
    # Compare integer counts at equal full denominators to make the exact 2pp
    # boundary independent of binary floating-point subtraction.
    denominator=initial['declared']
    low_count=final['strict_successes']-(initial['strict_successes']+denominator-initial['measured'])
    high_count=(final['strict_successes']+denominator-final['measured'])-initial['strict_successes']
    passed=100*low_count>=2*denominator
    verdict='PASS' if passed else 'EXTEND_TO_60' if horizon==30 else 'FAIL' if 100*high_count<2*denominator else 'INCONCLUSIVE'
    return {'condition':'v2-S2','gate':'T5','status':verdict,'admission_statistics_computed':True,
        'horizon':horizon,'seeds':[1301,1302],'initial_updates':[1,10],'final_updates':[horizon-9,horizon],
        'initial':initial,'final':final,'improvement_bounds':[lower,upper],
        'threshold':.02,'extension_used':horizon==60,'missing_outcomes_assigned_zero':False,
        'threshold_source':'PROTOCOL section 6 T5: at least two percentage points; one extension to 60',
        'interpretation':'technical feasibility selection, not evidence for the main efficacy hypothesis; p-val=n/a'}
