"""Validate identified likelihoods, conditional risk sets and integration using synthetic data only."""
import importlib.util
from pathlib import Path
import sys
import numpy as np
from scipy.special import expit

P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/prediction/irt_v2.py'
spec=importlib.util.spec_from_file_location('e13v2_irt_test',P)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)


def test_analytic_gradient_and_location_scale_likelihood():
    rng=np.random.default_rng(13);policies,items=4,5
    x=np.concatenate([np.linspace(-1.5,1.5,policies),rng.normal(size=items),rng.normal(0,.1,items),np.array([.2,-.1])])
    features=rng.normal(size=(items,2));n=np.full((policies,items),10.);y=rng.binomial(n.astype(int),.4)
    value,gradient=m.objective(x,y,n,features)
    finite=[]
    for i in range(len(x)):
        delta=np.zeros_like(x);delta[i]=1e-5
        finite.append((m.objective(x+delta,y,n,features)[0]-m.objective(x-delta,y,n,features)[0])/2e-5)
    np.testing.assert_allclose(gradient,finite,rtol=1e-5,atol=1e-6)
    theta,_,_,loga,_,b=m.unpack(x,policies,items,features);a=np.exp(loga)
    np.testing.assert_allclose(expit(a[None,:]*(theta[:,None]-b)),expit((a/2.3)[None,:]*((2.3*theta+1.2)[:,None]-(2.3*b+1.2))))
    assert np.isfinite(value)


def test_conditional_risk_sets_do_not_double_count_failed_hurdles():
    rows=m.conditional_counts([0,1,1,1],[1,0,1,1],[1,1,0,1],[1,1,1,0],[0,0,0,0],[0,0,0,0],(1,1))
    assert [(y.item(),n.item()) for y,n in rows]==[(2.,3.),(1.,2.),(0.,1.)]


def test_synthetic_recovery_five_starts_and_unseen_integration():
    rng=np.random.default_rng(1302);policies,items=8,12
    theta=np.linspace(-1.7,1.7,policies);theta=(theta-theta.mean())/theta.std()
    b=rng.normal(0,1,items);a=np.exp(rng.normal(0,.2,items));truth=expit(a[None,:]*(theta[:,None]-b))
    n=np.full((policies,items),100);n[rng.random(n.shape)<.15]=0;n[:3]=100
    y=rng.binomial(n,truth)
    fit=m.fit_2pl(y,n,theta[:,None])
    assert len(fit.starts)==5 and fit.admitted,fit.starts
    assert fit.max_probability_disagreement<=.02
    assert abs(fit.theta.mean())<1e-10 and abs(fit.theta.var()-1)<1e-10
    assert np.corrcoef(theta,fit.theta)[0,1]>.8
    assert np.mean(np.abs(fit.seen_items(theta[:,None])-truth))<.08
    predicted=fit.unseen_items(np.array([[0.]]),np.zeros((1,0)))
    assert predicted.shape==(1,1) and 0<predicted.item()<1


def test_empty_risk_set_is_explicit_and_baselines_use_only_training():
    import pytest
    with pytest.raises(m.IdentificationError,match='empty risk'):
        m.fit_2pl(np.zeros((3,3)),np.zeros((3,3)),np.zeros((3,1)))
    np.testing.assert_allclose(m.beta_baseline([2,0],[4,0],[7],[10]),[.5,8/12])
    got=m.monotone_calibration([0,1,2],[0,1,0],[1,1,1],[-1,0,1,2,3])
    np.testing.assert_allclose(got,[0,0,.5,.5,.5])


def test_beta_binomial_gradient_and_frozen_positive_weights():
    spec=importlib.util.spec_from_file_location('e13v2_marginal_test',P.parent/'marginal_v2.py')
    marginal=importlib.util.module_from_spec(spec);spec.loader.exec_module(marginal)
    rng=np.random.default_rng(1401);policies,items=3,4
    x=np.concatenate([[-1.,0.,1.],rng.normal(0,.1,items),rng.normal(0,.1,items),[np.log(20.)]])
    n=np.full((policies,items,8),5.);y=rng.binomial(5,.4,n.shape)
    _,g=marginal.bb_objective(x,y,n);finite=[]
    for i in range(len(x)):
        delta=np.zeros_like(x);delta[i]=1e-5
        finite.append((marginal.bb_objective(x+delta,y,n)[0]-marginal.bb_objective(x-delta,y,n)[0])/2e-5)
    np.testing.assert_allclose(g,finite,rtol=1e-5,atol=1e-5)
    models={k:{'a':np.ones(2),'b':np.zeros(2)} for k in ('d','t','p')}
    w=marginal.gradient_weights(models,[0,0,0]);np.testing.assert_allclose(w,np.full((2,3),1/3))
    assert np.all(w>0);np.testing.assert_allclose(w.sum(axis=1),1)
    parts={'e':1,'n_examples':1,'d':{'numerator':1,'denominator':2},'t':1,'p':{'numerator':1,'denominator':4},'raw_vacuity_hits':0}
    expected=(.5*1*.25)**(1/3)
    assert abs(marginal.weighted_reward(parts,w[0],0)-expected)<1e-12
    assert marginal.weighted_reward(parts,w[0],0)==marginal.weighted_reward(parts,w[0],0)
    import pytest
    with pytest.raises(ValueError,match='earlier train'):
        marginal.update_ability([{'split':'test','update':0}],models['d'],'d',current_update=1)
    with pytest.raises(ValueError,match='earlier train'):
        marginal.update_ability([{'split':'train','update':1}],models['d'],'d',current_update=1)


