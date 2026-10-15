"""Keep evaluation waits unattempted and retain cleanup and costs when stage preparation fails."""
from pathlib import Path
import importlib.util,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));sys.path.insert(0,str(Path(__file__).parent))
import evaluation_driver as m


def fixture(tmp_path):
    root=tmp_path/'evaluation';root.mkdir();leases=tmp_path/'leases';leases.mkdir()
    learning={'run':{'phase':'main','arm':'A','run_seed':13011},'resources':{'lease_root':str(leases)}}
    plan={'learning':learning,'snapshot_lock':{'sha256':'snapshot'}}
    snapshot={'configuration':{'root':str(root)},'boundary':1}
    config={'evaluation':{'stage_seconds':{'evaluation_generate':300}},'environment':{}}
    return plan,{'configuration':{'evaluation_runtime_contract':{}}},config,snapshot,root,leases


def test_busy_device_wait_leaves_no_evaluation_attempt(tmp_path,monkeypatch):
    plan,lp,config,snapshot,root,leases=fixture(tmp_path)
    monkeypatch.setattr(m,'reserve',lambda *a,**kw:{'status':'WAIT_FOR_IDLE_DEVICE'})
    monkeypatch.setattr(m,'materialize',lambda *a:pytest.fail('wait materialized an attempt'))
    result=m.execute(plan,lp,config,snapshot,'evaluation_generate','validation_b1_s000',[0])
    assert result['status']=='WAIT_FOR_IDLE_DEVICE' and not list(root.iterdir())


def test_preparation_failure_releases_owned_claim_and_keeps_cost(tmp_path,monkeypatch):
    plan,lp,config,snapshot,root,leases=fixture(tmp_path);lease={'id':'owned','status':'ACTIVE'}
    (leases/'owned.json').write_text(json.dumps(lease))
    monkeypatch.setattr(m,'reserve',lambda *a,**kw:{'status':'RESERVED','lease':lease})
    def fail(*a):raise ValueError('authored preparation failure')
    monkeypatch.setattr(m,'materialize',fail);calls=[]
    monkeypatch.setattr(m,'cleanup',lambda marker:calls.append(marker) or {'verified':True})
    def release(*a,**kw):
        (leases/'owned.json').write_text(json.dumps({**lease,'status':'RELEASED'}));return True
    monkeypatch.setattr(m,'release',release)
    monkeypatch.setattr(m,'stage_cost',lambda *a,**kw:{'status':'RECORDED','device_hours':.01,'cleanup':kw['cleanup']})
    with pytest.raises(ValueError,match='authored preparation'):m.execute(plan,lp,config,snapshot,'evaluation_generate','validation_b1_s000',[0])
    assert calls==['owned'] and json.loads((root/'validation_b1_s000_cost.json').read_text())['device_hours']==.01
    assert json.loads((root/'validation_b1_s000_parent_cleanup.json').read_text())['cleanup']['verified']


def test_existing_stage_cannot_claim_another_device(tmp_path,monkeypatch):
    plan,lp,config,snapshot,root,leases=fixture(tmp_path);(root/'validation_b1_s000').mkdir()
    monkeypatch.setattr(m,'reserve',lambda *a,**kw:pytest.fail('duplicate stage claimed a device'))
    assert m.execute(plan,lp,config,snapshot,'evaluation_generate','validation_b1_s000',[0])['status']=='RECOVERY_REQUIRED'


