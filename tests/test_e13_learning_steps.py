"""Exercise pre-response plans, changed-export rejection and complete/missing update accounting."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

PHASE=Path(__file__).resolve().parents[1]/'experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2/phase2'
sys.path.insert(0,str(PHASE))
spec=importlib.util.spec_from_file_location('e13_learning_steps',PHASE/'learning_steps.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from training_checkpoint import file_bindings


def fixture(tmp_path):
    train=tmp_path/'train';train.write_text('authored_a\nauthored_b\n')
    prompts=tmp_path/'prompts.json';prompts.write_text(json.dumps({t:{'task_id':t,'split':'train',
        'prompt_token_ids':[12,13],'required_paths':['/authored.lean']} for t in train.read_text().splitlines()}))
    placebo=tmp_path/'placebo.json';placebo.write_text('[0,0.2,1]')
    model=tmp_path/'initial';model.mkdir();(model/'weights.bin').write_bytes(b'authored')
    config={'runtime':{'train_ids':str(train)},'train_prompts':m.reference(prompts),'placebo_distribution':m.reference(placebo),
            'scoring':{'train_ids':str(train),'controller_fence':str(tmp_path/'score.lock')},
            'token_budget':{'targets':[10,20,30,40]}}
    state={'group_index':0,'update':1,'boundary_index':0,'generated_tokens':0,'optimizer_updates':0,
           'model':str(model),'checkpoint':None}
    run={'phase':'pilot','arm':'A','run_seed':1301,'execution_lock':{'sha256':'execution-sha'}}
    return config,state,run


def test_paired_prefixes_and_placebo_are_durable_before_response(tmp_path):
    config,state,run=fixture(tmp_path);plans=[]
    for arm in ['A','B','P']:
        run['arm']=arm;root=tmp_path/arm
        m.prefix(config,state,run,root)
        cells=json.loads((root/'cells.json').read_text());plan=json.loads((root/'plans.json').read_text())
        assert len(cells)==256 and len(plan)==32
        plans.append([(c['task_id'],c['seed'],c['group_index']) for c in cells])
        if arm=='P':assert all(len(p['placebo_draws'])==8 for p in plan)
    assert plans[0]==plans[1]==plans[2]
    with pytest.raises(FileExistsError):m.prefix(config,state,run,tmp_path/'P')


def generation(root,cells,*,main=False):
    folder=root/'generate/output';folder.mkdir(parents=True)
    (folder/'cells.json').write_text(json.dumps(cells))
    for i,cell in enumerate(cells):
        row={**cell,'output_token_ids':[14,151645],'generation_logprobs':[-.4,-.1],
             'finish_reason':'stop','at_token_cap':False,'completion':'authored'}
        (folder/f'{i:05d}.generation.json').write_text(json.dumps(row))
    terminal={'condition':'v2-S2','status':'COMPLETE','declared':len(cells),'completed':len(cells),
              'generated_tokens':2*len(cells),'complete_groups':len(cells)//8}
    if main:terminal['budget_state_after']={'generated_tokens':2*len(cells),'group_index':len(cells)//8,
        'update_groups':len(cells)//8,'update_due':True,'boundary_crossed':True,'next_target':10,'overshoot':6}
    (folder/'result.json').write_text(json.dumps(terminal));return folder


def test_main_scores_only_actual_complete_prefix_with_no_missing_reward_refill(tmp_path,monkeypatch):
    config,state,run=fixture(tmp_path);run['phase']='main';run['run_seed']=13011
    root=tmp_path/'update';m.prefix(config,state,run,root/'prefix')
    cells=json.loads((root/'prefix/cells.json').read_text())[:8];generation(root,cells,main=True)
    def scorer(cells,config,bound,execution):
        directory=Path(config['root']);directory.mkdir(parents=True)
        rows=[{**c,'status':'measured','strict':c['sample']%2,'cleanup_verified':True} for c in cells]
        rows[0].update(status='unresolved_measurement',strict=None)
        value={'rows':rows,'execution_sha256':execution};(directory/'result.json').write_text(json.dumps(value));return value
    monkeypatch.setattr(m,'score_batch',scorer)
    result=m.score(config,run,root);groups=json.loads((root/'score/groups.json').read_text())
    assert result['declared']==8 and result['complete_groups']==1 and result['measured']==7
    assert groups[0]['rows'][0]['reward'] is None and len(groups[0]['rows'])==8


def test_wholly_missing_update_retains_model_and_still_accounts_boundary_tokens(tmp_path):
    config,state,run=fixture(tmp_path);run.update(phase='main',run_seed=13011)
    root=tmp_path/'update';m.prefix(config,state,run,root/'prefix');cells=json.loads((root/'prefix/cells.json').read_text())[:8]
    generation(root,cells,main=True);out=root/'update/output';out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps({'condition':'v2-S2','status':'UNMEASURED','optimizer_updates':0}))
    updated=m.finish(state,run,root)
    assert updated['model']==state['model'] and updated['checkpoint'] is None and updated['optimizer_updates']==0
    assert updated['group_index']==1 and updated['generated_tokens']==16 and updated['boundary_index']==1
    boundary=json.loads((root/'boundary.json').read_text());assert boundary['overshoot']==6 and boundary['target']==10
    with pytest.raises(FileExistsError):m.finish(state,run,root)


def test_export_hash_and_exact_file_inventory_are_required(tmp_path):
    root=tmp_path/'export';root.mkdir();(root/'weights.bin').write_bytes(b'authored tensors')
    receipt={'condition':'v2-S2','status':'COMPLETE','bindings':file_bindings(root)}
    path=root/'export_receipt.json';path.write_text(json.dumps(receipt));sha=m.digest(path)
    assert m.verify_export(root,sha)==receipt
    (root/'generation_config.json').write_text('{}')
    with pytest.raises(ValueError,match='inventory changed'):m.verify_export(root,sha)
    (root/'generation_config.json').unlink();(root/'weights.bin').write_bytes(b'wrong tensors')
    with pytest.raises(ValueError,match='file changed'):m.verify_export(root,sha)


def test_measured_update_requires_export_from_that_native_checkpoint(tmp_path):
    config,state,run=fixture(tmp_path);root=tmp_path/'update';m.prefix(config,state,run,root/'prefix')
    cells=json.loads((root/'prefix/cells.json').read_text());generation(root,cells)
    after=root/'update/output/after';after.mkdir(parents=True);(after/'receipt.json').write_text('{}')
    result={'condition':'v2-S2','status':'MEASURED','optimizer_updates':1,'after_receipt_sha256':m.digest(after/'receipt.json')}
    (after.parent/'result.json').write_text(json.dumps(result))
    export=root/'export/output';export.mkdir(parents=True);(export/'weights.bin').write_bytes(b'authored')
    receipt={'condition':'v2-S2','status':'COMPLETE','bindings':file_bindings(export),'native_receipt_sha256':'wrong'}
    (export/'export_receipt.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='another native'):m.finish(state,run,root)
    assert not (root/'opportunity.json').exists()
