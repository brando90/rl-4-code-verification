"""Preserve selected-test hidden coverage finality, source identity and independent missingness."""
from pathlib import Path
import contextlib,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import selected_hidden as m
import selected_coverage_inputs as inputs_module
from test_e13_selected_coverage import fixture
from test_e13_selected_coverage_inputs import plan_fixture,put


def job(tmp_path,index=1):
    inputs,allowed,allow=fixture(tmp_path);cell=inputs['cells'][index]
    cell['suite']=put(tmp_path/'suite.json',{'n_tests':1,'tests':[]})
    root=tmp_path/'measurement';root.mkdir()
    return {'cell':cell,'identity':{k:cell[k] for k in m.IDENTITY},'execution_sha256':'authored',
        'root':str(root),'configuration':{'test_ids':str(allow),'lake':'unused','lake_bin':'unused'}}


@pytest.mark.parametrize('value,expected',[
    ({'status':'incomplete','fully_applicable':False,'hidden_pass_rate':1.},None),
    ({'status':'compile_failure','fully_applicable':False,'hidden_pass_rate':0.},0.),
    ({'status':'measured','fully_applicable':True,'hidden_pass_rate':.5},.5)])
def test_hidden_own_status_is_independent_of_official_compile_and_unknown_stays_missing(tmp_path,value,expected):
    data=job(tmp_path,2);calls=[]
    class Runtime:
        def __init__(self,*args):pass
        def evaluate(self,*args):calls.append(args);return value
    result=m.measure(data,Runtime)
    assert result['compile'] is False and len(calls)==1
    assert result['hidden_test_coverage']==expected and result['new_strict_measurements']==0
    assert m.read(result['hidden_receipt'])==value


def test_missing_sample_never_calls_adapter_or_chooses_another_sample(tmp_path):
    data=job(tmp_path,0)
    class Runtime:
        def __init__(self,*args):raise AssertionError('missing source must not run')
    result=m.measure(data,Runtime)
    assert result['hidden_status']=='missing_source' and result['hidden_test_coverage'] is None
    data['cell']['sample_idx']=1
    with pytest.raises(ValueError,match='fixed declared'):m.measure(data,Runtime)


def test_completed_or_interrupted_cell_is_not_implicitly_reexecuted(tmp_path):
    data=job(tmp_path);config={**data['configuration'],'root':str(tmp_path/'cells')};calls=[]
    def execute(job,root,marker,slots):
        calls.append(marker);value={**job['identity'],'status':'ACCOUNTED','cleanup_verified':True}
        m.write_new(root/'result.json',value);return value
    result=m.score_cell(data['cell'],0,config,'one',contextlib.nullcontext(),execute)
    assert m.score_cell(data['cell'],0,config,'one',contextlib.nullcontext(),execute)==result and len(calls)==1
    with pytest.raises(ValueError,match='attempt changed'):m.score_cell(data['cell'],0,config,'two',contextlib.nullcontext(),execute)
    def interrupted(*args):raise OSError('authored interruption')
    with pytest.raises(OSError):m.score_cell(data['cell'],1,config,'one',contextlib.nullcontext(),interrupted)
    recovered=m.score_cell(data['cell'],1,config,'one',contextlib.nullcontext(),execute)
    assert recovered['status']=='unresolved_measurement' and recovered['cleanup_verified'] and len(calls)==1


def parent_plan(tmp_path,monkeypatch):
    selection=plan_fixture(tmp_path,monkeypatch);monkeypatch.setattr(m,'published',lambda ref,repo:m.read(ref))
    L2=m.read(selection['L2'])
    sources=[Path(m.__file__).resolve(),*[PHASE/name for name in ('hidden_runtime.py','selected_coverage.py','selected_coverage_inputs.py','costs.py')]]
    sources.append(PHASE.parent/'phase1/score_anchor_ledger.py')
    old={b['path']:b for b in L2['bindings']};old.update({str(p):m.reference(p) for p in sources})
    L2['bindings']=list(old.values());selection['L2']=put(Path(selection['L2']['path']),L2)
    for key in ('selection','score_lock','score'):
        value=m.read(selection[key]);value['L2_sha256']=selection['L2']['sha256']
        if key=='score':value['scoring_lock_sha256']=selection['score_lock']['sha256']
        selection[key]=put(Path(selection[key]['path']),value)
    inputs=inputs_module.prepare(selection);allow=tmp_path/'allow.txt';allow.write_text('\n'.join(c['task_id'] for c in inputs['cells'])+'\n')
    suite=put(tmp_path/'suite.json',{'n_tests':0,'tests':[]})
    refs=[]
    for cell in inputs['cells']:
        cell['suite']=suite;strict=m.read(cell['strict']);refs.extend([cell['strict'],suite,strict['strict_receipt']])
        refs.extend(ref for ref in (cell.get('source'),strict.get('oracle_receipt')) if ref)
    input_ref=put(tmp_path/'hidden_inputs.json',inputs);refs += [input_ref,m.reference(allow)]
    unique={ref['path']:ref for ref in refs}
    controls=put(tmp_path/'controls.json',{'status':'PASS','cleanup_verified':True})
    config={'root':str(tmp_path/'hidden'),'controller_fence':str(tmp_path/'global.lock'),'test_ids':str(allow),'lake':'unused','lake_bin':'unused'}
    lock={'gate':'SELECTED_TEST_COVERAGE_CPU','condition':'v2-S2','status':'FROZEN','selection_plan':selection,
        'hidden_controls_result':controls,'configuration':config,'inputs':input_ref,'bindings':list(unique.values())}
    return {'lock':put(tmp_path/'lock.json',lock),'repository':'authored'}


def test_complete_parent_accounting_is_recovered_without_repeating_cells(tmp_path,monkeypatch):
    plan=parent_plan(tmp_path,monkeypatch);calls=[]
    def score(cell,index,config,sha,slots):
        calls.append(index);return {**{k:cell[k] for k in m.IDENTITY},'status':'ACCOUNTED','cleanup_verified':True}
    monkeypatch.setattr(m,'score_cell',score)
    result=m.run(plan)
    assert result['declared']==result['accounted']==222 and result['cleanup_unresolved']==0 and len(calls)==222
    assert m.run(plan)==result and len(calls)==222
    lock=m.read(plan['lock']);lock['selection_plan']['run']['boundary']=3;plan['lock']=put(Path(plan['lock']['path']),lock)
    with pytest.raises(ValueError):m.run(plan)
    assert len(calls)==222
