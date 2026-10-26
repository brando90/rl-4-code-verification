"""Exercise one-shot train-audit admissions, immutable inputs and terminal collection without model calls."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import sys
import zipfile

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_audit_hosted',PHASE/'audit_hosted.py')
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
            assert json.loads(state.read_text())['runs']['train_audit/H2_sol_high']['phase']=='admitting'
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
    row=json.loads(state.read_text())['runs']['train_audit/H2_sol_high']
    assert row['phase']=='admission_failed' and not row['automatic_retry']
    with pytest.raises(ValueError,match='never resubmit'):m.admit(plan,'H2_sol_high')
    assert len(calls)==1


def test_changed_binding_refused_before_transport(tmp_path,monkeypatch):
    path=tmp_path/'input';path.write_text('frozen');sha=m.digest(path);path.write_text('changed')
    lock={'gate':'TRAIN_AUDIT_HOSTED','condition':'v2-S2','status':'FROZEN',
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
    state.write_text(json.dumps({'runs':{'train_audit/'+n:{} for n in m.CONFIGS}}))
    h.poll=lambda:0;h.harvest=lambda *_:None
    directory=tmp_path/'harvests';directory.mkdir()
    for member in m.CONFIGS:
        raw=tmp_path/'judge/raw'/('train_audit__'+member)/'artifacts';raw.mkdir(parents=True)
        with zipfile.ZipFile(raw/'vb103_judge.zip','w') as archive:
            for source in bundle.iterdir():archive.writestr('vb103_judge/'+source.name,source.read_bytes())
        cells=[{**c,'task_id_vb':'authored-file','sample_idx':0,'status':'measured' if i<2 else 'unmeasured_infra',
                'score_raw':i,'transport_matches':i<2,'cost_usd':.1 if i<2 else None,'requests_sent':1 if i<2 else None}
               for i,c in enumerate(manifest['cells'])]
        (directory/('cells_train_audit__'+member+'.json')).write_text(json.dumps({'cells':cells,
             'receipt_inventory':{'missing':['authored_2'],'extra':[],'duplicates':[]}}))
    def aggregate(_):
        assert (tmp_path/'evaluation_attempt.json').exists()
        (tmp_path/'fsc_train_audit.json').write_text('{"cells":{},"n_ratings_measured":4}')
        return 0
    h.fsc=aggregate
    monkeypatch.setattr(m,'combine',lambda *a,**kw:{'condition':'v2-S2','declared':128,'coverage_known':0,'rows':[]})
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
    path=tmp_path/'harvests/cells_train_audit__H2_sol_high.json'
    value=json.loads(path.read_text());value['cells'].pop();path.write_text(json.dumps(value))
    h.fsc=lambda _:pytest.fail('statistics reached with changed denominator')
    with pytest.raises(ValueError,match='denominator changed'):m.collect(plan)
    assert not (tmp_path/'evaluation_attempt.json').exists()
