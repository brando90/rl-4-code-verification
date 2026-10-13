#!/usr/bin/env python3
"""Produce M0–M3e forecasts from earlier-rung data only, with explicit unsupported-risk and stability receipts."""
from dataclasses import asdict
import hashlib
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from irt_v2 import fit_2pl, conditional_counts, beta_baseline, monotone_calibration, IdentificationError


FEATURES=('python_character_count','python_token_count','industry_domain','reference_theorem_count')


def fold(group_id, n=5, domain='outer'):
    # Preserve the version-1 outer assignment exactly; inner folds use a separate domain.
    key=group_id if domain=='outer' else domain+'\0'+group_id
    return int(hashlib.sha256(key.encode()).hexdigest(),16)%n


def policy_features(size_billions,cumulative_sft_tokens):
    size,tokens=np.asarray(size_billions,float),np.asarray(cumulative_sft_tokens,float)
    if np.any(size<=0) or np.any(tokens<0):raise ValueError('invalid size/compute metadata')
    return np.column_stack([np.log(size),np.log1p(tokens)])


def _fit_predict(y,n,metadata,features,target_metadata,target_features,target_item_indices,prior_scale=1.):
    active_p=np.flatnonzero(n.sum(axis=1)>0)
    active_j=np.flatnonzero(n.sum(axis=0)>0)
    reduced_y=y[np.ix_(active_p,active_j)];reduced_n=n[np.ix_(active_p,active_j)]
    model=fit_2pl(reduced_y,reduced_n,metadata[active_p],features[active_j],prior_scale=prior_scale)
    predictions=model.unseen_items(target_metadata,target_features)
    seen=model.seen_items(target_metadata)
    local={int(j):i for i,j in enumerate(active_j)}
    for column,item in enumerate(target_item_indices):
        if int(item) in local:predictions[:,column]=seen[:,local[int(item)]]
    receipt={'starts':model.starts,'probability_disagreement':model.max_probability_disagreement,
             'admitted':model.admitted,'risk_trials':int(n.sum()),'risk_successes':int(y.sum()),
             'active_policies':active_p.tolist(),'active_items':active_j.tolist(),
             'empty_policies':int(len(n)-len(active_p)),'empty_items':int(n.shape[1]-len(active_j)),
             'prior_scale':prior_scale}
    return predictions,receipt


def forecast_panel(*, history, policy_metadata, item_features, target_metadata,
                   target_features, target_item_indices, earlier_successes, earlier_trials,
                   earlier_reward, calibration_x, calibration_y, calibration_trials):
    """Targets carry metadata and earlier-rung evidence, never target outcomes or target factors.

    history indices are local to the admitted training policy/item arrays. A target item index
    of -1 means unseen; its random effects are integrated using training-only hierarchy fits.
    """
    meta,features,tmeta,tfeatures=map(lambda x:np.asarray(x,float),
                                    (policy_metadata,item_features,target_metadata,target_features))
    pidx,jidx=np.asarray(history['policy_index'],int),np.asarray(history['item_index'],int)
    observed=np.asarray(history['observed'],bool);strict=np.asarray(history['strict'],float)
    shape=(len(meta),len(features));n=np.zeros(shape);y=np.zeros(shape)
    np.add.at(n,(pidx[observed],jidx[observed]),1)
    positive=observed&(strict==1)
    np.add.at(y,(pidx[positive],jidx[positive]),1)
    predictions={'M0':beta_baseline(earlier_successes,earlier_trials,y,n),
                 'M1':monotone_calibration(calibration_x,calibration_y,calibration_trials,earlier_reward)}
    receipts={}
    hurdle=conditional_counts(history['q1'],history['compile'],history['honest'],observed,pidx,jidx,shape)
    nested=(np.asarray(history['q1'],bool)&np.asarray(history['compile'],bool)&np.asarray(history['honest'],bool))
    chain_disagreements=int(np.sum(observed&(nested!=(strict==1))))
    for name,counts,xf,tf in [('M2',[(y,n)],np.zeros((len(features),0)),np.zeros((len(tfeatures),0))),
                               ('M3',hurdle,np.zeros((len(features),0)),np.zeros((len(tfeatures),0))),
                               ('M3e',hurdle,features,tfeatures)]:
        receipt={'components':[],'errors':[],'chain_disagreements':chain_disagreements if name!='M2' else 0}
        all_parts=[]
        for k,(successes,trials) in enumerate(counts):
            parts={}
            for prior in (1.,.5,2.):
                try:
                    pred,detail=_fit_predict(successes,trials,meta,xf,tmeta,tf,target_item_indices,prior)
                    parts[prior]=(pred,detail)
                except (IdentificationError,ValueError,FloatingPointError) as exc:
                    receipt['errors'].append({'component':k,'prior_scale':prior,'error':str(exc)})
            if 1. not in parts:continue
            pred,detail=parts[1.]
            detail['prior_sensitivity']={str(prior):{'max_prediction_change':float(np.max(np.abs(other[0]-pred))),
                                                    'admitted':other[1]['admitted'],'starts':other[1]['starts']}
                                         for prior,other in parts.items() if prior!=1.}
            receipt['components'].append(detail);all_parts.append(pred)
        receipt['admitted']=bool(not receipt['errors'] and not receipt['chain_disagreements'] and
            len(all_parts)==len(counts) and all(c['admitted'] for c in receipt['components']))
        predictions[name]=np.prod(all_parts,axis=0) if len(all_parts)==len(counts) else None
        receipts[name]=receipt
    target_shape=(len(tmeta),len(tfeatures))
    for name,pred in predictions.items():
        if pred is not None and (pred.shape!=target_shape or np.any(~np.isfinite(pred))):
            raise ValueError('incomplete or non-finite forecast matrix: '+name)
    return predictions,receipts


def select_candidate(inner_predictions,inner_labels,inner_groups):
    """Select M3 versus M3e using only identical inner held-out cells; ties prefer M3."""
    from evaluation_v2 import log_loss
    if len(inner_labels)!=len(inner_groups):raise ValueError('inner prediction/group mismatch')
    losses={}
    for name in ('M3','M3e'):
        pred=inner_predictions.get(name)
        losses[name]=float('inf') if pred is None else log_loss(inner_labels,pred)
    if not any(np.isfinite(v) for v in losses.values()):raise IdentificationError('no admitted inner candidate')
    return min(losses,key=lambda n:(losses[n],n!='M3')),losses
