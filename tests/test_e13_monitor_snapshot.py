"""Freeze monitor input chronology and model bytes under a paused controller without generation or fitting."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_monitor_snapshot',PHASE/'monitor_snapshot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path


def ref(path):return {'path':str(path),'sha256':m.digest(path)}


def fixture(tmp_path,monkeypatch):
    here=tmp_path/'phase2';here.mkdir();(tmp_path/'locks').mkdir()
    for name in m.SOURCES:(here/name).write_text('authored source '+name)
    monkeypatch.setattr(m,'HERE',here)
    root=tmp_path/'ledger/pilot/B/1301';root.mkdir(parents=True)
    run={'phase':'pilot','arm':'B','run_seed':1301,'execution_lock':{'sha256':'execution'}}
    put(root/'admission.json',{'status':'ADMITTED','execution_lock_sha256':'execution'})
    model=tmp_path/'model';model.mkdir();(model/'weights.safetensors').write_bytes(b'authored tiny weights')
    cells=[{'audit_id':f'audit_{i}','task_id':f'authored_{i}','group_id':f'group_{i}','split':'train'} for i in range(32)]
    cohort=put(tmp_path/'cohort.json',{'condition':'v2-S2','cells':cells})
    prompts=put(tmp_path/'prompts.json',{c['task_id']:{'task_id':c['task_id'],'split':'train','prompt_token_ids':[1,2],
        'required_paths':['solution.lean']} for c in cells})
    suites=put(tmp_path/'suites.json',{});ids=tmp_path/'train.txt';ids.write_text('\n'.join(c['task_id'] for c in cells)+'\n')
    initial=put(tmp_path/'initial.json',{'bindings':[ref(model/'weights.safetensors')]})
    config={'monitor':{'cohort':ref(cohort),'hidden_suites':ref(suites),'stage_seconds':{'monitor_preflight':300,'monitor_generate':900}},
            'train_prompts':ref(prompts),'initial_model_manifest':ref(initial),
            'runtime':{'initial_model':str(model),'train_ids':str(ids),'bindings':[]}}
    cp=put(tmp_path/'learning_config.json',config)
    state={'condition':'v2-S2','status':'WAIT_FOR_MONITOR','next_stage':'monitor','completed_updates':0,
           'execution_sha256':'execution','configuration_sha256':m.digest(cp),'model':str(model)}
    put(root/'state.json',state)
    paths=[*here.iterdir(),*model.iterdir(),cohort,prompts,suites,ids,initial,cp]
    execution={'bindings':[ref(p) for p in paths],'configuration':{'ledger':str(tmp_path/'ledger')}}
    monkeypatch.setattr(m,'learning_authority',lambda _: ({},execution,config))
    return {'learning':{'run':run,'configuration':str(cp)}},config,root,state


def test_freeze_retains_immutable_state_and_paired_monitor_randomness(tmp_path,monkeypatch):
    plan,config,root,state=fixture(tmp_path,monkeypatch)
    result=m.freeze(plan);lock=json.loads(Path(result['lock']).read_text())
    snapshot=json.loads(Path(lock['configuration']['snapshot']).read_text())
    assert result['model_calls']==snapshot['model_calls']==0 and len(snapshot['cells'])==32
    assert lock['controller_state_sha256']==m.digest(root/'state.json')
    with pytest.raises(FileExistsError):m.freeze(plan)
    state['completed_updates']=10;put(root/'state.json',state)
    next_lock=json.loads(Path(m.freeze(plan)['lock']).read_text())
    after=json.loads(Path(next_lock['configuration']['snapshot']).read_text())
    assert [r['seed'] for r in snapshot['cells']]==[r['seed'] for r in after['cells']]
    assert lock['model_binding_sha256']==next_lock['model_binding_sha256']
    # Advancing the live controller must not change any frozen prior bytes.
    assert all(m.digest(b['path'])==b['sha256'] for b in lock['bindings'])


def test_freeze_refuses_unpaused_controller_and_changed_initial_weights(tmp_path,monkeypatch):
    plan,config,root,state=fixture(tmp_path,monkeypatch)
    state['status']='RUNNING';put(root/'state.json',state)
    with pytest.raises(ValueError,match='not paused'):m.freeze(plan)
    state['status']='WAIT_FOR_MONITOR';put(root/'state.json',state)
    (Path(state['model'])/'weights.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='initial model changed'):m.freeze(plan)
    assert not (root/'monitors').exists()


def test_runtime_and_reservation_are_exclusive_and_bound_to_snapshot(tmp_path,monkeypatch):
    plan,config,root,state=fixture(tmp_path,monkeypatch)
    result=m.freeze(plan);lock=json.loads(Path(result['lock']).read_text())
    materialized=m.materialize(lock,config,'monitor_preflight',{'id':'owned'},result['sha256'])
    runtime=json.loads(Path(materialized['runtime']).read_text());reservation=json.loads(Path(materialized['reservation']).read_text())
    assert runtime['model']==lock['model'] and runtime['model_binding_sha256']==lock['model_binding_sha256']
    assert runtime['cells_path']==lock['configuration']['cells_path'] and materialized['maximum_seconds']==300
    assert reservation['configuration_sha256']==m.digest(materialized['runtime']) and reservation['snapshot_sha256']==result['sha256']
    with pytest.raises(FileExistsError):m.materialize(lock,config,'monitor_preflight',{'id':'owned'},result['sha256'])
    with pytest.raises(FileNotFoundError):m.materialize(lock,config,'monitor_generate',{'id':'next'},result['sha256'])
