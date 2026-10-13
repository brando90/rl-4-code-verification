#!/usr/bin/env python3
"""Evaluate the frozen candidate with paired group resampling, explicit undefined metrics and unchanged G1 thresholds."""
import numpy as np
from scipy.special import xlogy
from scipy.stats import rankdata, pearsonr, spearmanr, kendalltau


def log_loss(y,p):
    y,p=np.asarray(y,float),np.clip(np.asarray(p,float),1e-12,1-1e-12)
    if y.shape!=p.shape or np.any(~np.isfinite(y)) or np.any(~np.isfinite(p)):raise ValueError('incomplete paired labels/predictions')
    return float(np.mean(-xlogy(y,p)-xlogy(1-y,1-p)))


def auc(y,p):
    y,p=np.asarray(y,bool),np.asarray(p,float)
    pos=int(y.sum());neg=len(y)-pos
    if not pos or not neg:return None
    return float((rankdata(p)[y].sum()-pos*(pos+1)/2)/(pos*neg))


def correlation(x,y,kind):
    if len(x)<2 or np.ptp(x)==0 or np.ptp(y)==0:return None
    functions={'pearson':pearsonr,'spearman':spearmanr,'kendall':kendalltau}
    return float(functions[kind](x,y).statistic)


def metrics(y,p,policies):
    y,p,policies=np.asarray(y,float),np.asarray(p,float),np.asarray(policies)
    unique=np.unique(policies)
    means_y=np.array([y[policies==i].mean() for i in unique])
    means_p=np.array([p[policies==i].mean() for i in unique])
    return {'log_loss':log_loss(y,p),'auc':auc(y,p),'observed_mean':float(y.mean()),
            'predicted_mean':float(p.mean()),'mean_bias':float(np.mean(p-y)),
            'mean_absolute_error':float(np.mean(np.abs(p-y))),
            'brier':float(np.mean((p-y)**2)),
            **{k:correlation(y,p,k) for k in ('pearson','spearman','kendall')},
            **{'policy_'+k:correlation(means_y,means_p,k) for k in ('pearson','spearman','kendall')},
            'policies':len(unique)}


def calibration_bins(y,p,groups,bins=10):
    y,p,groups=np.asarray(y,float),np.asarray(p,float),np.asarray(groups)
    indexes=np.minimum((p*bins).astype(int),bins-1)
    return [{'bin':b,'cells':int(np.sum(indexes==b)),'groups':len(np.unique(groups[indexes==b])),
             'observed_mean':float(y[indexes==b].mean()),'predicted_mean':float(p[indexes==b].mean())}
            for b in range(bins) if np.any(indexes==b)]


def assess_g1(y,predictions,groups,policies,*,candidate='selected',draws=10000,seed=1302031,implementation_admitted=True):
    y,groups,policies=np.asarray(y,float),np.asarray(groups),np.asarray(policies)
    required=(candidate,'M0','M1','M2')
    if not len(y) or len(y)!=len(groups) or len(y)!=len(policies):raise ValueError('bad evaluation manifest')
    if np.any(~np.isfinite(y)) or not np.all(np.isin(y,[0,1])):raise ValueError('unknown target labels remain missing')
    usable={name:np.asarray(p) for name,p in predictions.items() if p is not None and np.asarray(p).shape==y.shape and np.all(np.isfinite(p))}
    missing=[name for name in required if name not in usable]
    point={name:metrics(y,p,policies) for name,p in usable.items()}
    unique=np.unique(groups);indices=[np.flatnonzero(groups==g) for g in unique]
    bootstrap={name:{k:[] for k,v in m.items() if k!='policies'} for name,m in point.items()}
    differences={name:[] for name in ('M0','M1') if name in usable and candidate in usable};rng=np.random.default_rng(seed)
    # Resample the same task groups for every model and every policy in each draw.
    for _ in range(draws):
        ix=np.concatenate([indices[i] for i in rng.integers(0,len(indices),len(indices))])
        values={name:metrics(y[ix],np.asarray(predictions[name])[ix],policies[ix]) for name in point}
        for name,m in values.items():
            for k,v in m.items():
                if k!='policies' and v is not None and np.isfinite(v):bootstrap[name][k].append(v)
        for baseline in differences:differences[baseline].append(values[candidate]['log_loss']-values[baseline]['log_loss'])
    intervals={name:{k:{'interval_95':np.quantile(v,[.025,.975]).tolist() if v else None,'valid_draws':len(v)} for k,v in values.items()} for name,values in bootstrap.items()}
    contrasts={name:{'estimate':point[candidate]['log_loss']-point[name]['log_loss'],
                     'interval_95':np.quantile(values,[.025,.975]).tolist(),'p_value':None,
                     'test':'gate uses prespecified paired-group 95% interval, not a p-value'} for name,values in differences.items()}
    rho=point[candidate]['policy_pearson'] if candidate in point else None
    bias_ci=intervals[candidate]['mean_bias']['interval_95'] if candidate in intervals else None
    # Operational calibration criterion is declared before L1v2, not selected from outcomes.
    calibration_ok=bool(bias_ci and bias_ci[0]<=0<=bias_ci[1])
    admitted=not missing and implementation_admitted and calibration_ok and rho is not None and rho>=.8 and all(v['interval_95'][1]<0 for v in contrasts.values())
    return {'status':'PASS' if admitted else 'FAIL','declared':len(y),'measured':len(y),'groups':len(unique),
            'metrics':point,'intervals':intervals,'paired_log_loss_contrasts':contrasts,
            'candidate':candidate,'missing_required_models':missing,'calibration_bins':calibration_bins(y,predictions[candidate],groups) if candidate in usable else [],
            'calibration_bias_interval_contains_zero':calibration_ok,
            'implementation_admitted':implementation_admitted,'draws':draws,'seed':seed,
            'interpretation':'fixed-fit task-group bootstrap; three-policy correlations are descriptive and unstable; no fit uncertainty resampling'}
