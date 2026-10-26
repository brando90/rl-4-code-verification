"""Retain failed runs, partial rollout costs and all exact main token-boundary identities."""
from pathlib import Path
import importlib.util,json,sys
import pytest
PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE));spec=importlib.util.spec_from_file_location('e13_learning_report',PHASE/'learning_report.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return {'path':str(path),'sha256':m.digest(path)}


def fixture(tmp_path,phase='pilot',count=1):
    state={'condition':'v2-S2','arm':'A','run_seed':1301 if phase=='pilot' else 13011,'phase':phase,
           'status':'COMPLETE','completed_updates':count,'optimizer_updates':count,'generated_tokens':16*count}
    for update in range(1,count+1):
        root=tmp_path/f'update_{update:05d}'
        rows=[{'cell_id':str(i),'status':'measured','strict':int(i==0),'cleanup_verified':True} for i in range(8)]
        scoring=put(root/'score/cells/result.json',{'rows':rows})
        put(root/'score/result.json',{'arm':'A','seed':state['run_seed'],'update':update,'declared':8,'measured':8,
            'strict_successes':1,'scoring':scoring})
        put(root/'opportunity.json',{'status':'ACCOUNTED','update':update,'arm':'A','run_seed':state['run_seed'],
            'phase':phase,'optimizer_updates':1,'generated_tokens':16,'complete_groups':1,'state_after':{'execution_sha256':'execution'}})
        for stage in ('generate','update','export'):
            put(root/stage/'dispatch/result.json',{'status':'RUNTIME_EXITED_ZERO','cleanup_verified':True})
        for index in range(8):put(root/'generate/output'/f'{index:05d}.generation.json',{'output_token_ids':[1,2]})
    return state


def test_failed_run_retains_partial_opportunity_tokens_without_counting_an_update(tmp_path):
    state=fixture(tmp_path);state.update(status='HALTED',failed_stage='update',error_type='RuntimeError')
    put(tmp_path/'update_00002/generate/output/00000.generation.json',{'output_token_ids':[1,2,3]})
    result,sources=m.summarize(tmp_path,state,{},'execution',{})
    assert result['status']=='HALTED' and result['optimizer_updates']==1
    assert result['all_retained_rollout_tokens']==19 and result['partial_opportunity_tokens']==3
    assert result['completed_learning_tokens']==16 and result['evaluation_pending']
    assert result['failed_stage']=='update' and len(result['trajectories'])==1


def test_main_completion_requires_every_token_boundary(tmp_path):
    state=fixture(tmp_path,phase='main')
    with pytest.raises(ValueError,match='four token boundaries'):m.summarize(tmp_path,state,{},'execution',{})


def test_four_main_boundary_receipts_remain_tied_to_exact_models(tmp_path,monkeypatch):
    state=fixture(tmp_path,phase='main',count=4)
    for index in range(1,5):
        put(tmp_path/f'update_{index:05d}/boundary.json',{'arm':'A','seed':13011,'boundary':index,
            'model':f'authored-model-{index}','generated_tokens':16*index,'target':16*index,'overshoot':0,'completed_updates':index})
    monkeypatch.setattr(m,'checkpoint',lambda value,*_:str(value['boundary'])*64)
    result,sources=m.summarize(tmp_path,state,{},'execution',{})
    assert result['stage']=='MAIN_TRAINING' and result['boundaries_accounted']==4
    assert result['boundaries']['3']['model_binding_sha256']=='3'*64
    assert result['optimizer_updates']==4 and result['all_retained_rollout_tokens']==64
    assert not result['efficacy_claim']


def test_terminal_counts_cannot_disagree_with_retained_scores(tmp_path):
    state=fixture(tmp_path);state['generated_tokens']=17
    with pytest.raises(ValueError,match='terminal learning counters'):m.summarize(tmp_path,state,{},'execution',{})


def test_unupdated_boundary_checks_physical_model_bytes(tmp_path):
    model=tmp_path/'initial';model.mkdir();weights=model/'weights.bin';weights.write_bytes(b'authored weights')
    ref={'path':str(weights),'sha256':m.digest(weights)}
    manifest=put(tmp_path/'manifest.json',{'bindings':[ref]})
    config={'runtime':{'initial_model':str(model)},'initial_model_manifest':manifest}
    boundary={'model':str(model),'export_files':[ref]}
    assert m.checkpoint(boundary,config,{str(weights):ref['sha256']})==manifest['sha256']
    weights.write_bytes(b'changed')
    with pytest.raises(ValueError,match='model changed'):m.checkpoint(boundary,config,{str(weights):ref['sha256']})