def test_complete_authored_evaluation_recovers_only_missing_neighbors_and_then_stays_closed(tmp_path,monkeypatch):
    import hashlib,time
    from evaluation_contract import identities
    plan,lp,config,snapshot,root,leases=fixture(tmp_path)
    ids=[f'authored_{i:03d}' for i in range(135)];allow=root/'allowlist';allow.write_text('\n'.join(ids))
    cells=identities(ids,'validation',arm='A',run_seed=13011,boundary=1)
    for cell in cells:cell.update(prompt_text='authored',chat_text_sha256=hashlib.sha256(b'authored').hexdigest(),prompt_token_ids=[1,2],required_paths=['solution.lean'])
    mp=root/'manifest.json';mp.write_text(json.dumps({'condition':'v2-S2','purpose':'validation','arm':'A','run_seed':13011,'boundary':1,'cells':cells}))
    snapshot.update(condition='v2-S2',status='FROZEN',purpose='validation',arm='A',run_seed=13011,L2_sha256='L2',model='authored-model',model_binding_sha256='model')
    snapshot['configuration'].update(manifest=str(mp),allowlist=str(allow))
    snapshot['bindings']=[{'path':str(p),'sha256':m.digest(p)} for p in (mp,allow)]
    config.update(runtime={},evaluation={'stage_seconds':{'evaluation_preflight':300,'evaluation_generate':300}})
    execution={'bindings':[{'path':str(Path(m.__file__).parent/name),'sha256':m.digest(Path(m.__file__).parent/name)}
        for name in ('evaluation_driver.py','evaluation_ledger.py','evaluation_stage.py')]}
    # costs.py is an unchanged shared source; supply its source identity to this
    # authored driver test without copying or modifying the real implementation.
    real_digest=m.digest
    cost_path=Path(m.__file__).parent/'costs.py'
    execution['bindings'].append({'path':str(cost_path),'sha256':real_digest(PHASE/'costs.py')})
    monkeypatch.setattr(m,'digest',lambda p:real_digest(PHASE/'costs.py') if Path(p)==cost_path else real_digest(p))
    monkeypatch.setattr(m,'authorize',lambda _:(lp,execution,config,snapshot))
    calls=[]
    def reserve(resources,*,update,stage_key,seconds):
        lease={'id':stage_key,'status':'ACTIVE','owner':'e13v2','started_unix':time.time()-36}
        (leases/(stage_key+'.json')).write_text(json.dumps(lease));return {'status':'RESERVED','lease':lease}
    monkeypatch.setattr(m,'reserve',reserve)
    def launch(dispatch):
        runtime=json.loads(Path(dispatch['config']).read_text());folder=Path(dispatch['dispatch_root']);folder.mkdir()
        key=dispatch['stage_key'];calls.append(key)
        status='RUNTIME_EXITED_ZERO';error=None
        if dispatch['stage']=='evaluation_preflight':
            m.write_new(Path(runtime['attempt_root'])/'preflight.json',{'status':'PASS','scope':'non-probe infrastructure only',
                'admission_statistics_computed':False,'generated_tokens':1,'visible_index':'2'})
        else:
            out=Path(runtime['stage_root']);out.mkdir();indexes=runtime['indexes']
            if key.endswith('s000'):indexes=indexes[:128];status='INCOMPLETE_INFRA';error='BrokenPipeError'
            for index in indexes:m.write_new(out/f'{index:05d}.generation.json',{**cells[index],'condition':'v2-S2',
                'output_token_ids':[3,4],'completion':'authored','finish_reason':'stop','at_token_cap':False,'generated_tokens':2,'prompt_tokens':2})
        result={'status':status,'snapshot_sha256':'snapshot','stage_key':key,'lease_id':key,'cleanup_verified':True,
                'model_binding_sha256':'model','error_type':error}
        m.write_new(folder/'result.json',result);m.write_new(folder/'cleanup.json',{'verified':True})
        p=leases/(key+'.json');lease=json.loads(p.read_text());ended=time.time()
        lease.update(status='RELEASED',released_unix=ended,device_hours=(ended-lease['started_unix'])/3600);p.write_text(json.dumps(lease))
        return result
    monkeypatch.setattr(m,'launch',launch)
    result=m.run(plan)
    assert result['status']=='COMPLETE' and result['declared']==1080 and result['completed']==1080
    assert result['identical_retries']==128 and result['known_generated_tokens']==2160
    assert result['missing_cost_receipts']==[] and len(result['costs'])==6
    previous=list(calls);assert m.run(plan)==result and calls==previous
