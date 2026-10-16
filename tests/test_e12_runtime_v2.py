"""Verify v2 runtime bookkeeping, probe isolation, bounded retry, cache identity and primary cohorts."""
import hashlib
import json
from pathlib import Path
import sys
import pytest

SCRIPTS=Path(__file__).resolve().parents[1]/'experiments/12_scsc_vs_hidden_gold_tests_vbv1_across_systems/expt_v2/scripts'
sys.path.insert(0,str(SCRIPTS))
from runtime_v2 import Runtime
from adapter_v2 import declarations, cell_outcome, per_test_plan
from support_v2 import atomic_json, workers_allowed
import evaluate_v2 as ev
import controls_v2 as ctl
from analyze_v2 import cohort, p23, fraction_ci
import numpy as np


def suite():
    gold='def f (x : Nat) : Nat := x\n'
    return {'task_id':'t','symbols':declarations(gold)[0], 'n_tests':2,
            'tests':[{'statement':'f 1 = 1','symbols':{'f':'f'}},
                     {'statement':'f 2 = 2','symbols':{'f':'f'}}]}


class FakeRuntime(Runtime):
    def lean(self,path,extra=()):
        return {'status':'error','outputs':{0:True},'returncode':1}


def test_partial_runtime_is_missing_not_failure(tmp_path):
    rt=FakeRuntime(tmp_path)
    out=rt.evaluate(suite(),'def f (x : Nat) : Nat := x\n','Test',{'status':'ok'})
    assert out['hidden_all_pass'] is None and out['hidden_all_evaluable_pass'] is True
    assert out['n_type_unknown']==1 and out['n_evaluable']==1 and not out['fully_applicable']
    assert [r['status'] for r in out['per_test']]==['pass','type_unknown']


def test_compile_error_does_not_launch_hidden_bridge(tmp_path):
    rt=Runtime(tmp_path)
    rt.lean=lambda *a:pytest.fail('must not launch bridge')
    out=rt.evaluate(suite(),'def f (x : Nat) : Nat := x\n','Bad',{'status':'error'})
    assert out['n_evaluable']==0 and out['hidden_all_pass'] is None


def test_probe_contains_arguments_but_no_expected_values(tmp_path):
    su=suite();su['tests'][0]['statement']='f 1 = 99999'
    source='def first (x : Nat) : Nat := x\ndef alternate (x : Nat) : Nat := x\n'
    rt=Runtime(tmp_path);seen=[]
    def lean(path,extra=()):
        text=path.read_text();seen.append((path.name,text))
        return {'status':'ok','outputs':{0:True,1:True},'returncode':0}
    rt.lean=lean
    out=rt.evaluate(su,source,'Candidate',{'status':'ok'})
    probes=[text for name,text in seen if '_Agreement_' in name]
    assert probes and all('99999' not in text for text in probes)
    assert all(d['step']==3 for d in out['diagnostics'])
    assert any('99999' in text for name,text in seen if '_Bridge' in name)


def row():
    return {'panel':'primary','system':'s','task_id':'t','recorded_compiles':True,'join_status':'bound',
            'IC_tests':1.,'IC_proofs':1.,'FSC':1.,'subset':'Core614','source_status':'ok'}


def test_noncompiling_and_no_tests_are_distinct():
    r={**row(),'recorded_compiles':False}
    a=ev.make_record(r,suite());assert a['hidden_all_pass']==0 and a['hidden_pass_rate']==0
    b=ev.make_record(r,{**suite(),'n_tests':0,'tests':[]})
    assert b['status']=='no_tests' and b['hidden_all_pass'] is None


def test_resume_jsonl_archives_incomplete_tail(tmp_path):
    p=tmp_path/'cells.jsonl';p.write_bytes(b'{"x":1}\n{"x":')
    assert ev.recover_jsonl(p)==[{'x':1}]
    assert p.read_bytes()==b'{"x":1}\n' and len(list(tmp_path.glob('*.partial_tail.*')))==1


