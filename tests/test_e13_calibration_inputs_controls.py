"""Check train-only calibration alignment, denominator preservation and frozen numerical controls."""
from pathlib import Path
import sys
import copy

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase1'
sys.path.insert(0,str(ROOT))
import calibration_inputs as inputs
import calibration_controls as controls


def rows():
    tasks=[f'fixture_task_{i}' for i in range(5)]
    return [{'batch':b,'policy':p,'cell_id':f'{b}/{t}/{s}','task_id':t,'sample_idx':s,
             'split':'train','status':'measured','strict':0,'q1':1,'compile':0,'honest':0,
             'd':{'numerator':s%4,'denominator':4},'t':0,'p':{'numerator':0,'denominator':2}}
            for b,p in zip(inputs.BATCHES,inputs.POLICIES) for t in tasks for s in range(8)],tasks


def test_missing_cell_retains_slot_without_becoming_observed_failure():
    data,tasks=rows();data[0]['status']='unresolved_measurement'
    result=inputs.anchor_arrays(data,tasks)
    assert result['observed'].shape==(3,5,8) and result['observed'].sum()==119
    assert result['components']['p'][1][0,0,0]==0
    assert result['components']['p'][0][0,0,1]==0 and result['components']['p'][1][0,0,1]==2
    assert result['observed'][0,0,1]
    h=inputs.history(result);assert len(h['strict'])==120 and h['observed'].sum()==119
    report=inputs.pattern_report(result);assert report['declared']==120 and report['missing']==1
    assert report['components']['p']['denominator']==238


@pytest.mark.parametrize('defect',['test','duplicate','missing','identity','policy'])
def test_refuse_heldout_or_changed_declared_panel(defect):
    data,tasks=rows()
    if defect=='test':data[0]['split']='test'
    if defect=='duplicate':data.append(copy.deepcopy(data[0]))
    if defect=='missing':data.pop()
    if defect=='identity':data[0]['cell_id']='changed'
    if defect=='policy':data[0]['policy']='another-policy'
    with pytest.raises(ValueError):inputs.anchor_arrays(data,tasks)


@pytest.mark.parametrize('bad',[{'numerator':.5,'denominator':1},{'numerator':2,'denominator':1},
                               {'numerator':0,'denominator':-1}])
def test_fraction_likelihood_keeps_integer_denominators(bad):
    data,tasks=rows();data[0]['d']=bad
    with pytest.raises(ValueError,match='integer denominators'):inputs.anchor_arrays(data,tasks)


def test_disconnected_denominator_pattern_fails_recovery_without_fitting(monkeypatch):
    n=np.zeros((3,4,8),int);n[:2,:2]=10;n[2,2:]=10
    monkeypatch.setattr(controls,'fit_beta_binomial',lambda *a:pytest.fail('unidentified fit must not run'))
    result=controls.recover_denominators(n)
    assert result['status']=='FAIL' and not controls.connected(n)
    assert result['total_denominator']==480 and result['zero_cells']==48


def test_gradient_and_likelihood_gauge_controls_pass():
    result=controls.numerical_controls()
    assert result['status']=='PASS'
    assert result['fixed_initializations']==[1302011,1302012,1302013,1302014,1302015]
    assert max(result['gradient_max_absolute_errors'].values())<1e-5
    assert result['likelihood_invariance_error']<1e-9


def test_primary_objective_is_exactly_the_frozen_marginal_objective():
    rng=np.random.default_rng(101);n=np.full((3,5,8),10);y=rng.binomial(n,.4)
    x=np.r_[[-1.2,0.,1.2],np.zeros(5),np.zeros(5),np.log(20.)]
    expected=controls.bb_objective(x,y,n);actual=controls.prior_objective(x,y,n,1.)
    assert actual[0]==expected[0];np.testing.assert_array_equal(actual[1],expected[1])


