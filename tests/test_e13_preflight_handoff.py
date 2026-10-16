"""Fence pre-admission handoff reconciliation to the exact retained two-failure history and one new health launch."""
from pathlib import Path
import copy,json,sys
import pytest
P=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(P))
import preflight_handoff as m


def fixture(tmp_path,monkeypatch):
    root=tmp_path/'technical/T2/attempt_3';root.mkdir(parents=True);(root/'costs').mkdir()
    (root/'costs/preflight.json').write_text('{"device_hours":0.05259}')
    ledger=tmp_path/'ledger/T2'
    for number in [1,2]:
        d=ledger/f'attempt_{number}';d.mkdir(parents=True)
        (d/'attempt.json').write_text(json.dumps({'attempt':number}))
        (d/'result.json').write_text(json.dumps({'status':'INCOMPLETE_INFRA','admission_statistics_computed':False}))
    state={'status':'HALTED','next_stage':'preflight','LP_sha256':'old','configuration_sha256':'old_config'}
    (root/'state.json').write_text(json.dumps(state));snapshot=tmp_path/'failed_state.json';snapshot.write_text(json.dumps(state))
    failed={'status':'INCOMPLETE_INFRA_PRE_ADMISSION','numbered_attempt_3_admitted':False,
        'admission_statistics_computed':False,'generated_experiment_responses':0,'optimizer_updates':0,
        'cleanup_verified':True,'error_type':'PermissionError','offloaded_state_preflight':{'status':'PASS'},
        'evidence':[{'path':str(snapshot),'sha256':m.digest(snapshot)}]}
    cp=tmp_path/'config.json';cp.write_text('{}')
    plan={'gate':'T2','attempt':3,'LP':{'sha256':'new'},'successor':{'path':'fix'},'repository':'repo',
          'configuration':str(cp),'resource_plan':{'lease_root':str(tmp_path/'leases')},'prerequisites':{'T1':'pass'}}
    recovery={'previous_preflight_LP':{'sha256':'old'},'previous_configuration_sha256':'old_config','failed_preflight':{'path':'failure'}}
    fix={'gate':'A4_TECHNICAL_FIX','status':'FROZEN','science_sha256':'science','successor_LP':plan['LP'],'preflight_recovery':recovery}
    lock={'configuration':{'technical_ledger':str(tmp_path/'ledger')},'bindings':[{'path':str(P/'preflight_handoff.py'),'sha256':m.digest(P/'preflight_handoff.py')}]}
    config={'work_root':str(tmp_path/'technical'),'stage_seconds':{'T2':{'preflight':900}},'environment':{}}
    monkeypatch.setattr(m,'authorize',lambda _:(lock,config,'science'))
    monkeypatch.setattr(m,'published',lambda ref,*args:fix if ref['path']=='fix'else failed)
    return root,ledger,plan,state,recovery,failed


@pytest.mark.parametrize('change',['admission','third_ledger','evaluated','prior_pass','wrong_lp','wrong_config','generated'])
def test_no_admitted_or_measured_work_can_be_reconciled(tmp_path,monkeypatch,change):
    root,ledger,plan,state,recovery,failed=fixture(tmp_path,monkeypatch)
    if change=='admission':state['admission']='already'
    elif change=='third_ledger':(ledger/'attempt_3').mkdir()
    elif change=='evaluated':(ledger/'attempt_2/evaluation_attempt.json').write_text('{}')
    elif change=='prior_pass':(ledger/'attempt_2/result.json').write_text('{"status":"PASS"}')
    elif change=='wrong_lp':state['LP_sha256']='different'
    elif change=='wrong_config':state['configuration_sha256']='different'
    else:(root/'generate_update').mkdir()
    (root/'state.json').write_text(json.dumps(state))
    monkeypatch.setattr(m,'reserve',lambda *a,**k:pytest.fail('invalid reconciliation claimed a device'))
    with pytest.raises(ValueError):m.tick(plan)


