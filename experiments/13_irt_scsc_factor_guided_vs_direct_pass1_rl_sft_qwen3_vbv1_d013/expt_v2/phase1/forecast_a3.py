"""Preserve frozen model fits while an unavailable A3 reward predictor remains explicitly missing."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'prediction'))
from forecast_v2 import _fit_predict
from irt_v2 import beta_baseline,monotone_calibration,conditional_counts,IdentificationError

def forecast_a3(*, history, policy_metadata, item_features, target_metadata,
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
    predictions={'M0':beta_baseline(earlier_successes,earlier_trials,y,n)}
    receipts={}
    try:
        if not np.isfinite(earlier_reward).all():
            raise IdentificationError('wholly missing earlier reward predictor')
        predictions['M1']=monotone_calibration(calibration_x,calibration_y,calibration_trials,earlier_reward)
    except (IdentificationError,ValueError,FloatingPointError) as exc:
        predictions['M1']=None
        receipts['M1']={'admitted':False,'errors':[{'error':str(exc)}]}
    # M2/M3/M3e still use only their admitted observed histories. An unavailable
    # calibration baseline must not suppress the prespecified M2 report.

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
