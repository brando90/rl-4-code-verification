"""Preserve full evaluation populations and prevent unselected or post-main-designed test evaluation."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,importlib.util,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));sys.path.insert(0,str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location('e13_evaluation_snapshot',PHASE/'evaluation_snapshot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_complete_authored_validation_manifest_keeps_historical_per_sample_seeds(monkeypatch):
    ids=[f'authored_{i:03d}' for i in range(135)];tasks=[SimpleNamespace(task_id=key,instruction=key) for key in ids]
    monkeypatch.setattr(m,'render',lambda instruction,*a:{'text':instruction,'chat_text_sha256':hashlib.sha256(instruction.encode()).hexdigest(),
        'required_paths':['solution.lean']})
    value=m.manifest(ids,tasks,SimpleNamespace(encode=lambda text:[1,2]),'authored',purpose='validation',arm='A',run_seed=13011,boundary=2)
    assert len(value['cells'])==1080
    for cell in value['cells']:assert cell['seed']==91*100003+cell['sample_idx'] and cell['boundary']==2
    with pytest.raises(ValueError,match='prompt population'):m.manifest(ids,tasks[:-1],None,None,purpose='validation',arm='A',run_seed=13011,boundary=2)


def selection_fixture(monkeypatch):
    monkeypatch.setattr(m,'HERE',PHASE)
    run={'arm':'B','run_seed':13012,'execution_lock':{'sha256':'L2'}}
    boundary={'sha256':'boundary','model_binding_sha256':'model'}
    selected={'gate':'VALIDATION_SELECTION','condition':'v2-S2','status':'SELECTED','arm':'B','run_seed':13012,
        'boundary':3,'L2_sha256':'L2','model_binding_sha256':'model','boundary_receipt_sha256':'boundary',
        'evaluation_contract_sha256':m.digest(PHASE/'evaluation_contract.py')}
    analysis={'gate':'SELECTED_TEST_ANALYSIS','condition':'v2-S2','status':'FROZEN'}
    values={'selected':selected,'analysis':analysis}
    monkeypatch.setattr(m,'published',lambda ref,_:values[ref['name']])
    plan={'purpose':'test','boundary':3,'learning':{'run':run},'selection':{'name':'selected'},
          'analysis_lock':{'name':'analysis','path':'authored-analysis','sha256':'analysis-sha'}}
    execution={'bindings':[{'path':'authored-analysis','sha256':'analysis-sha'}]}
    return plan,{'boundaries':{'3':boundary}},execution,values


def test_test_snapshot_requires_own_selected_boundary(monkeypatch):
    plan,main,execution,values=selection_fixture(monkeypatch)
    assert m.selection_authority(plan,main,execution,'authored')['model_binding_sha256']=='model'
    values['selected']['boundary']=2
    with pytest.raises(ValueError,match='not selected'):m.selection_authority(plan,main,execution,'authored')


def test_test_analysis_must_already_be_bound_before_main(monkeypatch):
    plan,main,execution,values=selection_fixture(monkeypatch);execution['bindings']=[]
    with pytest.raises(ValueError,match='before main training'):m.selection_authority(plan,main,execution,'authored')


def test_inconclusive_selection_never_opens_test_execution(monkeypatch):
    plan,main,execution,values=selection_fixture(monkeypatch);values['selected']['status']='INCONCLUSIVE'
    with pytest.raises(ValueError,match='not selected'):m.selection_authority(plan,main,execution,'authored')
