"""Fit train marginal rewards and a separate conditional strict forecast without batch-2 outcomes."""
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
from scipy.special import expit,ndtr,ndtri
from numpy.polynomial.legendre import leggauss

from calibration_controls import connected,fit_bb_prior,numerical_controls,recover_denominators
from calibration_inputs import history,pattern_report
from fit_controls import pattern_controls
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'prediction'))
from irt_v2 import fit_2pl,conditional_counts,IdentificationError
from marginal_v2 import gradient_weights,weighted_reward
from recovery_v2 import recover_pattern


def fitted_record(fitted):
    return {'theta':fitted.theta,'a':fitted.a,'b':fitted.b,'starts':fitted.starts,
            'admitted':fitted.admitted,'probability_disagreement':fitted.max_probability_disagreement}


def probabilities(model):
    return expit(model['a'][None,:]*(model['theta'][:,None]-model['b'][None,:]))


def fit_component(y,n,component,prior=1.):
    if not connected(n):raise IdentificationError('empty or disconnected component panel')
    if component=='t':return fitted_record(fit_2pl(y.sum(axis=2),n.sum(axis=2),np.zeros((3,0)),prior_scale=prior))
    return fit_bb_prior(y,n,prior)


def calibration_diagnostic(y,n,q):
    """Describe posterior point predictions on calibration responses, never held-out accuracy."""
    valid=n>0;prediction=np.broadcast_to(q[:,:,None],n.shape)
    observed=np.divide(y,n,out=np.zeros_like(y,dtype=float),where=valid)
    rows=[]
    for policy in range(y.shape[0]):
        active=valid[policy];denominator=int(n[policy].sum());count=int(active.sum())
        rows.append({'policy_index':policy,'observed_outputs':count,'count_denominator':denominator,
            'observed_fraction_mean':float(observed[policy][active].mean()) if count else None,
            'predicted_fraction_mean':float(prediction[policy][active].mean()) if count else None,
            'mean_bias':float((prediction[policy]-observed[policy])[active].mean()) if count else None,
            'mean_absolute_error':float(np.abs(prediction[policy]-observed[policy])[active].mean()) if count else None,
            'observed_count_weighted_mean':float(y[policy].sum()/denominator) if denominator else None,
            'predicted_count_weighted_mean':float((n[policy]*prediction[policy]).sum()/denominator) if denominator else None})
    return {'scope':'in-sample posterior point-predictive calibration, not generalization or an added gate',
            'policies':rows}




def calibration_bins(y,n,q,groups):
    """Use the ten equally spaced bins frozen in L1, with response fractions as observations."""
    valid=n>0;pred=np.broadcast_to(q[:,:,None],n.shape)
    obs=np.divide(y,n,out=np.zeros_like(y,dtype=float),where=valid)
    group_grid=np.broadcast_to(np.asarray(groups)[None,:,None],n.shape)
    indices=np.minimum((pred*10).astype(int),9);result=[]
    for b in range(10):
        selected=valid&(indices==b)
        if selected.any():result.append({'bin':b,'responses':int(selected.sum()),
            'groups':len(np.unique(group_grid[selected])),'observed_mean':float(obs[selected].mean()),
            'predicted_mean':float(pred[selected].mean()),'mean_bias':float((pred-obs)[selected].mean())})
    return result

def calibration_intervals(y,n,q,groups,*,draws=10000,seed=1302031):
    """Resample complete train task groups, retaining all policies and response slots together."""
    groups=np.asarray(groups)
    if groups.shape!=(y.shape[1],) or draws<1:raise ValueError('unaligned calibration task groups')
    valid=n>0;pred=np.broadcast_to(q[:,:,None],n.shape)
    obs=np.divide(y,n,out=np.zeros_like(y,dtype=float),where=valid)
    per_item=np.stack([valid.sum(axis=2),(obs*valid).sum(axis=2),(pred*valid).sum(axis=2),
        ((pred-obs)*valid).sum(axis=2),(np.abs(pred-obs)*valid).sum(axis=2),
        n.sum(axis=2),y.sum(axis=2),(n*pred).sum(axis=2)],axis=2)
    unique=np.unique(groups);aggregate=np.stack([per_item[:,groups==g].sum(axis=1) for g in unique],axis=1)
    metrics=('observed_fraction_mean','predicted_fraction_mean','mean_bias','mean_absolute_error',
             'observed_count_weighted_mean','predicted_count_weighted_mean')
    samples=np.full((y.shape[0]+1,draws,6),np.nan);rng=np.random.default_rng(seed)
    for start in range(0,draws,100):
        size=min(100,draws-start);indices=rng.integers(0,len(unique),(size,len(unique)))
        totals=aggregate[:,indices,:].sum(axis=2)
        totals=np.concatenate([totals,totals.sum(axis=0,keepdims=True)],axis=0)
        for k in range(6):
            numerator=totals[:,:,k+1 if k<4 else k+2];denominator=totals[:,:,0 if k<4 else 5]
            samples[:,start:start+size,k]=np.divide(numerator,denominator,out=np.full_like(numerator,np.nan),where=denominator>0)
    return {'unit':'complete train task group, paired across policies and responses; fixed fitted predictions','draws':draws,'seed':seed,
        'groups':len(unique),'confidence':.95,'p_value':None,'p_value_reason':'descriptive in-sample calibration, no hypothesis test',
        'policies':[{'policy_index':i if i<y.shape[0] else 'pooled','metrics':{name:{'interval':np.nanquantile(samples[i,:,k],[.025,.975]).tolist()
            if np.isfinite(samples[i,:,k]).any() else [None,None],
            'defined_draws':int(np.isfinite(samples[i,:,k]).sum())} for k,name in enumerate(metrics)}} for i in range(y.shape[0]+1)]}

