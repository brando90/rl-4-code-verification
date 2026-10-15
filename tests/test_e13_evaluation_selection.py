"""Bind validation selection to all four checkpoints from one frozen main run without test admission."""
import importlib.util
from pathlib import Path
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_evaluation_selection',PHASE/'evaluation_selection.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
    reports=[{'condition':'v2-S2','stage':'VALIDATION_SCORE','arm':'B','run_seed':13011,'boundary':i,
        'LP_sha256':'LP','L2_sha256':'L2','evaluation_contract_sha256':'contract','cleanup_unresolved':0,
        'generation_sha256':'1'*64,'scoring_sha256':'2'*64,'model_binding_sha256':str(i)*64,
        'boundary_receipt_sha256':str(i)*64,'summary':{'declared':1080,'measured':1080,'missing':0,
        'task_count':135,'samples_per_task':8,'successes':100}} for i in (1,2,3,4)]
    kwargs={'arm':'B','run_seed':13011,'LP_sha256':'LP','L2_sha256':'L2','contract_sha256':'contract'}
    return reports,kwargs


def test_ties_choose_later_actual_model_but_do_not_admit_test():
    reports,kwargs=fixture();result=m.evaluate(reports,**kwargs)
    assert result['status']=='SELECTED' and result['boundary']==4 and result['model_binding_sha256']=='4'*64
    assert not result['test_admitted'] and len(result['all_four_validation_summaries'])==4


def test_missing_values_that_can_change_the_winner_remain_inconclusive():
    reports,kwargs=fixture();reports[0]['summary'].update(measured=1079,missing=1)
    result=m.evaluate(reports,**kwargs)
    assert result['status']=='INCONCLUSIVE' and result['boundary'] is None and result['model_binding_sha256'] is None


def test_mixed_seed_settings_and_unresolved_cleanup_cannot_select():
    reports,kwargs=fixture();reports[1]['run_seed']=13012
    with pytest.raises(ValueError,match='cross runs'):m.evaluate(reports,**kwargs)
    reports,kwargs=fixture();reports[1]['evaluation_contract_sha256']='changed'
    with pytest.raises(ValueError,match='cross runs'):m.evaluate(reports,**kwargs)
    reports,kwargs=fixture();reports[1]['cleanup_unresolved']=1
    with pytest.raises(ValueError,match='cleanup'):m.evaluate(reports,**kwargs)


def test_missing_checkpoint_or_model_binding_cannot_select():
    reports,kwargs=fixture()
    with pytest.raises(ValueError,match='four complete'):m.evaluate(reports[:3],**kwargs)
    reports[0]['model_binding_sha256']=''
    with pytest.raises(ValueError,match='provenance'):m.evaluate(reports,**kwargs)