def test_reuse_requires_source_hash_and_success_receipt(tmp_path):
    rt=Runtime(tmp_path/'new');old=tmp_path/'old';modules=old/'evaluation_A2/modules';modules.mkdir(parents=True)
    raw=b'def f : Nat := 1\n';sha=hashlib.sha256(raw).hexdigest();r={**row(),'sha256':sha}
    key=hashlib.sha256(('t:'+sha).encode()).hexdigest();mod='E12Eval'+key[:24]
    (modules/(mod+'.lean')).write_bytes(raw);(modules/(mod+'.olean')).write_bytes(b'compiled')
    atomic_json(old/'evaluation_A2'/(key+'.json'),{'input_sha256':sha,'compile':{'status':'ok'}})
    assert ev.reuse_module(rt,r,mod,old)['reused']
    assert (rt.root/'modules'/(mod+'.olean')).read_bytes()==b'compiled'
    (modules/(mod+'.lean')).write_text('changed')
    assert ev.reuse_module(rt,r,mod,old) is None


def test_infra_retry_is_bounded_and_resume_reuses_receipt(tmp_path,monkeypatch):
    rt=Runtime(tmp_path/'runtime');candidate=tmp_path/'candidate.lean';candidate.write_text('def f (x : Nat) : Nat := x\n')
    r={**row(),'path':str(candidate),'sha256':ev.digest(candidate)}
    key=hashlib.sha256(('t:'+r['sha256']).encode()).hexdigest();calls=[]
    def evaluate(*args):
        calls.append(1);return {'compile':{'status':'error','returncode':-9},'diagnostics':[]}
    rt.evaluate=evaluate
    ev.evaluate_group(rt,(key,[r]),{'t':suite()},tmp_path/'no_old')
    assert len(calls)==2
    ev.evaluate_group(rt,(key,[r]),{'t':suite()},tmp_path/'no_old')
    assert len(calls)==2


def test_resume_rejects_changed_runtime_receipt(tmp_path):
    rt=Runtime(tmp_path);r={**row(),'sha256':'abc'}
    atomic_json(tmp_path/'key.json',{'runtime_hashes':{},'input_sha256':'abc','task_id':'t'})
    with pytest.raises(AssertionError):ev.evaluate_group(rt,('key',[r]),{})


def test_primary_vs_sensitivity_cohort():
    r={**row(),'compiles':True,'applicable':True,'fully_applicable':False,'hidden_all_pass':None,
       'hidden_all_evaluable_pass':True,'hidden_pass_rate':1.,'all_mappings_unambiguous':True}
    assert not cohort([r])[0]['applicable']
    assert cohort([r],True)[0]['hidden_all_pass'] is True
    assert p23([r],np.random.default_rng(2),draws=3)['n_cells']==0
    assert p23([r],np.random.default_rng(2),draws=3,any_evaluable=True)['n_cells']==1


def test_fraction_bootstrap_resamples_tasks_with_all_systems():
    rows=[{'task_id':'a','good':True},{'task_id':'a','good':False},{'task_id':'b','good':True}]
    out=fraction_ci(rows,lambda r:r['good'],lambda r:True,np.random.default_rng(1),draws=100)
    assert out['n']==2 and out['denominator']==3 and out['fraction']==pytest.approx(2/3)
    assert out['task_bootstrap_95']['low']==.5 and out['task_bootstrap_95']['high']==1.


def test_controls_require_50_compiling_mutants():
    r={'task_id':'t','n_tests':2,'C1':{'n_pass':2,'all_pass':True},
       'C2':{'all_symbols_mapped':True,'all_pass':True},'C3':{'compile':{'status':'ok'},'killed':True},'C4':{'rejected':True}}
    out=ctl.report([r],[r]);assert not out['C3']['passes'] and not out['all_controls_pass']


def test_workers_reject_high_load(monkeypatch):
    monkeypatch.setattr('support_v2.os.getloadavg',lambda:(21.,0.,0.))
    assert workers_allowed(2)==2
    with pytest.raises(ValueError):workers_allowed(4)


def test_bounds_retain_every_declared_cell_and_separate_no_test_exclusion():
    from analyze_v2 import system_table
    failed=ev.make_record({**row(),'recorded_compiles':False},suite())
    no_tests=ev.make_record({**row(),'task_id':'no_test'},{**suite(),'n_tests':0,'tests':[]})
    table=system_table([failed,no_tests])[0]
    assert table['n_declared']==2 and table['n_no_tests']==1
    assert table['hidden_bounds']==[0.,0.]
    assert table['hidden_bounds_all_declared']==[0.,.5]
