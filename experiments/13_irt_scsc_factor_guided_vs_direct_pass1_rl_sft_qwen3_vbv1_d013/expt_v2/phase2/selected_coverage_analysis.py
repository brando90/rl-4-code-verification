"""Describe fixed selected-test coverage differences with all missing slots and no unregistered noninferiority claim."""
from __future__ import annotations

import math
import numpy as np
from selected_test_analysis import SEEDS,bootstrap_means

METRICS=('formal_specification_coverage','hidden_test_coverage','theorem_count')


def validate(rows,tasks,arms):
    if (len(tasks)!=222 or len({t['task_id'] for t in tasks})!=222
            or sum(t['domain']=='core' for t in tasks)!=152
            or sum(t['domain']=='IndustrySet' for t in tasks)!=70
            or any(t.get('split')!='test' or not t.get('group_id') for t in tasks)):
        raise ValueError('complete frozen test task/group/domain metadata required')
    if arms not in (['A','B','P'],['A','B','C','P']):raise ValueError('pre-main eligible arm set required')
    indexes={t['task_id']:i for i,t in enumerate(tasks)}
    arrays={metric:{arm:np.full((3,222),np.nan) for arm in arms} for metric in METRICS}
    seen=set();checkpoints={}
    for row in rows:
        key=(row['arm'],row['run_seed'],row['task_id']);arm,seed,task=key
        if key in seen or arm not in arms or seed not in SEEDS or task not in indexes:
            raise ValueError('duplicate or undeclared coverage cell')
        if row.get('condition')!='v2-S2' or row.get('split')!='test' or type(row.get('sample_idx')) is not int or row['sample_idx']!=0:
            raise ValueError('fixed preselected sample identity changed')
        if not set(METRICS)<=set(row):raise ValueError('every metric must be explicitly measured or missing')
        absent=(row.get('boundary') is None and row.get('status')=='not_evaluated'
                and isinstance(row.get('reason'),str) and bool(row['reason'])
                and all(row.get(metric) is None for metric in METRICS))
        if not (absent or type(row.get('boundary')) is int and row['boundary'] in (1,2,3,4)):
            raise ValueError('selected checkpoint or missing-run receipt required')
        checkpoints.setdefault((arm,seed),row['boundary'])
        if checkpoints[(arm,seed)]!=row['boundary']:raise ValueError('multiple selected checkpoints within a run')
        for metric in METRICS:
            value=row.get(metric)
            if value is not None:
                if metric=='theorem_count':
                    if type(value) is not int or value<0:raise ValueError('theorem counts must be nonnegative integers or missing')
                elif type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=1:
                    raise ValueError('independent coverage must be in [0,1] or missing')
                if absent:raise ValueError('unselected checkpoint cannot have a measurement')
                arrays[metric][arm][SEEDS.index(seed),indexes[task]]=value
        seen.add(key)
    if len(seen)!=len(arms)*3*222:raise ValueError('every declared fixed coverage sample needs a terminal receipt')
    return arrays


def summarize(values,tasks,indexes,*,bounded,bootstrap_seed):
    part=values[:,indexes];known=np.isfinite(part);n=part.size;measured=int(known.sum());missing=n-measured
    lower=float(np.nansum(part)/n);upper=(float((np.nansum(part)+missing)/n) if bounded else None) if missing else lower
    result={'declared':n,'measured':measured,'missing':missing,'tasks':len(indexes),'seeds':3,'samples_per_task':1,
        'measured_cohort_mean':float(np.nansum(part)/measured) if measured else None,
        'full_manifest_mean':None if missing else lower,'full_manifest_mean_bounds':[lower,upper],
        'upper_bound_unbounded':bool(missing and not bounded),'confidence_interval_95':None,
        'seed_means':None,'p_value':None,'p_value_reason':'descriptive independent coverage, no registered noninferiority test'}
    if not missing:
        result.update(seed_means=part.mean(axis=1).tolist(),
            confidence_interval_95=bootstrap_means(part,tasks,indexes,bootstrap_seed=bootstrap_seed))
    return result


def difference(left,right,tasks,indexes,*,bounded,bootstrap_seed):
    a=left[:,indexes];b=right[:,indexes];paired=np.isfinite(a)&np.isfinite(b)
    na=int((~np.isfinite(a)).sum());nb=int((~np.isfinite(b)).sum());n=a.size
    base=float((np.nansum(a)-np.nansum(b))/n)
    lower=base-nb/n if bounded else None if nb else base
    upper=base+na/n if bounded else None if na else base
    result={'declared_pairs':n,'paired_observed':int(paired.sum()),'missing_pairs':int((~paired).sum()),
        'paired_common_cohort_mean':float((a-b)[paired].mean()) if paired.any() else None,
        'full_manifest_difference_bounds':[lower,upper],
        'lower_bound_unbounded':bool(nb and not bounded),'upper_bound_unbounded':bool(na and not bounded),
        'mean_difference':None,'seed_differences':None,'confidence_interval_95':None,
        'p_value':None,'p_value_reason':'descriptive coverage difference; no registered noninferiority margin/test',
        'noninferiority_margin':None,'noninferiority_established':False}
    if paired.all():
        effects=a-b;result.update(mean_difference=float(effects.mean()),seed_differences=effects.mean(axis=1).tolist(),
            confidence_interval_95=bootstrap_means(effects,tasks,indexes,bootstrap_seed=bootstrap_seed),
            paired_task_seed_regressions=int((effects<0).sum()),paired_task_seed_improvements=int((effects>0).sum()),
            paired_task_seed_ties=int((effects==0).sum()))
    return result


def evaluate(rows,tasks,arms,*,bootstrap_seed=1302301):
    arrays=validate(rows,tasks,arms)
    populations={'pooled':list(range(222)),'core':[i for i,t in enumerate(tasks) if t['domain']=='core'],
        'IndustrySet':[i for i,t in enumerate(tasks) if t['domain']=='IndustrySet']}
    contrasts=['B-A','B-P','P-A']+(['C-A','C-B','C-P'] if 'C' in arms else [])
    result={'condition':'v2-S2','stage':'SELECTED_TEST_INDEPENDENT_COVERAGE_ANALYSIS',
        'eligible_arms':arms,'main_seeds':list(SEEDS),'sample_idx':0,'declared_tasks':222,
        'H5':'not established: no prospectively justified noninferiority margin; missing independent outcomes remain unavailable',
        'noninferiority_established':False,'confirmatory_claim_admitted':False,
        'uncertainty':'10,000 paired seed/task-group percentile draws conditional on selected checkpoints; descriptive with three seeds; no full-population inferential interval when incomplete',
        'bootstrap_seed':bootstrap_seed,'bootstrap_draws':10000,'populations':{},'model_calls':0}
    for population,indexes in populations.items():
        result['populations'][population]={}
        for metric,values in arrays.items():
            bounded=metric!='theorem_count'
            result['populations'][population][metric]={
                'arms':{arm:summarize(value,tasks,indexes,bounded=bounded,bootstrap_seed=bootstrap_seed) for arm,value in values.items()},
                'contrasts':{name:difference(values[name[0]],values[name[2]],tasks,indexes,bounded=bounded,bootstrap_seed=bootstrap_seed) for name in contrasts}}
    return result
