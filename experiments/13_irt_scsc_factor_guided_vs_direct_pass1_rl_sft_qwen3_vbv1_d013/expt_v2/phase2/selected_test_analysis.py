"""Analyze complete paired seed blocks with declared missing-value bounds and exploratory inference only."""
from __future__ import annotations

import itertools
import math
import numpy as np

SEEDS=(13011,13012,13013)


def sign_swap(differences):
    values=np.asarray(differences,dtype=float)
    if values.shape!=(3,) or not np.isfinite(values).all():raise ValueError('exactly three paired finite seed effects required')
    observed=abs(float(values.mean()))
    simulated=[abs(float(np.mean(values*np.asarray(sign)))) for sign in itertools.product((-1,1),repeat=3)]
    p=sum(v>=observed-1e-15 for v in simulated)/8
    return {'p_value':p,'permutations':8,'minimum_two_sided_p':.25,
            'test':'two-sided exact paired-seed sign swap; null: arm labels exchangeable within each seed block'}


def holm(pvalues):
    if not pvalues or any(p is not None and (not math.isfinite(p) or not 0<=p<=1) for p in pvalues.values()):
        raise ValueError('invalid predeclared multiplicity family')
    # An unavailable primary contrast remains in its frozen family as p=1 for
    # adjustment of the observed contrasts; its own result stays unavailable.
    ordered=sorted(pvalues,key=lambda key:1 if pvalues[key] is None else pvalues[key])
    running=0.;result={};n=len(ordered)
    for i,key in enumerate(ordered):
        value=pvalues[key];running=max(running,min(1.,(n-i)*(1 if value is None else value)))
        result[key]=running if value is not None else None
    return result


def validate(rows,tasks,arms):
    if len(tasks)!=222 or len({t['task_id'] for t in tasks})!=222:raise ValueError('complete fixed test population required')
    if sum(t['domain']=='core' for t in tasks)!=152 or sum(t['domain']=='IndustrySet' for t in tasks)!=70:
        raise ValueError('official test domains changed')
    if any(t.get('split')!='test' or not t.get('group_id') for t in tasks):raise ValueError('test split/group metadata required')
    if arms not in (['A','B','P'],['A','B','C','P']):raise ValueError('eligible arms must be frozen before main')
    index={t['task_id']:i for i,t in enumerate(tasks)}
    values={arm:np.full((3,222,16),np.nan) for arm in arms};seen=set()
    checkpoints={}
    for row in rows:
        key=(row['arm'],row['run_seed'],row['task_id'],row['sample_idx'])
        arm,seed,task,sample=key
        if key in seen or arm not in arms or seed not in SEEDS or task not in index or type(sample) is not int or not 0<=sample<16:
            raise ValueError('duplicate or undeclared selected-test cell')
        absent=(row.get('boundary') is None and row.get('status')=='not_evaluated'
                and row.get('strict') is None and isinstance(row.get('reason'),str) and bool(row['reason']))
        if (row.get('split')!='test' or row.get('condition')!='v2-S2'
                or not (absent or type(row.get('boundary')) is int and row['boundary'] in (1,2,3,4))):
            raise ValueError('selected-test identity changed')
        run=(arm,seed);checkpoints.setdefault(run,row['boundary'])
        if checkpoints[run]!=row['boundary']:raise ValueError('multiple selected checkpoints in one test run')
        value=row.get('strict')
        if value is not None and (type(value) not in (int,bool) or value not in (0,1)):
            raise ValueError('strict outcome must be binary or missing')
        if value is not None:values[arm][SEEDS.index(seed),index[task],sample]=value
        seen.add(key)
    if len(seen)!=len(arms)*3*222*16:raise ValueError('every declared selected-test slot needs a terminal receipt')
    return values


def pass_k(successes,k,n=16):
    if type(successes) is not int or not 0<=successes<=n or not 1<=k<=n:raise ValueError('invalid pass-at-k denominator')
    return 1-math.comb(n-successes,k)/math.comb(n,k) if n-successes>=k else 1.


def summarize(values,indexes):
    part=values[:,indexes,:];known=np.isfinite(part);n=part.size;s=int(np.nansum(part));missing=n-int(known.sum())
    bounds={}
    for k in (1,4,16):
        counts=np.nansum(part,axis=2).astype(int);unknown=np.sum(~known,axis=2)
        lower=np.asarray([[pass_k(int(x),k) for x in row] for row in counts])
        upper=np.asarray([[pass_k(int(x),k) for x in row] for row in counts+unknown])
        bounds[str(k)]={'mean':float(lower.mean()) if not missing else None,
                       'full_manifest_bounds':[float(lower.mean()),float(upper.mean())]}
    return {'declared':n,'measured':int(known.sum()),'missing':missing,'successes':s,
            'observed_cell_mean':s/int(known.sum()) if known.any() else None,
            'strict_mean':s/n if not missing else None,'strict_mean_bounds':[s/n,(s+missing)/n],
            'pass_at_k':bounds,'seeds':3,'tasks':len(indexes),'samples_per_task':16}


def bootstrap_means(task_effect,tasks,indexes,*,bootstrap_seed):
    """Pair arms before resampling, then retain complete groups inside every sampled seed block."""
    groups={}
    for local,index in enumerate(indexes):groups.setdefault(tasks[index]['group_id'],[]).append(local)
    clusters=[np.asarray(groups[key],dtype=int) for key in sorted(groups)]
    rng=np.random.default_rng(bootstrap_seed);draws=np.empty(10000)
    # Both arms share every seed and task-group draw. Groups are resampled inside
    # each sampled seed block; all samples/tasks in a selected group stay intact.
    for i in range(10000):
        means=[]
        for seed in rng.integers(0,3,size=3):
            sampled=np.concatenate([clusters[j] for j in rng.integers(0,len(clusters),size=len(clusters))])
            means.append(task_effect[seed,sampled].mean())
        draws[i]=np.mean(means)
    return np.quantile(draws,[.025,.975]).tolist()