def test_busy_polls_preserve_state_cost_and_numbered_attempts(tmp_path,monkeypatch):
    root,ledger,plan,state,recovery,failed=fixture(tmp_path,monkeypatch);calls=[]
    monkeypatch.setattr(m,'reserve',lambda *a,**k:calls.append(k)or {'status':'WAIT_FOR_IDLE_DEVICE'})
    for _ in range(2):assert m.tick(plan)['status']=='WAIT_FOR_IDLE_DEVICE'
    assert json.loads((root/'state.json').read_text())==state
    assert len(list(ledger.glob('attempt_*/attempt.json')))==2
    assert [x['stage_key']for x in calls]==['preflight_handoff_0000','preflight_handoff_0001']
    assert all(x['attempt']==3 and x['seconds']==900 for x in calls)
    assert (root/'costs/preflight.json').read_text()=='{"device_hours":0.05259}'


@pytest.mark.parametrize('succeeds',[True,False])
def test_one_actual_health_launch_preserves_history_and_cannot_replay(tmp_path,monkeypatch,succeeds):
    root,ledger,plan,state,recovery,failed=fixture(tmp_path,monkeypatch)
    leases=Path(plan['resource_plan']['lease_root']);leases.mkdir();canonical=leases/'fresh.json';canonical.write_text('{"id":"fresh","status":"ACTIVE"}')
    monkeypatch.setattr(m,'reserve',lambda *a,**k:{'status':'RESERVED','lease':{'id':'fresh'}})
    def dynamic(config,gate,key,folder,lease):
        health=folder/'preflight/health';health.mkdir(parents=True)
        (health/'preflight.json').write_text(json.dumps({'status':'PASS','scope':'non-probe infrastructure only','admission_statistics_computed':False,'generated_tokens':1,'visible_index':'0'}))
        (health/'dtensor_state_preflight.json').write_text('{"status":"PASS","shutdown":{"status":"PASS"}}')
        p=folder/'preflight/runtime.json';p.write_text('{}');return p
    monkeypatch.setattr(m,'dynamic_config',dynamic)
    def prepare(**kwargs):
        p=kwargs['preparation_root'];p.mkdir();q=p/'plan.json';q.write_text('{}');return q
    monkeypatch.setattr(m,'prepare',prepare)
    def launch(path,**kwargs):
        canonical.write_text('{"id":"fresh","status":"RELEASED","device_hours":0.1}')
        (path.parent/'dispatch_cleanup.json').write_text('{"verified":true}')
        return {'status':'RUNTIME_FINISHED' if succeeds else 'INCOMPLETE_INFRA'}
    monkeypatch.setattr(m,'launch_local',launch);monkeypatch.setattr(m,'snapshot',lambda _: {})
    monkeypatch.setattr(m,'stage_cost',lambda *a,**k:{'device_hours':k['lease']['device_hours'],'cleanup_verified':k['cleanup']['verified']})
    admissions=[]
    def admit(*args,**kwargs):
        admissions.append(kwargs);d=ledger/'attempt_3';d.mkdir();return d,{'attempt':3}
    monkeypatch.setattr(m,'admit',admit)
    result=m.tick(plan)
    if succeeds:
        assert result['status']=='PREFLIGHT_RECOVERED' and len(admissions)==1
        final=json.loads((root/'state.json').read_text());assert final['LP_sha256']=='new' and final['next_stage']=='generate_update'
        assert final['configuration_sha256']==m.digest(plan['configuration'])
    else:
        assert result['status']=='INCOMPLETE_INFRA' and admissions==[]
        assert json.loads((root/'state.json').read_text())==state
    with pytest.raises((ValueError,RuntimeError)):m.tick(plan)
    assert (root/'costs/preflight.json').read_text()=='{"device_hours":0.05259}'
    assert json.loads((root/'costs/preflight_handoff_0000.json').read_text())['device_hours']==.1
    assert m.verify_failure(root,failed)
