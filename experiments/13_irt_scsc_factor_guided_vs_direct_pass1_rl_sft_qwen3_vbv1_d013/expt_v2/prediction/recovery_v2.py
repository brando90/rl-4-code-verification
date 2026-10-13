#!/usr/bin/env python3
"""Validate synthetic parameter recovery under an unchanged observed risk-count pattern before interpreting fitted abilities."""
from pathlib import Path
import sys
import numpy as np
from scipy.special import expit
sys.path.insert(0,str(Path(__file__).resolve().parent))
from irt_v2 import fit_2pl, IdentificationError


def recover_pattern(trials,*,seed=1302041):
    n=np.asarray(trials,int)
    active_p=np.flatnonzero(n.sum(axis=1)>0);active_j=np.flatnonzero(n.sum(axis=0)>0)
    n=n[np.ix_(active_p,active_j)]
    if n.shape[0]<3 or n.shape[1]<3:return {'status':'FAIL','reason':'insufficient connected risk information'}
    rng=np.random.default_rng(seed)
    theta=np.linspace(-1.7,1.7,n.shape[0]);theta=(theta-theta.mean())/theta.std()
    a=np.exp(rng.normal(0,.2,n.shape[1]));b=rng.normal(0,1,n.shape[1]);truth=expit(a[None,:]*(theta[:,None]-b))
    y=rng.binomial(n,truth)
    try:model=fit_2pl(y,n,theta[:,None])
    except IdentificationError as exc:return {'status':'FAIL','reason':str(exc),'seed':seed}
    fitted=expit(model.a[None,:]*(model.theta[:,None]-model.b))
    ability_correlation=float(np.corrcoef(theta,model.theta)[0,1]);error=float(np.mean(np.abs(fitted-truth)))
    return {'status':'PASS' if model.admitted and ability_correlation>=.8 and error<=.08 else 'FAIL',
            'ability_correlation':ability_correlation,'probability_mean_absolute_error':error,
            'active_policies':len(active_p),'active_items':len(active_j),'trials':int(n.sum()),
            'seed':seed,'starts':model.starts,'probability_disagreement':model.max_probability_disagreement,
            'threshold_source':'prospective implementation controls frozen in L1v2; not outcome-derived',
            'interpretation':'conditional on the observed missingness/risk-count pattern; one fixed synthetic recovery replicate'}
