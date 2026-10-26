"""Keep completed monitor scoring and hidden execution tied to immutable inputs without repeating measurements."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_monitor_processing',PHASE/'monitor_processing.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path


def ref(path):return {'path':str(path),'sha256':m.digest(path)}


def score_fixture(tmp_path,monkeypatch):
    generated=tmp_path/'monitor_generate/output';generated.mkdir(parents=True)
    cells=[{'cell_id':str(i),'task_id':f'authored_{i}','split':'train','arm':'B','run_seed':1301,'update':0,'sample':0,'group_index':i} for i in range(32)]
    put(generated/'cells.json',cells)
    put(generated/'monitor_result.json',{'status':'COMPLETE','declared':32,'completed':32,'learning_rollout_tokens':0})
    dispatch=put(tmp_path/'monitor_generate/dispatch/result.json',{'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True,'snapshot_sha256':'snapshot'})
    for i,cell in enumerate(cells):put(generated/f'{i:05d}.generation.json',cell)
    lock={'configuration':{'root':str(tmp_path)},'arm':'B','run_seed':1301,'update':0,'execution_sha256':'execution','model_binding_sha256':'model'}
    config={'scoring':{'controller_fence':str(tmp_path/'global/score.lock')}}
    monkeypatch.setattr(m,'authority',lambda _: (lock,{'cells':cells},{},config));calls=[]
    def score(cells,config,bound,execution):
        assert (tmp_path/'strict/inputs.json').exists()
        calls.append(1);value={'rows':[{**c,'status':'measured','cleanup_verified':True,'strict':0} for c in cells],'measured':32}
        put(Path(config['root'])/'result.json',value);return value
    monkeypatch.setattr(m,'score_batch',score)
    return {'snapshot_lock':{'sha256':'snapshot'}},calls,dispatch


def test_complete_monitor_scoring_recovers_without_another_scorer_call(tmp_path,monkeypatch):
    plan,calls,dispatch=score_fixture(tmp_path,monkeypatch)
    result=m.score(plan)
    assert result['accounted']==32 and result['cleanup_unresolved']==0 and result['automatic_retries']==0
    assert m.score(plan)==result and len(calls)==1
    put(tmp_path/'monitor_generate/output/00000.generation.json',{'changed':True})
    with pytest.raises(ValueError,match='saved monitor generation changed'):m.score(plan)
    assert len(calls)==1


def test_unresolved_generator_cleanup_prevents_processor_measurement(tmp_path,monkeypatch):
    plan,calls,dispatch=score_fixture(tmp_path,monkeypatch)
    value=json.loads(dispatch.read_text());value['cleanup_verified']=False;put(dispatch,value)
    with pytest.raises(ValueError,match='cleaned snapshot'):m.score(plan)
    assert not calls and not (tmp_path/'strict/inputs.json').exists()


def hidden_fixture(tmp_path,monkeypatch):
    inputs=put(tmp_path/'inputs.json',{'condition':'v2-S2','declared':32,'arm':'B','run_seed':1301,'update':0,'cells':[]})
    files=[Path(m.__file__).resolve(),PHASE/'monitor_cpu.py',PHASE/'hidden_runtime.py',PHASE/'costs.py']
    pilot={'gate':'LEARNING_PILOT','status':'FROZEN','bindings':[ref(p) for p in files]}
    snapshot={'execution_sha256':'pilot','arm':'B','run_seed':1301,'update':0}
    lock={'gate':'PILOT_MONITOR_CPU','condition':'v2-S2','status':'FROZEN','execution_sha256':'pilot',
          'pilot_execution_lock':{'name':'pilot','sha256':'pilot'},'snapshot_lock':{'name':'snapshot','sha256':'snapshot'},
          'snapshot_sha256':'snapshot','hidden_controls_result':{'name':'controls'},'arm':'B','run_seed':1301,'update':0,
          'model_binding_sha256':'model','bindings':[ref(inputs)],'configuration':{'inputs':str(inputs),'root':str(tmp_path/'hidden')}}
    values={'lock':lock,'pilot':pilot,'snapshot':snapshot,'controls':{'status':'PASS','cleanup_verified':True}}
    monkeypatch.setattr(m,'published',lambda reference,_:values[reference['name']]);calls=[]
    def run(inputs,config,execution):
        calls.append(1)
        assert (Path(config['root'])/'parent_attempt.json').exists()
        return {'condition':'v2-S2','stage':'PILOT_MONITOR_HIDDEN','execution_sha256':execution,'declared':32,'accounted':32,
                'cleanup_unresolved':0,'automatic_retries':0,'rows':[{'cell_id':str(i),'cleanup_verified':True} for i in range(32)]}
    monkeypatch.setattr(m,'run_cells',run)
    return {'lock':{'name':'lock','sha256':'cpu-lock'},'repository':'authored'},values,calls


def test_completed_hidden_monitor_recovers_and_retains_rows_hash(tmp_path,monkeypatch):
    plan,values,calls=hidden_fixture(tmp_path,monkeypatch)
    result=m.hidden(plan)
    assert result['accounted']==32 and result['snapshot_sha256']=='snapshot' and result['execution_sha256']=='cpu-lock'
    assert result['rows_sha256']==m.digest(tmp_path/'hidden/rows.json')
    assert m.hidden(plan)==result and len(calls)==1
    put(tmp_path/'hidden/rows.json',[])
    with pytest.raises(ValueError,match='completed monitor hidden result changed'):m.hidden(plan)
    assert len(calls)==1


def test_changed_prelearning_processor_source_prevents_hidden_measurement(tmp_path,monkeypatch):
    plan,values,calls=hidden_fixture(tmp_path,monkeypatch);values['pilot']['bindings'][0]['sha256']='changed'
    with pytest.raises(ValueError,match='before learning'):m.hidden(plan)
    assert not calls and not (tmp_path/'hidden/parent_attempt.json').exists()


def test_parent_interruption_after_hidden_rows_recovers_without_overwriting_cost(tmp_path,monkeypatch):
    plan,values,calls=hidden_fixture(tmp_path,monkeypatch)
    original=m.write_new
    def interrupted(path,value):
        if path.name=='terminal.json':raise OSError('authored parent interruption')
        return original(path,value)
    monkeypatch.setattr(m,'write_new',interrupted)
    with pytest.raises(OSError,match='parent interruption'):m.hidden(plan)
    cost=(tmp_path/'hidden/cost.json').read_bytes()
    rows=json.loads((tmp_path/'hidden/rows.json').read_text())
    # The underlying run_cells recovers each existing cell receipt; no new worker.
    monkeypatch.setattr(m,'run_cells',lambda *args:{'condition':'v2-S2','stage':'PILOT_MONITOR_HIDDEN',
        'execution_sha256':'cpu-lock','declared':32,'accounted':32,'cleanup_unresolved':0,'automatic_retries':0,'rows':rows})
    monkeypatch.setattr(m,'write_new',original)
    result=m.hidden(plan)
    assert result['accounted']==32 and len(calls)==1
    assert (tmp_path/'hidden/cost.json').read_bytes()==cost


def test_parent_interruption_after_strict_cost_recovers_retained_scoring(tmp_path,monkeypatch):
    plan,calls,dispatch=score_fixture(tmp_path,monkeypatch)
    original=m.write_new
    def interrupted(path,value):
        if path.name=='terminal.json':raise OSError('authored parent interruption')
        return original(path,value)
    monkeypatch.setattr(m,'write_new',interrupted)
    with pytest.raises(OSError,match='parent interruption'):m.score(plan)
    cost=(tmp_path/'strict/cost.json').read_bytes()
    monkeypatch.setattr(m,'score_batch',lambda *args:json.loads((tmp_path/'strict/cells/result.json').read_text()))
    monkeypatch.setattr(m,'write_new',original)
    assert m.score(plan)['accounted']==32 and len(calls)==1
    assert (tmp_path/'strict/cost.json').read_bytes()==cost
