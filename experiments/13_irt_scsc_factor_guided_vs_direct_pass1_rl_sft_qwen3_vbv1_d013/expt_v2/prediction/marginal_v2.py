#!/usr/bin/env python3
"""Fit train-anchor beta-binomial component models and freeze positive per-group gradient weights."""
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, betaln, digamma
sys.path.insert(0,str(Path(__file__).resolve().parent))
from irt_v2 import fit_2pl, ability_scale, IdentificationError, START_SEEDS


def bb_objective(x,y,n,*,fixed_items=None):
    """Per-output beta-binomial counts; zero denominators carry no likelihood information."""
    policies,items,_=y.shape
    if fixed_items is None:
        theta,scale=ability_scale(x[:policies]);b=x[policies:policies+items];loga=x[policies+items:policies+2*items]
        logphi=x[-1]
    else:
        theta=x;b,loga,logphi=fixed_items;scale=None
    a=np.exp(loga);phi=np.exp(logphi);eta=a[None,:]*(theta[:,None]-b[None,:]);q=expit(eta)
    # Bounded logits prevent undefined beta functions at a rounded probability of one.
    q=np.clip(q,1e-12,1-1e-12);alpha=q[:,:,None]*phi;beta=(1-q[:,:,None])*phi
    likelihood=betaln(y+alpha,n-y+beta)-betaln(alpha,beta)
    loss=-np.sum(likelihood)
    da=digamma(y+alpha)-digamma(alpha);db=digamma(n-y+beta)-digamma(beta)
    score=-phi*np.sum(da-db,axis=2)*q*(1-q)
    gt=np.sum(score*a[None,:],axis=1)
    if fixed_items is not None:
        return float(loss+.5*np.sum(theta**2)),gt+theta
    gu=(gt-gt.mean()-theta*np.mean(gt*theta))/scale
    gb=-np.sum(score*a[None,:],axis=0)+b/4
    ga=np.sum(score*eta,axis=0)+loga/.25
    gphi=-phi*np.sum(q[:,:,None]*da+(1-q[:,:,None])*db-digamma(n+phi)+digamma(phi))+(logphi-np.log(20.))
    loss+=np.sum(b*b)/8+np.sum(loga*loga)/.5+.5*np.sum(theta*theta)+.5*(logphi-np.log(20.))**2
    mean=x[:policies].mean();loss+=.5*policies*(mean**2+(scale-1)**2);gu+=mean+(scale-1)*theta
    return float(loss),np.concatenate([gu,gb,ga,[gphi]])


def fit_beta_binomial(y,n):
    y,n=np.asarray(y,float),np.asarray(n,float)
    if y.shape!=n.shape or y.ndim!=3 or np.any(y<0) or np.any(y>n) or not np.all(np.isfinite(y+n)):
        raise ValueError('invalid per-output component counts')
    policies,items,_=y.shape
    if policies<3 or np.any(n.sum(axis=(1,2))==0) or np.any(n.sum(axis=(0,2))==0):
        raise IdentificationError('unidentified anchor component risk set')
    if y.sum()==0 or y.sum()==n.sum():raise IdentificationError('constant anchor component')
    starts=[];values=[];grids=[]
    for seed in START_SEEDS:
        rng=np.random.default_rng(seed)
        x=np.concatenate([np.linspace(-1.5,1.5,policies)+rng.normal(0,.15,policies),rng.normal(0,.1,items),rng.normal(0,.05,items),[np.log(20.)]])
        bounds=[(None,None)]*(policies+items)+[(np.log(.1),np.log(5.))]*items+[(np.log(.05),np.log(10000.))]
        result=minimize(bb_objective,x,args=(y,n),jac=True,method='L-BFGS-B',bounds=bounds,
                        options={'maxiter':2000,'maxls':50,'ftol':1e-10,'gtol':1e-7,'maxcor':20})
        theta,_=ability_scale(result.x[:policies]);b=result.x[policies:policies+items];a=np.exp(result.x[policies+items:policies+2*items])
        grid=expit(a[None,:]*(np.linspace(-3,3,25)[:,None]-b))
        starts.append({'seed':seed,'converged':bool(result.success),'objective':float(result.fun),'finite':bool(np.isfinite(result.fun) and np.all(np.isfinite(result.jac)))})
        grids.append(grid);values.append({'theta':theta,'b':b,'a':a,'logphi':float(result.x[-1])})
    disagreement=float(np.max(np.ptp(np.stack(grids),axis=0)));best=int(np.argmin([s['objective'] for s in starts]))
    return {**values[best],'starts':starts,'probability_disagreement':disagreement,
            'admitted':all(s['converged'] and s['finite'] for s in starts) and disagreement<=.02}