def test_synthetic_recovery_preserves_zeros_and_denominator_pattern():
    n=np.full((3,40,8),20);n[0,::5,:3]=0
    result=controls.recover_denominators(n)
    assert result['status']=='PASS' and result['zero_cells']==24 and result['total_denominator']==18720
    assert result['probability_mean_absolute_error']<=.08 and result['ability_correlation']>=.8
    assert len(result['starts'])==5 and result['probability_disagreement']<=.02


def test_grouped_calibration_intervals_retain_pairing_and_counts():
    import calibration_fit as fit
    n=np.full((3,5,8),4);y=np.full_like(n,2);q=np.full((3,5),.6)
    result=fit.calibration_intervals(y,n,q,['pair','pair','b','c','d'],draws=100)
    assert result['groups']==4 and result['draws']==100 and result['p_value'] is None
    for row in result['policies']:
        np.testing.assert_allclose(row['metrics']['mean_bias']['interval'],[.1,.1])
        np.testing.assert_allclose(row['metrics']['observed_count_weighted_mean']['interval'],[.5,.5])
        assert row['metrics']['mean_absolute_error']['defined_draws']==100


def test_unseen_item_integration_uses_symmetric_frozen_prior():
    from calibration_fit import integrated_unseen
    assert abs(integrated_unseen(0)-.5)<1e-12
    assert 0<integrated_unseen(-1)<.5<integrated_unseen(1)<1
    assert abs(integrated_unseen(-1)+integrated_unseen(1)-1)<1e-12


def variance_fixture():
    data,tasks=rows()
    for r in data:r.update(e=1,n_examples=1,raw_vacuity_hits=0)
    arrays=inputs.anchor_arrays(data,tasks)
    models={k:{'a':np.ones(5),'b':np.zeros(5),'theta':np.array([-1.,0.,1.])} for k in ('d','t','p')}
    return arrays,models


def test_weighted_variance_counts_constant_strict_groups_with_frozen_weights():
    from calibration_fit import reward_variance
    arrays,models=variance_fixture();result=reward_variance(arrays,models)
    assert result['status']=='PASS' and result['known_constant_strict_groups']==5
    assert result['nonzero_variance_known_groups']==5 and result['fraction_bounds']==[1.,1.]
    np.testing.assert_allclose(result['weights'],np.full((5,3),1/3))
    arrays['strict'][2]=1
    for t in arrays['tasks']:
        for s in range(8):arrays['table'][('full1',t,s)]['strict']=1
    result=reward_variance(arrays,models)
    assert result['status']=='FAIL' and result['fraction_bounds']==[0.,0.]


def test_unknown_group_eligibility_cannot_be_silently_dropped():
    from calibration_fit import reward_variance
    arrays,models=variance_fixture()
    arrays['observed'][2,0]=False
    for j in range(1,5):arrays['strict'][2,j,0]=1
    result=reward_variance(arrays,models)
    assert result['status']=='INCONCLUSIVE' and result['fraction_bounds']==[0.,1.]
    assert result['known_constant_strict_groups']==0 and result['unknown_eligibility_or_variance_groups']==1


def test_strict_forecast_uses_conditional_hurdles_not_marginal_fractions(monkeypatch):
    import calibration_fit as fit
    from types import SimpleNamespace
    data,tasks=rows()
    for row in data:
        s=row['sample_idx'];row.update(q1=int(s%4!=0),compile=int(s%3!=0),honest=int(s%2!=0))
        row['strict']=int(row['q1'] and row['compile'] and row['honest'])
    arrays=inputs.anchor_arrays(data,tasks);arrays['groups']=tasks
    monkeypatch.setattr(fit,'pattern_controls',lambda *a:{'status':'PASS'})
    def model(y,n,metadata,**kw):
        return SimpleNamespace(theta=np.array([-1.,1.,0.]),a=np.ones(n.shape[1]),b=np.zeros(n.shape[1]),
            starts=[],admitted=True,max_probability_disagreement=0.)
    monkeypatch.setattr(fit,'fit_2pl',model)
    saved={};result=fit.fit_strict_forecast(arrays,lambda k,v:saved.update({k:v}))
    np.testing.assert_allclose(result['probabilities'],np.full(5,.125))
    np.testing.assert_allclose(result['M2_diagnostic'],np.full(5,.5))
    for y,n in arrays['components'].values():y[:]=n
    again=fit.fit_strict_forecast(arrays,lambda *a:None)
    np.testing.assert_array_equal(result['probabilities'],again['probabilities'])
    assert set(saved)=={'strict_pattern_controls','strict_M2','strict_Q1','strict_Q2','strict_Q3'}


