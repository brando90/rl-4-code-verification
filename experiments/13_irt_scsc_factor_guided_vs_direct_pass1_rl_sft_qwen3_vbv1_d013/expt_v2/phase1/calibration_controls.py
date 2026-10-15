"""Validate train marginal calibration using frozen objectives and the actual denominator pattern."""
from pathlib import Path
import sys
import hashlib
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,betaln

# No fit occurs on import; the execution driver verifies the published method first.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'prediction'))
from irt_v2 import ability_scale,START_SEEDS,IdentificationError,fit_2pl
from marginal_v2 import bb_objective,fit_beta_binomial


def connected(trials):
    n=np.asarray(trials)
    if n.ndim==3:n=n.sum(axis=2)
    if n.shape[0]<3 or n.shape[1]<3 or np.any(n.sum(axis=0)==0) or np.any(n.sum(axis=1)==0):
        return False
    ps={0};js=set()
    while True:
        next_j={j for p in ps for j in np.flatnonzero(n[p]>0)}
        next_p={p for j in next_j for p in np.flatnonzero(n[:,j]>0)}
        if next_p==ps and next_j==js:break
        ps,js=next_p,next_j
    return len(ps)==n.shape[0] and len(js)==n.shape[1]


def prior_objective(x,y,n,prior_scale):
    """Sensitivity changes only the declared difficulty and log-discrimination prior scales."""
    loss,gradient=bb_objective(x,y,n)
    policies,items,_=y.shape;b=x[policies:policies+items];loga=x[policies+items:policies+2*items]
    change=1/prior_scale**2-1
    loss+=change*(np.sum(b*b)/8+np.sum(loga*loga)/.5)
    gradient[policies:policies+items]+=change*b/4
    gradient[policies+items:policies+2*items]+=change*loga/.25
    return float(loss),gradient


def fit_bb_prior(y,n,prior_scale):
    y,n=np.asarray(y,float),np.asarray(n,float)
    if prior_scale==1.:return fit_beta_binomial(y,n)
    if prior_scale not in (.5,2.):raise ValueError('unfrozen prior scale')
    if not connected(n):raise IdentificationError('unconnected marginal denominator pattern')
    policies,items,_=y.shape;starts=[];values=[];grids=[]
    for seed in START_SEEDS:
        rng=np.random.default_rng(seed)
        x=np.r_[np.linspace(-1.5,1.5,policies)+rng.normal(0,.15,policies),rng.normal(0,.1,items),rng.normal(0,.05,items),np.log(20.)]
        bounds=[(None,None)]*(policies+items)+[(np.log(.1),np.log(5.))]*items+[(np.log(.05),np.log(10000.))]
        result=minimize(prior_objective,x,args=(y,n,prior_scale),jac=True,method='L-BFGS-B',bounds=bounds,
                        options={'maxiter':2000,'maxls':50,'ftol':1e-10,'gtol':1e-7,'maxcor':20})
        theta,_=ability_scale(result.x[:policies]);b=result.x[policies:policies+items];a=np.exp(result.x[policies+items:policies+2*items])
        grid=expit(a[None,:]*(np.linspace(-3,3,25)[:,None]-b))
        starts.append({'seed':seed,'converged':bool(result.success),'objective':float(result.fun),
                       'finite':bool(np.isfinite(result.fun) and np.isfinite(result.jac).all()),'iterations':int(result.nit)})
        values.append({'theta':theta,'a':a,'b':b,'logphi':float(result.x[-1])});grids.append(grid)
    disagreement=float(np.max(np.ptp(np.stack(grids),axis=0)));best=int(np.argmin([s['objective'] for s in starts]))
    return {**values[best],'starts':starts,'probability_disagreement':disagreement,
            'admitted':all(s['converged'] and s['finite'] for s in starts) and disagreement<=.02}


def numerical_controls():
    rng=np.random.default_rng(1302152);n=rng.integers(0,15,size=(3,5,8));y=rng.binomial(n,.4)
    x=np.r_[[-1.2,0,1.2],rng.normal(0,.2,5),rng.normal(0,.1,5),np.log(20.)]
    errors={}
    for prior in (1.,.5,2.):
        loss,grad=prior_objective(x,y,n,prior);finite=[]
        for k in range(len(x)):
            step=np.zeros_like(x);step[k]=1e-5
            finite.append((prior_objective(x+step,y,n,prior)[0]-prior_objective(x-step,y,n,prior)[0])/2e-5)
        errors[str(prior)]=float(np.max(np.abs(grad-finite))) if np.isfinite(loss) and np.isfinite(grad).all() else float('inf')
    theta=np.array([-1.,0.,1.]);a=np.array([.5,1.,2.]);b=np.array([-.2,0,.7])
    before=expit(a*(theta[:,None]-b));after=expit((a/2.3)*((2.3*theta+1.2)[:,None]-(2.3*b+1.2)))
    invariance=float(np.max(np.abs(before-after)))
    fixed_y=np.array([[0,1,2],[1,2,3],[2,3,4]]);fixed_n=np.full((3,3),5)
    def ll(q):return float(np.sum(betaln(fixed_y+q*20,fixed_n-fixed_y+(1-q)*20)-betaln(q*20,(1-q)*20)))
    likelihood_error=abs(ll(before)-ll(after))
    return {'status':'PASS' if max(errors.values())<=1e-5 and invariance<=1e-12 and likelihood_error<=1e-9 else 'FAIL',
            'gradient_max_absolute_errors':errors,'gradient_tolerance':1e-5,'invariance_error':invariance,
            'invariance_tolerance':1e-12,'likelihood_invariance_error':likelihood_error,'likelihood_invariance_tolerance':1e-9,'fixed_initializations':list(START_SEEDS),'seed':1302152}


def recover_denominators(n,*,seed=1302041):
    """Keep every actual zero and per-output denominator; draw one fixed synthetic replicate."""
    n=np.asarray(n,int);receipt={'seed':seed,'shape':list(n.shape),'zero_cells':int((n==0).sum()),
        'total_denominator':int(n.sum()),'pattern_sha256':hashlib.sha256(n.astype('<i8').tobytes()).hexdigest()}
    if not connected(n):return {**receipt,'status':'FAIL','reason':'empty or disconnected denominator pattern'}
    rng=np.random.default_rng(seed);theta=np.linspace(-1.7,1.7,n.shape[0]);theta=(theta-theta.mean())/theta.std()
    a=np.exp(rng.normal(0,.2,n.shape[1]));b=rng.normal(0,1,n.shape[1]);truth=expit(a*(theta[:,None]-b))
    latent=rng.beta(truth[:,:,None]*20,(1-truth[:,:,None])*20,size=n.shape);y=rng.binomial(n,latent)
    try:fitted=fit_beta_binomial(y,n)
    except IdentificationError as exc:return {**receipt,'status':'FAIL','reason':str(exc)}
    prediction=expit(fitted['a']*(fitted['theta'][:,None]-fitted['b']))
    corr=float(np.corrcoef(theta,fitted['theta'])[0,1]);error=float(np.mean(np.abs(prediction-truth)))
    return {**receipt,'status':'PASS' if fitted['admitted'] and corr>=.8 and error<=.08 else 'FAIL',
        'ability_correlation':corr,'probability_mean_absolute_error':error,'starts':fitted['starts'],
        'probability_disagreement':fitted['probability_disagreement'],
        'threshold_source':'same .80 ability correlation/.08 probability error controls as frozen recovery_v2; one fixed synthetic replicate'}
