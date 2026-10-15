"""Exercise measured cost boundaries and refuse missing costs as complete resource allocations."""
from importlib.machinery import SourceFileLoader
from importlib.util import spec_from_loader,module_from_spec
from pathlib import Path
import subprocess,sys,copy
import pytest
source=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2/costs.py'
spec=spec_from_loader('e13_draft_costs',SourceFileLoader('e13_draft_costs',str(source)))
m=module_from_spec(spec);spec.loader.exec_module(m)

def test_measure_actual_waited_child_cpu_and_owned_file_growth(tmp_path):
 before=m.snapshot(tmp_path)
 subprocess.run([sys.executable,'-c','sum(i*i for i in range(1000000))'],check=True)
 (tmp_path/'owned').write_bytes(b'x'*8192)
 result=m.difference(before,m.snapshot(tmp_path))
 assert result['wall_seconds']>0 and result['accounted_cpu_hours']>0 and result['logical_bytes']==8192
 assert result['files']==1 and result['allocated_bytes']>=8192

def test_closed_lease_cost_requires_exact_ids_cleanup_and_interval():
 rows=[{'id':'a','owner':'e13v2','status':'RELEASED','device_hours':.5,'started_unix':10,'released_unix':1810}]
 assert m.device_cost(rows,expected_ids=['a'],cleanup_receipts={'a':{'verified':True}})['device_hours']==.5
 with pytest.raises(ValueError,match='cleanup'):m.device_cost(rows,expected_ids=['a'],cleanup_receipts={'a':{'verified':False}})
 rows[0]['device_hours']=.4
 with pytest.raises(ValueError,match='interval'):m.device_cost(rows,expected_ids=['a'],cleanup_receipts={'a':{'verified':True}})

def components():
 return [{'category':k,'name':k,'planned_units':2,'measured_units':1,'evidence':[{'path':'authored','sha256':'authored'}],
          'measured_cost':{'device_hours':1.,'cpu_hours':2.,'wall_hours':3.,'storage_bytes':4.}} for k in sorted(m.REQUIRED)]

def test_all_cost_categories_and_25_percent_reserve_are_explicit():
 rows=components();result=m.project(rows)
 assert result['status']=='COMPLETE_ESTIMATE' and result['with_reserve']['device_hours']==20.
 assert result['with_reserve']['storage_bytes']==80. and not result['allocation_granted']
 with pytest.raises(ValueError,match='categories'):m.project(rows[:-1])
 with pytest.raises(ValueError,match='25 percent'):m.project(rows,reserve_fraction=0)

def test_missing_is_not_zero_and_explicit_omissions_need_reasons():
 rows=components();rows[0]['measured_cost']['cpu_hours']=None
 result=m.project(rows)
 assert result['status']=='INCOMPLETE_COSTS' and result['with_reserve']['cpu_hours'] is None
 assert result['measured_component_subtotals']['cpu_hours']==28.
 rows[0]={'name':rows[0]['name'],'category':rows[0]['category'],'not_applicable':True,'planned_units':0}
 with pytest.raises(ValueError,match='reason'):m.project(rows)
 rows[0]['reason']='authored test component explicitly absent'
 assert m.project(rows)['status']=='COMPLETE_ESTIMATE'

def test_stage_cost_keeps_missing_device_receipt_unknown_and_cpu_only_explicit(tmp_path):
 before=m.snapshot(tmp_path);after=m.snapshot(tmp_path)
 cpu=m.stage_cost(before,after,stage='score')
 assert cpu['device_hours']==0 and cpu['status']=='RECORDED'
 incomplete=m.stage_cost(before,after,stage='update',lease={'id':'unresolved','status':'ACTIVE','owner':'e13v2'})
 assert incomplete['device_hours'] is None and incomplete['status']=='INCOMPLETE_DEVICE_COST'
 lease={'id':'closed','owner':'e13v2','status':'RELEASED','device_hours':.5,'started_unix':10,'released_unix':1810}
 complete=m.stage_cost(before,after,stage='update',lease=lease,cleanup={'verified':True})
 assert complete['status']=='RECORDED' and complete['device_hours']==.5
 assert not complete['admission_statistics_computed']