def fit_anchor_panel(rows,policies,tasks):
    if len(policies)<3 or len(set(policies))!=len(policies):raise IdentificationError('three distinct anchor policies required')
    if any(r['split']!='train' for r in rows):raise ValueError('anchor fitting accepts train only')
    table={(r['policy'],r['task_id'],r['sample_idx']):r for r in rows}
    if len(table)!=len(rows) or set(table)!={(p,t,s) for p in policies for t in tasks for s in range(8)}:
        raise ValueError('incomplete or duplicated anchor manifest')
    models={}
    for component in ('d','t','p'):
        y=np.zeros((len(policies),len(tasks),8));n=np.zeros_like(y)
        for i,policy in enumerate(policies):
            for j,task in enumerate(tasks):
                for k in range(8):
                    row=table[(policy,task,k)]
                    if row['status']!='measured':raise IdentificationError('unmeasured anchor cell')
                    value=row[component]
                    y[i,j,k]=value if component=='t' else value['numerator'];n[i,j,k]=1 if component=='t' else value['denominator']
        if component=='t':
            fitted=fit_2pl(y.sum(axis=2),n.sum(axis=2),np.arange(len(policies))[:,None])
            models[component]={'theta':fitted.theta,'a':fitted.a,'b':fitted.b,'admitted':fitted.admitted,'starts':fitted.starts,'probability_disagreement':fitted.max_probability_disagreement}
        else:models[component]=fit_beta_binomial(y,n)
    return models


def gradient_weights(models,abilities):
    a=np.column_stack([models[k]['a'] for k in ('d','t','p')]);b=np.column_stack([models[k]['b'] for k in ('d','t','p')])
    q=expit(a*(np.asarray(abilities)[None,:]-b));raw=a*np.maximum(1-q,np.finfo(float).eps)
    return raw/raw.sum(axis=1,keepdims=True)


def weighted_reward(parts,weights,strict):
    if strict==1:return 1.
    if not parts['e'] or not parts['n_examples'] or not parts['p']['denominator'] or parts['raw_vacuity_hits']:return 0.
    values=[parts['d']['numerator']/parts['d']['denominator'] if parts['d']['denominator'] else 0.,parts['t'],parts['p']['numerator']/parts['p']['denominator']]
    weights=np.asarray(weights,float)
    if weights.shape!=(3,) or np.any(weights<=0) or abs(weights.sum()-1)>1e-10:raise ValueError('invalid frozen group weights')
    return float(np.exp(np.sum(weights*np.log(np.maximum(.01,values)))))


def update_ability(prior_rollouts,model,component,*,current_update):
    """Use only earlier train updates and frozen item parameters; no current-group feedback."""
    if not prior_rollouts or any(r['split']!='train' or r.get('update',current_update)>=current_update for r in prior_rollouts):
        raise ValueError('ability refit requires identified earlier train updates')
    indexes=np.array([r['item_index'] for r in prior_rollouts],int)
    y=np.array([r[component] if component=='t' else r[component]['numerator'] for r in prior_rollouts],float)
    n=np.array([1 if component=='t' else r[component]['denominator'] for r in prior_rollouts],float)
    a,b=model['a'][indexes],model['b'][indexes];phi=np.exp(model.get('logphi',np.log(20.)))
    def loss(x):
        q=np.clip(expit(a*(x[0]-b)),1e-12,1-1e-12);alpha=q*phi;beta=(1-q)*phi
        value=-np.sum(betaln(y+alpha,n-y+beta)-betaln(alpha,beta))+.5*x[0]**2
        gradient=-np.sum(phi*(digamma(y+alpha)-digamma(alpha)-digamma(n-y+beta)+digamma(beta))*q*(1-q)*a)+x[0]
        return float(value),np.array([gradient])
    result=minimize(loss,np.array([0.]),jac=True,method='L-BFGS-B',options={'maxiter':2000,'ftol':1e-10,'gtol':1e-7})
    if not result.success or not np.isfinite(result.fun):raise IdentificationError('current ability refit failed; C stops')
    return float(result.x[0])
