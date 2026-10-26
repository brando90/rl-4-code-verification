"""Exercise exact paused-checkpoint monitor authority, controller fencing and owned child cleanup without devices."""
from pathlib import Path
import fcntl
import importlib.util
import json
import socket
import sys
import time
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_monitor_supervisor',PHASE/'monitor_supervisor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'ledger/pilot/B/1301';root.mkdir(parents=True)
    run={'phase':'pilot','arm':'B','run_seed':1301,'execution_lock':{'sha256':'execution'},'repository':'authored'}
    put(root/'admission.json',{'status':'ADMITTED','execution_lock_sha256':'execution'})
    state=put(root/'state.json',{'status':'WAIT_FOR_MONITOR','next_stage':'monitor','completed_updates':0,'execution_sha256':'execution'})
    snap=put(tmp_path/'snapshot.json',{});cells=put(tmp_path/'cells.json',[])
    inputs=[{'path':str(p),'sha256':m.digest(p)} for p in (snap,cells)]
    snapshot={'gate':'PILOT_MONITOR_SNAPSHOT','condition':'v2-S2','status':'FROZEN','execution_sha256':'execution',
        'arm':'B','run_seed':1301,'update':0,'model':'authored-model','model_binding_sha256':'model-sha',
        'controller_state_sha256':m.digest(state),'bindings':inputs}
    paths=[PHASE/'monitor_supervisor.py',PHASE/'monitor_runtime.py',PHASE/'monitor_preparation.py',
           PHASE.parent/'phase1/device_binding.py',PHASE.parent/'phase1/lp1.py',PHASE.parent/'phase1/anchor_lease.py']
    execution={'bindings':[{'path':str(p),'sha256':m.digest(p)} for p in paths],
               'configuration':{'ledger':str(tmp_path/'ledger')}}
    lp={'configuration':{'training_runtime_contract':{'numerical_dtype':'float16'}}}
    monkeypatch.setattr(m,'verify_learning',lambda _: (lp,execution,'science'))
    monkeypatch.setattr(m,'published',lambda *_:snapshot)
    lease={'id':'owned','phase':'v2-S2-learning-pilot','owner':'e13v2','status':'ACTIVE',
           'host':socket.gethostname().split('.')[0],'started_unix':time.time(),'expires_unix':time.time()+1000,
           'run_key':'B/1301/0/monitor_preflight'}
    lease_root=tmp_path/'leases';lease_path=put(lease_root/'owned.json',lease)
    config={'condition':'v2-S2','stage':'monitor_preflight','learning_phase':'pilot','arm':'B','run_seed':1301,'update':0,
            'model':'authored-model','model_binding_sha256':'model-sha','numerical_dtype':'float16','bindings':execution['bindings']+inputs,
            'snapshot':str(snap),'cells_path':str(cells),'lease_id':'owned','lease_path':str(lease_path),'python':sys.executable}
    cp=put(tmp_path/'runtime.json',config)
    reservation=put(root/'monitors/update_00000/monitor_preflight.json',{'execution_sha256':'execution','snapshot_sha256':'snapshot',
        'stage':'monitor_preflight','configuration_sha256':m.digest(cp),'lease_id':'owned','maximum_seconds':300})
    plan={'run':run,'stage':'monitor_preflight','config':str(cp),'reservation':str(reservation),'snapshot_lock':{'sha256':'snapshot'},
          'lease_root':str(lease_root),'maximum_seconds':300,'dispatch_root':str(tmp_path/'dispatch'),'environment':{}}
    return plan,config,lease,root


def test_monitor_refuses_a_controller_that_advanced_from_its_frozen_checkpoint(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch)
    assert m.authorize(plan)[1]==lease
    state=json.loads((root/'state.json').read_text());state['completed_updates']=1;put(root/'state.json',state)
    with pytest.raises(ValueError,match='controller moved'):m.authorize(plan)


def test_monitor_refuses_another_runs_lease_and_changed_numerics(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch)
    lease['run_key']='C/1301/0/monitor_preflight';put(Path(config['lease_path']),lease)
    with pytest.raises(ValueError,match='canonical local'):m.authorize(plan)
    config['numerical_dtype']='bfloat16';put(Path(plan['config']),config)
    with pytest.raises(ValueError,match='contract differs'):m.authorize(plan)


def test_monitor_holds_the_learning_controller_fence_through_child_cleanup(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch)
    dummy=tmp_path/'runtime';dummy.mkdir();(dummy/'monitor_runtime.py').write_text('raise SystemExit(7)\n')
    monkeypatch.setattr(m,'authorize',lambda _: (config,lease,{}));monkeypatch.setattr(m,'HERE',dummy)
    monkeypatch.setattr(m,'launch_environment',lambda *_:{'CUDA_VISIBLE_DEVICES':'2'});calls=[]
    def cleanup(marker):
        with (root/'controller.lock').open('a') as check:
            with pytest.raises(BlockingIOError):fcntl.flock(check,fcntl.LOCK_EX|fcntl.LOCK_NB)
        calls.append(('cleanup',marker));return {'verified':True,'signals':[]}
    monkeypatch.setattr(m,'cleanup',cleanup)
    monkeypatch.setattr(m,'release',lambda _,marker,**kw:calls.append(('release',marker,kw['cleanup_verified'])) or True)
    result=m.launch(plan)
    assert result['status']=='INCOMPLETE_INFRA' and result['worker_exit_code']==7 and result['snapshot_sha256']=='snapshot'
    assert calls==[('cleanup','owned'),('release','owned',True)]
    assert json.loads((Path(plan['dispatch_root'])/'launch.json').read_text())['visible_index']=='2'
    with pytest.raises(FileExistsError):m.launch(plan)


def test_competing_learning_controller_prevents_monitor_launch(tmp_path,monkeypatch):
    plan,config,lease,root=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'launch_reserved',lambda _:pytest.fail('monitor launched beside a live learning controller'))
    with (root/'controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):m.launch(plan)
    assert not Path(plan['dispatch_root']).exists()
