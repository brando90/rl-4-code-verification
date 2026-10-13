"""Synthetic controls for historical readback reuse, route isolation and admission completeness."""
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

V2=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2'


def module(name):
    spec=importlib.util.spec_from_file_location('test_e13v2_'+name,V2/'reproduction'/f'{name}.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def test_test_source_is_rejected_before_opening_in_ordinary_route(tmp_path,monkeypatch):
    worker=module('cell_worker')
    def prohibited(*args,**kwargs):raise AssertionError('test source accessed')
    monkeypatch.setattr(worker,'sha256',prohibited)
    with pytest.raises(ValueError,match='sealed-route'):
        worker.measure({'split':'test'},tmp_path,'ordinary')


def test_shared_source_keeps_base_and_ladder_semantics(tmp_path):
    worker=module('cell_worker')
    scorer=Path(os.environ.get('E13_SCORER_ROOT','/absent'))
    if not (scorer/'scripts/scsc/run_real_eval.py').exists():
        if os.environ.get('E13_REQUIRE_LEAN_INTEGRATION')=='1':pytest.fail('required frozen scorer unavailable')
        pytest.skip('requires pinned historical reader')
    vacuity=worker.load('score_teacher_files',worker.E08/'score_teacher_files.py');vacuity.SCORER=scorer
    source=tmp_path/'vacuous.lean';source.write_text('example : True := by trivial\ntheorem t : True := by trivial\n')
    old={'scored_response':{'compiles':True,'n_examples':1,'n_theorems_stated':1,'n_theorems_proved':1,'truncated':False}}
    assert worker.ladder_readback(source,old,True,tmp_path/'known')=={'value':0.,'status':'scored'}
    assert worker.ladder_readback(source,old,False,tmp_path/'unknown')=={'value':None,'status':'unmeasured'}
    parts={'e':1,'n_examples':1,'p':{'numerator':1,'denominator':1},'d':{'numerator':2,'denominator':2},'t':1,'raw_vacuity_hits':2}
    assert worker.family_reward(parts,1)==1 and worker.family_reward(parts,0)==0
    raw={'vacuity':{'unparseable':[]},'kernel':{'probe_ok':True}}
    assert worker.family_consistency(parts,1,raw)=='consistent'
    assert worker.family_consistency(parts,0,raw)=='vacuity'


def test_opaque_receipt_discloses_only_completeness_hashes_and_equality(tmp_path,capsys):
    route=module('run_route');(tmp_path/'opaque').mkdir()
    (tmp_path/'opaque_manifest.jsonl').write_text('private manifest')
    (tmp_path/'opaque/results.jsonl').write_text('private result')
    rows=[{'cell_id':'sealed-id'}]
    results=[{'status':'measured','oracle_equal':False,'consistency':'typed_vacuity','strict':1,'task_id':'sealed-id'}]
    assert route.route_receipt(tmp_path,'opaque',rows,results)=='FAIL'
    printed=capsys.readouterr().out
    assert 'sealed-id' not in printed and 'vacuity' not in printed and 'strict' not in printed
    result=json.loads(printed)
    assert result['accounted']==1 and result['complete_required'] and result['equality']=='FAIL'
    results[0]['status']='unresolved_measurement'
    assert route.route_receipt(tmp_path,'opaque',rows,results)=='INCOMPLETE'


def test_combined_gate_never_advances_incomplete_or_mismatched_route():
    combine=module('run_all').combine
    rows=[{'route':r,'declared':n,'accounted':n,'measured':n,'typed_deterministic_limits':0,'complete_required':True,'equality':'PASS'} for r,n in [('ordinary',33456),('opaque',5328)]]
    assert combine(rows)['status']=='PASS'
    rows[1]['complete_required']=False
    assert combine(rows)['status']=='INCOMPLETE'
    rows[1]['complete_required']=True;rows[1]['equality']='FAIL'
    assert combine(rows)['status']=='FAIL'


def test_g0_uses_all_eight_samples_and_one_class_auc_is_undefined():
    evaluate=module('g0').evaluate
    earlier=[[[0,.1*k] for k in range(8)] for _ in range(4)]
    later=[[[0,.1*k] for k in range(8)] for _ in range(4)]
    result=evaluate(earlier,later,['pair','pair','b','c'],draws=10)
    assert result['dense_only']==4 and result['tasks']==4 and result['groups']==3
    assert result['auc'] is None and result['auc_valid_bootstrap_draws']==0
    later[0][7][0]=1
    result=evaluate(earlier,later,['pair','pair','b','c'],draws=10)
    assert result['dense_only']==3 and result['later_positive_in_subset']==1 and result['auc']==.5
    with pytest.raises(ValueError,match='missing task/sample'):
        evaluate([r[:7] for r in earlier],later,['pair','pair','b','c'],draws=10)
