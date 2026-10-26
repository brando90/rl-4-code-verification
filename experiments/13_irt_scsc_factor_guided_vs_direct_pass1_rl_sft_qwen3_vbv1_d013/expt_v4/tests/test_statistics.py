"""TLDR: Check known G0 estimates, paired bootstraps, conservative pilot selection and placebo binding."""
import copy
import hashlib
import math
import numpy as np
import pytest
from group_selection import qhat, select_tasks, choose_group_size, t2_subset
from placebo import reference, precompute, draw, density_report
from pilot_metrics import t5, extension_plan, token_budget, token_matching


def batch(successes=1):
    tasks=[f't{i:02}' for i in range(32)]
    return [{'task_id':t,'sample_idx':s,'split':'train','strict':int(s<successes),'factored_reward':s/31}
            for t in tasks for s in range(32)],tasks


@pytest.mark.parametrize('g',[8,16])
@pytest.mark.parametrize('s',[0,1,32])
def test_known_qhat(s,g):assert qhat(s,g)==pytest.approx(g/32 if s==1 else 0)


def test_selection_is_exact_rng_over_sorted_ids():
    ids=[f't{i:03}' for i in range(539)]
    expected=np.random.default_rng(1304001).choice(sorted(ids),32,replace=False).tolist()
    assert select_tasks(ids[::-1])==expected


def test_constant_one_success_selects16_known_bounds():
    rows,order=batch();r=choose_group_size(rows,order)
    assert r['G']==16
    for c in r['completions']:
        assert c['N8']==64 and c['N16']==128 and c['M8']==8 and c['M16']==8
        assert c['lower95_N16_minus_1p2_N8']==pytest.approx(51.2)
        assert c['lower95_M16_minus_3']==5


def test_missing_completion_veto_and_no_signal():
    rows,order=batch(0)
    for r in rows:
        if r['sample_idx']==0:r['strict']=None
    result=choose_group_size(rows,order)
    assert result['G']==8
    assert [c['choose16'] for c in result['completions']]==[False,True]


def test_whole_task_paired_bootstrap_independent_oracle():
    rows,order=batch()
    for i,r in enumerate(rows):r['strict']=int(r['sample_idx']<((i//32)%9))
    result=choose_group_size(rows,order)
    q8=np.array([qhat(i%9,8) for i in range(32)])
    q16=np.array([qhat(i%9,16) for i in range(32)])
    samples=np.random.default_rng(1304002).integers(0,32,(10000,32))
    expect=np.percentile((256*q16[samples]-1.2*256*q8[samples]).mean(1),5)
    assert result['completions'][0]['lower95_N16_minus_1p2_N8']==pytest.approx(expect)


@pytest.mark.parametrize('g',[8,16])
def test_subset_uses_seeded_order_then_low_sample_indices(g):
    rows,order=batch();chosen=t2_subset(rows[::-1],order,g)
    assert len(chosen)==256//g and sum(map(len,chosen))==256
    assert [x[0]['task_id'] for x in chosen]==order[:256//g]
    assert all([r['sample_idx'] for r in x]==list(range(g)) for x in chosen)


def test_missing_g0_slot_rejected():
    rows,order=batch()
    with pytest.raises(ValueError):choose_group_size(rows[:-1],order)


@pytest.mark.parametrize('missing,status',[(102,'ADMITTED'),(103,'EXCLUDED')])
def test_placebo_90_percent(missing,status):
    rows,_=batch()
    for r in rows[:missing]:r['factored_reward']=None
    assert reference(rows)['status']==status


def test_placebo_decimal_hash_and_prebind(tmp_path):
    rows,_=batch();ref=reference(rows)
    expected=''.join(format(v,'.17g')+'\n' for v in sorted(r['factored_reward'] for r in rows)).encode()
    assert ref['distribution_sha256']==hashlib.sha256(expected).hexdigest()
    first=precompute(ref,[1301,1302],2,tmp_path/'draws.json',first_response_exists=False)
    assert first['draws']['1301/1']==[draw(ref,1301,1,i) for i in range(256)]
    assert first['draws']['1301/1']!=first['draws']['1302/1']
    with pytest.raises(ValueError):precompute(ref,[1301],2,tmp_path/'late.json',first_response_exists=True)
    with pytest.raises(FileExistsError):precompute(ref,[1301],2,tmp_path/'draws.json',first_response_exists=False)


def test_reward_variance_report_preserves_missing_denominators():
    report=density_report([[0.,1.],[None,1.]],[[.5,.5],[0.,1.]])
    assert report['B']['measured_slots']==3 and report['B']['complete_groups']==1
    assert report['B']['mean_within_group_variance']==.25
    assert report['P']['nonzero_variance_group_fraction']==.5
    assert report['P']['mean_within_group_variance']==.125


def pilot(horizon=30):
    return [{'arm':a,'seed':s,'update':u,'completed':True,'strict':[0]*256,'generated_tokens':[10]*256}
            for a in ('A','B','P') for s in (1301,1302) for u in range(1,horizon+1)]


def test_t5_missing_conservative_and_replication_does_not_rescue():
    rows=pilot()
    for r in rows:
        if r['arm']=='A' and r['seed']==1302 and r['update']>=21:r['strict']=[1]*256
        if r['arm']=='A' and r['seed']==1301 and r['update']<=10:r['strict'][0]=None
    assert t5(rows)['conservative_gain']==pytest.approx(-1/256)
    assert t5(rows,seed=1302)['status']=='PASS'
    plan=extension_plan(rows)
    assert plan['action']=='EXTEND_ALL_SIX' and len(plan['trajectories'])==6


def test_extension_once_and_pass_threshold():
    rows=pilot(60)
    assert extension_plan(rows,60)['action']=='STOP_PUBLISH'
    for r in rows:
        if r['arm']=='A' and r['seed']==1301 and r['update']>=51:r['strict'][:6]=[1]*6
    assert t5(rows,60)['status']=='PASS'
    assert extension_plan(rows,60)['action']=='MAIN_RESOURCE_CHECK'


def test_T_uses_both_A_seeds_first30_despite_extension():
    rows=pilot(60)
    for r in rows:
        if r['seed']==1302:r['generated_tokens']=[11]*256
        if r['update']>30 or r['arm']!='A':r['generated_tokens']=[12288]*256
    assert token_budget(rows)['T']==25600*11
    assert token_budget(rows)['slots']==15360
    with pytest.raises(ValueError):token_budget([r for r in rows if not(r['arm']=='A' and r['seed']==1302 and r['update']==30)])


def test_token_matching_keeps_one_percent_and_crossing_group():
    assert token_matching(1000000,1009999,1000000,16)
    assert not token_matching(1000000,1010001,1000000,8)
    with pytest.raises(ValueError):token_matching(1000000,1200000,1000000,8)


def test_placebo_rejects_reordered_reference_and_heldout_slots(tmp_path):
    rows,_=batch();ref=reference(rows);ref['values'].reverse()
    with pytest.raises(ValueError,match='changed'):
        precompute(ref,[1301],1,tmp_path/'bad.json',first_response_exists=False)
    rows[0]['split']='test'
    with pytest.raises(ValueError,match='held-out'):reference(rows)
