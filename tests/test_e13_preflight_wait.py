"""Reproduce the late device collision and keep pre-admission waits outside scientific attempts."""
from pathlib import Path
import json,sys,traceback
from types import SimpleNamespace
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import preflight_wait as m
import runtime


def collision_fixture(root):
    root.mkdir(parents=True)
    values={'dispatch_result.json':{'exit_code':1,'supervisor_receipt':None,'cleanup_verified':True,'released':{'status':'RELEASED'}},
        'dispatch_cleanup.json':{'verified':True},'execution.json':{'status':'PREFLIGHT_RESERVED','attempt':0,'admission_statistics_computed':False}}
    for name,value in values.items():(root/name).write_text(json.dumps(value))
    (root/'dispatch.log').write_text('check_lease(config)\nRuntimeError: another execution now occupies the leased device\n')
    return root


def test_reproduces_actual_runtime_guard_and_classifies_no_runtime(tmp_path,monkeypatch):
    lease=tmp_path/'lease.json';lease.write_text(json.dumps({'id':'ours','uuid':'GPU-authored'}));config={'lease_path':str(lease)}
    monkeypatch.setattr(runtime,'check_visible_device',lambda _:None)
    monkeypatch.setattr(runtime.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='GPU-authored, 99999999\n'))
    original=Path.read_bytes
    monkeypatch.setattr(Path,'read_bytes',lambda self: b'E13_EXECUTION_ID=another-owner\0'if str(self)=='/proc/99999999/environ'else original(self))
    try:
        runtime.check_lease(config)
        pytest.fail('foreign compute process was accepted')
    except RuntimeError:
        error=traceback.format_exc()
    root=collision_fixture(tmp_path/'dispatch');(root/'dispatch.log').write_text(error)
    assert m.collision(root)['cleanup_verified'] is True
    assert not (root/'supervisor').exists()


@pytest.mark.parametrize('defect',['runtime_started','wrong_error','admitted','cleanup_unknown','active_lease'])
def test_other_failures_never_admit_wait_recovery(tmp_path,defect):
    root=collision_fixture(tmp_path/'dispatch')
    if defect=='runtime_started':(root/'supervisor').mkdir()
    elif defect=='wrong_error':(root/'dispatch.log').write_text('check_lease(config)\nRuntimeError: model failed\n')
    else:
        p=root/('execution.json'if defect=='admitted'else'dispatch_result.json');v=json.loads(p.read_text())
        if defect=='admitted':v['attempt']=1
        elif defect=='cleanup_unknown':v['cleanup_verified']=False
        else:v['released']['status']='ACTIVE'
        p.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='pre-runtime'):m.collision(root)


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'technical/T2/attempt_1';collision_fixture(root/'preflight/dispatch')
    cp=tmp_path/'config.json';cp.write_text('{}')
    plan={'gate':'T2','attempt':1,'LP':{'sha256':'lp'},'repository':'repo','configuration':str(cp),'resource_plan':{'lease_root':str(tmp_path/'leases')}}
    state={'status':'HALTED','next_stage':'preflight','LP_sha256':'lp','configuration_sha256':m.digest(cp)}
    (root/'state.json').write_text(json.dumps(state))
    config={'work_root':str(tmp_path/'technical'),'stage_seconds':{'T2':{'preflight':900}},'environment':{}}
    lock={'configuration':{'technical_ledger':str(tmp_path/'ledger')}}
    fix={'gate':'PREFLIGHT_DEVICE_WAIT','status':'FROZEN','LP':plan['LP'],'science_sha256':'science','technical_gate':'T2','prospective_attempt':1,
        'bindings':[{'path':str(P/'preflight_wait.py'),'sha256':m.digest(P/'preflight_wait.py')}]}
    monkeypatch.setattr(m,'authorize',lambda _: (lock,config,'science'));monkeypatch.setattr(m,'published',lambda *a:fix)
    return root,plan,state


