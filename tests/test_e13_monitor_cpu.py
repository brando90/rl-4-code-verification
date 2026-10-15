"""Keep monitor sources tied to saved strict evidence while independent hidden scores retain missingness."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_monitor_cpu',PHASE/'monitor_cpu.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return path


def ref(path):return {'path':str(path),'sha256':m.digest(path)}


def fixture(tmp_path):
    cells=[];rows=[];suites={};score=tmp_path/'scores'
    for i in range(32):
        task=f'authored_{i}';cell={'cell_id':f'B/1301/10/{task}/0','audit_id':str(i),'task_id':task,'group_id':str(i),
             'split':'train','arm':'B','run_seed':1301,'update':10,'sample':0,'group_index':i}
        cells.append(cell);folder=score/f'{i:05d}';folder.mkdir(parents=True)
        source=folder/'solution.lean';source.write_text('def authored := 1\n')
        put(folder/'evidence/oracle/oracle.json',{'compile':True})
        row={**cell,'status':'measured','cleanup_verified':True,'source_sha256':m.digest(source),'strict':0}
        put(folder/'result.json',row);rows.append(row)
        suites[task]=ref(put(tmp_path/f'suite_{i}.json',{'n_tests':1,'tests':[]}))
    snapshot={'condition':'v2-S2','arm':'B','run_seed':1301,'update':10,'declared':32,'frozen_before_generation':True,'cells':cells}
    ids=tmp_path/'train.txt';ids.write_text('\n'.join(c['task_id'] for c in cells)+'\n')
    return snapshot,{'rows':rows},score,suites,ids


def test_official_compile_is_reused_instead_of_inferred_from_strict(tmp_path):
    snapshot,scoring,score,suites,ids=fixture(tmp_path)
    inputs=m.prepare(snapshot,scoring,score,suites,output=tmp_path/'inputs')
    first=inputs['cells'][0];strict=json.loads(Path(first['strict']['path']).read_text())
    assert strict['strict']==0 and strict['compile'] is True
    assert inputs['new_strict_measurements']==inputs['new_hidden_measurements']==0
    assert len(inputs['cells'])==32


def test_changed_source_and_missing_cell_cannot_prepare_monitor(tmp_path):
    snapshot,scoring,score,suites,ids=fixture(tmp_path)
    (score/'00000/solution.lean').write_text('changed')
    with pytest.raises(ValueError,match='strict source'):m.prepare(snapshot,scoring,score,suites,output=tmp_path/'bad_source')
    scoring['rows'].pop()
    with pytest.raises(ValueError,match='denominator'):m.prepare(snapshot,scoring,score,suites,output=tmp_path/'bad_count')


def test_partial_hidden_tests_remain_unknown_and_no_strict_rescore(tmp_path):
    snapshot,scoring,score,suites,ids=fixture(tmp_path);inputs=m.prepare(snapshot,scoring,score,suites,output=tmp_path/'inputs')
    cell=inputs['cells'][0];root=tmp_path/'measure';root.mkdir()
    job={'cell':cell,'identity':{k:cell[k] for k in m.IDENTITY},'configuration':{'train_ids':str(ids)},
         'root':str(root),'execution_sha256':'bound'}
    calls=[]
    def hidden(*args):calls.append(args);return {'status':'incomplete','fully_applicable':False,'hidden_pass_rate':1.}
    result=m.measure(job,hidden=hidden)
    assert len(calls)==1 and result['compile'] is True and result['hidden_test_coverage'] is None
    assert result['new_strict_measurements']==0 and Path(result['hidden_receipt']['path']).exists()


def test_finished_hidden_cell_is_not_replayed_and_binding_change_rejected(tmp_path):
    snapshot,scoring,score,suites,ids=fixture(tmp_path);inputs=m.prepare(snapshot,scoring,score,suites,output=tmp_path/'inputs')
    cell=inputs['cells'][0];config={'root':str(tmp_path/'execution'),'train_ids':str(ids)};calls=[]
    def execute(job,root,marker,slots):
        calls.append(job);result={**job['identity'],'status':'ACCOUNTED','cleanup_verified':True}
        m.write_new(root/'result.json',result);return result
    first=m.score_cell(cell,0,config,'frozen',None,executor=execute)
    assert m.score_cell(cell,0,config,'frozen',None,executor=execute)==first and len(calls)==1
    with pytest.raises(ValueError,match='binding changed'):m.score_cell(cell,0,config,'changed',None,executor=execute)
