"""Verify current-ability recovery and leakage/missingness guards on authored data."""
from pathlib import Path
import importlib.util,sys
import numpy as np
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_online_ability',PHASE/'online_ability.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
 rng=np.random.default_rng(77);tasks=['authored_a','authored_b','authored_c'];rows=[]
 for i in range(600):
  j=i%3;n=0 if i%7==0 else 7;q=m.expit(.4-[-1.,0.,1.][j])
  rows.append({'cell_id':str(i),'task_id':tasks[j],'split':'train','arm':'C','run_seed':1301,'update':i%10+1,
   'status':'measured','d':{'numerator':int(rng.binomial(n,q)),'denominator':n},
   'p':{'numerator':int(rng.binomial(n,q)),'denominator':n},'t':int(rng.binomial(1,q))})
 models={c:{'a':[1.]*3,'b':[-1.,0.,1.],'logphi':float(np.log(20.))} for c in ('d','t','p')}
 return rows,tasks,models


def test_five_start_ability_recovery_uses_real_missing_denominators_and_saves():
 rows,tasks,models=fixture();saved={}
 result=m.refit(rows,tasks,models,current_update=11,save=lambda k,v:saved.update({k:v}))
 assert result['admitted'] and len(saved)==3
 assert np.max(abs(np.array(result['abilities'])-.4))<.15
 assert saved['d']['empty_cells']==86 and saved['t']['empty_cells']==0
 assert all(len(r['fits']['1.0']['starts'])==5 for r in saved.values())
 assert all(r['likelihood_invariance_error']<=1e-9 for r in saved.values())
 again=m.refit(rows,tasks,models,current_update=11,save=lambda *args:None)
 assert result==again


@pytest.mark.parametrize('change',[{'split':'test'},{'update':11},{'arm':'B'},{'run_seed':1302}])
def test_heldout_current_group_other_arm_or_run_cannot_enter_refit(change):
 rows,tasks,models=fixture();rows[0].update(change)
 with pytest.raises(ValueError):m.refit(rows,tasks,models,current_update=11,save=lambda *args:None)


def test_missing_or_constant_component_stops_C_without_substituted_weights():
 rows,tasks,models=fixture()
 for row in rows:row['p']={'numerator':0,'denominator':0}
 result=m.refit(rows,tasks,models,current_update=11,save=lambda *args:None)
 assert not result['admitted'] and result['abilities'] is None
 assert result['components']['p']['empty_cells']==600
 assert 'prior alone' in result['components']['p']['reason']


def test_n_one_beta_binomial_is_exact_Bernoulli_and_gradient():
 x=np.array([.3]);a=np.array([.5,1.,2.]);b=np.array([-1.,0.,1.]);y=np.array([0,1,1]);n=np.ones(3)
 loss,grad=m.objective(x,y,n,a,b,np.log(20.));q=m.expit(a*(x[0]-b))
 assert loss==pytest.approx(-np.sum(y*np.log(q)+(1-y)*np.log1p(-q))+.5*x[0]**2,abs=1e-12)
 assert grad[0]==pytest.approx(np.sum(a*(q-y))+x[0],abs=1e-12)
