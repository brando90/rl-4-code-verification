"""Keep the prospective independent test sample fixed through missing responses and changed scoring evidence."""
from pathlib import Path
import copy,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
import selected_coverage_inputs as m


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return m.reference(path)


def fixture(tmp_path):
    tasks=[{'task_id':f'authored_{i:03d}','split':'test','group_id':str(i//2)} for i in range(222)]
    run={'arm':'A','run_seed':13011,'boundary':4};rows=[];root=tmp_path/'scores'
    for index,cell in enumerate(m.identities([t['task_id'] for t in tasks],'test',**run)):
        row={**cell,'status':'missing_generation','attempts':0,'strict':None,'cleanup_verified':True}
        if cell['sample_idx']==0:
            if index in (16,32):
                folder=root/f'{index:05d}'/'attempt_1';folder.mkdir(parents=True)
                source=folder/'solution.lean';source.write_text('import Mathlib\n')
                row.update(status='measured',attempts=1,strict=0,compile=index==16,source_sha256=m.digest(source))
                put(folder/'evidence/oracle/oracle.json',{'compile':row['compile']})
            put(root/f'{index:05d}'/'result.json',row)
        rows.append(row)
    return tasks,{'rows':rows},root,run


def test_all_222_fixed_samples_retained_without_replacement_or_rescoring(tmp_path):
    tasks,data,root,run=fixture(tmp_path)
    # A successful alternative is not eligible to replace the missing sample 0.
    data['rows'][1].update(status='measured',strict=1)
    result=m.normalize(tasks,data,root,run,output=tmp_path/'out')
    assert result['declared']==222 and result['new_strict_measurements']==result['model_calls']==0
    assert all(c['sample_idx']==0 for c in result['cells'])
    assert result['cells'][0]['source'] is None and not result['missing_sample_replacement']
    assert [m.read(c['strict'])['compile'] for c in result['cells'][:3]]==[None,True,False]
    with pytest.raises(FileExistsError):m.normalize(tasks,data,root,run,output=tmp_path/'out')


@pytest.mark.parametrize('mutation',('duplicate','identity','cleanup','source','oracle','saved'))
def test_changed_population_or_physical_evidence_is_refused(tmp_path,mutation):
    tasks,data,root,run=fixture(tmp_path)
    if mutation=='duplicate':data['rows'][-1]=copy.deepcopy(data['rows'][0])
    elif mutation=='identity':data['rows'][1]['boundary']=3
    elif mutation=='cleanup':data['rows'][1]['cleanup_verified']=False
    elif mutation=='source':(root/'00016/attempt_1/solution.lean').write_text('changed')
    elif mutation=='oracle':put(root/'00016/attempt_1/evidence/oracle/oracle.json',{'compile':False})
    else:put(root/'00016/result.json',{})
    with pytest.raises(ValueError):m.normalize(tasks,data,root,run,output=tmp_path/'out')
    assert not (tmp_path/'out').exists()


def plan_fixture(tmp_path,monkeypatch):
    tasks,data,root,run=fixture(tmp_path);monkeypatch.setattr(m,'published',lambda ref,repo:m.read(ref))
    task_ref=put(tmp_path/'tasks.json',tasks)
    method=put(tmp_path/'method.json',{'gate':'SELECTED_TEST_ANALYSIS','condition':'v2-S2','status':'FROZEN',
        'tasks':task_ref,'bindings':[task_ref],'independent_coverage':{'sample_idx':0,'tasks_per_run':222}})
    L2=put(tmp_path/'L2.json',{'gate':'L2','condition':'v2-S2','status':'FROZEN',
        'eligible_arms':['A','B','P'],'main_seeds':[13011,13012,13013],
        'bindings':[method,m.reference(PHASE/'selected_coverage_inputs.py'),m.reference(PHASE/'evaluation_contract.py')]})
    shared={'condition':'v2-S2',**run,'L2_sha256':L2['sha256'],'evaluation_contract_sha256':m.digest(PHASE/'evaluation_contract.py'),
        'model_binding_sha256':'model','boundary_receipt_sha256':'boundary','snapshot_sha256':'snapshot'}
    selection=put(tmp_path/'selection.json',{**shared,'gate':'VALIDATION_SELECTION','status':'SELECTED'})
    score_lock=put(tmp_path/'score_lock.json',{**shared,'gate':'EVALUATION_SCORE_INPUTS','status':'FROZEN','purpose':'test',
        'bindings':[],'configuration':{'root':str(root)}})
    scoring=put(root/'result.json',data)
    score=put(tmp_path/'score.json',{**shared,'stage':'SELECTED_TEST_SCORE','status':'INCOMPLETE','cleanup_unresolved':0,
        'scoring_lock_sha256':score_lock['sha256'],'scoring':scoring,'scoring_sha256':scoring['sha256']})
    return {'repository':'authored','L2':L2,'method':method,'selection':selection,'score':score,'score_lock':score_lock,
        'run':run,'output':str(tmp_path/'out')}


def test_published_selected_checkpoint_and_pre_main_method_admit_preparation_only(tmp_path,monkeypatch):
    plan=plan_fixture(tmp_path,monkeypatch);result=m.prepare(plan)
    assert len(result['cells'])==222 and result['model_calls']==0
    provenance=json.loads((Path(plan['output'])/'provenance.json').read_text())
    assert provenance['selection']==plan['selection'] and 'before any' in provenance['required_next']


@pytest.mark.parametrize('changed',('post_main','wrong_selection','unselected','raw_score'))
def test_unfrozen_or_wrong_checkpoint_cannot_open_coverage_inputs(tmp_path,monkeypatch,changed):
    plan=plan_fixture(tmp_path,monkeypatch)
    if changed=='raw_score':Path(m.read(plan['score'])['scoring']['path']).write_text('{}')
    else:
        key='L2' if changed=='post_main' else 'selection';value=m.read(plan[key])
        if changed=='post_main':value['bindings']=[]
        elif changed=='wrong_selection':value['model_binding_sha256']='other'
        else:value['status']='INCONCLUSIVE'
        plan[key]=put(Path(plan[key]['path']),value)
    with pytest.raises(ValueError):m.prepare(plan)
    assert not Path(plan['output']).exists()


def test_normalized_sample_evidence_rejoins_the_full_published_population(tmp_path):
    tasks,data,root,run=fixture(tmp_path);inputs=m.normalize(tasks,data,root,run,output=tmp_path/'out')
    assert m.verify_evidence(inputs,tasks,data,root,run)
    data['rows'].pop()
    with pytest.raises(ValueError,match='population changed'):m.verify_evidence(inputs,tasks,data,root,run)


@pytest.mark.parametrize('changed',('source_copy','receipt_copy','modified_normalized'))
def test_equal_bytes_elsewhere_or_changed_normalized_outcome_cannot_replace_saved_evidence(tmp_path,changed):
    tasks,data,root,run=fixture(tmp_path);inputs=m.normalize(tasks,data,root,run,output=tmp_path/'out')
    cell=inputs['cells'][1];strict=m.read(cell['strict'])
    if changed=='source_copy':
        path=tmp_path/'elsewhere.lean';path.write_bytes(Path(cell['source']['path']).read_bytes());cell['source']=m.reference(path)
    elif changed=='receipt_copy':
        strict['strict_receipt']=put(tmp_path/'elsewhere.json',m.read(strict['strict_receipt']))
        cell['strict']=put(Path(cell['strict']['path']),strict)
    else:
        strict['strict']=1;cell['strict']=put(Path(cell['strict']['path']),strict)
    with pytest.raises(ValueError,match='selected|published'):m.verify_evidence(inputs,tasks,data,root,run)
