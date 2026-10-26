"""Check A6's prospective null-predictor transition with authored gate receipts only."""
from pathlib import Path
import sys,copy
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parent))
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
from a6_phase2_admission import select_arms_a6

def fixture():return [
 {'gate':'G0_A3','status':'PASS'},
 {'condition':'v2-S2','status':'PASS','numerical_dtype':'float16','admission_statistics_computed':True},
 {'status':'FROZEN','condition':'v2-S2','C_calibration_admitted':False},
 {'gate':'G1','status':'INCONCLUSIVE'},
 {'gate':'H2','condition':'v2-S2','status':'UNAVAILABLE','H2':{'predictor':None,'status':'UNAVAILABLE'},'F2':{'status':'UNAVAILABLE','prospectively_frozen_value':.75},'batch2':{'armed':False,'responses':0,'status':'SKIPPED_A6'},'disable_arm_C':True},
 {'condition':'v2-S2','status':'SOUND','LP_admitted':True,'cleanup_unresolved':0,'declared':512}]

def test_null_predictor_does_not_become_fake_measured_h2():
 values=fixture();r=select_arms_a6(*values)
 assert r['eligible_arms']==['A','B','P']and r['T5_arm']=='B'and values[4]['status']=='UNAVAILABLE'

@pytest.mark.parametrize('status',['UNSOUND','UNRESOLVED','INCOMPLETE-INFRA'])
def test_a6_without_soundness_cannot_admit_lp(status):
 values=fixture();values[-1]['status']=status;values[-1]['LP_admitted']=False
 with pytest.raises(ValueError,match='sound'):select_arms_a6(*values)

@pytest.mark.parametrize('key,value',[('status','INCONCLUSIVE'),('disable_arm_C',False),('batch2',{'armed':True,'responses':0,'status':'SKIPPED_A6'})])
def test_a6_waiver_is_exact(key,value):
 values=fixture();values[4][key]=value
 with pytest.raises(ValueError,match='waiver'):select_arms_a6(*values)

def test_generation_count_and_clean_scoring_are_required():
 for key,value in [('declared',511),('cleanup_unresolved',1)]:
  values=fixture();values[-1][key]=value
  with pytest.raises(ValueError,match='sound'):select_arms_a6(*values)
