"""Exercise layout admission against forged receipts and scientifically changed configurations."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
import yaml

S=Path(__file__).parents[1]/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts'
spec=importlib.util.spec_from_file_location('sft_layout_e08',S/'sft_layout_e08.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture(tmp_path):
    v=tmp_path/'expt_v1';(v/'configs').mkdir(parents=True);(v/'results').mkdir()
    (tmp_path/'PROTOCOL.md').write_text('frozen');(v/'results/sft_schedule.json').write_text('{}')
    base=yaml.safe_load((m.EXPV/'configs/e08_sft_14B.yaml').read_text())
    (v/'configs/e08_sft_14B.yaml').write_text(yaml.safe_dump(base))
    c=copy.deepcopy(base);c['cluster']['gpus_per_node']=2;c['policy']['dtensor_cfg'].update(tensor_parallel_size=2,cpu_offload=True)
    (v/'configs/candidate.yaml').write_text(yaml.safe_dump(c))
    d={'protocol_sha256':m.digest(tmp_path/'PROTOCOL.md'),'schedule_sha256':m.digest(v/'results/sft_schedule.json'),'routes':[
        {'id':'historical','status':'admitted','gpus':8,'tensor_parallel_size':8,'cpu_offload':False,'config':'configs/e08_sft_14B.yaml','config_sha256':m.digest(v/'configs/e08_sft_14B.yaml'),'admission_kind':'historical_protocol'},
        {'id':'small','status':'pending','gpus':2,'tensor_parallel_size':2,'cpu_offload':True,'config':'configs/candidate.yaml','config_sha256':m.digest(v/'configs/candidate.yaml'),'admission_kind':'prospective_layout'}]}
    p=v/'registry.json';p.write_text(json.dumps(d));return v,p,d

def test_pending_smaller_route_cannot_launch(tmp_path):
    v,p,d=fixture(tmp_path)
    assert m.choose_layout(2,registry=p,expv=v) is None
    assert m.choose_layout(8,registry=p,expv=v)['id']=='historical'

@pytest.mark.parametrize('field,value',[('precision','float16'),('train_global_batch_size',4),('max_grad_norm',0.5)])
def test_scientific_change_rejected(field,value):
    a=yaml.safe_load((m.EXPV/'configs/e08_sft_14B.yaml').read_text());b=copy.deepcopy(a);b['policy'][field]=value
    with pytest.raises(ValueError,match='scientific config'):m.invariant_config(a,b)

def test_recipe_or_data_order_cannot_change():
    a=yaml.safe_load((m.EXPV/'configs/e08_sft_14B.yaml').read_text())
    for category,field,value in [('sft','seed',1),('data','shuffle',True)]:
        b=copy.deepcopy(a);b[category][field]=value
        with pytest.raises(ValueError):m.invariant_config(a,b)

def test_smaller_route_needs_all_checks_and_unchanged_evidence(tmp_path):
    v,p,d=fixture(tmp_path);r=d['routes'][1];r['status']='admitted';p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='checks incomplete'):m.admitted_layouts(p,v)
    e=v/'results/evidence.json';e.write_text('{"fixture":true}')
    r['evidence']={'checks':{k:'PASS' for k in m.REQUIRED_CHECKS},'files':[{'path':'results/evidence.json','sha256':m.digest(e)}]};p.write_text(json.dumps(d))
    assert m.choose_layout(2,registry=p,expv=v)['id']=='small'
    e.write_text('changed')
    with pytest.raises(ValueError,match='evidence changed'):m.admitted_layouts(p,v)

def test_historical_receipt_cannot_authorize_changed_layout(tmp_path):
    v,p,d=fixture(tmp_path);d['routes'][1].update(status='admitted',admission_kind='historical_protocol');p.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='historical admission'):m.admitted_layouts(p,v)

def test_changed_admitted_config_rejected(tmp_path):
    v,p,d=fixture(tmp_path);(v/'configs/e08_sft_14B.yaml').write_text('changed')
    with pytest.raises(ValueError,match='hash/path'):m.admitted_layouts(p,v)


def test_segment_resume_cannot_change_layout(tmp_path):
    v,p,d=fixture(tmp_path)
    layout=m.admitted_layouts(p,v)[0]
    root=tmp_path/'production'
    m.record_run(root,layout)
    m.record_run(root,layout)
    changed=dict(layout,id='different',gpus=2)
    with pytest.raises(ValueError,match='another layout'):m.record_run(root,changed)


def test_prospective_layout_refuses_existing_checkpoint(tmp_path):
    v,p,d=fixture(tmp_path);root=tmp_path/'production';(root/'checkpoints/step_2').mkdir(parents=True)
    with pytest.raises(ValueError,match='pinned Base'):m.record_run(root,d['routes'][1])
