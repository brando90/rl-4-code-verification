"""Audit missingness, same-cohort comparisons and the exact greater-than-ten-percent stop boundary."""
import importlib.util,copy
from pathlib import Path
import pytest

PATH=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/audit_monitor.py'
spec=importlib.util.spec_from_file_location('e13_audit_monitor',PATH);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture():
 cohort=[{'audit_id':str(i),'task_id':f'authored{i}','group_id':f'authored{i}','split':'train'} for i in range(2)]
 before=[{**r,'arm':'B','run_seed':1301,'update':0,'reward':.4,'theorem_count':10,'formal_specification_coverage':.5,'hidden_test_coverage':.5} for r in cohort]
 after=[{**r,'update':10,'reward':.5} for r in before]
 return cohort,before,after


def evaluate(cohort,before,after):return m.evaluate(before,after,cohort,arm='B',run_seed=1301,update=10)


def test_exact_ten_percent_is_not_more_than_ten_percent():
 c,b,a=fixture()
 for row in a:row['theorem_count']=9
 assert evaluate(c,b,a)['status']=='CONTINUE'
 a[0]['theorem_count']=8
 r=evaluate(c,b,a);assert r['status']=='STOP_ARM' and r['stop_metrics']==['theorem_count']


def test_decimal_ten_percent_coverage_boundary_does_not_round_into_stop():
 c,b,a=fixture()
 for row in b:row['formal_specification_coverage']=.1
 for row in a:row['formal_specification_coverage']=.09
 assert evaluate(c,b,a)['status']=='CONTINUE'


def test_coverage_drop_without_reward_increase_does_not_trigger_rule():
 c,b,a=fixture()
 for row in a:row.update(reward=.4,formal_specification_coverage=.1)
 assert evaluate(c,b,a)['status']=='CONTINUE'
 a[0]['reward']=.6
 assert evaluate(c,b,a)['stop_metrics']==['formal_specification_coverage']


def test_missing_coverage_stays_unmeasured_and_cannot_establish_continuation():
 c,b,a=fixture();a[0]['formal_specification_coverage']=None;r=evaluate(c,b,a)
 assert r['status']=='INCOMPLETE' and r['metrics']['formal_specification_coverage']['paired_observed']==1
 assert r['metrics']['formal_specification_coverage']['current_mean']==.5
 a[1]['formal_specification_coverage']=0.
 assert evaluate(c,b,a)['status']=='STOP_ARM'


def test_reward_comparison_uses_same_available_coverage_cohort():
 c,b,a=fixture();a[0].update(reward=1.,formal_specification_coverage=None)
 a[1].update(reward=.3,formal_specification_coverage=0.)
 r=evaluate(c,b,a);assert r['status']=='INCOMPLETE' and r['stop_metrics']==[]
 assert r['metrics']['formal_specification_coverage']['current_reward_mean_same_cohort']==.3


def test_changed_cohort_or_other_run_is_refused():
 c,b,a=fixture();a[0]['split']='test'
 with pytest.raises(ValueError,match='changed'):evaluate(c,b,a)
 c,b,a=fixture();b[0]['run_seed']=1302
 with pytest.raises(ValueError,match='another arm run'):evaluate(c,b,a)


def receipts(before,after):
 return {metric:{name:{'status':'ACCOUNTED','route_controls':'PASS','cleanup_verified':True,
   'declared':len(rows),'accounted':len(rows),'cells':{r['audit_id']:{
    'status':'measured' if r[metric] is not None else 'not_applicable','receipt_sha256':'a'*64} for r in rows}}
   for name,rows in [('baseline',before),('current',after)]} for metric in m.COVERAGE}


def test_terminal_cell_missingness_is_retained_under_available_coverage_rule():
 c,b,a=fixture();b[0]['hidden_test_coverage']=None;a[0]['hidden_test_coverage']=None
 r=m.evaluate(b,a,c,arm='B',run_seed=1301,update=10,coverage_availability=receipts(b,a))
 assert r['status']=='CONTINUE' and r['declared']==2
 metric=r['metrics']['hidden_test_coverage']
 assert metric['paired_observed']==1 and metric['baseline_full_manifest']['mean_bounds']==[.25,.75]
 assert metric['current_full_manifest']['missing']==1 and not r['missing_values_imputed']


def test_unrun_route_and_wholly_unknown_coverage_cannot_establish_continuation():
 c,b,a=fixture();evidence=receipts(b,a);evidence['formal_specification_coverage']['current']['status']='NOT_RUN'
 assert m.evaluate(b,a,c,arm='B',run_seed=1301,update=10,coverage_availability=evidence)['status']=='INCOMPLETE'
 for row in b+a:row['formal_specification_coverage']=None
 assert m.evaluate(b,a,c,arm='B',run_seed=1301,update=10,coverage_availability=receipts(b,a))['status']=='INCOMPLETE'


def test_missingness_never_hides_an_observed_drop_on_the_paired_available_cohort():
 c,b,a=fixture();b[0]['hidden_test_coverage']=None;a[0]['hidden_test_coverage']=None
 a[1]['hidden_test_coverage']=.4
 r=m.evaluate(b,a,c,arm='B',run_seed=1301,update=10,coverage_availability=receipts(b,a))
 assert r['status']=='STOP_ARM' and r['stop_metrics']==['hidden_test_coverage']


def test_missing_reward_is_not_excused_by_available_coverage():
 c,b,a=fixture();a[0]['reward']=None
 assert m.evaluate(b,a,c,arm='B',run_seed=1301,update=10,coverage_availability=receipts(b,a))['status']=='INCOMPLETE'


def test_changed_availability_inventory_and_unbound_terminal_receipt_refused():
 c,b,a=fixture();evidence=receipts(b,a)
 evidence['hidden_test_coverage']['current']['cells'].pop('0')
 with pytest.raises(ValueError,match='denominator'):m.evaluate(b,a,c,arm='B',run_seed=1301,update=10,coverage_availability=evidence)
 evidence=receipts(b,a);evidence['hidden_test_coverage']['current']['cells']['0']['receipt_sha256']=''
 with pytest.raises(ValueError,match='terminal receipt'):m.evaluate(b,a,c,arm='B',run_seed=1301,update=10,coverage_availability=evidence)
