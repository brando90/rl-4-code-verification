"""Require published scientific/technical prerequisites and immutable learning-stage reservations."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_learning_ledger',PHASE/'learning_ledger.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path,monkeypatch):
    phase1={'G0':{'gate':'G0_A3','status':'PASS'},
        'LP1':{'condition':'v2-S2','status':'PASS','numerical_dtype':'float16','admission_statistics_computed':True},
        'calibration':{'condition':'v2-S2','status':'FROZEN','C_calibration_admitted':True},
        'G1':{'gate':'G1','status':'PASS'},'H2':{'gate':'H2','status':'PASS'}}
    values={**phase1,**{k:{'gate':k,'status':'PASS','condition':'v2-S2','science_sha256':'science'} for k in ('T1','T2','T3','T4')},
        'audit':{'condition':'v2-S2','declared':128,'accounted':128,'audits_ran':True,
                 'independent_checks_functioning':True,'cleanup_unresolved':0,'reward_increasing_mutations':[]}}
    paths=[PHASE/n for n in ('learning_ledger.py','learning_runtime.py','learning_generation.py','audit_monitor.py','MONITOR_S2_METHOD.md')]
    execution={'gate':'LEARNING_PILOT','condition':'v2-S2','status':'FROZEN','LP_sha256':'lp-sha','train_audit_sha256':'audit-sha',
        'configuration':{'ledger':str(tmp_path/'runs')},'bindings':[{'path':str(p),'sha256':m.digest(p)} for p in paths]}
    values['execution']=execution
    monkeypatch.setattr(m,'pilot_lock',lambda *_:({'phase1_results':{k:{'name':k} for k in phase1}},'science'))
    monkeypatch.setattr(m,'published',lambda ref,repo:values[ref['name']])
    plan={'repository':'authored','LP':{'sha256':'lp-sha'},'phase':'pilot','arm':'B','run_seed':1301,
          'technical_results':{k:{'name':k} for k in ('T1','T2','T3','T4')},
          'train_audit':{'name':'audit','sha256':'audit-sha'},'execution_lock':{'name':'execution','sha256':'execution-sha'}}
    return plan,values,execution


def test_learning_requires_final_technical_and_independent_audit_admission(tmp_path,monkeypatch):
    plan,values,_=fixture(tmp_path,monkeypatch)
    first=m.admit(plan)
    assert m.admit(plan)==first and first['status']=='ADMITTED' and not first['automatic_retry']
    values['T4']['status']='INCONCLUSIVE'
    with pytest.raises(ValueError,match='technical prerequisite'):m.admit(plan)
    values['T4']['status']='PASS';values['audit']['independent_checks_functioning']=False
    with pytest.raises(ValueError,match='independent checks'):m.admit(plan)


def test_disabled_C_and_unregistered_seed_do_not_get_admitted(tmp_path,monkeypatch):
    plan,values,_=fixture(tmp_path,monkeypatch);plan['arm']='C';values['G1']['status']='INCONCLUSIVE'
    with pytest.raises(ValueError,match='not prospectively admitted'):m.admit(plan)
    plan['arm']='B';plan['run_seed']=1302
    with pytest.raises(ValueError,match='not prospectively admitted'):m.admit(plan)


def test_each_learning_stage_is_reserved_once_and_terminal_runs_cannot_dispatch(tmp_path,monkeypatch):
    plan,_,_=fixture(tmp_path,monkeypatch);m.admit(plan)
    root=tmp_path/'runs/pilot/B/1301'
    args={'update':1,'stage':'generate','execution_sha':'execution-sha','inputs':{'prefix':'authored-sha'}}
    path=m.reserve_stage(root,**args);saved=json.loads(path.read_text())
    assert not saved['automatic_retry'] and saved['inputs_sha256']==m.signature(args['inputs'])
    with pytest.raises(FileExistsError):m.reserve_stage(root,**args)
    (root/'terminal.json').write_text('{}');args['stage']='update'
    with pytest.raises(ValueError,match='already terminal'):m.reserve_stage(root,**args)


def test_main_needs_fixed_seeds_passed_T5_and_feasible_L2_budget(tmp_path,monkeypatch):
    plan,values,execution=fixture(tmp_path,monkeypatch)
    plan.update(phase='main',run_seed=13011,T5={'name':'T5','sha256':'t5-sha'})
    execution.update(gate='L2',T5_sha256='t5-sha',main_seeds=[13011,13012,13013],token_budget={'one_percent_matching_feasible':True})
    values['T5']={'gate':'T5','condition':'v2-S2','status':'PASS'}
    assert m.admit(plan)['phase']=='main'
    execution['token_budget']['one_percent_matching_feasible']=False
    with pytest.raises(ValueError,match='token-matching'):m.admit(plan)


def test_changed_monitor_source_binding_refuses_learning(tmp_path,monkeypatch):
    plan,_,execution=fixture(tmp_path,monkeypatch)
    execution['bindings'][-1]['sha256']='0'*64
    with pytest.raises(ValueError,match='implementation unbound'):m.admit(plan)