def arm_summary(values,tasks,indexes,*,bootstrap_seed):
    result=summarize(values,indexes);part=values[:,indexes,:]
    result['confidence_interval_95']=None;result['seed_means']=None
    if np.isfinite(part).all():
        means=part.mean(axis=2)
        result.update(seed_means=means.mean(axis=1).tolist(),
                      confidence_interval_95=bootstrap_means(means,tasks,indexes,bootstrap_seed=bootstrap_seed),
                      bootstrap_draws=10000,bootstrap_seed=bootstrap_seed,
                      interval_interpretation='descriptive paired-seed/task-group percentile interval, conditional on selected checkpoints; only three seeds')
    return result


def contrast(left,right,tasks,indexes,*,bootstrap_seed):
    a=left[:,indexes,:];b=right[:,indexes,:];paired=np.isfinite(a)&np.isfinite(b)
    n=a.size;unknown_a=~np.isfinite(a);unknown_b=~np.isfinite(b)
    lower=float(np.sum(np.nan_to_num(a)-np.nan_to_num(b)-unknown_b)/n)
    upper=float(np.sum(np.nan_to_num(a)+unknown_a-np.nan_to_num(b))/n)
    common=np.where(paired,a-b,np.nan);observed=int(paired.sum())
    value={'declared_pairs':n,'paired_observed':observed,'missing_pairs':n-observed,
           'paired_common_cohort_mean':float(np.nansum(common)/observed) if observed else None,
           'full_manifest_difference_bounds':[lower,upper],'mean_difference':None,'seed_differences':None,
           'confidence_interval_95':None,'p_value':None,'bootstrap_draws':0,
           'inference':'exploratory; three seed blocks; no confirmatory alpha=.05 claim'}
    if not paired.all():
        value['reason']='full-seed inferential estimate unavailable with missing selected-test outcomes'
        return value
    task_effect=(a-b).mean(axis=2);seed_effect=task_effect.mean(axis=1)
    value.update(mean_difference=float(seed_effect.mean()),seed_differences=seed_effect.tolist(),**sign_swap(seed_effect))
    interval=bootstrap_means(task_effect,tasks,indexes,bootstrap_seed=bootstrap_seed)
    value.update(confidence_interval_95=interval,bootstrap_draws=10000,
        bootstrap_seed=bootstrap_seed,resampling='paired seed blocks, then task groups within sampled blocks; percentile interval, descriptive with three seeds',
        paired_task_seed_regressions=int(np.sum(task_effect<0)),paired_task_seed_improvements=int(np.sum(task_effect>0)),
        paired_task_seed_ties=int(np.sum(task_effect==0)),paired_task_seed_denominator=int(task_effect.size))
    return value


def evaluate(rows,tasks,arms,*,bootstrap_seed=1302301):
    values=validate(rows,tasks,arms)
    populations={'pooled':list(range(222)),'core':[i for i,t in enumerate(tasks) if t['domain']=='core'],
                 'IndustrySet':[i for i,t in enumerate(tasks) if t['domain']=='IndustrySet']}
    primary=['B-A']+(['C-A'] if 'C' in arms else [])
    secondary=['B-P','P-A']+(['C-B','C-P'] if 'C' in arms else [])
    result={'condition':'v2-S2','stage':'SELECTED_TEST_ANALYSIS','primary_contrasts':primary,
            'eligible_arms':arms,'main_seeds':list(SEEDS),'C_claim':'eligible; missing outcomes reported explicitly' if 'C' in arms else 'unmeasured: C gated out before main',
            'populations':{},'H5':'unresolved; strict outcomes do not establish independent coverage noninferiority',
            'confirmatory_claim_admitted':False,'new_model_calls':0,
            'runs_without_selected_checkpoint':[{'arm':a,'run_seed':seed} for a,seed in sorted(
                {(r['arm'],r['run_seed']) for r in rows if r['boundary'] is None})]}
    for domain,indexes in populations.items():
        effects={key:contrast(values[key[0]],values[key[2]],tasks,indexes,bootstrap_seed=bootstrap_seed)
                 for key in primary+secondary}
        adjusted=holm({key:effects[key]['p_value'] for key in primary})
        for key in primary:effects[key]['holm_adjusted_p']=adjusted[key]
        result['populations'][domain]={'arms':{arm:arm_summary(value,tasks,indexes,bootstrap_seed=bootstrap_seed) for arm,value in values.items()},
            'contrasts':effects,'multiplicity':'Holm across the frozen primary contrasts within this population; pooled is primary, domains descriptive'}
    forecast={}
    for key,prediction in {'B-A':.02,'C-A':.03,'P-A':0.}.items():
        observed=result['populations']['pooled']['contrasts'].get(key,{}).get('mean_difference')
        forecast[key]={'prediction':prediction,'observed':observed,
                       'observed_minus_prediction':observed-prediction if observed is not None else None,
                       'status':'OBSERVED_POINT_ERROR' if observed is not None else 'UNAVAILABLE',
                       'source':'PROTOCOL section 8 F3, to be frozen before main; numerical appraisal, not an efficacy gate'}
    result['F3']=forecast
    return result