def fit_marginals(arrays,save):
    """Every declared fit/control is attempted once and persisted, including failed components."""
    models={};receipts={};numeric=numerical_controls();save('marginal_numerical_controls',numeric)
    for component,(y,n) in arrays['components'].items():
        receipt={'component':component,'errors':[],'priors':{},'controls':None}
        recovery=recover_pattern(n.sum(axis=2)) if component=='t' else recover_denominators(n)
        receipt['controls']=recovery;save(component+'_recovery',recovery)
        for prior in (1.,.5,2.):
            try:
                fitted=fit_component(y,n,component,prior);q=probabilities(fitted)
                detail={**fitted,'prior_scale':prior,'calibration':calibration_diagnostic(y,n,q)}
                if prior==1.:
                    detail['calibration_intervals']=calibration_intervals(y,n,q,arrays['groups'])
                    detail['calibration_bins']=calibration_bins(y,n,q,arrays['groups'])
                    interval=detail['calibration_intervals']['policies'][-1]['metrics']['mean_bias']['interval']
                    detail['calibration_bias_interval_contains_zero']=bool(interval[0] is not None and interval[0]<=0<=interval[1])
                receipt['priors'][str(prior)]=detail;save(component+'_prior_'+str(prior),detail)
                if prior==1.:models[component]=fitted
            except (IdentificationError,ValueError,FloatingPointError) as exc:
                error={'prior_scale':prior,'error_type':type(exc).__name__,'error':str(exc)}
                receipt['errors'].append(error);save(component+'_prior_'+str(prior),error)
        if component in models:
            reference=probabilities(models[component]);sensitivity={}
            for prior,model in receipt['priors'].items():
                if prior=='1.0':continue
                changes=np.max(np.abs(probabilities(model)-reference),axis=0)
                sensitivity[prior]={'max_probability_change':float(changes.max()),'per_item_max_change':changes,
                    'items_change_at_least_point_one':np.flatnonzero(changes>=.1),
                    'flag_scope':'descriptive sensitivity flag, not an additional gate threshold'}
            receipt['prior_sensitivity']=sensitivity
        receipt['admitted']=bool(numeric['status']=='PASS' and recovery['status']=='PASS' and not receipt['errors']
                                  and len(receipt['priors'])==3 and all(x['admitted'] for x in receipt['priors'].values())
                                  and receipt['priors']['1.0']['calibration_bias_interval_contains_zero'])
        receipts[component]=receipt;save(component+'_receipt',receipt)
    return models,receipts,numeric


def integrated_unseen(theta,prior=1.):
    """The frozen 31-node prior integration for an item with no observed risk-set data."""
    nodes,weights=leggauss(31);u=(nodes+1)/2;weights=weights/2
    b=2*prior*ndtri(u);lo,hi=ndtr(np.log([.1,5.])/(.5*prior))
    a=np.exp(.5*prior*ndtri(lo+(hi-lo)*u))
    return float(np.einsum('ij,i,j->',expit(a[None,:]*(theta-b[:,None])),weights,weights))


