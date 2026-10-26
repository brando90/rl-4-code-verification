"""Exercise prospective independent-metric joins on authored receipts without opening real test tasks."""
from pathlib import Path
import sys
import numpy as np
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import selected_coverage_join as m


def setup(monkeypatch):
    run={'arm':'B','run_seed':13011,'selection':'selection','test_score':'score'}
    rows=[{'cell_id':f'B/13011/4/test/authored_{i}/0','task_id':f'authored_{i}','sample_idx':0,'split':'test',
       'condition':'v2-S2','arm':'B','run_seed':13011,'boundary':4,'status':'measured','compile':True,'strict':0,'p':{'denominator':3}}for i in range(222)]
    availability=[{'boundary':4,'not_evaluated_reason':None}]
    monkeypatch.setattr(m,'collect_strict',lambda *a:(rows,[],availability))
    refs={'score':{'model_binding_sha256':'model'}}
    monkeypatch.setattr(m,'published',lambda ref,repository:refs[ref] if isinstance(ref,str) else refs[ref['path']])
    monkeypatch.setattr(m,'read',lambda ref:refs[ref] if isinstance(ref,str) else refs[ref['path']])
    monkeypatch.setattr(m,'execution',lambda *a:{})
    for prefix,metric in [('hidden','hidden_test_coverage'),('hosted','formal_specification_coverage')]:
        key=prefix+'_absent';run[prefix+'_unavailable']=key
        refs[key]={'condition':'v2-S2','stage':'SELECTED_TEST_COVERAGE_UNAVAILABLE','status':'NOT_EVALUATED',
          'metric':metric,'L2_sha256':'L2','arm':'B','run_seed':13011,'boundary':4,'reason':'authored unavailable route'}
    return run,rows,refs,availability

def go(run):return m.collect([run],[],['A','B','P'],'L2','contract','repo')

def test_missing_routes_preserve_theorem_count(monkeypatch):
    run,rows,refs,avail=setup(monkeypatch);out,sources,reasons=go(run)
    assert len(out)==222 and len(reasons)==2 and len(sources)==2
    assert all(r['theorem_count']==3 and r['hidden_test_coverage'] is None and r['formal_specification_coverage'] is None for r in out)

def test_unavailable_selection_retains_complete_missing_population(monkeypatch):
    run,rows,refs,avail=setup(monkeypatch);avail[0].update(boundary=None,not_evaluated_reason='main HALTED')
    for row in rows:row.update(boundary=None,status='not_evaluated');row.pop('p')
    out,_,_=go(run);assert len(out)==222 and all(r['theorem_count'] is None and r['boundary'] is None for r in out)
    run['hidden_result']='forbidden'
    with pytest.raises(ValueError,match='unavailable strict'):go(run)

def test_wrong_checkpoint_missing_route_is_rejected(monkeypatch):
    run,rows,refs,avail=setup(monkeypatch);refs['hidden_absent']['boundary']=3
    with pytest.raises(ValueError,match='same-checkpoint'):go(run)

def test_continuous_hidden_values_rejoin_saved_measurement(monkeypatch):
    run,rows,refs,avail=setup(monkeypatch);run.update(hidden_result='hidden',hidden_lock={'sha256':'execution'})
    hidden=[]
    for i,row in enumerate(rows):
        hidden.append({**row,'cleanup_verified':True,'hidden_test_coverage':.375,'hidden_receipt':f'h{i}'})
        refs[f'h{i}']={'fully_applicable':True,'hidden_pass_rate':.375,'status':'measured'}
    refs['hidden_rows']=hidden
    refs['hidden']={'condition':'v2-S2','stage':'SELECTED_TEST_HIDDEN','status':'ACCOUNTED','arm':'B','run_seed':13011,
      'boundary':4,'L2_sha256':'L2','model_binding_sha256':'model','execution_sha256':'execution','declared':222,'accounted':222,
      'cleanup_unresolved':0,'automatic_retries':0,'rows_sha256':'rows','rows':{'path':'hidden_rows','sha256':'rows'}}
    out,_,_=go(run);assert all(r['hidden_test_coverage']==.375 and r['formal_specification_coverage'] is None for r in out)
    hidden[0]['hidden_test_coverage']=.5
    with pytest.raises(ValueError,match='detached'):go(run)

@pytest.mark.parametrize('change',['sample','duplicate','checkpoint'])
def test_hidden_integrity_failures_reject_aggregation(monkeypatch,change):
    run,rows,refs,avail=setup(monkeypatch)
    expected={r['cell_id']:r for r in rows};changed=[dict(r)for r in rows]
    if change=='sample':changed[0]['sample_idx']=1
    elif change=='duplicate':changed[-1]=dict(changed[0])
    else:changed[0]['boundary']=3
    with pytest.raises(ValueError):m.table(changed,expected)


def test_hosted_measurements_keep_compile_gate_and_validated_three_by_two_ratings(monkeypatch):
    run,rows,refs,_=setup(monkeypatch)
    run.update(hosted_result='hosted',hosted_lock={'sha256':'hosted_execution'})
    hosted=[{**r,'formal_specification_coverage':.625,'ratings':{'complete_3x2':True,'FSC':.625}}for r in rows]
    rows[0]['compile']=False;hosted[0].update(compile=False,formal_specification_coverage=0,ratings=None)
    rows[1].update(compile=None,status='unavailable');hosted[1].update(compile=None,formal_specification_coverage=None,ratings=None)
    refs['hosted']={'condition':'v2-S2','stage':'SELECTED_TEST_HOSTED','declared':222,
        'lock_sha256':'hosted_execution','actual_bundle_verified':True,'requested_identity_verified':True,'rows':hosted}
    out,_,_=go(run)
    assert out[0]['formal_specification_coverage']==0 and out[1]['formal_specification_coverage'] is None
    assert out[2]['formal_specification_coverage']==.625
    hosted[0]['formal_specification_coverage']=.625
    with pytest.raises(ValueError,match='compile-gating'):go(run)
    hosted[0]['formal_specification_coverage']=0
    refs['hosted']['actual_bundle_verified']=False
    with pytest.raises(ValueError,match='validated judge'):go(run)


def test_execution_requires_same_selection_and_unchanged_physical_inputs(tmp_path,monkeypatch):
    path=tmp_path/'authored_input.json';path.write_text('{}')
    run={'selection':'selection','test_score':'score'}
    lock={'gate':'SELECTED_TEST_COVERAGE_CPU','condition':'v2-S2','status':'FROZEN',
        'selection_plan':{'repository':'repo','L2':{'sha256':'L2'},'selection':'selection','score':'score',
            'run':{'arm':'B','run_seed':13011,'boundary':4}},
        'bindings':[{'path':str(path),'sha256':m.digest(path)}]}
    refs={'lock':lock,'selection':{'arm':'B','run_seed':13011,'boundary':4}}
    monkeypatch.setattr(m,'published',lambda ref,repo:refs[ref])
    assert m.execution('lock',run,'SELECTED_TEST_COVERAGE_CPU','L2','repo')==lock
    lock['selection_plan']['score']='other'
    with pytest.raises(ValueError,match='selected strict'):m.execution('lock',run,'SELECTED_TEST_COVERAGE_CPU','L2','repo')
    lock['selection_plan']['score']='score';path.write_text('{"changed":true}')
    with pytest.raises(ValueError,match='input changed'):m.execution('lock',run,'SELECTED_TEST_COVERAGE_CPU','L2','repo')
