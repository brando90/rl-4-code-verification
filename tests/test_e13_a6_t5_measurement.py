"""Check A6 B-reward feasibility boundaries using authored arrays only."""
from pathlib import Path
import importlib.machinery,importlib.util
import pytest
import sys
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import a6_t5_measurement as m

def fixture(horizon,early=.1,late=.12):return [{'arm':'B','seed':1301,'split':'train','update':i,'rewards':[early if i<=10 else late]*256}for i in range(1,horizon+1)]
def test_exact_two_percentage_points_pass():
 r=m.evaluate(fixture(30),horizon=30);assert r['status']=='PASS'and r['improvement_bounds']==[.02,.02]and r['arm']=='B'
def test_one_extension_then_fail():
 assert m.evaluate(fixture(30,late=.119),horizon=30)['status']=='EXTEND_TO_60'
 assert m.evaluate(fixture(60,late=.119),horizon=60)['status']=='FAIL'
def test_final_window_is_51_to_60():
 rows=fixture(60,late=.1)
 for r in rows[50:]:r['rewards']=[.12]*256
 assert m.evaluate(rows,horizon=60)['status']=='PASS'
def test_missing_slots_never_imputed():
 rows=fixture(60);rows[-1]['rewards']=[None]*256;r=m.evaluate(rows,horizon=60)
 assert r['status']=='INCONCLUSIVE'and r['final']['measured']==2304 and r['final']['declared']==2560
@pytest.mark.parametrize('change',['arm','seed','missing_update','duplicate_update'])
def test_other_arm_seed_or_cohort_refused(change):
 rows=fixture(30)
 if change=='arm':rows[0]['arm']='A'
 elif change=='seed':rows[0]['seed']=1302
 elif change=='missing_update':rows.pop()
 else:rows.append(rows[-1])
 with pytest.raises(ValueError):m.evaluate(rows,horizon=30)
