"""Verify paired prompts, prospective weights, exact reward guards and scorer-independent placebo draws."""
from pathlib import Path
import importlib.util,sys,copy
import numpy as np
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_arm_rewards',PHASE/'arm_rewards.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def plan(arm,**kw):
 return m.plan_group(arm,seed=1301,update=1,group_index=0,tasks=['authored_a','authored_b'],**kw)


def rows(p):
 return [{**c,'status':'measured','strict':0,'e':True,'n_examples':1,'raw_vacuity_hits':[],
          'd':{'numerator':1,'denominator':2},'t':1,'p':{'numerator':1,'denominator':4}} for c in p['cells']]


def test_uniform_arms_share_prompt_and_rollout_randomness_with_independent_placebo():
 plans=[plan(a,**({'placebo_distribution':[0.,.2,1.]} if a=='P' else {})) for a in ('A','B','P')]
 assert len({p['task_id'] for p in plans})==1
 assert all([c['seed'] for c in p['cells']]==[c['seed'] for c in plans[0]['cells']] for p in plans)
 p=plans[-1];data=rows(p);before=m.rewards(p,data)
 for r in data:r.update(status='unresolved_measurement',strict=None,d=None,t=None,p=None)
 assert m.rewards(p,data)==before==p['placebo_draws']
 assert plan('P',placebo_distribution=[0.,.2,1.])==p
 with pytest.raises(TypeError):m.plan_group('P',seed=1301,update=1,group_index=0,tasks=['authored_a'],response='leak')


def test_equal_component_weights_reproduce_B_and_guards_remain_identical():
 models={k:{'a':[1.,1.],'b':[0.,0.]} for k in ('d','t','p')}
 p=plan('C',models=models,abilities=[0.,0.,0.]);assert np.allclose(p['weights'],[1/3]*3)
 data=rows(p);assert m.rewards(p,data)==pytest.approx([.5]*8)
 assert all(x==pytest.approx(m.family_reward(r,0)) for x,r in zip(m.rewards(p,data),data))
 data[0]['strict']=1;data[1]['raw_vacuity_hits']=['authored'];data[2]['n_examples']=0
 result=m.rewards(p,data);assert result[:3]==[1.,0.,0.]
 models['d']['a'][0]=4.;assert p['weights']==[1/3]*3  # Saved group weights are not a live view.


def test_missing_B_reward_stays_missing_and_heldout_rows_are_refused():
 p=plan('B');data=rows(p);data[0]['status']='unresolved_measurement'
 assert m.rewards(p,data)[0] is None
 data[1]['split']='test'
 with pytest.raises(ValueError,match='split changed'):m.rewards(p,data)


def test_C_weights_positive_normalized_and_item_order_cannot_change():
 models={k:{'a':[.1,5.],'b':[-2.,2.]} for k in ('d','t','p')}
 p=plan('C',models=models,abilities=[-2.,0.,3.]);assert min(p['weights'])>0 and sum(p['weights'])==pytest.approx(1.)
 assert p==plan('C',models=models,abilities=[-2.,0.,3.])
 with pytest.raises(ValueError,match='sorted train'):m.plan_group('A',seed=1,update=1,group_index=0,tasks=['b','a'])
 models['p']['a'][0]=0.
 with pytest.raises(ValueError,match='bounds'):plan('C',models=models,abilities=[0.,0.,0.])
