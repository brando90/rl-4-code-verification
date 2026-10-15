"""Exercise receipt-bound cost projection, unknown costs, reserve accounting and refusal of changed evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_cost_recipe',PHASE/'cost_recipe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path):
    path=tmp_path/'measured.json';path.write_text(json.dumps({'n':8,'device':2.,'cpu':3.,'wall':4.,'bytes':100}))
    sources={'probe':{'path':str(path),'sha256':m.digest(path)}}
    def term(field):return {'source':'probe','field':[field],'scale':1.}
    from costs import REQUIRED
    recipe={'condition':'v2-S2','reserve_fraction':.25,'components':[{
        'name':category,'category':category,'planned_units':16,'measured_units':term('n'),
        'measured_cost':{u:[term(f)] for u,f in zip(m.UNITS,('device','cpu','wall','bytes'))},
        'scope':'authored receipt','projection_assumption':'twice the eight measured units'} for category in sorted(REQUIRED)],
        'unreported_external_costs':['hosted sandbox processor usage is not reported']}
    return recipe,sources,path


def measurements():
    return {k:1. for k in ('device_hours_per_update','generated_tokens_per_device_second','lean_wall_seconds',
        'lean_cpu_hours','raw_storage_growth_bytes','native_checkpoint_bytes','export_bytes','calibration_cpu_hours',
        'evaluation_device_hours','evaluation_cpu_hours')}


def test_all_categories_and_reserve_accounted_without_granting_allocation(tmp_path):
    recipe,sources,path=fixture(tmp_path);value=m.materialize(recipe,sources)
    assert value['status']=='COMPLETE_ESTIMATE' and value['with_reserve']['device_hours']==40
    assert value['with_reserve']['storage_bytes']==2000
    verdict=m.gate(value,measurements())
    assert verdict['status']=='PASS' and not verdict['learning_allocation_admitted']
    assert not value['allocation_granted'] and len(value['unreported_external_costs'])==1


def test_missing_receipt_field_prevents_complete_cost_claim(tmp_path):
    recipe,sources,path=fixture(tmp_path);recipe['components'][0]['measured_cost']['cpu_hours'][0]['field']=['not_reported']
    value=m.materialize(recipe,sources)
    assert value['with_reserve']['cpu_hours'] is None and value['status']=='INCOMPLETE_COSTS'
    assert m.gate(value,measurements())['status']=='INCONCLUSIVE'
    measured=measurements();measured['evaluation_device_hours']=None
    assert m.gate(value,measured)['missing_measurements']==['evaluation_device_hours']


def test_changed_receipt_or_implicit_zero_is_rejected(tmp_path):
    recipe,sources,path=fixture(tmp_path);path.write_text('{}')
    with pytest.raises(ValueError,match='changed'):m.materialize(recipe,sources)
    recipe,sources,path=fixture(tmp_path);recipe['components'][0]['measured_cost']['device_hours']=[]
    with pytest.raises(ValueError,match='implicit-zero'):m.materialize(recipe,sources)
    assert m.resolve({'zero_reason':'processor-only stage; no graphics device lease'},sources)[0]==0
    with pytest.raises(ValueError,match='scope'):m.resolve({'zero_reason':''},sources)


def test_zero_denominator_missing_category_or_invalid_measurement_cannot_pass(tmp_path):
    recipe,sources,path=fixture(tmp_path);recipe['components'][0]['measured_units']={'zero_reason':'invalid denominator'}
    with pytest.raises(ValueError,match='denominator'):m.materialize(recipe,sources)
    recipe,sources,path=fixture(tmp_path);recipe['components'].pop()
    with pytest.raises(ValueError,match='categories'):m.materialize(recipe,sources)
    recipe,sources,path=fixture(tmp_path);value=m.materialize(recipe,sources);measured=measurements()
    measured['generated_tokens_per_device_second']=0
    assert m.gate(value,measured)['status']=='INCONCLUSIVE'
    measured['lean_cpu_hours']=-1
    with pytest.raises(ValueError,match='finite numeric'):m.gate(value,measured)
