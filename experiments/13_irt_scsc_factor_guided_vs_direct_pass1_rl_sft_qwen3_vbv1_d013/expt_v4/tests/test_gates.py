"""TLDR: Reject technical gates with missing signal, changed replay state or invalid maximum-length evidence."""
import copy
import pytest
from gates import probability_agreement, select_t2_reward, advantages, t2, replay_binding, t3, t4, REPLAY_KEYS


def positions(n=800):
    return [{'response':i//100,'position':i%100,'token':1,'generator_support':[1,2],
             'certified':True,'top_k_certified':True,'nucleus_certified':True,'trainer_support':[1,2],'generator_logp':-.7,'trainer_logp':-.7,'discarded_mass':.5} for i in range(n)]


def test_t1_complete_counts_quantiles():
    p=positions();r=probability_agreement(p,expected_positions=800)
    assert r['status']=='PASS' and r['median_discarded_mass']==.5 and r['p99_discarded_mass']==.5
    with pytest.raises(ValueError):probability_agreement(p[:-1],expected_positions=800)


@pytest.mark.parametrize('kind',['support','identical','median','p99','truncation'])
def test_each_t1_failure(kind):
    p=positions()
    if kind=='support':p[0]['trainer_support']=[2]
    elif kind=='identical':
        for r in p[:9]:r['trainer_support']=[1,3]
    elif kind=='median':
        for r in p:r['trainer_logp']+=.011
    elif kind=='p99':
        for r in p[:9]:r['trainer_logp']+=.11
    else:
        for r in p[:9]:r['trainer_logp']+=1
    assert probability_agreement(p,expected_positions=800)['status']=='FAIL'


def groups():return [[{'strict':0,'factored_reward':s/7} for s in range(8)] for g in range(32)]


def test_t2_reward_preference_and_stop_without_resampling():
    g=groups();assert select_t2_reward(g)['arm']=='B'
    g[0][0]['strict']=1;assert select_t2_reward(g)['arm']=='A'
    g[0][1]['strict']=None;assert select_t2_reward(g)['arm']=='B'
    for row in g:
        for r in row:r['factored_reward']=0
    assert select_t2_reward(g)=={'status':'STOP_NO_SIGNAL','arm':None,'resample':False}
    adv=advantages(g,'strict');assert adv[0]['sample_mask']==[0]*8


def t2_args():
    return dict(advantages=[-1,1],preclip_gradient_norm=[.5],before_weights='a'*64,after_weights='b'*64,
                refit_positions=positions(100),old_supports=[[1],[2]],new_supports=[[1],[3]])


def test_t2_reports_preclip_and_support_change():
    r=t2(**t2_args());assert r['status']=='PASS' and r['preclip_gradient_norm']==.5 and r['support_changed_fraction']==.5


@pytest.mark.parametrize('key,value',[('advantages',[0,0]),('advantages',[float('nan'),1]),
    ('preclip_gradient_norm',[0.]),('preclip_gradient_norm',float('inf')),('after_weights','a'*64)])
def test_t2_weight_decay_alone_cannot_pass(key,value):
    args=t2_args();args[key]=value;assert t2(**args)['status']=='FAIL'


def test_t2_refit_error_and_support_failure():
    args=t2_args()
    for r in args['refit_positions']:r['trainer_logp']+=.02
    assert t2(**args)['status']=='FAIL'
    args=t2_args();args['refit_positions'][0]['trainer_support']=[2]
    assert t2(**args)['status']=='FAIL'


def test_t3_binds_every_replay_component():
    binding=replay_binding(**{k:'a'*64 for k in REPLAY_KEYS})
    assert t3(1.,1.0009,binding,binding)['status']=='PASS'
    assert t3(1.,1.002,binding,binding)['status']=='FAIL'
    for key in REPLAY_KEYS:
        changed=replay_binding(**{k:('b' if k==key else 'a')*64 for k in REPLAY_KEYS})
        assert t3(1.,1.,binding,changed)['status']=='FAIL'


def test_t4_requires_maximum_length_forward_backward():
    args=dict(device_seconds=7200,updates=2,peak_memory_bytes=50000,probe_sequence_length=20041,
              maximum_train_prompt=7753,probe_forward_backward=True,generated_tokens=1000,
              generation_seconds=10,lean_wall_seconds=30,timeout_count=1,scoring_slots=256,storage_growth_bytes=123)
    r=t4(**args);assert r['status']=='PASS' and r['device_hours_per_update']==1 and r['deterministic_timeout_rate']==1/256
    args['probe_sequence_length']=15945;assert t4(**args)['status']=='FAIL'


def test_gate_statistic_reserved_once_even_if_evaluation_crashes(tmp_path):
    from gate_receipts import evaluate_once,allow_infrastructure_retry
    def broken():raise RuntimeError('interrupted statistic')
    with pytest.raises(RuntimeError):evaluate_once(tmp_path,'V4-G0',[],broken)
    with pytest.raises(FileExistsError):evaluate_once(tmp_path,'V4-G0',[],lambda: {'G':16})
    assert allow_infrastructure_retry([{'generated_responses':0,'statistics_computed':False}]*2)
    assert not allow_infrastructure_retry([{'generated_responses':0,'statistics_computed':False}]*3)
    assert not allow_infrastructure_retry([{'generated_responses':1,'statistics_computed':False}])
    assert not allow_infrastructure_retry([{'generated_responses':0,'statistics_computed':True}])
