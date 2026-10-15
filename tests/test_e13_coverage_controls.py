"""Check one-shot hosted admission, source-hash checks and frozen judge envelope criteria without calls."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_coverage_controls',PHASE/'coverage_controls.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def admission_fixture(tmp_path,monkeypatch,*,failure=False):
    state={'runs':{}};calls=[];path=tmp_path/'state.json';path.write_text(json.dumps(state))
    pack=tmp_path/'manifest.json';pack.write_text(json.dumps({'control_cells':[{'task_id':f'authored_{i}'} for i in range(25)]}))
    lock=tmp_path/'lock.json';lock.write_text('{}')
    def save(s):path.write_text(json.dumps(s))
    h=SimpleNamespace(RESULTS=tmp_path,suite_spec=lambda suite:{'benchmark':'authored-benchmark','pack_receipt':pack},
        read_json=lambda p:json.loads(Path(p).read_text()),load_state=lambda:json.loads(path.read_text()),
        save_state=save,stamp=lambda:'authored timestamp',request_benchmark=lambda spec,name:'authored-request',
        judge_config=lambda name:{'selector':'frozen-selector','max_tokens':16384,'reasoning_effort':'high'})
    class Transport:
        def endpoint(self,*a):return 'unused','unused'
        def identity(self):return {'transport':'hosted','organization':'authored-org','tracker_url':'authored-tracker'}
        def run(self,args,timeout):
            # The durable ambiguous-admission marker must precede the external call.
            assert json.loads(path.read_text())['runs']['controls/H2_sol_high']['phase']=='admitting'
            calls.append(args)
            if failure:raise TimeoutError('authored interrupted admission')
            return SimpleNamespace(returncode=0,stdout='Run ID: 11111111-2222-3333-4444-555555555555\n',stderr='')
    monkeypatch.setattr(m,'published',lambda plan:({'lock':str(lock)},{'concurrency':5},{'work':str(tmp_path)},h,Transport()))
    return calls,path


def test_completed_admission_is_never_submitted_twice(tmp_path,monkeypatch):
    calls,path=admission_fixture(tmp_path,monkeypatch)
    result=m.admit('authored-plan','H2_sol_high');assert result['declared_ratings']==25
    assert len(calls)==1 and calls[0][0:3]==['run','start','--agent']
    assert ['-k','reasoning_effort','high']==calls[0][-3:]
    with pytest.raises(ValueError,match='prior admission'):m.admit('authored-plan','H2_sol_high')
    assert len(calls)==1


def test_ambiguous_admission_stays_durable_and_cannot_be_retried(tmp_path,monkeypatch):
    calls,path=admission_fixture(tmp_path,monkeypatch,failure=True)
    with pytest.raises(TimeoutError):m.admit('authored-plan','H2_sol_high')
    row=json.loads(path.read_text())['runs']['controls/H2_sol_high']
    assert row['phase']=='admission_failed' and not row['automatic_retry']
    with pytest.raises(ValueError,match='prior admission'):m.admit('authored-plan','H2_sol_high')
    assert len(calls)==1


def test_private_binding_changed_refuses_before_transport_or_call(tmp_path,monkeypatch):
    source=tmp_path/'input.txt';source.write_text('original')
    prepared=tmp_path/'prepared.json';prepared.write_text(json.dumps({'bindings':[{'path':str(source),'sha256':m.digest(source)}]}))
    source.write_text('changed')
    lock=tmp_path/'lock.json';lock.write_text(json.dumps({'gate':'TRAIN_COVERAGE_ROUTE_CONTROLS','status':'FROZEN',
        'condition':'v2-S2','private_prepared':str(prepared),'bindings':[{'path':str(prepared),'sha256':m.digest(prepared)}]}))
    plan=tmp_path/'plan.json';plan.write_text(json.dumps({'lock':str(lock),'published_revision':'authored'}))
    monkeypatch.setattr(m,'REPO',tmp_path)
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:None)
    monkeypatch.setattr(m.subprocess,'check_output',lambda *a,**k:lock.read_bytes())
    monkeypatch.setattr(m,'Transport',lambda *a:pytest.fail('transport reached after changed binding'))
    with pytest.raises(ValueError,match='private control binding'):m.published(plan)


def test_durable_attempt_marker_fences_replay_after_summary_state_loss(tmp_path,monkeypatch):
    calls,path=admission_fixture(tmp_path,monkeypatch)
    m.admit('authored-plan','H2_sol_high')
    path.write_text(json.dumps({'runs':{}}))
    with pytest.raises(ValueError,match='prior admission'):m.admit('authored-plan','H2_sol_high')
    assert len(calls)==1 and (tmp_path/'H2_sol_high_attempt.json').exists()
