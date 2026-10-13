#!/usr/bin/env python3
"""Fit identified two-parameter logistic models and integrate unseen-item random effects without held-out labels."""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logsumexp, ndtr, ndtri
from numpy.polynomial.legendre import leggauss

START_SEEDS = (1302011, 1302012, 1302013, 1302014, 1302015)
A_BOUNDS = (.1, 5.)
MAX_DISAGREEMENT = .02


class IdentificationError(ValueError):
    """A risk set or numerical fit cannot support the prespecified fitted condition."""


def ability_scale(u):
    centered = u - u.mean()
    scale = np.sqrt(np.mean(centered**2))
    if scale < 1e-10:
        raise IdentificationError('degenerate ability scale')
    return centered / scale, scale


def unpack(x, policies, items, features):
    theta, scale = ability_scale(x[:policies])
    residual = x[policies:policies+items]
    loga = x[policies+items:policies+2*items]
    beta = x[policies+2*items:]
    b = residual + features @ beta
    return theta, scale, residual, loga, beta, b


def objective(x, successes, trials, features, prior_scale=1.):
    """Binomial log likelihood with analytic gradient; zero trial cells contribute nothing."""
    policies, items = trials.shape
    theta, scale, residual, loga, beta, b = unpack(x, policies, items, features)
    a = np.exp(loga)
    eta = a[None,:] * (theta[:,None] - b[None,:])
    loss = np.sum(trials*np.logaddexp(0, eta) - successes*eta)
    score = trials*expit(eta) - successes
    gtheta = np.sum(score*a[None,:],axis=1)
    gu = (gtheta-gtheta.mean()-theta*np.mean(gtheta*theta))/scale
    likelihood_b = -np.sum(score*a[None,:],axis=0)
    gb = likelihood_b + residual/(4*prior_scale**2)
    ga = np.sum(score*eta,axis=0) + loga/(.25*prior_scale**2)
    gbet = features.T@likelihood_b + beta/(4*prior_scale**2)
    loss += .5*np.sum(theta**2) + np.sum(residual**2)/(8*prior_scale**2)
    loss += np.sum(loga**2)/(.5*prior_scale**2) + np.sum(beta**2)/(8*prior_scale**2)
    # This fixes the redundant raw-coordinate gauge without altering theta's identified scale.
    mean = x[:policies].mean()
    loss += .5*policies*(mean**2+(scale-1)**2)
    gu += mean+(scale-1)*theta
    return float(loss), np.concatenate([gu,gb,ga,gbet])


@dataclass
class Fit:
    theta: np.ndarray
    a: np.ndarray
    b: np.ndarray
    beta: np.ndarray
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    ability_regression: np.ndarray
    starts: list
    max_probability_disagreement: float
    admitted: bool
    prior_scale: float = 1.

    def forecast_ability(self, metadata):
        return np.column_stack([np.ones(len(metadata)),np.asarray(metadata,float)]) @ self.ability_regression

    def seen_items(self, metadata):
        theta=self.forecast_ability(metadata)
        return expit(self.a[None,:]*(theta[:,None]-self.b[None,:]))

    def unseen_items(self, metadata, features, quadrature_points=31):
        """Integrate fixed-prior item effects conditional on training-fitted hierarchy coefficients."""
        x=(np.asarray(features,float)-self.feature_mean)/self.feature_scale
        centers=x@self.beta
        theta=self.forecast_ability(metadata)
        nodes,weights=leggauss(quadrature_points)
        u=(nodes+1)/2;weights=weights/2
        b_noise=2*self.prior_scale*ndtri(u)
        lo,hi=ndtr(np.log(A_BOUNDS)/(.5*self.prior_scale))
        a_nodes=np.exp(.5*self.prior_scale*ndtri(lo+(hi-lo)*u))
        values=expit(a_nodes[None,None,None,:]*(theta[:,None,None,None]-centers[None,:,None,None]-b_noise[None,None,:,None]))
        return np.einsum('pijk,j,k->pi',values,weights,weights)


