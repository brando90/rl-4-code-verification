"""TLDR: Verify the frozen experiment-19 forecast and publish only descriptive G0 aggregates."""
import json
from pathlib import Path
import math
import numpy as np
from scipy.stats import spearmanr,rankdata
from rl4cv.forecast import verify_forecast
from common import write_new

FORECAST_SHA256='abb0cb3115b86fd3107a565fdfacd53343f285b7d27b34fd30d4dcb682436286'
FIELDS=('q_mixed_G8','panel_strict_rate','features_only_q_mixed_G8')


def verified(path):
    path=Path(path)
    if not verify_forecast(path) or path.with_suffix('.sha256').read_text().split()[0]!=FORECAST_SHA256:
        raise ValueError('frozen experiment-19 forecast changed')
    return json.loads(path.read_text())


def q8(s):return 1-(math.comb(s,8) if s>=8 else 0)/math.comb(32,8)-(math.comb(32-s,8) if 32-s>=8 else 0)/math.comb(32,8)


def auc(x,y):
    yes=int(sum(y));no=len(y)-yes
    if not yes or not no:return None
    return float((rankdata(x)[np.array(y,dtype=bool)].sum()-yes*(yes+1)/2)/(yes*no))


def correlation(x,y):
    if len(set(x))<2 or len(set(y))<2:return None
    return float(spearmanr(x,y).statistic)


def score(path,rows,tasks,G,private_root):
    forecast=verified(path);table=forecast['per_task']
    index={t:i for i,t in enumerate(table['task_id'])}
    if len(tasks)!=32 or len(set(tasks))!=32 or set(tasks)!=set(forecast['v4_g0']['tasks']):
        raise ValueError('forecast/G0 seeded cohort differs')
    counts=[]
    for task in tasks:
        own=[r for r in rows if r['task_id']==task]
        if len(own)!=32 or len({r['sample_idx'] for r in own})!=32:raise ValueError('G0 inventory incomplete')
        s=sum(r['strict']==1 for r in own);missing=sum(r['strict'] is None for r in own)
        counts.append({'task_id':task,'successes':s,'missing':missing,
                       **{k:table[k][index[task]] for k in FIELDS}})
    private_root=Path(private_root);private_root.mkdir(parents=True,exist_ok=True)
    write_new(private_root/'private_forecast_join.json',{'forecast_sha256':FORECAST_SHA256,'rows':counts})
    # Missing outcomes are never invented; complete-cohort estimate plus completion ranges.
    complete=[r for r in counts if r['missing']==0]
    y=[q8(r['successes']) for r in complete];mixed=[1<=r['successes']<=31 for r in complete]
    rng=np.random.default_rng(1304019)
    draws=rng.integers(len(complete),size=(10000,len(complete))) if complete else []
    metrics={}
    for field in FIELDS:
        x=[r[field] for r in complete];rho=correlation(x,y);a=auc(x,mixed)
        boot_r=[];boot_a=[]
        for draw in draws:
            r=correlation([x[i] for i in draw],[y[i] for i in draw]);b=auc([x[i] for i in draw],[mixed[i] for i in draw])
            if r is not None:boot_r.append(r)
            if b is not None:boot_a.append(b)
        metrics[field]={'spearman':rho,'auc_mixed_1_to_31':a,
             'spearman_ci95':np.quantile(boot_r,[.025,.975]).tolist() if boot_r else None,
             'auc_ci95':np.quantile(boot_a,[.025,.975]).tolist() if boot_a else None,
             'defined_bootstrap_draws':{'spearman':len(boot_r),'auc':len(boot_a)},'p_value':None}
    mean=float(np.mean(y)) if y else None
    result={'forecast_verified':True,'forecast_sha256':FORECAST_SHA256,'descriptive_only':True,
        'gate_input':False,'declared_tasks':32,'complete_tasks':len(complete),
        'missing_slots':sum(r['missing'] for r in counts),'forecasts':metrics,'mean_qhat8':mean,
        'mean_qhat8_ci95':np.quantile([np.mean([y[i] for i in d]) for d in draws],[.025,.975]).tolist() if y else None,
        'chosen_G':G,'uncertainty':'10000 whole-task bootstrap draws; complete tasks only; undefined draws counted; no model/calibration uncertainty',
        'p_value':None,'mean_qhat8_full_cohort_bounds':[
            sum(min(q8(s) for s in range(r['successes'],r['successes']+r['missing']+1)) for r in counts)/32,
            sum(max(q8(s) for s in range(r['successes'],r['successes']+r['missing']+1)) for r in counts)/32]}
    write_new(private_root/'forecast_aggregates.json',result)
    return result
