"""Compute frozen P1–P3, coverage, A1/A2 sensitivities and secondary summaries with paired task-cluster bootstrap intervals."""
import hashlib
import json
from pathlib import Path
import warnings
import numpy as np
from scipy.stats import rankdata, kendalltau
from extract_hidden_tests import PHASE
from rl4cv.forecast import verify_forecast

SEED=20261009
DRAWS=10000
FACTORS=('IC_tests','IC_proofs','FSC')


def finite(value):
    return float(value) if np.isfinite(value) else None


def corr(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    if len(x)<2 or np.ptp(x)==0 or np.ptp(y)==0:return float('nan')
    return float(np.corrcoef(x,y)[0,1])


def agreement(x,y):
    mask=np.isfinite(x)&np.isfinite(y);x=np.asarray(x)[mask];y=np.asarray(y)[mask]
    return {'n_systems':len(x),'pearson':finite(corr(x,y)),
            'spearman':finite(corr(rankdata(x),rankdata(y))),
            'kendall_tau_b':finite(kendalltau(x,y).statistic) if len(x)>1 else None,
            'mean_score':finite(np.mean(x)),'mean_hidden':finite(np.mean(y)),
            'bias_score_minus_hidden':finite(np.mean(x-y)),
            'mean_absolute_difference':finite(np.mean(np.abs(x-y)))}


def interval(values):
    a=np.array([v for v in values if v is not None and np.isfinite(v)],dtype=float)
    return {'low':float(np.quantile(a,.025)) if len(a) else None,
            'high':float(np.quantile(a,.975)) if len(a) else None,
            'n_defined':len(a),'n_requested':len(values)}


def auc(scores,labels):
    scores=np.asarray(scores);labels=np.asarray(labels);n1=int(np.sum(labels==1));n0=int(np.sum(labels==0))
    if not n1 or not n0:return float('nan')
    ranks=rankdata(scores)
    return float((np.sum(ranks[labels==1])-n1*(n1+1)/2)/(n1*n0))


def scsc(row):
    if row['IC_tests'] is None or row['IC_proofs'] is None:return None
    if row['IC_tests']*row['IC_proofs']==0:return 0.
    return (row['IC_tests']*row['IC_proofs']*row['FSC'])**(1/3) if row['FSC'] is not None else None


def system_table(rows):
    grouped={}
    for row in rows:grouped.setdefault((row['panel'],row['system']),[]).append(row)
    out=[]
    for (panel,system),rr in sorted(grouped.items()):
        measured=[r for r in rr if all(r.get(f) is not None for f in FACTORS)]
        evaluated=[r for r in rr if r['status']!='no_tests' and r['hidden_all_pass'] is not None]
        cohort=[r for r in rr if r['status']!='no_tests'];missing=len(cohort)-len(evaluated)
        total=sum(r['hidden_all_pass'] for r in evaluated);compiled=[r for r in rr if r['compiles'] is True]
        applicable=[r for r in compiled if r['applicable']]
        primary_hidden=[r for r in measured if r['hidden_all_pass'] is not None and r['status']!='no_tests']
        means={f:float(np.mean([r[f] for r in measured])) if measured else None for f in FACTORS}
        kernel=[r for r in rr if r.get('kernel_binary') is not None]
        verified=[r for r in kernel if r['kernel_binary']==1]
        v_known=[r for r in verified if r['hidden_all_pass'] is not None and r['status']!='no_tests']
        out.append({'panel':panel,'system':system,'n_declared':len(rr),'n_common_measured':len(measured),
                    'factor_means_common':means,'factor_means_available':{f:float(np.mean([r[f] for r in rr if r.get(f) is not None])) if any(r.get(f) is not None for r in rr) else None for f in FACTORS},'system_score':float(np.cbrt(np.prod(list(means.values())))) if measured else None,
                    'n_compiling':len(compiled),'compile_rate':len(compiled)/len(rr),'n_applicable':len(applicable),
                    'applicability':len(applicable)/len(compiled) if compiled else None,
                    'n_no_tests':len(rr)-len(cohort),'n_hidden_observed':len(evaluated),'n_hidden_missing':missing,
                    'hidden_all_pass_count':total,'hidden_all_pass_mean':total/len(evaluated) if evaluated else None,
                    'hidden_pass_rate_mean':float(np.mean([r['hidden_pass_rate'] for r in evaluated])) if evaluated else None,
                    'hidden_bounds':[total/len(cohort),(total+missing)/len(cohort)] if cohort else None,
                    'P1_n_hidden':len(primary_hidden),'P1_hidden_mean':float(np.mean([r['hidden_all_pass'] for r in primary_hidden])) if primary_hidden else None,
                    'kernel_binary_n':len(kernel),'kernel_binary_mean':float(np.mean([r['kernel_binary'] for r in kernel])) if kernel else None,
                    'n_kernel_verified':len(verified),'n_kernel_verified_hidden_observed':len(v_known),
                    'hidden_all_pass_given_kernel':float(np.mean([r['hidden_all_pass'] for r in v_known])) if v_known else None,
                    'hidden_given_kernel_bounds':[sum(r['hidden_all_pass'] for r in v_known)/len(verified),
                        (sum(r['hidden_all_pass'] for r in v_known)+len(verified)-len(v_known))/len(verified)] if verified else None,
                    'mapping_step_counts':{str(step):sum(r['mapping_steps'].count(step) for r in rr) for step in (1,2,3,4)}})
    return out


def p1(rows,rng,draws=DRAWS,sensitivity=False,subset=None):
    rows=[r for r in rows if subset is None or r['subset']==subset]
    systems=sorted({r['system'] for r in rows});tasks=sorted({r['task_id'] for r in rows})
    si={s:i for i,s in enumerate(systems)};ti={t:i for i,t in enumerate(tasks)}
    factors=np.full((len(systems),len(tasks),3),np.nan);hidden=np.full((len(systems),len(tasks)),np.nan);graded=hidden.copy()
    for row in rows:
        i,j=si[row['system']],ti[row['task_id']]
        if sensitivity and row['source_status'] in ('model_error','incomplete'):
            factors[i,j]=0
            if row['status']!='no_tests':hidden[i,j]=0;graded[i,j]=0
        elif all(row.get(f) is not None for f in FACTORS):
            factors[i,j]=[row[f] for f in FACTORS]
            if row['hidden_all_pass'] is not None and row['status']!='no_tests':hidden[i,j]=row['hidden_all_pass'];graded[i,j]=row['hidden_pass_rate']
    def aggregates(indices):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            means=np.nanmean(factors[:,indices,:],axis=1);score=np.cbrt(np.prod(means,axis=1))
            h=np.nanmean(hidden[:,indices],axis=1);g=np.nanmean(graded[:,indices],axis=1)
        return score,h,g,means
    x,y,g,means=aggregates(np.arange(len(tasks)));point=agreement(x,y)
    keys=[k for k in point if k!='n_systems'];boot={k:[] for k in keys};sysboot={k:[] for k in keys}
    for _ in range(draws):
        bx,by,_,_=aggregates(rng.integers(0,len(tasks),len(tasks)));a=agreement(bx,by)
        ix=rng.integers(0,len(systems),len(systems));b=agreement(x[ix],y[ix])
        for k in keys:boot[k].append(a[k]);sysboot[k].append(b[k])
    return {'subset':subset or 'pooled','sensitivity_A1':sensitivity,'n_tasks':len(tasks),'systems':systems,
            **point,'task_bootstrap_95':{k:interval(v) for k,v in boot.items()},
            'system_bootstrap_95':{k:interval(v) for k,v in sysboot.items()},
            'per_system':[{'system':s,'score':finite(x[i]),'hidden':finite(y[i]),'n_factor':int(np.isfinite(factors[i,:,0]).sum()),'n_hidden':int(np.isfinite(hidden[i]).sum())} for i,s in enumerate(systems)],
            'graded_outcome':agreement(x,g),'factor_correlations':{f:agreement(means[:,i],y) for i,f in enumerate(FACTORS)}}


def pooled_stats(rows,score_field='scsc'):
    groups={}
    for r in rows:
        x=scsc(r) if score_field=='scsc' else r[score_field]
        if x is not None:groups.setdefault(r['system'],[]).append((x,r['hidden_all_pass'],r['hidden_pass_rate']))
    xrank=[];yrank=[];labels=[]
    for group in groups.values():
        x,y,g=map(np.asarray,zip(*group));n=len(x)
        xrank.extend((rankdata(x)-.5)/n);yrank.extend((rankdata(g)-.5)/n);labels.extend(y)
    return {'auc':finite(auc(xrank,labels)),'spearman_within_system':finite(corr(xrank,yrank)),
            'n_cells':len(labels),'n_pass':int(sum(labels)),'n_fail':int(len(labels)-sum(labels))}


def p23(rows,rng,draws=DRAWS,unambiguous=False,subset=None):
    cells=[r for r in rows if r['compiles'] is True and r['applicable'] and scsc(r) is not None
           and (not unambiguous or r['all_mappings_unambiguous']) and (subset is None or r['subset']==subset)]
    tasks=sorted({r['task_id'] for r in rows if subset is None or r['subset']==subset})
    clusters={t:[] for t in tasks}
    for r in cells:clusters[r['task_id']].append(r)
    point=pooled_stats(cells);auc_draws=[];rho_draws=[]
    for _ in range(draws):
        sample=[r for i in rng.integers(0,len(tasks),len(tasks)) for r in clusters[tasks[i]]]
        stats=pooled_stats(sample);auc_draws.append(stats['auc']);rho_draws.append(stats['spearman_within_system'])
    by_system={}
    for system in sorted({r['system'] for r in cells}):
        ss=[r for r in cells if r['system']==system];n1=sum(r['hidden_all_pass'] for r in ss);n0=len(ss)-n1
        by_system[system]={'n_cells':len(ss),'n_pass':n1,'n_fail':n0,
                           'auc':finite(auc([scsc(r) for r in ss],[r['hidden_all_pass'] for r in ss])) if min(n0,n1)>=10 else None}
    return {**point,'n_tasks_in_resampling_frame':len(tasks),'n_observed_tasks':len({r['task_id'] for r in cells}),
            'unambiguous_steps_1_2_only':unambiguous,'subset':subset or 'pooled',
            'auc_bootstrap_95':interval(auc_draws),'spearman_bootstrap_95':interval(rho_draws),
            'per_system':by_system,'factor_descriptives':{f:pooled_stats(cells,f) for f in ['IC_proofs','FSC']}}


def main():
    for name in ('e12_phase_a_forecast','e12_phase_a_forecast_amendment_A1','e12_phase_a_forecast_amendment_A2'):
        assert verify_forecast(PHASE/'forecasts'/(name+'.json'))
    completion=json.loads((PHASE/'results/evaluation_complete.json').read_text());assert completion['complete']
    source=Path(completion['outcomes_path']);assert hashlib.sha256(source.read_bytes()).hexdigest()==completion['outcomes_sha256']
    rows=[json.loads(line) for line in source.read_text().splitlines()];assert len(rows)==43840
    primary=[r for r in rows if r['panel']=='primary'];rng=np.random.default_rng(SEED)
    result={'settings':{'seed':SEED,'draws':DRAWS,'bootstrap_unit':'paired task clusters, all systems retained','p_value':'n/a',
                        'P2_definition':'pooled ROC AUC on within-system normalized midranks; midranks recomputed in each bootstrap',
                        'P3_definition':'Pearson of pooled within-system normalized midranks of score and graded outcome; recomputed each bootstrap',
                        'repeat_scoring':'single saved run per cell; no additional scoring repeats'},'outcomes_sha256':completion['outcomes_sha256']}
    result['systems']=system_table(rows)
    print('System summaries complete',flush=True)
    result['P1']=p1(primary,rng);print('P1 complete',flush=True)
    result['sensitivity_A1']=p1(primary,rng,sensitivity=True);print('A1 complete',flush=True)
    result['P2_P3']=p23(primary,rng);print('P2/P3 complete',flush=True)
    result['sensitivity_A2']=p23(primary,rng,unambiguous=True);print('A2 complete',flush=True)
    result['subsets']={}
    for subset in ['Core614','IndustrySet282']:
        result['subsets'][subset]={'P1':p1(primary,rng,subset=subset),'P2_P3':p23(primary,rng,subset=subset),
                                  'systems':system_table([r for r in primary if r['subset']==subset])}
        print(subset+' complete',flush=True)
    compiling=[r for r in primary if r['compiles'] is True];napp=sum(r['applicable'] for r in compiling)
    counts={str(step):sum(r['mapping_steps'].count(step) for r in primary) for step in (1,2,3,4)};total=sum(counts.values())
    result['G_A']={'n_compiling':len(compiling),'n_applicable':napp,'fraction':napp/len(compiling) if compiling else None,'threshold':.5,
                   'passes':bool(compiling) and napp/len(compiling)>=.5}
    result['mapping_steps']={'counts':counts,'n_mapped_symbols':total,'shares':{k:v/total if total else None for k,v in counts.items()}}
    q=result['P2_P3'];result['verdicts']={'P1_holds':result['P1']['spearman'] is not None and result['P1']['spearman']>=.8,
      'P2_holds':q['auc'] is not None and q['auc']>=.6 and q['auc_bootstrap_95']['low'] is not None and q['auc_bootstrap_95']['low']>.5,
      'P3_holds':q['spearman_within_system'] is not None and q['spearman_within_system']>0 and q['spearman_bootstrap_95']['low'] is not None and q['spearman_bootstrap_95']['low']>0,
      'coverage_verdict':'PASS' if result['G_A']['passes'] else 'LIMITED COVERAGE'}
    eligible=[r for r in primary if r['compiles'] is True and r['applicable'] and scsc(r) is not None]
    high=sorted([r for r in eligible if r['hidden_all_pass']==0],key=lambda r:(-scsc(r),r['system'],r['task_id']))[:10]
    low=sorted([r for r in eligible if r['hidden_all_pass']==1],key=lambda r:(scsc(r),r['system'],r['task_id']))[:10]
    result['disagreement_selection']=[{k:r.get(k) for k in ['system','task_id','IC_tests','IC_proofs','FSC','hidden_all_pass','hidden_pass_rate','n_tests','n_applicable','n_unknown','mapping_steps','receipt']}|{'scsc':scsc(r),'group':label} for label,rr in [('high_score_failing',high),('low_score_passing',low)] for r in rr]
    (PHASE/'results/analysis_e12.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result['verdicts']),flush=True)


if __name__=='__main__':main()
