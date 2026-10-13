#!/usr/bin/env python3
"""Evaluate the preregistered G0 using complete validation rows, never test outcomes."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'prediction'))
from evaluation_v2 import auc


def evaluate(earlier,later,groups,*,draws=10000,seed=1302051):
    """Each task retains all eight samples. Dense-only means B varies but strict does not."""
    if len(earlier)!=len(later) or len(earlier)!=len(groups):raise ValueError('unpaired tasks')
    e,l=np.asarray(earlier,float),np.asarray(later,float)
    if e.shape!=(len(groups),8,2) or l.shape!=e.shape or not np.isfinite(e).all() or not np.isfinite(l).all():
        raise ValueError('missing task/sample measurement')
    if not np.isin(e[:,:,0],[0,1]).all() or not np.isin(l[:,:,0],[0,1]).all():raise ValueError('invalid strict label')
    dense=(np.ptp(l[:,:,0],axis=1)==0)&(np.ptp(l[:,:,1],axis=1)>0)
    zero=e[:,:,0].sum(axis=1)==0
    outcome=l[:,:,0].sum(axis=1)>0;score=e[:,:,1].mean(axis=1)
    point_auc=auc(outcome[zero],score[zero])
    unique=np.unique(groups);indices=[np.flatnonzero(np.asarray(groups)==g) for g in unique]
    rng=np.random.default_rng(seed);shares=[];aucs=[]
    for _ in range(draws):
        ix=np.concatenate([indices[i] for i in rng.integers(0,len(indices),len(indices))])
        shares.append(float(dense[ix].mean()));ix=ix[zero[ix]]
        value=auc(outcome[ix],score[ix])
        if value is not None:aucs.append(value)
    return {'tasks':len(groups),'samples_per_task':8,'groups':len(unique),
            'dense_only':int(dense.sum()),'dense_only_share':float(dense.mean()),
            'dense_only_interval_95':np.quantile(shares,[.025,.975]).tolist(),
            'zero_success_earlier_tasks':int(zero.sum()),'later_positive_in_subset':int(outcome[zero].sum()),
            'auc':point_auc,'auc_interval_95':np.quantile(aucs,[.025,.975]).tolist() if aucs else None,
            'auc_valid_bootstrap_draws':len(aucs),'bootstrap_draws':draws,'bootstrap_seed':seed,
            'uncertainty':'paired task-group percentile bootstrap; resample full cohort, then condition on zero earlier successes',
            'p_value':None,'test':'prespecified point thresholds; no hypothesis-test p-value'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args()
    if json.loads((a.root/'public_result.json').read_text())['status']!='PASS':raise ValueError('R2 has not passed')
    rows={};groups={}
    for line in (a.root/'ordinary/results.jsonl').open():
        row=json.loads(line)
        if row['split']=='test':raise ValueError('test is sealed')
        if row['split']!='validation':continue
        groups[row['task_id']]=row['group_id']
        if row['status']!='measured':continue
        for value in row['readbacks']:
            if value['family']!='ladder':continue
            key=(value['policy'],row['task_id'],row['sample_idx'])
            if key in rows:raise ValueError('duplicate sample')
            rows[key]=(value['value'],value['factored_reward'])
    if len(groups)!=135:raise ValueError('validation denominator changed')
    tasks=sorted(groups);result={'gate':'G0','status':'FAIL','threshold_source':'PROTOCOL section 3; PLAN section 4',
        'dense_only_minimum':21,'dense_only_denominator':135,'auc_minimum':.65,'strata':{}}
    for size in ('1p7B','4B','8B'):
        try:
            earlier=[[rows[(f'sft_{size}_f0p5',t,k)] for k in range(8)] for t in tasks]
            later=[[rows[(f'sft_{size}_f1p0',t,k)] for k in range(8)] for t in tasks]
            result['strata'][size]=evaluate(earlier,later,[groups[t] for t in tasks])
        except (KeyError,ValueError) as exc:result['strata'][size]={'status':'INCOMPLETE','reason':str(exc),'tasks':135}
    primary=result['strata']['4B']
    if 'dense_only' in primary and primary['dense_only']>=21 and primary['auc'] is not None and primary['auc']>=.65:result['status']='PASS'
    path=a.root/'G0_result.json'
    with path.open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
