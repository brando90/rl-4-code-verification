"""Require prospective authority and complete evidence before one independent-coverage analysis on synthetic populations."""
from pathlib import Path
import json
import sys
import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import selected_coverage_analysis_driver as m
import selected_coverage_join as join
import selected_analysis_driver as strict


def put(path,value):
    path.write_text(json.dumps(value))
    return {'path':str(path),'sha256':m.digest(path),'revision':'authored'}


def fixture(tmp_path,monkeypatch):
    for module in (m,join,strict):
        monkeypatch.setattr(module,'published',lambda ref,repo:m.read(ref))
    tasks=[{'task_id':f'authored_{i:03d}','split':'test','group_id':str(i//2),
            'domain':'core' if i<152 else 'IndustrySet'} for i in range(222)]
    task_ref=put(tmp_path/'tasks.json',tasks)
    names=('selected_coverage_analysis_driver.py','selected_coverage_analysis.py','selected_coverage_join.py',
           'selected_analysis_driver.py','selected_test_analysis.py','evaluation_contract.py')
    methods=[{'path':str(PHASE/name),'sha256':m.digest(PHASE/name)} for name in names]
    method=put(tmp_path/'method.json',{'gate':'SELECTED_TEST_COVERAGE_ANALYSIS','condition':'v2-S2','status':'FROZEN',
        'arms':['A','B','P'],'seeds':list(m.SEEDS),'sample_idx':0,'bootstrap_seed':1302301,'tasks':task_ref,'bindings':[task_ref,*methods]})
    main=put(tmp_path/'L2.json',{'gate':'L2','condition':'v2-S2','status':'FROZEN','eligible_arms':['A','B','P'],
        'main_seeds':list(m.SEEDS),'bindings':[method,*methods]})
    runs=[]
    for arm in ('A','B','P'):
        for seed in m.SEEDS:
            result=put(tmp_path/f'{arm}_{seed}.json',{'stage':'MAIN_TRAINING','condition':'v2-S2',
                'arm':arm,'run_seed':seed,'L2_sha256':main['sha256'],'status':'HALTED'})
            runs.append({'arm':arm,'run_seed':seed,'main_result':result})
    inputs=put(tmp_path/'inputs.json',{'gate':'SELECTED_TEST_COVERAGE_ANALYSIS_INPUTS','condition':'v2-S2',
        'status':'FROZEN','method':method,'L2':main,'runs':runs,'bindings':[r['main_result'] for r in runs]})
    return {'repository':'authored','inputs':inputs,'output':str(tmp_path/'analysis')}


def test_complete_missing_population_analyzed_once_without_model_calls(tmp_path,monkeypatch):
    plan=fixture(tmp_path,monkeypatch)
    result=m.run(plan)
    assert len(result['run_availability'])==9 and result['model_calls']==0
    assert len(json.loads((Path(plan['output'])/'rows.json').read_text()))==1998
    formal=result['populations']['pooled']['formal_specification_coverage']
    assert formal['arms']['A']['declared']==666 and formal['arms']['A']['missing']==666
    assert formal['contrasts']['B-A']['full_manifest_difference_bounds']==[-1,1]
    assert result['noninferiority_established'] is False
    with pytest.raises(FileExistsError):m.run(plan)


@pytest.mark.parametrize('change',['post_main_method','unbound_source','changed_metadata','sample'])
def test_changed_authority_rejects_before_analysis(tmp_path,monkeypatch,change):
    plan=fixture(tmp_path,monkeypatch);inputs=m.read(plan['inputs'])
    if change=='post_main_method':
        main=m.read(inputs['L2']);main['bindings']=main['bindings'][1:]
        inputs['L2']=put(Path(inputs['L2']['path']),main)
    elif change=='unbound_source':inputs['bindings']=inputs['bindings'][:-1]
    elif change=='changed_metadata':
        method=m.read(inputs['method']);path=Path(method['tasks']['path']);path.write_text(path.read_text()+' ')
    else:
        method=m.read(inputs['method']);method['sample_idx']=1
        inputs['method']=put(Path(inputs['method']['path']),method)
        main=m.read(inputs['L2']);main['bindings'][0]=inputs['method']
        inputs['L2']=put(Path(inputs['L2']['path']),main)
    plan['inputs']=put(Path(plan['inputs']['path']),inputs)
    with pytest.raises(ValueError):m.run(plan)
    assert not Path(plan['output']).exists()
