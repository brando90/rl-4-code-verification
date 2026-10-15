"""Prospective, five-start current-ability refits with fixed train-anchor item parameters."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, betaln, digamma

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'prediction'))
from irt_v2 import START_SEEDS
from arm_rewards import marginal_arrays


def objective(x,y,n,a,b,logphi,prior_sd=1.):
    theta=float(x[0]);q=np.clip(expit(a*(theta-b)),1e-12,1-1e-12)
    phi=np.exp(logphi);alpha=q*phi;beta=(1-q)*phi
    loss=-np.sum(betaln(y+alpha,n-y+beta)-betaln(alpha,beta))
    gradient=-np.sum(phi*(digamma(y+alpha)-digamma(alpha)-digamma(n-y+beta)+digamma(beta))*q*(1-q)*a)
    return float(loss+.5*(theta/prior_sd)**2),np.array([gradient+theta/prior_sd**2])


def fit(y,n,a,b,logphi,*,prior_sd=1.):
    """For n=1 the frozen beta-binomial likelihood is exactly Bernoulli."""
    starts=[];values=[];probabilities=[];gradient_errors=[]
    for seed in START_SEEDS:
        x=np.array([np.random.default_rng(seed).normal(0,1)])
        loss,gradient=objective(x,y,n,a,b,logphi,prior_sd)
        delta=np.array([1e-5])
        finite_difference=(objective(x+delta,y,n,a,b,logphi,prior_sd)[0]-objective(x-delta,y,n,a,b,logphi,prior_sd)[0])/2e-5
        gradient_errors.append(float(abs(gradient[0]-finite_difference)))
        result=minimize(objective,x,args=(y,n,a,b,logphi,prior_sd),jac=True,method='L-BFGS-B',
            options={'maxiter':2000,'maxls':50,'ftol':1e-10,'gtol':1e-7,'maxcor':20})
        finite=bool(np.isfinite(result.fun) and np.isfinite(result.jac).all() and np.isfinite(loss+gradient).all())
        starts.append({'seed':seed,'converged':bool(result.success),'finite':finite,
            'objective':float(result.fun),'iterations':int(result.nit)})
        values.append(float(result.x[0]));probabilities.append(expit(a*(result.x[0]-b)))
    spread=float(np.ptp(np.stack(probabilities),axis=0).max())
    best=int(np.argmin([s['objective'] for s in starts]));error=max(gradient_errors)
    return {'ability':values[best],'starts':starts,'probability_disagreement':spread,
        'finite_gradient_max_error':error,'prior_sd':prior_sd,
        'admitted':all(s['converged'] and s['finite'] for s in starts) and spread<=.02 and error<=1e-5}


def counts(rows,tasks,component,*,current_update):
    if current_update<11 or (current_update-1)%10 or not rows:
        raise ValueError('refit is before updates 11,21,... using prior train rollouts')
    if len({r['cell_id'] for r in rows})!=len(rows):raise ValueError('duplicate prior rollout')
    index={t:i for i,t in enumerate(tasks)};y=[];n=[];indices=[]
    for row in rows:
        if row['split']!='train' or row['task_id'] not in index or not 1<=row['update']<current_update or row['arm']!='C':
            raise ValueError('refit requires only this C run earlier train rollouts')
        if row['status']!='measured':value=total=0
        elif component=='t':value=row['t'];total=1
        else:value=row[component]['numerator'];total=row[component]['denominator']
        if type(value) is not int or type(total) is not int or not 0<=value<=total:
            raise ValueError('invalid measured component count')
        y.append(value);n.append(total);indices.append(index[row['task_id']])
    if len({r['run_seed'] for r in rows})!=1:raise ValueError('mixed C run seeds')
    return np.array(y,float),np.array(n,float),np.array(indices,int)


def recover(n,a,b,logphi,*,seed=1302241):
    """One seeded synthetic draw at four fixed abilities, preserving each real missing denominator."""
    truth=np.array([-1.5,-.5,.5,1.5]);rng=np.random.default_rng(seed);estimates=[];errors=[];admitted=True
    phi=np.exp(logphi)
    for theta in truth:
        q=np.clip(expit(a*(theta-b)),1e-12,1-1e-12)
        y=rng.binomial(n.astype(int),rng.beta(q*phi,(1-q)*phi))
        result=fit(y,n,a,b,logphi);admitted=admitted and result['admitted']
        estimates.append(result['ability']);errors.append(np.mean(abs(expit(a*(result['ability']-b))-q)))
    correlation=float(np.corrcoef(truth,estimates)[0,1]);mae=float(np.mean(errors))
    return {'seed':seed,'true_abilities':truth.tolist(),'recovered_abilities':estimates,
        'ability_correlation':correlation,'probability_mean_absolute_error':mae,
        'status':'PASS' if admitted and correlation>=.8 and mae<=.08 else 'FAIL'}


def refit(rows,tasks,models,*,current_update,save):
    """Persist each component once. Caller must hold an exclusive, published execution attempt."""
    arrays=marginal_arrays(models,tasks);out={};abilities=[]
    for component in ('d','t','p'):
        y,n,index=counts(rows,tasks,component,current_update=current_update)
        a=arrays[component]['a'][index];b=arrays[component]['b'][index]
        logphi=float(arrays[component].get('logphi',np.log(20.)))
        if not np.isfinite(logphi) or not np.log(.05)<=logphi<=np.log(10000.):raise ValueError('invalid frozen dispersion')
        receipt={'component':component,'current_update':current_update,'declared_cells':len(rows),
            'empty_cells':int((n==0).sum()),'total_denominator':int(n.sum()),
            'pattern_sha256':hashlib.sha256(np.column_stack([index,n]).astype('<i8').tobytes()).hexdigest()}
        if n.sum()==0 or y.sum()==0 or y.sum()==n.sum():
            receipt.update(admitted=False,reason='empty or constant observed risk set; prior alone is not identification')
            save(component,receipt);out[component]=receipt;continue
        q=expit(a*(.37-b));transformed=expit((a/2.3)*((.37*2.3+1.2)-(b*2.3+1.2)))
        phi=np.exp(logphi)
        def ll(p):return np.sum(betaln(y+p*phi,n-y+(1-p)*phi)-betaln(p*phi,(1-p)*phi))
        invariance=float(abs(ll(q)-ll(transformed)))
        receipt['likelihood_invariance_error']=invariance
        receipt['recovery']=recover(n,a,b,logphi)
        receipt['fits']={str(sd):fit(y,n,a,b,logphi,prior_sd=sd) for sd in (1.,.5,2.)}
        fitted=receipt['fits']['1.0'];prediction=expit(a*(fitted['ability']-b));active=n>0;observed=y[active]/n[active]
        receipt['in_sample_calibration']={'observed_mean':float(observed.mean()),'predicted_mean':float(prediction[active].mean()),
            'mean_bias':float((prediction[active]-observed).mean()),'mean_absolute_error':float(abs(prediction[active]-observed).mean())}
        receipt['admitted']=bool(invariance<=1e-9 and receipt['recovery']['status']=='PASS' and all(f['admitted'] for f in receipt['fits'].values()))
        save(component,receipt);out[component]=receipt;abilities.append(fitted['ability'])
    admitted=all(r['admitted'] for r in out.values())
    return {'condition':'v2-S2','admitted':admitted,'abilities':abilities if admitted else None,
        'components':out,'failure_action':'stop C; never reuse or substitute weights'}
