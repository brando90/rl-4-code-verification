"""Require A6 soundness, B feasibility and the separate complete A token budget before main learning."""
from pathlib import Path
import sys
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_learning_ledger as m
import test_e13_learning_ledger as old
from test_e13_a6_phase2_admission import fixture as phase1

def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(old,'m',m)
    plan,values,execution=old.fixture(tmp_path,monkeypatch)
    keys=('G0','LP1','calibration','G1','H2','A6');values.update(dict(zip(keys,phase1())))
    monkeypatch.setattr(m,'pilot_lock',lambda *_:({'phase1_results':{k:{'name':k}for k in keys}},'science'))
    names=('a6_learning_ledger.py','a6_phase2_admission.py','learning_runtime.py','learning_generation.py','audit_monitor.py','MONITOR_S2_METHOD.md')
    execution['bindings']=[{'path':str(P/n),'sha256':m.digest(P/n)}for n in names]
    return plan,values,execution

def test_pilot_keeps_technical_audit_and_disabled_arm_guards(tmp_path,monkeypatch):
    plan,values,execution=fixture(tmp_path,monkeypatch)
    assert m.admit(plan)['status']=='ADMITTED'
    values['T4']['status']='INCONCLUSIVE'
    with pytest.raises(ValueError,match='technical prerequisite'):m.admit(plan)
    values['T4']['status']='PASS';plan['arm']='C'
    with pytest.raises(ValueError,match='prospectively admitted'):m.admit(plan)
    plan['arm']='B';values['A6']['status']='UNSOUND'
    with pytest.raises(ValueError,match='sound'):m.admit(plan)

def main_fixture(tmp_path,monkeypatch):
    plan,values,execution=fixture(tmp_path,monkeypatch)
    plan.update(phase='main',run_seed=13011,T5={'name':'T5','sha256':'t5'},A_budget={'name':'budget','sha256':'budget'})
    budget={'one_percent_matching_feasible':True,'T':25600*2048}
    execution.update(gate='L2',T5_sha256='t5',A_budget_sha256='budget',token_budget=budget,main_seeds=[13011,13012,13013])
    values['T5']={'condition':'v2-S2','gate':'T5','status':'PASS','arm':'B','seeds':[1301],
        'metric':'own train reward','pilot_execution_sha256':'pilot'}
    values['budget']={'condition':'v2-S2','gate':'A_PILOT_TOKEN_BUDGET','status':'FROZEN','arm':'A',
        'seeds':[1301,1302],'horizon':30,'pilot_slots':15360,'LP_sha256':'lp-sha','pilot_execution_sha256':'pilot','token_budget':dict(budget)}
    return plan,values,execution

def test_main_uses_published_a_budget_with_b_feasibility(tmp_path,monkeypatch):
    plan,values,execution=main_fixture(tmp_path,monkeypatch)
    assert m.admit(plan)['phase']=='main'
    execution['token_budget']['T']+=25600
    with pytest.raises(ValueError,match='A-pilot budget'):m.admit(plan)

@pytest.mark.parametrize('key,bad',[('arm','B'),('pilot_slots',7680),('pilot_execution_sha256','other')])
def test_wrong_budget_population_or_pilot_is_rejected(tmp_path,monkeypatch,key,bad):
    plan,values,_=main_fixture(tmp_path,monkeypatch);values['budget'][key]=bad
    with pytest.raises(ValueError,match='A-pilot budget'):m.admit(plan)

def test_a_strict_t5_cannot_admit_main(tmp_path,monkeypatch):
    plan,values,_=main_fixture(tmp_path,monkeypatch);values['T5']['arm']='A'
    with pytest.raises(ValueError,match='B own-reward'):m.admit(plan)
