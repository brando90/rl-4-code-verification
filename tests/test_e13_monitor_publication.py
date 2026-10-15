"""Keep monitor publication preparation separate from actual statistical decisions."""
from pathlib import Path
import importlib.util,json,sys
import pytest
REPO=Path(__file__).resolve().parents[1]
PHASE=REPO/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('authored_monitor_publication',PHASE/'monitor_publication.py')
f=load('authored_monitor_decision_fixture',REPO/'tests/test_e13_monitor_decision.py')
import monitor_decision


def fixture(tmp_path,monkeypatch):
    snapshot,current=f.fixture(tmp_path/'measurements')
    here=tmp_path/'phase2';here.mkdir();(tmp_path/'locks').mkdir();monkeypatch.setattr(m,'HERE',here)
    lock_path=tmp_path/'snapshot.json';lock_path.write_text('{}')
    snapshot_ref={'name':'snapshot','path':str(lock_path),'sha256':m.digest(lock_path)}
    current['snapshot_lock']=snapshot_ref
    current_ref=f.put(tmp_path/'current.json',current);current_ref['name']='current'
    cohort=f.put(tmp_path/'cohort.json',{'cells':snapshot['cells']})
    controls=f.put(tmp_path/'controls.json',{'condition':'v2-S2','status':'PASS'});controls['name']='controls'
    pilot={'bindings':[cohort]};config={'monitor':{'cohort':cohort}}
    frozen={'bindings':[],'arm':'B','run_seed':1301,'update':0,'execution_sha256':'execution','model_binding_sha256':'model'}
    root=tmp_path/'root';root.mkdir()
    monkeypatch.setattr(m,'context',lambda _: (frozen,snapshot,pilot,config,{'bindings':[]}, {},root,'authored'))
    values={'current':current,'controls':{'condition':'v2-S2','status':'PASS'}}
    monkeypatch.setattr(m,'published',lambda ref,_:values[ref['name']])
    monkeypatch.setattr(monitor_decision,'published',lambda ref,_:values[ref['name']])
    plan={'current':current_ref,'snapshot_lock':snapshot_ref,'coverage_controls_result':controls,
          'hidden_controls_result':controls,'learning':{'run':{'execution_lock':{'sha256':'execution'}}}}
    return plan,values,frozen,root


def test_publish_decision_inputs_keeps_statistics_uncomputed(tmp_path,monkeypatch):
    plan,values,snapshot,root=fixture(tmp_path,monkeypatch)
    result=m.freeze_decision(plan)
    lock=json.loads(Path(result['path']).read_text())
    assert result['status']=='PREPARED_FOR_PUBLICATION' and not result['admission_statistics_computed']
    assert lock['gate']=='PILOT_MONITOR_DECISION_INPUTS' and lock['configuration']['root']==str(root/'decision')
    assert not (root/'decision/evaluation_attempt.json').exists()
    sources={b['path'] for b in lock['bindings']}
    assert values['current']['rows']['path'] in sources
    assert all(ref['path'] in sources for ref in values['current']['cell_receipts'].values())


def test_wrong_snapshot_refuses_decision_input_freeze(tmp_path,monkeypatch):
    plan,values,snapshot,root=fixture(tmp_path,monkeypatch)
    values['current']['model_binding_sha256']='another-model'
    with pytest.raises(ValueError,match='another checkpoint'):m.freeze_decision(plan)
    assert not list((tmp_path/'locks').iterdir())


def test_initial_monitor_cannot_import_another_baseline(tmp_path,monkeypatch):
    plan,values,snapshot,root=fixture(tmp_path,monkeypatch);plan['baseline']={'name':'another'}
    with pytest.raises(ValueError,match='initial monitor'):m.freeze_decision(plan)
    assert not list((tmp_path/'locks').iterdir())


