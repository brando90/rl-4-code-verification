"""Retain evaluation lease identity, exclusive attempts and cleanup after a real failed child."""
from pathlib import Path
import fcntl,importlib.util,json,socket,sys,time
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_evaluation_supervisor',PHASE/'evaluation_supervisor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'evaluation';root.mkdir();key='validation_b1_preflight'
    run={'phase':'main','arm':'A','run_seed':13011,'execution_lock':{'sha256':'main'}}
    snapshot={'purpose':'validation','arm':'A','run_seed':13011,'boundary':1,'model':'authored-model',
        'model_binding_sha256':'model-sha','bindings':[],
        'configuration':{'root':str(root),'manifest':'authored-manifest','allowlist':'authored-allowlist'}}
    lp={'configuration':{'evaluation_runtime_contract':{'numerical_dtype':'float16'}}}
    monkeypatch.setattr(m,'snapshot_authority',lambda _:(lp,{}, {},snapshot))
    lease={'id':'owned','phase':'v2-S2-main','owner':'e13v2','status':'ACTIVE','host':socket.gethostname().split('.')[0],
        'started_unix':time.time(),'expires_unix':time.time()+1000,'run_key':f'A/13011/1/{key}'}
    lease_root=tmp_path/'leases';lease_path=put(lease_root/'owned.json',lease)
    runtime={'condition':'v2-S2','stage':'evaluation_preflight','stage_key':key,'purpose':'validation','arm':'A','run_seed':13011,
        'boundary':1,'model':'authored-model','model_binding_sha256':'model-sha','snapshot_sha256':'snapshot',
        'manifest':'authored-manifest','allowlist':'authored-allowlist','stage_root':str(root/key/'output'),
        'attempt_root':str(root/key/'health'),'numerical_dtype':'float16','bindings':[],'lease_id':'owned',
        'lease_path':str(lease_path),'python':sys.executable}
    cp=put(root/key/'runtime.json',runtime)
    reservation=put(root/(key+'.json'),{'L2_sha256':'main','snapshot_sha256':'snapshot','stage':'evaluation_preflight',
        'stage_key':key,'configuration_sha256':m.digest(cp),'lease_id':'owned','maximum_seconds':300})
    plan={'learning':{'run':run},'snapshot_lock':{'sha256':'snapshot'},'stage':'evaluation_preflight','stage_key':key,
        'config':str(cp),'reservation':str(reservation),'dispatch_root':str(root/key/'dispatch'),
        'lease_root':str(lease_root),'maximum_seconds':300,'environment':{}}
    return plan,runtime,lease,root


def test_other_runs_lease_cannot_launch_evaluation(tmp_path,monkeypatch):
    plan,runtime,lease,root=fixture(tmp_path,monkeypatch);assert m.authorize(plan)[1]==lease
    lease['run_key']='B/13011/1/validation_b1_preflight';put(Path(runtime['lease_path']),lease)
    with pytest.raises(ValueError,match='canonical local main-run'):m.authorize(plan)


def test_checkpoint_and_numerics_cannot_change_after_reservation(tmp_path,monkeypatch):
    plan,runtime,lease,root=fixture(tmp_path,monkeypatch);runtime['model']='different-model';put(Path(plan['config']),runtime)
    with pytest.raises(ValueError,match='runtime identity'):m.authorize(plan)
    runtime['model']='authored-model';runtime['numerical_dtype']='bfloat16';put(Path(plan['config']),runtime)
    with pytest.raises(ValueError,match='contract differs'):m.authorize(plan)


def test_real_child_failure_cleans_under_exclusive_evaluation_fence(tmp_path,monkeypatch):
    plan,runtime,lease,root=fixture(tmp_path,monkeypatch)
    dummy=tmp_path/'runtime';dummy.mkdir();(dummy/'evaluation_runtime.py').write_text('raise SystemExit(7)\n')
    monkeypatch.setattr(m,'HERE',dummy);monkeypatch.setattr(m,'launch_environment',lambda *_:{'CUDA_VISIBLE_DEVICES':'2'})
    calls=[]
    def cleanup(marker):
        with (root/'device_controller.lock').open('a') as f:
            with pytest.raises(BlockingIOError):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        calls.append(('cleanup',marker));return {'verified':True,'signals':[]}
    monkeypatch.setattr(m,'cleanup',cleanup)
    monkeypatch.setattr(m,'release',lambda _,marker,**kw:calls.append(('release',marker,kw['cleanup_verified'])) or True)
    result=m.launch(plan)
    assert result['status']=='INCOMPLETE_INFRA' and result['worker_exit_code']==7 and result['cleanup_verified']
    assert calls==[('cleanup','owned'),('release','owned',True)]
    assert json.loads((Path(plan['dispatch_root'])/'launch.json').read_text())['visible_index']=='2'
    with pytest.raises(FileExistsError):m.launch(plan)


def test_competing_evaluation_controller_cannot_launch_a_second_segment(tmp_path,monkeypatch):
    plan,runtime,lease,root=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'launch_reserved',lambda _:pytest.fail('duplicate segment launched'))
    with (root/'device_controller.lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):m.launch(plan)
    assert not Path(plan['dispatch_root']).exists()
