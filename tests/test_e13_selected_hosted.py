"""Exercise one-shot selected-test admissions, immutable inputs and terminal collection without model calls."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import sys
import zipfile

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_selected_hosted',PHASE/'selected_hosted.py')
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
            assert json.loads(state.read_text())['runs']['selected_test/H2_sol_high']['phase']=='admitting'
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
    row=json.loads(state.read_text())['runs']['selected_test/H2_sol_high']
    assert row['phase']=='admission_failed' and not row['automatic_retry']
    with pytest.raises(ValueError,match='never resubmit'):m.admit(plan,'H2_sol_high')
    assert len(calls)==1



def collection_fixture(tmp_path,monkeypatch):
    plan,config,h,manifest,_,state=fixture(tmp_path,monkeypatch)
    for name in ('inputs','cpu_rows'):
        path=tmp_path/(name+'.json');path.write_text('{}' if name=='inputs' else '[]');config[name]=str(path)
    train=tmp_path/'train.txt';train.write_text('authored\n');config['test_ids']=str(train)
    bundle=tmp_path/'bundle';bundle.mkdir();config['bundle']=str(bundle)
    for name in ('judge_call.py','setup.sh','contract.yaml'):(bundle/name).write_text('authored '+name)
    state.write_text(json.dumps({'runs':{'selected_test/'+n:{} for n in m.CONFIGS}}))
    h.poll=lambda:0;h.harvest=lambda *_:None
    directory=tmp_path/'harvests';directory.mkdir()
    for member in m.CONFIGS:
        raw=tmp_path/'judge/raw'/('selected_test__'+member)/'artifacts';raw.mkdir(parents=True)
        with zipfile.ZipFile(raw/'vb103_judge.zip','w') as archive:
            for source in bundle.iterdir():archive.writestr('vb103_judge/'+source.name,source.read_bytes())
        cells=[{**c,'task_id_vb':'authored-file','sample_idx':0,'status':'measured' if i<2 else 'unmeasured_infra',
                'score_raw':i,'transport_matches':i<2,'cost_usd':.1 if i<2 else None,'requests_sent':1 if i<2 else None}
               for i,c in enumerate(manifest['cells'])]
        (directory/('cells_selected_test__'+member+'.json')).write_text(json.dumps({'cells':cells,
             'receipt_inventory':{'missing':['authored_2'],'extra':[],'duplicates':[]}}))
    def aggregate(_):
        assert (tmp_path/'evaluation_attempt.json').exists()
        (tmp_path/'fsc_selected_test.json').write_text('{"cells":{},"n_ratings_measured":4}')
        return 0
    h.fsc=aggregate
    monkeypatch.setattr(m,'combine',lambda *a,**kw:{'condition':'v2-S2','declared':222,'coverage_known':0,'rows':[]})
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
    path=tmp_path/'harvests/cells_selected_test__H2_sol_high.json'
    value=json.loads(path.read_text());value['cells'].pop();path.write_text(json.dumps(value))
    h.fsc=lambda _:pytest.fail('statistics reached with changed denominator')
    with pytest.raises(ValueError,match='denominator changed'):m.collect(plan)
    assert not (tmp_path/'evaluation_attempt.json').exists()



def authority_fixture(tmp_path,monkeypatch,*,missing_method=False):
    import selected_coverage_inputs as normalizer
    from test_e13_selected_coverage_inputs import plan_fixture,put
    from technical_driver import read,reference
    selection=plan_fixture(tmp_path,monkeypatch)
    sources=[PHASE/n for n in ('selected_hosted.py','selected_coverage.py','selected_coverage_inputs.py','coverage_pack.py','hosted_coverage.py','coverage_controls.py')]
    sources.append(m.REPO/'src/rl4cv/valkyrie_transport.py')
    L2=read(selection['L2']);bindings={b['path']:b for b in L2['bindings']}
    bindings.update({str(p):reference(p) for p in sources if not (missing_method and p.name=='selected_hosted.py')})
    L2['bindings']=list(bindings.values());selection['L2']=put(Path(selection['L2']['path']),L2)
    for key in ('selection','score_lock','score'):
        value=read(selection[key]);value['L2_sha256']=selection['L2']['sha256']
        if key=='score':value['scoring_lock_sha256']=selection['score_lock']['sha256']
        selection[key]=put(Path(selection[key]['path']),value)
    inputs=normalizer.prepare(selection);allow=tmp_path/'test_ids.txt';allow.write_text('\n'.join(c['task_id'] for c in inputs['cells'])+'\n')
    config={'work':str(tmp_path),'inputs':str(Path(selection['output'])/'inputs.json'),'test_ids':str(allow),'prepared':str(tmp_path/'prepared.json')}
    config['bundle']=str(tmp_path/'bundle');Path(config['bundle']).mkdir()
    for name in ('judge_call.py','setup.sh','contract.yaml'):(Path(config['bundle'])/name).write_text('authored '+name)
    for key,value in [('route_identity',{'verdict':'PASS','vals_managed_credential_provenance_verified':True}),('registry_catalog',{}),('migration_provenance',{})]:
        config[key]=put(tmp_path/(key+'.json'),value)['path']
    manifest={'verdict':'PASS','split':'test','declared':222,'n_declared_ratings':6,'repeats':[1,2,3],'configs':list(m.CONFIGS),
        'compiled_files':1,**selection['run'],'cells':[{'selected_cell_id':inputs['cells'][1]['cell_id'],'repeat':repeat} for repeat in (1,2,3)]}
    pack=put(tmp_path/'pack.json',manifest)
    prepared={'configuration':config,'pack_sha256':pack['sha256'],'bindings':[pack,*[reference(p) for p in Path(config['bundle']).iterdir()]]}
    put(Path(config['prepared']),prepared)
    original={'configuration':config,'bindings':[]}
    controls=put(tmp_path/'controls.json',{'status':'PASS','condition':'v2-S2','actual_bundle_verified':True})
    previous=put(tmp_path/'control_lock.json',original)
    required=sources+[Path(config[k]) for k in ('prepared','inputs','test_ids','route_identity')]
    lock={'gate':'SELECTED_TEST_COVERAGE_HOSTED','condition':'v2-S2','status':'FROZEN','configuration':config,
        'selection_plan':selection,'bindings':[reference(p) for p in required],'coverage_controls_result':controls,
        'coverage_controls_lock':previous,'declared_ratings':6,'members':list(m.CONFIGS)}
    plan={'lock':put(tmp_path/'lock.json',lock),'repository':'authored'}
    monkeypatch.setattr(m,'published',lambda ref,repo:read(ref))
    monkeypatch.setattr(m,'helper',lambda config:SimpleNamespace(suite_spec=lambda suite:{'pack_receipt':pack['path']}))
    calls=[]
    class Transport:
        def __init__(self,*args):calls.append('construct')
        def preflight(self):calls.append('preflight')
        def require_receipt(self,receipt):calls.append('receipt')
    monkeypatch.setattr(m,'Transport',Transport)
    return plan,calls


def test_selected_hosted_authority_joins_exact_fixed_official_sources(tmp_path,monkeypatch):
    plan,calls=authority_fixture(tmp_path,monkeypatch)
    result=m.authorize(plan)
    assert result[4]['declared']==222 and calls==['construct','preflight','receipt']


def test_hosted_implementation_must_precede_main_before_transport(tmp_path,monkeypatch):
    plan,calls=authority_fixture(tmp_path,monkeypatch,missing_method=True)
    with pytest.raises(ValueError,match='not frozen before main'):m.authorize(plan)
    assert calls==[]
