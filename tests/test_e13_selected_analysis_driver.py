"""Keep all paired test slots, original checkpoint authority and prospective analysis finality across failed runs."""
from pathlib import Path
import copy,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import selected_analysis_driver as m


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return {'path':str(path),'sha256':m.digest(path),'revision':'authored'}


def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(m,'published',lambda ref,repo:m.read(ref))
    tasks=[{'task_id':f'authored_{i:03d}','split':'test','group_id':str(i//2),'domain':'core' if i<152 else 'IndustrySet'} for i in range(222)]
    runs=[]
    for arm in ['A','B','P']:
        for seed in m.SEEDS:
            main={'condition':'v2-S2','stage':'MAIN_TRAINING','arm':arm,'run_seed':seed,'L2_sha256':'L2','status':'HALTED'}
            runs.append({'arm':arm,'run_seed':seed,'main_result':put(tmp_path/f'{arm}_{seed}_main.json',main)})
    r=runs[0];main=m.read(r['main_result']);main.update(status='COMPLETE',cleanup_unresolved=0,boundaries={'4':{'model_binding_sha256':'model','sha256':'boundary'}})
    r['main_result']=put(Path(r['main_result']['path']),main)
    selection={'gate':'VALIDATION_SELECTION','condition':'v2-S2','arm':'A','run_seed':13011,'L2_sha256':'L2',
        'evaluation_contract_sha256':m.digest(PHASE/'evaluation_contract.py'),'status':'SELECTED','boundary':4,
        'model_binding_sha256':'model','boundary_receipt_sha256':'boundary'}
    r['selection']=put(tmp_path/'selection.json',selection)
    population=m.identities([t['task_id'] for t in tasks],'test',arm='A',run_seed=13011,boundary=4)
    rows=[{**c,'status':'measured','strict':i%2} for i,c in enumerate(population)]
    rows[0].update(status='deterministic_resource_limit',strict=None)
    scoring=put(tmp_path/'scoring.json',{'rows':rows})
    score={**selection,'stage':'SELECTED_TEST_SCORE','status':'INCOMPLETE','cleanup_unresolved':0,'scoring':scoring,
        'scoring_sha256':scoring['sha256'],'summary':{'declared':3552,'measured':3551,'missing':1,'successes':1776,'task_count':222,'samples_per_task':16}}
    r['test_score']=put(tmp_path/'score.json',score)
    return runs,tasks


def collect(runs,tasks):return m.collect(runs,tasks,['A','B','P'],'L2',m.digest(PHASE/'evaluation_contract.py'),'authored')


def test_failed_main_runs_keep_every_paired_slot_and_missing_score(tmp_path,monkeypatch):
    runs,tasks=fixture(tmp_path,monkeypatch);rows,refs,availability=collect(runs,tasks)
    assert len(rows)==3*3*222*16 and sum(r['strict'] is not None for r in rows)==3551
    assert sum(r['status']=='not_evaluated' for r in rows)==8*3552
    assert len(availability)==9 and availability[1]['not_evaluated_reason']=='main HALTED'
    assert m.read(runs[0]['test_score'])['scoring'] in refs


def test_wrong_selected_model_and_duplicate_raw_slot_are_refused(tmp_path,monkeypatch):
    runs,tasks=fixture(tmp_path,monkeypatch);ref=runs[0]['selection'];v=m.read(ref);v['model_binding_sha256']='other'
    runs[0]['selection']=put(Path(ref['path']),v)
    with pytest.raises(ValueError,match='retained main boundary'):collect(runs,tasks)
    v['model_binding_sha256']='model';runs[0]['selection']=put(Path(ref['path']),v)
    ref=runs[0]['test_score'];v=m.read(ref);data=m.read(v['scoring']);data['rows'][-1]=copy.deepcopy(data['rows'][0])
    v['scoring']=put(Path(v['scoring']['path']),data);v['scoring_sha256']=v['scoring']['sha256'];runs[0]['test_score']=put(Path(ref['path']),v)
    with pytest.raises(ValueError,match='omitted declared cells'):collect(runs,tasks)


def test_inconclusive_selection_and_unstarted_runs_remain_missing(tmp_path,monkeypatch):
    runs,tasks=fixture(tmp_path,monkeypatch);r=runs[0];v=m.read(r['selection']);v.update(status='INCONCLUSIVE',boundary=None)
    r['selection']=put(Path(r['selection']['path']),v);del r['test_score']
    other=runs[1];main=m.read(other['main_result']);main.update(status='NOT_STARTED',blocked_by=runs[2]['main_result'])
    other['main_result']=put(Path(other['main_result']['path']),main)
    rows,refs,_=collect(runs,tasks);assert len(rows)==31968 and all(r['strict'] is None for r in rows)
    assert runs[2]['main_result'] in refs


def test_selected_but_unavailable_test_requires_retained_same_run_reason(tmp_path,monkeypatch):
    runs,tasks=fixture(tmp_path,monkeypatch);r=runs[0];del r['test_score']
    value={'stage':'SELECTED_TEST_UNAVAILABLE','condition':'v2-S2','status':'NOT_EVALUATED','arm':'A','run_seed':13011,
        'boundary':4,'L2_sha256':'L2','reason':'fixed resource allowance exhausted'}
    r['unavailable']=put(tmp_path/'unavailable.json',value)
    rows,_,_=collect(runs,tasks);assert all(r['boundary']==4 for r in rows[:3552]) and all(r['strict'] is None for r in rows)
    value['run_seed']=13012;r['unavailable']=put(Path(r['unavailable']['path']),value)
    with pytest.raises(ValueError,match='another checkpoint'):collect(runs,tasks)


def test_missing_run_or_imputed_unmeasured_cell_is_refused(tmp_path,monkeypatch):
    runs,tasks=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='all declared'):collect(runs[:-1],tasks)
    r=runs[0];v=m.read(r['test_score']);data=m.read(v['scoring']);data['rows'][0]['strict']=0
    v['scoring']=put(Path(v['scoring']['path']),data);v['scoring_sha256']=v['scoring']['sha256'];r['test_score']=put(Path(r['test_score']['path']),v)
    with pytest.raises(ValueError,match='imputed'):collect(runs,tasks)


def analysis_plan(tmp_path,monkeypatch):
    runs,tasks=fixture(tmp_path,monkeypatch);task_ref=put(tmp_path/'tasks.json',tasks)
    methods=[{'path':str(PHASE/name),'sha256':m.digest(PHASE/name)} for name in ('selected_analysis_driver.py','selected_test_analysis.py','evaluation_contract.py')]
    method=put(tmp_path/'method.json',{'gate':'SELECTED_TEST_ANALYSIS','condition':'v2-S2','status':'FROZEN',
        'arms':['A','B','P'],'seeds':list(m.SEEDS),'bootstrap_seed':1302301,'tasks':task_ref,'bindings':[task_ref,*methods]})
    main=put(tmp_path/'L2.json',{'gate':'L2','condition':'v2-S2','status':'FROZEN','eligible_arms':['A','B','P'],'main_seeds':list(m.SEEDS),'bindings':[method,*methods]})
    for r in runs:
        for key in ('main_result','selection','test_score'):
            if key in r:
                ref=r[key];v=m.read(ref);v['L2_sha256']=main['sha256'];r[key]=put(Path(ref['path']),v)
    _,refs,_=m.collect(runs,tasks,['A','B','P'],main['sha256'],m.digest(PHASE/'evaluation_contract.py'),'authored')
    lock=put(tmp_path/'inputs.json',{'gate':'SELECTED_TEST_ANALYSIS_INPUTS','condition':'v2-S2','status':'FROZEN',
        'method':method,'L2':main,'runs':runs,'bindings':refs})
    return {'repository':'authored','inputs':lock,'output':str(tmp_path/'analysis')}


def test_analysis_is_exclusive_and_uses_only_pre_main_method(tmp_path,monkeypatch):
    plan=analysis_plan(tmp_path,monkeypatch);calls=[]
    def evaluate(rows,tasks,arms,bootstrap_seed):
        m.validate(rows,tasks,arms);calls.append(bootstrap_seed);return {'condition':'v2-S2'}
    monkeypatch.setattr(m,'evaluate',evaluate)
    result=m.run(plan);assert calls==[1302301] and len(result['run_availability'])==9
    with pytest.raises(FileExistsError):m.run(plan)
    assert calls==[1302301]


def test_post_main_method_or_changed_metadata_cannot_analyze(tmp_path,monkeypatch):
    plan=analysis_plan(tmp_path,monkeypatch);inputs=m.read(plan['inputs']);main=m.read(inputs['L2']);main['bindings']=main['bindings'][1:]
    inputs['L2']=put(Path(inputs['L2']['path']),main);plan['inputs']=put(Path(plan['inputs']['path']),inputs)
    with pytest.raises(ValueError,match='not frozen before main'):m.run(plan)
    assert not Path(plan['output']).exists()


def test_changed_pre_main_task_metadata_is_refused_before_analysis(tmp_path,monkeypatch):
    plan=analysis_plan(tmp_path,monkeypatch);inputs=m.read(plan['inputs']);method=m.read(inputs['method'])
    task=Path(method['tasks']['path']);task.write_text(task.read_text()+' ')
    with pytest.raises(ValueError,match='binding changed'):m.run(plan)
    assert not Path(plan['output']).exists()