def test_hosted_preparation_binds_exact_snapshot_and_validated_recipe_without_calls(tmp_path,monkeypatch):
    from types import SimpleNamespace
    plan,values,snapshot,root=fixture(tmp_path,monkeypatch)
    bundle=tmp_path/'bundle';bundle.mkdir()
    for name in ('judge_call.py','setup.sh','contract.yaml'):(bundle/name).write_text('authored fixture')
    original={'bundle':str(bundle),'benchmark_prefix':'veribench-rl4cv-e13v2-s2'}
    for key in ('train_ids','route_identity','registry_catalog','migration_provenance'):
        path=tmp_path/(key+'.json');path.write_text(json.dumps({'models':{'model':{'provider_properties':{}}}}) if key=='registry_catalog' else '{}')
        original[key]=str(path)
    validated=f.put(tmp_path/'validated.json',original);plan['validated_configuration']=validated
    controls_lock=f.put(tmp_path/'controls_lock.json',{'configuration':original,'bindings':[]});controls_lock['name']='controls_lock'
    plan['coverage_controls_lock']=controls_lock
    values['controls_lock']={'configuration':original,'bindings':[]};values['controls']['actual_bundle_verified']=True
    for key in ('cpu_lock','cpu_result'):
        plan[key]=f.put(tmp_path/(key+'.json'),{})
    f.put(root/'hidden_inputs/inputs.json',{'cells':[]});f.put(root/'hidden/rows.json',[])
    def helper(config):
        work=Path(config['work']);private=work/'private';results=work/'results'
        private.mkdir(exist_ok=True);results.mkdir(exist_ok=True)
        return SimpleNamespace(PRIVATE=private,RESULTS=results,
            suite_spec=lambda _:{'pack_receipt':results/'pack.json'},
            judge_config=lambda _: {'selector':'model','max_tokens':100},
            judge_run=SimpleNamespace(worst_cost=lambda *a:.25))
    def build(config,inputs,rows):
        pack={'source_bindings':[],'n_declared_ratings':6,'compiled_files':1,
              'cells':[{'instruction_bytes':10} for _ in range(3)]}
        f.put(helper(config).RESULTS/'pack.json',pack);return pack
    monkeypatch.setattr(m,'helper',helper);monkeypatch.setattr(m,'build',build)
    result=m.prepare_hosted(plan);lock=json.loads(Path(result['lock']).read_text())
    assert lock['snapshot_lock']==plan['snapshot_lock'] and lock['declared_ratings']==6
    assert lock['configuration']['snapshot_name']=='b-1301-u0'
    assert lock['configuration']['bundle']==str(bundle) and lock['request_attempts_per_rating']==2
    assert result['model_calls']==0 and result['estimated_maximum_two_attempt_usd']==3.
    assert all(m.digest(b['path'])==b['sha256'] for b in lock['bindings'])


def test_prepared_measurement_retains_all_physical_sources_without_deciding(tmp_path,monkeypatch):
    plan,values,snapshot,root=fixture(tmp_path,monkeypatch)
    previous=m.context(plan);manifest=previous[1];source_root=tmp_path/'measurements'
    source=source_root/'source.lean';source_ref={'path':str(source),'sha256':m.digest(source)}
    normalized=[]
    for i,cell in enumerate(manifest['cells']):
        strict=source_root/f'{i}.normalized.json'
        normalized.append({**cell,'source':source_ref,'strict':{'path':str(strict),'sha256':m.digest(strict)}})
    inputs=f.put(root/'hidden_inputs/inputs.json',{**manifest,'cells':normalized})
    hidden=json.loads((source_root/'hidden.json').read_text());cpu={k:v for k,v in hidden.items() if k!='rows'}
    f.put(root/'hidden/rows.json',hidden['rows'])
    f.put(root/'strict/terminal.json',{'snapshot_sha256':plan['snapshot_lock']['sha256'],'cleanup_unresolved':0,
        'scoring':{'path':str(source_root/'scoring.json'),'sha256':m.digest(source_root/'scoring.json')}})
    modified=list(previous);modified[4]={'configuration':{'inputs':inputs['path']}};modified[5]=cpu
    monkeypatch.setattr(m,'context',lambda _:tuple(modified))
    hosted=json.loads((source_root/'hosted.json').read_text());hosted['lock_sha256']='hosted-lock'
    raw=f.put(root/'hosted/result.json',hosted)
    values['hosted_result']={k:v for k,v in hosted.items() if k!='rows'};values['hosted_result']['private_result']=raw
    values['hosted_lock']={'gate':'PILOT_MONITOR_HOSTED','snapshot_lock':plan['snapshot_lock']}
    cleanup=json.loads((source_root/'cleanup.json').read_text());values['cleanup']=cleanup
    plan['hosted_cleanup']=f.put(root/'cleanup.json',cleanup);plan['hosted_cleanup']['name']='cleanup'
    plan['hosted_lock']={'name':'hosted_lock','sha256':'hosted-lock'};plan['hosted_result']={'name':'hosted_result'}
    result=m.prepare_decision(plan);header=json.loads(Path(result['path']).read_text())
    assert result['status']=='MEASUREMENTS_PREPARED_FOR_PUBLICATION' and not result['admission_statistics_computed']
    assert len(header['cell_receipts'])==32 and header['execution_sha256']=='execution'
    values['assembled']=header
    assert len(monitor_decision.measurement({'name':'assembled'},'authored',execution_sha='execution',arm='B',run_seed=1301,update=0)[1])==32
    assert not (root/'decision/evaluation_attempt.json').exists()