def fit_strict_forecast(arrays,save):
    """H2 forecasts multiply conditional hurdle probabilities, never marginal fractions."""
    h=history(arrays);shape=arrays['observed'].shape[:2]
    controls=pattern_controls(h,shape);save('strict_pattern_controls',controls)
    counts=conditional_counts(h['q1'],h['compile'],h['honest'],h['observed'],h['policy_index'],h['item_index'],shape)
    strict_n=arrays['observed'].sum(axis=2);strict_y=(arrays['strict']*arrays['observed']).sum(axis=2)
    predictions={};receipts={}
    risk={
        'M2':(arrays['strict'],arrays['observed']),
        'Q1':(arrays['q1'],arrays['observed']),
        'Q2':(arrays['compile'],arrays['observed']&arrays['q1'].astype(bool)),
        'Q3':(arrays['honest'],arrays['observed']&arrays['q1'].astype(bool)&arrays['compile'].astype(bool))}
    for name,(y,n) in [('M2',(strict_y,strict_n)),*[(f'Q{i+1}',pair) for i,pair in enumerate(counts)]]:
        active=np.flatnonzero(n.sum(axis=0)>0);missing=np.flatnonzero(n.sum(axis=0)==0)
        detail={'active_items':active,'empty_items':missing,'status':'FAIL','priors':{},
            'constant_items':np.flatnonzero((n.sum(axis=0)>0)&((y.sum(axis=0)==0)|(y.sum(axis=0)==n.sum(axis=0)))),
            'empty_policies':np.flatnonzero(n.sum(axis=1)==0)}
        for prior in (1.,.5,2.):
            record={'prior_scale':prior,'status':'FAIL'}
            try:
                # All three anchor policy abilities must have actual information.
                model=fit_2pl(y[:,active],n[:,active],np.zeros((3,0)),prior_scale=prior)
                prediction=np.full(shape[1],integrated_unseen(model.theta[-1],prior))
                prediction[active]=expit(model.a*(model.theta[-1]-model.b))
                record.update(status='PASS' if model.admitted else 'FAIL',fit=fitted_record(model),
                              predictions=prediction,empty_items_use_integrated_fixed_prior=True)
                if prior==1.:
                    predictions[name]=prediction
                    q=np.array([np.full(shape[1],integrated_unseen(theta)) for theta in model.theta])
                    q[:,active]=expit(model.a[None,:]*(model.theta[:,None]-model.b[None,:]))
                    raw_y,raw_n=risk[name];raw_y=raw_y*raw_n
                    record['calibration']=calibration_diagnostic(raw_y,raw_n,q)
                    record['calibration_intervals']=calibration_intervals(raw_y,raw_n,q,arrays['groups'])
                    record['calibration_bins']=calibration_bins(raw_y,raw_n,q,arrays['groups'])
                    interval=record['calibration_intervals']['policies'][-1]['metrics']['mean_bias']['interval']
                    record['calibration_bias_interval_contains_zero']=bool(interval[0] is not None and interval[0]<=0<=interval[1])
            except (IdentificationError,ValueError,FloatingPointError) as exc:
                record.update(status='FAIL',error_type=type(exc).__name__,error=str(exc))
            detail['priors'][str(prior)]=record
        if name in predictions:
            detail['prior_sensitivity']={prior:{'per_item_probability_change':np.abs(record['predictions']-predictions[name]),
                'maximum_probability_change':float(np.max(np.abs(record['predictions']-predictions[name])))}
                for prior,record in detail['priors'].items() if prior!='1.0' and 'predictions' in record}
        if (all(r['status']=='PASS' for r in detail['priors'].values())
                and detail['priors']['1.0']['calibration_bias_interval_contains_zero']):detail['status']='PASS'
        receipts[name]=detail;save('strict_'+name,detail)
    selected=np.prod([predictions[k] for k in ('Q1','Q2','Q3')],axis=0) if all(k in predictions for k in ('Q1','Q2','Q3')) else None
    admitted=bool(selected is not None and controls['status']=='PASS' and all(receipts[k]['status']=='PASS' for k in ('Q1','Q2','Q3')))
    return {'selected_model':'M3 conditional conjunction, fixed before batch-2 outcomes','probabilities':selected,
            'M2_diagnostic':predictions.get('M2'),'admitted':admitted,'controls':controls,'fits':receipts}


def reward_variance(arrays,models):
    """Use one fixed weight vector per full1 task; uncertain groups stay in bounds."""
    if set(models)!={'d','t','p'}:
        return {'status':'INCONCLUSIVE','reason':'marginal model unavailable','weights':None}
    abilities=[models[k]['theta'][-1] for k in ('d','t','p')];weights=gradient_weights(models,abilities)
    if np.any(weights<=0) or not np.allclose(weights.sum(axis=1),1.,atol=1e-12):
        raise ValueError('invalid frozen gradient weights')
    eligible=success=uncertain=0
    for j,task in enumerate(arrays['tasks']):
        observed=arrays['observed'][2,j];strict=arrays['strict'][2,j]
        known=strict[observed]
        if len(known) and np.ptp(known)>0:continue
        if not observed.all():uncertain+=1;continue
        eligible+=1
        rewards=[weighted_reward(arrays['table'][('full1',task,s)],weights[j],int(strict[s])) for s in range(8)]
        success+=int(np.ptp(rewards)>0)
    denominator=eligible+uncertain
    low=success/denominator if denominator else None
    high=(success+uncertain)/denominator if denominator else None
    status='INCONCLUSIVE' if denominator==0 else 'PASS' if low>=.15 else 'FAIL' if high<.15 else 'INCONCLUSIVE'
    return {'status':status,'weights':weights,'abilities':abilities,'known_constant_strict_groups':eligible,
            'unknown_eligibility_or_variance_groups':uncertain,'nonzero_variance_known_groups':success,
            'fraction_bounds':[low,high],'threshold':.15,'threshold_source':'PROTOCOL section 4',
            'declared_train_groups':len(arrays['tasks'])}