def test_calibration_requires_publication_before_reading_outcomes(tmp_path,monkeypatch):
    import json,calibration
    plan=tmp_path/'plan.json';plan.write_text(json.dumps({'root':str(tmp_path/'run')}))
    def refuse(_):raise ValueError('unpublished method')
    monkeypatch.setattr(calibration,'verify',refuse)
    monkeypatch.setattr(calibration,'load_arrays',lambda _:pytest.fail('outcomes read before publication'))
    with pytest.raises(ValueError,match='unpublished'):calibration.run(plan)
    assert not (tmp_path/'run').exists()


def test_calibration_partial_failure_is_recorded_and_never_retried(tmp_path,monkeypatch):
    import json,calibration
    root=tmp_path/'run';binding=tmp_path/'binding.json';binding.write_text('{}')
    plan=tmp_path/'plan.json';plan.write_text(json.dumps({'root':str(root),'method_lock':str(binding),
        'input_lock':str(binding),'method_revision':'fixture'}))
    monkeypatch.setattr(calibration,'verify',lambda _:({'g1_lock':str(binding),'B_reward_source':'fixture'},{}))
    data,tasks=rows();arrays=inputs.anchor_arrays(data,tasks)
    monkeypatch.setattr(calibration,'load_arrays',lambda _:arrays)
    monkeypatch.setattr(calibration,'placebo',lambda *a:{'values':[0.],'measured':1,'declared':40})
    calls=[]
    def failure(arrays,save):
        calls.append('fit');save('retained_fit',{'status':'fixture partial'});raise RuntimeError('synthetic fit interruption')
    monkeypatch.setattr(calibration,'fit_marginals',failure)
    with pytest.raises(RuntimeError,match='interruption'):calibration.run(plan)
    receipt=json.loads((root/'result.json').read_text());assert receipt['status']=='INCOMPLETE' and receipt['retries']==0
    original=(root/'retained_fit.json').read_bytes()
    with pytest.raises(FileExistsError):calibration.run(plan)
    assert calls==['fit'] and (root/'retained_fit.json').read_bytes()==original


def test_failed_strict_calibration_diagnostic_cannot_leave_a_pass_receipt(monkeypatch):
    import calibration_fit as fit
    from types import SimpleNamespace
    data,tasks=rows();arrays=inputs.anchor_arrays(data,tasks);arrays['groups']=tasks
    monkeypatch.setattr(fit,'pattern_controls',lambda *a:{'status':'PASS'})
    monkeypatch.setattr(fit,'fit_2pl',lambda y,n,*a,**k:SimpleNamespace(theta=np.array([-1.,0.,1.]),
        a=np.ones(n.shape[1]),b=np.zeros(n.shape[1]),starts=[],admitted=True,max_probability_disagreement=0.))
    def failure(*a,**k):raise ValueError('synthetic diagnostic failure')
    monkeypatch.setattr(fit,'calibration_intervals',failure)
    result=fit.fit_strict_forecast(arrays,lambda *a:None)
    assert not result['admitted']
    assert all(r['status']=='FAIL' for r in result['fits'].values())
    assert all(r['priors']['1.0']['status']=='FAIL' for r in result['fits'].values())
