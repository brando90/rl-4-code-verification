"""Retain fixed monitor missingness, physical evidence and one final decision without model calls."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))

def load(name):
    spec=importlib.util.spec_from_file_location('e13_'+name,PHASE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

m=load('monitor_decision');join=load('monitor_measurements')


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return {'path':str(path),'sha256':m.digest(path)}


def fixture(tmp_path,update=0,denominator=2,official_compile=True):
    tmp_path.mkdir(parents=True,exist_ok=True)
    cells=[];normalized=[];strict=[];hidden=[];formal=[]
    source=tmp_path/'source.lean';source.write_text('def authored : Nat := 1\n')
    source_ref={'path':str(source),'sha256':m.digest(source)}
    for i in range(32):
        cell={'cell_id':f'B/1301/{update}/{i}','audit_id':f'audit_{i}','task_id':f'authored_{i}',
              'group_id':f'group_{i}','split':'train','arm':'B','run_seed':1301,'update':update,'sample':0,'group_index':i}
        cells.append(cell)
        row={**cell,'status':'measured','strict':0,'cleanup_verified':True,'source_sha256':source_ref['sha256'],
             'e':True,'n_examples':1,'raw_vacuity_hits':0,'d':{'numerator':1,'denominator':2},
             'p':{'numerator':1,'denominator':denominator},'t':1}
        saved=put(tmp_path/f'{i}.saved.json',row);strict.append(row)
        oracle=put(tmp_path/f'{i}.oracle.json',{'compile':official_compile})
        normalized_ref=put(tmp_path/f'{i}.normalized.json',{**row,'compile':official_compile,'strict_receipt':saved,'oracle_receipt':oracle})
        normalized.append({**cell,'source':source_ref,'strict':normalized_ref})
        hidden.append({**cell,'compile':official_compile,'cleanup_verified':True,'strict_receipt':normalized_ref,
                       'hidden_test_coverage':.75 if i<31 else None,'hidden_status':'measured' if i<31 else 'no_tests'})
        formal.append({**cell,'compile':official_compile,'formal_specification_coverage':.8 if official_compile else 0.})
    snapshot={'condition':'v2-S2','stage':'PILOT_MONITOR_SNAPSHOT','declared':32,'frozen_before_generation':True,
              'arm':'B','run_seed':1301,'update':update,'cells':cells}
    inputs={**snapshot,'cells':normalized}
    scoring=put(tmp_path/'scoring.json',{'rows':strict})
    hidden_ref=put(tmp_path/'hidden.json',{'condition':'v2-S2','stage':'PILOT_MONITOR_HIDDEN','declared':32,'accounted':32,
        'cleanup_unresolved':0,'rows':hidden})
    hosted_ref=put(tmp_path/'hosted.json',{'condition':'v2-S2','stage':'PILOT_MONITOR_HOSTED','declared':32,
                                         'declared_ratings':192,'rows':formal})
    cleanup=put(tmp_path/'cleanup.json',{'registered_processes_exited':True,'port_free':True,
        'owned_remote_entries_removed':[{'operation':n,'exit_code':0} for n in ('service','auth_secret')]})
    controls={k:{'condition':'v2-S2','status':'PASS'} for k in m.COVERAGE}
    result=join.assemble(snapshot,inputs,scoring_ref=scoring,hidden_ref=hidden_ref,hosted_ref=hosted_ref,
                         controls=controls,hosted_cleanup_ref=cleanup,output=tmp_path/'joined')
    result.update(execution_sha256='execution',model_binding_sha256='model',snapshot_lock={'name':'snapshot'})
    return snapshot,result


def test_missing_hidden_applicability_stays_declared_and_can_form_available_baseline(tmp_path):
    snapshot,header=fixture(tmp_path);rows=m.read_checked(header['rows']);availability=m.read_checked(header['availability'])
    assert len(rows)==32 and rows[-1]['hidden_test_coverage'] is None
    result=m.baseline_decision(rows,snapshot['cells'],arm='B',run_seed=1301,availability=availability)
    assert result['status']=='CONTINUE'
    metric=result['metrics']['hidden_test_coverage']
    assert metric['paired_observed']==31 and metric['baseline_full_manifest']['missing']==1
    assert metric['baseline_full_manifest']['mean_bounds']==[31*.75/32,(31*.75+1)/32]


def test_unavailable_route_or_missing_reward_prevents_baseline_continuation(tmp_path):
    snapshot,header=fixture(tmp_path);rows=m.read_checked(header['rows']);availability=m.read_checked(header['availability'])
    availability['formal_specification_coverage']['cleanup_verified']=False
    assert m.baseline_decision(rows,snapshot['cells'],arm='B',run_seed=1301,availability=availability)['status']=='INCOMPLETE'
    availability['formal_specification_coverage']['cleanup_verified']=True;rows[0]['reward']=None
    assert m.baseline_decision(rows,snapshot['cells'],arm='B',run_seed=1301,availability=availability)['status']=='INCOMPLETE'


def test_physical_receipt_and_source_bytes_are_checked_before_decision(tmp_path,monkeypatch):
    snapshot,header=fixture(tmp_path);monkeypatch.setattr(m,'published',lambda *_:header)
    args={'execution_sha':'execution','arm':'B','run_seed':1301,'update':0}
    assert len(m.measurement({},'authored',**args)[1])==32
    path=Path(header['cell_receipts']['audit_0']['path']);value=json.loads(path.read_text())
    Path(value['source_bindings'][0]['path']).write_text('{}')
    with pytest.raises(ValueError,match='source evidence changed'):m.measurement({},'authored',**args)


def authority(tmp_path,monkeypatch):
    snapshot,header=fixture(tmp_path)
    cohort=put(tmp_path/'cohort.json',{'cells':snapshot['cells']})
    sources=[Path(m.__file__).resolve(),PHASE/'audit_monitor.py',PHASE/'MONITOR_S2_METHOD.md']
    pilot={'gate':'LEARNING_PILOT','condition':'v2-S2','status':'FROZEN',
           'bindings':[{'path':str(p),'sha256':m.digest(p)} for p in sources]+[cohort]}
    lock={'gate':'PILOT_MONITOR_DECISION_INPUTS','condition':'v2-S2','status':'FROZEN','arm':'B','run_seed':1301,'update':0,
          'pilot_execution_lock':{'name':'pilot','sha256':'execution'},'current':{'name':'current','sha256':'current-sha'},
          'coverage_controls_result':{'name':'controls'},'hidden_controls_result':{'name':'controls'},
          'bindings':[cohort],'configuration':{'cohort':cohort,'root':str(tmp_path/'decision')}}
    frozen={'gate':'PILOT_MONITOR_SNAPSHOT','condition':'v2-S2','status':'FROZEN','execution_sha256':'execution',
            'arm':'B','run_seed':1301,'update':0,'model_binding_sha256':'model'}
    values={'lock':lock,'pilot':pilot,'current':header,'snapshot':frozen,'controls':{'condition':'v2-S2','status':'PASS'}}
    monkeypatch.setattr(m,'published',lambda reference,_:values[reference['name']])
    return {'lock':{'name':'lock','sha256':'lock-sha'},'repository':'authored'},values


def test_one_decision_is_recorded_before_evaluation_and_never_recomputed(tmp_path,monkeypatch):
    plan,values=authority(tmp_path,monkeypatch)
    original=m.baseline_decision
    def evaluate(*a,**kw):
        assert (tmp_path/'decision/evaluation_attempt.json').exists()
        return original(*a,**kw)
    monkeypatch.setattr(m,'baseline_decision',evaluate)
    result=m.run(plan)
    assert result['gate']=='PILOT_MONITOR' and result['status']=='CONTINUE' and result['model_binding_sha256']=='model'
    monkeypatch.setattr(m,'baseline_decision',lambda *a,**kw:pytest.fail('monitor decision repeated'))
    with pytest.raises(FileExistsError):m.run(plan)


def test_wrong_pre_response_checkpoint_prevents_any_decision_attempt(tmp_path,monkeypatch):
    plan,values=authority(tmp_path,monkeypatch);values['snapshot']['model_binding_sha256']='another-model'
    with pytest.raises(ValueError,match='checkpoint differs'):m.run(plan)
    assert not (tmp_path/'decision/evaluation_attempt.json').exists()


def test_observed_stop_survives_an_incomplete_coverage_route(tmp_path,monkeypatch):
    plan,values=authority(tmp_path,monkeypatch)
    initial=m.run(plan);values['baseline']=values['current'];values['baseline_decision']=initial
    _,current=fixture(tmp_path/'current_measurements',update=10,denominator=1)
    availability=m.read_checked(current['availability']);availability['hidden_test_coverage']['cleanup_verified']=False
    current['availability']=put(Path(current['availability']['path']),availability)
    values['current']=current;values['snapshot']['update']=10
    lock=values['lock'];lock.update(update=10,baseline={'name':'baseline','sha256':'current-sha'},
                                  baseline_decision={'name':'baseline_decision'})
    lock['configuration']['root']=str(tmp_path/'decision10')
    result=m.run(plan)
    assert result['status']=='STOP_ARM' and 'theorem_count' in result['stop_metrics']
    assert result['metrics']['theorem_count']['relative_change']==-.5
    assert not result['metrics']['hidden_test_coverage']['available_route_and_complete_accounting']


def test_independent_hidden_compile_status_is_not_inferred_from_official_oracle(tmp_path):
    snapshot,header=fixture(tmp_path,official_compile=False)
    rows=m.read_checked(header['rows']);availability=m.read_checked(header['availability'])
    assert rows[0]['formal_specification_coverage']==0 and rows[0]['hidden_test_coverage']==.75
    assert availability['formal_specification_coverage']['cells']['audit_0']['status']=='compile_failure'
    assert availability['hidden_test_coverage']['cells']['audit_0']['status']=='measured'
    assert m.baseline_decision(rows,snapshot['cells'],arm='B',run_seed=1301,availability=availability)['status']=='CONTINUE'
