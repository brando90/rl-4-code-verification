"""Exercise one-shot pilot-monitor admissions, immutable inputs and terminal collection without model calls."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import sys
import zipfile

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_monitor_hosted',PHASE/'monitor_hosted.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def fixture(tmp_path,monkeypatch, failure=False):
    state=tmp_path/'state.json';state.write_text('{"runs":{}}');calls=[]
    manifest={'cells':[{'task_id':f'authored_{i}'} for i in range(3)],'n_declared_ratings':6}
    h=SimpleNamespace(RESULTS=tmp_path,suite_spec=lambda _: {'benchmark':'authored-benchmark'},
        load_state=lambda:json.loads(state.read_text()),save_state=lambda s:state.write_text(json.dumps(s)),
        stamp=lambda:'authored timestamp',request_benchmark=lambda *_:'authored-request',
        judge_config=lambda _: {'selector':'frozen-selector','max_tokens':16384,'reasoning_effort':'high'})
    class Transport:
        def endpoint(self,*_): pass
        def identity(self): return {'transport':'hosted','organization':'authored'}
        def run(self,args,timeout):
            assert (tmp_path/'H2_sol_high_attempt.json').exists()
            assert json.loads(state.read_text())['runs']['pilot_monitor/H2_sol_high']['phase']=='admitting'
            calls.append(args)
            if failure:raise TimeoutError('ambiguous authored admission')
            return SimpleNamespace(returncode=0,stderr='',stdout='Organization: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa\nRun ID: 11111111-2222-3333-4444-555555555555\n')
    config={'work':str(tmp_path)}
    monkeypatch.setattr(m,'authorize',lambda _: ({'concurrency':3},config,h,Transport(),manifest))
    return {'lock':{'sha256':'authored-sha'}},config,h,manifest,calls,state


def test_admission_records_before_call_and_never_resubmits_even_if_state_lost(tmp_path,monkeypatch):
    plan,_,_,_,calls,state=fixture(tmp_path,monkeypatch)
    result=m.admit(plan,'H2_sol_high')
    assert result['run_id']=='11111111-2222-3333-4444-555555555555' and result['declared_ratings']==3
    assert calls[0][-3:]==['-k','reasoning_effort','high']
    state.write_text('{"runs":{}}')
    with pytest.raises(ValueError,match='never resubmit'):m.admit(plan,'H2_sol_high')
    assert len(calls)==1


def test_ambiguous_admission_preserved_without_second_call(tmp_path,monkeypatch):
    plan,_,_,_,calls,state=fixture(tmp_path,monkeypatch,True)
    with pytest.raises(TimeoutError):m.admit(plan,'H2_sol_high')
    row=json.loads(state.read_text())['runs']['pilot_monitor/H2_sol_high']
    assert row['phase']=='admission_failed' and not row['automatic_retry']
    with pytest.raises(ValueError,match='never resubmit'):m.admit(plan,'H2_sol_high')
    assert len(calls)==1


def test_changed_binding_refused_before_transport(tmp_path,monkeypatch):
    path=tmp_path/'input';path.write_text('frozen');sha=m.digest(path);path.write_text('changed')
    lock={'gate':'PILOT_MONITOR_HOSTED','condition':'v2-S2','status':'FROZEN',
          'bindings':[{'path':str(path),'sha256':sha}]}
    monkeypatch.setattr(m,'publication',lambda *_:lock)
    monkeypatch.setattr(m,'Transport',lambda *_:pytest.fail('transport reached after changed binding'))
    with pytest.raises(ValueError,match='binding changed'):m.authorize({'lock':{},'repository':'authored'})


def collection_fixture(tmp_path,monkeypatch):
    plan,config,h,manifest,_,state=fixture(tmp_path,monkeypatch)
    for name in ('inputs','cpu_rows'):
        path=tmp_path/(name+'.json');path.write_text('{}' if name=='inputs' else '[]');config[name]=str(path)
    train=tmp_path/'train.txt';train.write_text('authored\n');config['train_ids']=str(train)
    bundle=tmp_path/'bundle';bundle.mkdir();config['bundle']=str(bundle)
    for name in ('judge_call.py','setup.sh','contract.yaml'):(bundle/name).write_text('authored '+name)
    state.write_text(json.dumps({'runs':{'pilot_monitor/'+n:{} for n in m.CONFIGS}}))
    h.poll=lambda:0;h.harvest=lambda *_:None
    directory=tmp_path/'harvests';directory.mkdir()
    for member in m.CONFIGS:
        raw=tmp_path/'judge/raw'/('pilot_monitor__'+member)/'artifacts';raw.mkdir(parents=True)
        with zipfile.ZipFile(raw/'vb103_judge.zip','w') as archive:
            for source in bundle.iterdir():archive.writestr('vb103_judge/'+source.name,source.read_bytes())
        cells=[{**c,'task_id_vb':'authored-file','sample_idx':0,'status':'measured' if i<2 else 'unmeasured_infra',
                'score_raw':i,'transport_matches':i<2,'cost_usd':.1 if i<2 else None,'requests_sent':1 if i<2 else None}
               for i,c in enumerate(manifest['cells'])]
        (directory/('cells_pilot_monitor__'+member+'.json')).write_text(json.dumps({'cells':cells,
             'receipt_inventory':{'missing':['authored_2'],'extra':[],'duplicates':[]}}))
    def aggregate(_):
        assert (tmp_path/'evaluation_attempt.json').exists()
        (tmp_path/'fsc_pilot_monitor.json').write_text('{"cells":{},"n_ratings_measured":4}')
        return 0
    h.fsc=aggregate
    monkeypatch.setattr(m,'combine',lambda *a,**kw:{'condition':'v2-S2','declared':32,'coverage_known':0,'rows':[]})
    return plan,h


def test_collection_preserves_missing_charges_repeats_and_exclusive_evaluation(tmp_path,monkeypatch):
    plan,h=collection_fixture(tmp_path,monkeypatch)
    result=m.collect(plan)
    assert result['actual_bundle_verified'] and result['declared_ratings']==6 and result['measured_ratings']==4
    assert not result['requested_identity_verified']
    cost=result['charges']['H2_sol_high']
    assert cost['known_charges']==2 and cost['model_usd'] is None and cost['request_attempts_known']==2
    variability=result['repeat_variability']['H2_sol_high']['authored-file#0']
    assert variability['measured_repeats']==2 and variability['sample_standard_deviation_0_5']==pytest.approx(2**-.5)
    h.harvest=lambda *_:pytest.fail('repeat harvest after final evaluation')
    with pytest.raises(ValueError,match='never recompute'):m.collect(plan)


def test_wrong_actual_bundle_prevents_statistics(tmp_path,monkeypatch):
    plan,h=collection_fixture(tmp_path,monkeypatch)
    (tmp_path/'bundle/setup.sh').write_text('changed executable')
    h.fsc=lambda _:pytest.fail('statistics reached with wrong executable')
    with pytest.raises(ValueError,match='differs from frozen'):m.collect(plan)
    assert not (tmp_path/'evaluation_attempt.json').exists()


def test_changed_receipt_denominator_prevents_statistics(tmp_path,monkeypatch):
    plan,h=collection_fixture(tmp_path,monkeypatch)
    path=tmp_path/'harvests/cells_pilot_monitor__H2_sol_high.json'
    value=json.loads(path.read_text());value['cells'].pop();path.write_text(json.dumps(value))
    h.fsc=lambda _:pytest.fail('statistics reached with changed denominator')
    with pytest.raises(ValueError,match='denominator changed'):m.collect(plan)
    assert not (tmp_path/'evaluation_attempt.json').exists()


def authority_fixture(tmp_path,monkeypatch):
    """Exercise the real monitor authority with authored published-record stand-ins."""
    def put(name,value):
        path=tmp_path/name;path.write_text(json.dumps(value));return path
    config={'work':str(tmp_path),'bundle':str(tmp_path/'bundle')}
    Path(config['bundle']).mkdir()
    for name in ('judge_call.py','setup.sh','contract.yaml'):(Path(config['bundle'])/name).write_text('authored '+name)
    for name,value in [('inputs',{'arm':'B','run_seed':1301,'update':10}),('cpu_rows',[]),
                       ('route_identity',{'verdict':'PASS','vals_managed_credential_provenance_verified':True})]:
        config[name]=str(put(name+'.json',value))
    config['train_ids']=str(tmp_path/'train.txt');Path(config['train_ids']).write_text('authored\n')
    config['prepared']=str(tmp_path/'prepared.json')
    manifest={'verdict':'PASS','split':'train','declared_audit_cells':32,'n_declared_ratings':6,
              'repeats':[1,2,3],'cells':[{} for _ in range(3)],'compiled_files':1}
    pack=put('pack.json',manifest)
    prepared={'configuration':config,'pack_sha256':m.digest(pack),'bindings':[
        {'path':str(p),'sha256':m.digest(p)} for p in [pack,*Path(config['bundle']).iterdir()]]}
    Path(config['prepared']).write_text(json.dumps(prepared))
    snapshot={'gate':'PILOT_MONITOR_SNAPSHOT','condition':'v2-S2','status':'FROZEN','execution_sha256':'pilot-sha',
              'model_binding_sha256':'model-sha','arm':'B','run_seed':1301,'update':10,'bindings':[]}
    names=('monitor_preparation.py','monitor_runtime.py','monitor_cpu.py','monitor_coverage.py',
           'monitor_hosted.py','coverage_pack.py','hosted_coverage.py','audit_monitor.py')
    pilot={'gate':'LEARNING_PILOT','condition':'v2-S2','status':'FROZEN',
           'bindings':[{'path':str(PHASE/n),'sha256':m.digest(PHASE/n)} for n in names]}
    cpu={'condition':'v2-S2','stage':'PILOT_MONITOR_HIDDEN','accounted':32,'cleanup_unresolved':0,
         'rows_sha256':m.digest(config['cpu_rows']),'snapshot_sha256':'snapshot-sha','execution_sha256':'cpu-lock-sha',
         'arm':'B','run_seed':1301,'update':10}
    values={'controls':{'status':'PASS','condition':'v2-S2','actual_bundle_verified':True},
            'control_lock':{'bindings':[]},'cpu_lock':{'gate':'PILOT_MONITOR_CPU','snapshot_sha256':'snapshot-sha','bindings':[]},
            'cpu':cpu,'snapshot':snapshot,'pilot':pilot}
    lock={'gate':'PILOT_MONITOR_HOSTED','condition':'v2-S2','status':'FROZEN','configuration':config,
          'declared_ratings':6,'members':list(m.CONFIGS),'execution_sha256':'pilot-sha','model_binding_sha256':'model-sha'}
    for key,name,sha in [('coverage_controls_result','controls','controls-sha'),('coverage_controls_lock','control_lock','control-lock-sha'),
        ('cpu_execution_lock','cpu_lock','cpu-lock-sha'),('cpu_result','cpu','cpu-sha'),
        ('snapshot_lock','snapshot','snapshot-sha'),('pilot_execution_lock','pilot','pilot-sha')]:
        lock[key]={'name':name,'sha256':sha}
    required=[PHASE/n for n in ('monitor_hosted.py','monitor_coverage.py','coverage_pack.py','hosted_coverage.py','coverage_controls.py')]
    required += [Path(config[k]) for k in ('prepared','inputs','cpu_rows','train_ids','route_identity')]
    required.append(m.REPO/'src/rl4cv/valkyrie_transport.py')
    lock['bindings']=[{'path':str(p),'sha256':m.digest(p)} for p in required];values['lock']=lock
    monkeypatch.setattr(m,'publication',lambda reference,repository:values[reference['name']])
    monkeypatch.setattr(m,'helper',lambda _:SimpleNamespace(suite_spec=lambda _: {'pack_receipt':str(pack)}))
    calls=[]
    class Transport:
        def __init__(self,*a):calls.append('construct')
        def preflight(self):calls.append('preflight')
        def require_receipt(self,receipt):calls.append('receipt')
    monkeypatch.setattr(m,'Transport',Transport)
    return {'lock':{'name':'lock'},'repository':'authored'},values,calls


def test_published_monitor_authority_rejects_cross_checkpoint_processor_evidence(tmp_path,monkeypatch):
    plan,values,calls=authority_fixture(tmp_path,monkeypatch)
    assert m.authorize(plan)[0]==values['lock'] and calls==['construct','preflight','receipt']
    calls.clear();values['cpu']['snapshot_sha256']='different-snapshot'
    with pytest.raises(ValueError,match='another snapshot'):m.authorize(plan)
    assert calls==[]


def test_monitor_implementation_must_be_frozen_before_learning(tmp_path,monkeypatch):
    plan,values,calls=authority_fixture(tmp_path,monkeypatch)
    values['pilot']['bindings'][0]['sha256']='changed-method'
    with pytest.raises(ValueError,match='before learning'):m.authorize(plan)
    assert calls==[]
