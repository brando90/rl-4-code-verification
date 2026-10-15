"""Recover device monitor progress without replay and release unused claims on preparation errors."""
from pathlib import Path
import importlib.util,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_monitor_driver',PHASE/'monitor_driver.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'snapshot';root.mkdir();leases=tmp_path/'leases';leases.mkdir()
    snapshot={'configuration':{'root':str(root)},'update':0,'model_binding_sha256':'model'}
    execution={'bindings':[{'path':str(Path(m.__file__).resolve()),'sha256':m.digest(m.__file__)}]}
    config={'monitor':{'stage_seconds':{'monitor_preflight':600,'monitor_generate':1800}},'environment':{}}
    plan={'snapshot_lock':{'sha256':'snapshot'},'learning':{'run':{'arm':'B','run_seed':1301},'resources':{'lease_root':str(leases)}}}
    monkeypatch.setattr(m,'authority',lambda _: (snapshot,{},execution,config))
    calls=[]
    def reserve(plan,update,stage_key,seconds):
        calls.append(('reserve',stage_key));lease={'id':stage_key,'status':'ACTIVE'};put(leases/(stage_key+'.json'),lease)
        return {'status':'RESERVED','lease':lease}
    def materialize(snapshot,config,stage,lease,sha):
        path=root/stage;path.mkdir();return {'runtime':str(path/'runtime.json'),'reservation':str(root/(stage+'.json')),
            'dispatch_root':str(path/'dispatch'),'maximum_seconds':config['monitor']['stage_seconds'][stage]}
    def release(root,identifier,cleanup_verified):
        calls.append(('release',identifier));value={'id':identifier,'status':'RELEASED'};put(Path(root)/(identifier+'.json'),value);return value
    def launch(plan):
        calls.append(('launch',plan['stage']));result={'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True,
            'snapshot_sha256':'snapshot','model_binding_sha256':'model'}
        put(Path(plan['dispatch_root'])/'result.json',result)
        if plan['stage']=='monitor_preflight':put(root/'monitor_preflight/health/preflight.json',{'status':'PASS'})
        release(leases,plan['stage'],True);return result
    monkeypatch.setattr(m,'reserve',reserve);monkeypatch.setattr(m,'materialize',materialize)
    monkeypatch.setattr(m,'launch',launch);monkeypatch.setattr(m,'release',release)
    monkeypatch.setattr(m,'cleanup',lambda _: {'verified':True})
    monkeypatch.setattr(m,'check_preflight',lambda _:None)
    return plan,root,calls


def test_clean_completed_device_stages_are_never_relaunched(tmp_path,monkeypatch):
    plan,root,calls=fixture(tmp_path,monkeypatch)
    assert m.run(plan)['status']=='WAIT_FOR_PROCESSOR'
    assert [v for k,v in calls if k=='launch']==['monitor_preflight','monitor_generate']
    before=list(calls);assert m.run(plan)['status']=='WAIT_FOR_PROCESSOR';assert calls==before


def test_idle_wait_does_not_materialize_or_attempt_generation(tmp_path,monkeypatch):
    plan,root,calls=fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(m,'reserve',lambda *a,**kw:{'status':'WAIT_FOR_IDLE_DEVICE','device_claims':0})
    assert m.run(plan)['status']=='WAIT_FOR_IDLE_DEVICE'
    assert not (root/'monitor_preflight').exists() and not calls


def test_preparation_failure_releases_unused_claim_and_is_not_replayed(tmp_path,monkeypatch):
    plan,root,calls=fixture(tmp_path,monkeypatch)
    def broken(*a):
        (root/'monitor_preflight').mkdir();raise ValueError('authored bad runtime')
    monkeypatch.setattr(m,'materialize',broken)
    with pytest.raises(ValueError,match='bad runtime'):m.run(plan)
    assert ('release','monitor_preflight') in calls
    assert json.loads((root/'monitor_preflight_parent_cleanup.json').read_text())['cleanup']['verified']
    before=list(calls);assert m.run(plan)['status']=='RECOVERY_REQUIRED';assert calls==before


def test_failed_closed_stage_remains_final(tmp_path,monkeypatch):
    plan,root,calls=fixture(tmp_path,monkeypatch)
    put(root/'monitor_preflight/dispatch/result.json',{'status':'INCOMPLETE_INFRA','cleanup_verified':True,
        'snapshot_sha256':'snapshot','model_binding_sha256':'model'})
    assert m.run(plan)['status']=='HALTED' and not calls