def fit_2pl(successes, trials, metadata, features=None, *, prior_scale=1.):
    successes,trials=np.asarray(successes,float),np.asarray(trials,float)
    if successes.shape != trials.shape or successes.ndim!=2 or np.any(~np.isfinite(successes)) or np.any(~np.isfinite(trials)):
        raise ValueError('invalid binomial arrays')
    if np.any(successes<0) or np.any(successes>trials) or np.any(trials<0):
        raise ValueError('invalid counts')
    policies,items=trials.shape
    if policies<3 or items<3 or np.any(trials.sum(axis=1)==0) or np.any(trials.sum(axis=0)==0):
        raise IdentificationError('empty risk-set policy/item or insufficient connected panel')
    if successes.sum()==0 or successes.sum()==trials.sum():
        raise IdentificationError('constant risk-set outcome')
    # Connectivity prevents unrelated policy/item scales from being pooled silently.
    reached_p={0};reached_j=set()
    while True:
        js={j for p in reached_p for j in np.flatnonzero(trials[p]>0)}
        ps={p for j in js for p in np.flatnonzero(trials[:,j]>0)}
        if ps==reached_p and js==reached_j:break
        reached_p,reached_j=ps,js
    if len(reached_p)!=policies or len(reached_j)!=items:
        raise IdentificationError('disconnected risk set')
    metadata=np.asarray(metadata,float)
    if metadata.ndim!=2 or metadata.shape[0]!=policies or not np.all(np.isfinite(metadata)):
        raise ValueError('invalid policy metadata')
    features=np.zeros((items,0)) if features is None else np.asarray(features,float)
    if features.ndim!=2 or features.shape[0]!=items or not np.all(np.isfinite(features)):
        raise ValueError('invalid item features')
    fm=features.mean(axis=0);fs=features.std(axis=0);fs=np.where(fs>0,fs,1.)
    features=(features-fm)/fs
    starts=[];candidates=[];grids=[]
    for seed in START_SEEDS:
        rng=np.random.default_rng(seed)
        u=np.linspace(-1.5,1.5,policies)+rng.normal(0,.15,policies)
        x=np.concatenate([u,rng.normal(0,.1,items),rng.normal(0,.05,items),np.zeros(features.shape[1])])
        bounds=[(None,None)]*(policies+items)+[(np.log(.1),np.log(5.))]*items+[(None,None)]*features.shape[1]
        result=minimize(objective,x,args=(successes,trials,features,prior_scale),jac=True,method='L-BFGS-B',bounds=bounds,
                        options={'maxiter':2000,'maxls':50,'ftol':1e-10,'gtol':1e-7,'maxcor':20})
        theta,_,residual,loga,beta,b=unpack(result.x,policies,items,features)
        a=np.exp(loga)
        grid=expit(a[None,:]*(np.linspace(-3,3,25)[:,None]-b[None,:]))
        gradients=objective(result.x,successes,trials,features,prior_scale)[1]
        finite=bool(np.all(np.isfinite(gradients)) and np.all(np.isfinite(grid)))
        starts.append({'seed':seed,'converged':bool(result.success),'finite':finite,'objective':float(result.fun),
                       'iterations':int(result.nit),'gradient_max':float(np.max(np.abs(gradients))), 'message':str(result.message)})
        candidates.append((theta,a,b,beta));grids.append(grid)
    disagreement=float(np.max(np.ptp(np.stack(grids),axis=0)))
    best=int(np.argmin([s['objective'] for s in starts]));theta,a,b,beta=candidates[best]
    design=np.column_stack([np.ones(policies),metadata])
    regression=np.linalg.lstsq(design,theta,rcond=1e-10)[0]
    admitted=all(s['converged'] and s['finite'] for s in starts) and disagreement<=MAX_DISAGREEMENT
    return Fit(theta,a,b,beta,fm,fs,regression,starts,disagreement,admitted,prior_scale)


def conditional_counts(q1, compile_success, honest, observed, policy_index, item_index, shape):
    """Create each conditional risk set once; partial fractions never enter this likelihood."""
    q1,compile_success,honest,observed=map(lambda x:np.asarray(x,bool),(q1,compile_success,honest,observed))
    risk_sets=(observed,observed&q1,observed&q1&compile_success)
    labels=(q1,compile_success,honest)
    out=[]
    for risk,label in zip(risk_sets,labels):
        n=np.zeros(shape);y=np.zeros(shape)
        np.add.at(n,(np.asarray(policy_index)[risk],np.asarray(item_index)[risk]),1)
        positive=risk&label
        np.add.at(y,(np.asarray(policy_index)[positive],np.asarray(item_index)[positive]),1)
        out.append((y,n))
    return out


def beta_baseline(earlier_successes, earlier_trials, training_successes, training_trials):
    y,n=np.asarray(earlier_successes,float),np.asarray(earlier_trials,float)
    pooled=(float(np.sum(training_successes))+1)/(float(np.sum(training_trials))+2)
    return np.where(n>0,(y+1)/(n+2),pooled)


def monotone_calibration(train_x, train_y, train_weight, predict_x):
    """Weighted pool-adjacent-violators calibration, trained only on admitted earlier/later pairs."""
    x,y,w=map(lambda a:np.asarray(a,float),(train_x,train_y,train_weight))
    if not (len(x)==len(y)==len(w)) or not len(x) or np.any(w<=0) or not np.all(np.isfinite(np.concatenate([x,y,w]))):
        raise ValueError('invalid calibration cohort')
    order=np.argsort(x,kind='stable');x,y,w=x[order],y[order],w[order]
    blocks=[]
    for value in np.unique(x):
        match=x==value
        blocks.append([value,value,float(w[match].sum()),float((y[match]*w[match]).sum())])
        while len(blocks)>1 and blocks[-2][3]/blocks[-2][2]>blocks[-1][3]/blocks[-1][2]:
            right=blocks.pop();left=blocks.pop()
            blocks.append([left[0],right[1],left[2]+right[2],left[3]+right[3]])
    knots={edge:b[3]/b[2] for b in blocks for edge in (b[0],b[1])}
    centers=np.array(sorted(knots));means=np.array([knots[k] for k in centers])
    return np.interp(np.asarray(predict_x,float),centers,means)