def test_repeated_busy_polls_preserve_original_failure_and_no_admission(tmp_path,monkeypatch):
    root,plan,state=fixture(tmp_path,monkeypatch);calls=[]
    monkeypatch.setattr(m,'reserve',lambda *a,**k:calls.append(k)or{'status':'WAIT_FOR_IDLE_DEVICE'})
    monkeypatch.setattr(m,'admit',lambda *a,**k:pytest.fail('busy preflight admitted a gate'))
    for _ in range(2):assert m.tick(plan,{})['status']=='WAIT_FOR_IDLE_DEVICE'
    assert json.loads((root/'state.json').read_text())==state
    assert [c['stage_key']for c in calls]==['preflight_wait_0000','preflight_wait_0001']
    assert all(c['attempt']==1 and c['seconds']==900 for c in calls)
    assert len(list((root/'preflight_wait').glob('*/terminal.json')))==2
    assert not (tmp_path/'ledger').exists()


def test_partial_recovery_cannot_replay_and_admitted_gate_is_rejected(tmp_path,monkeypatch):
    root,plan,state=fixture(tmp_path,monkeypatch)
    (root/'preflight_wait/poll_0000').mkdir(parents=True)
    monkeypatch.setattr(m,'reserve',lambda *a,**k:pytest.fail('unreconciled attempt claimed a device'))
    with pytest.raises(RuntimeError,match='never replay'):m.tick(plan,{})
    state['admission']='already-admitted';(root/'state.json').write_text(json.dumps(state))
    with pytest.raises(ValueError,match='unadmitted'):m.tick(plan,{})


def test_successful_new_preflight_admits_once_and_preserves_failed_cost(tmp_path,monkeypatch):
    root,plan,state=fixture(tmp_path,monkeypatch);(root/'costs').mkdir()
    old_cost=root/'costs/preflight.json';old_cost.write_text('{"device_hours":0.015}')
    plan['prerequisites']={'T1':{'status':'PASS'}}
    leases=tmp_path/'leases';leases.mkdir();canonical=leases/'new.json'
    canonical.write_text(json.dumps({'id':'new','status':'ACTIVE'}))
    monkeypatch.setattr(m,'reserve',lambda *a,**k:{'status':'RESERVED','lease':{'id':'new'}})
    def dynamic(config,gate,key,folder,lease):
        health=folder/'preflight/health';health.mkdir(parents=True)
        (health/'preflight.json').write_text(json.dumps({'status':'PASS','scope':'non-probe infrastructure only',
            'admission_statistics_computed':False,'generated_tokens':1,'visible_index':'2'}))
        p=folder/'preflight/runtime.json';p.write_text('{}');return p
    monkeypatch.setattr(m,'dynamic_config',dynamic)
    def prepare(**kwargs):
        p=kwargs['preparation_root'];p.mkdir();q=p/'plan.json';q.write_text('{}');return q
    monkeypatch.setattr(m,'prepare',prepare)
    def launch(path,**kwargs):
        canonical.write_text(json.dumps({'id':'new','status':'RELEASED','device_hours':.05}))
        (path.parent/'dispatch_cleanup.json').write_text('{"verified":true}')
        return {'status':'RUNTIME_FINISHED'}
    monkeypatch.setattr(m,'launch_local',launch)
    monkeypatch.setattr(m,'snapshot',lambda _: {})
    monkeypatch.setattr(m,'stage_cost',lambda *a,**k:{'device_hours':k['lease']['device_hours'],'cleanup_verified':k['cleanup']['verified']})
    admissions=[]
    def admit(*args,**kwargs):
        admissions.append(kwargs);return tmp_path/'ledger/T2/attempt_1',{'attempt':1}
    monkeypatch.setattr(m,'admit',admit)
    assert m.tick(plan,{})=={'status':'PREFLIGHT_RECOVERED','numbered_attempt_admitted':True}
    final=json.loads((root/'state.json').read_text());assert final['status']=='READY' and final['next_stage']=='generate_update'
    assert len(admissions)==1 and admissions[0]['prerequisites']==plan['prerequisites']
    assert json.loads(old_cost.read_text())=={'device_hours':.015}
    assert json.loads((root/'costs/preflight_wait_0000.json').read_text())=={'device_hours':.05,'cleanup_verified':True}
    assert (root/'preflight/dispatch/dispatch.log').exists()
    with pytest.raises(ValueError,match='unadmitted'):m.tick(plan,{})