def test_future_test_rows_never_enter_forecast_harness_and_base_compute_finite():
    spec=importlib.util.spec_from_file_location('e13v2_nested_test',P.parent/'nested_forecast_v2.py')
    nested=importlib.util.module_from_spec(spec);spec.loader.exec_module(nested)
    import pytest
    with pytest.raises(ValueError,match='test is sealed'):
        nested.run_forecast([{'split':'test'}],[],{}, {})
    assert np.isfinite(nested.policy_features([4.],[0.])).all()


def test_nested_forecast_never_fits_full_schedule_labels(monkeypatch):
    spec=importlib.util.spec_from_file_location('e13v2_nested_isolation',P.parent/'nested_forecast_v2.py')
    nested=importlib.util.module_from_spec(spec);spec.loader.exec_module(nested)
    systems=[{'label':f's{size}_f{f}','size':f'{size}B','fraction':str(f),'cumulative_assistant_tokens':int(100*f)}
             for size in (1.7,4,8) for f in (0,.125,.25,.5,.75,1.)]
    tasks=[f't{i}' for i in range(40)];groups={t:t for t in tasks};features={t:[i,i%3,0,1] for i,t in enumerate(tasks)}
    rows=[{'split':'validation','policy':s['label'],'task_id':t,'sample_idx':k,'strict_status':'scored',
           'strict':int(k<3),'factored_reward':.4,'q1':True,'compile':True,'honest':bool(k<3)}
          for s in systems for t in tasks for k in range(8)]
    calls=[]
    def fake_forecast(**kw):
        assert np.max(kw['policy_metadata'][:,1])<np.log1p(100)
        train_ids=set(kw['item_features'][:,0]);target_ids=set(kw['target_features'][:,0])
        if all(i==-1 for i in kw['target_item_indices']):assert not train_ids & target_ids
        calls.append(len(kw['history']['strict']))
        shape=(len(kw['target_metadata']),len(kw['target_features']))
        predictions={name:np.full(shape,.4 if name!='M3e' else .45) for name in ['M0','M1','M2','M3','M3e']}
        return predictions,{name:{'admitted':True} for name in ['M2','M3','M3e']}
    monkeypatch.setattr(nested,'forecast_panel',fake_forecast)
    first=nested.run_forecast(rows,systems,features,groups,draws=4)
    for row in rows:
        if row['policy'].endswith('_f1.0'):row['strict']=1-row['strict']
    second=nested.run_forecast(rows,systems,features,groups,draws=4)
    assert len(calls)==48
    for scheme in first:
        assert first[scheme]['predictions']==second[scheme]['predictions']
        assert len(first[scheme]['predictions']['selected'])==3*40*8


def test_failed_candidate_keeps_baseline_and_m2_results():
    spec=importlib.util.spec_from_file_location('e13v2_metrics_test',P.parent/'evaluation_v2.py')
    ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev)
    result=ev.assess_g1([0,1,0,1],{'selected':None,'M0':np.full(4,.5),'M1':np.full(4,.5),'M2':np.full(4,.5)},['a','a','b','b'],['x','y','x','y'],draws=4)
    assert result['status']=='FAIL' and result['missing_required_models']==['selected']
    assert 'M2' in result['metrics'] and result['declared']==4
    assert result['intervals']['M2']['log_loss']['valid_draws']==4
    assert ev.auc([0,0],[.1,.2]) is None


def test_domain_vocabulary_uses_training_only():
    from features_v2 import extract,matrices
    first=extract('x = 1\n','finance',['Nat'])
    heldout=extract('y = 2\n','never-seen',['Nat','Int'])
    train,target,receipt=matrices([first],[heldout])
    assert receipt['domain_categories']==['finance']
    assert train[0,-1]==1 and target[0,-1]==0
    assert first['python_token_count']==3 and heldout['reference_theorem_count']==2
