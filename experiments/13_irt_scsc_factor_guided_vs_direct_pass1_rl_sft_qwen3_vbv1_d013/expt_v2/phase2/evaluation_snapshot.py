"""Freeze a complete historical-sampler evaluation population only for an admitted retained main checkpoint."""
from __future__ import annotations

import json
from pathlib import Path

from learning_driver import authorize as learning_authority
from learning_report import checkpoint
from evaluation_contract import identities,render,POPULATIONS
from evaluation_generation import validate_manifest
from technical_ledger import published
from technical_driver import bindings,read
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def selection_authority(plan,main,execution,repository):
    purpose=plan['purpose'];boundary=plan['boundary'];run=plan['learning']['run']
    if purpose not in POPULATIONS or boundary not in (1,2,3,4):raise ValueError('undeclared evaluation split or checkpoint')
    value=main['boundaries'][str(boundary)]
    if purpose=='test':
        selected=published(plan['selection'],repository);analysis=published(plan['analysis_lock'],repository)
        expected={'gate':'VALIDATION_SELECTION','condition':'v2-S2','status':'SELECTED','arm':run['arm'],
            'run_seed':run['run_seed'],'boundary':boundary,'L2_sha256':run['execution_lock']['sha256'],
            'model_binding_sha256':value['model_binding_sha256'],'boundary_receipt_sha256':value['sha256']}
        if any(selected.get(k)!=v for k,v in expected.items()):raise ValueError('test checkpoint was not selected for this main run')
        science={b['path']:b['sha256'] for b in execution['bindings']}
        if (analysis.get('gate'),analysis.get('condition'),analysis.get('status'))!=('SELECTED_TEST_ANALYSIS','v2-S2','FROZEN'):
            raise ValueError('test analysis must be frozen before main outcomes')
        if science.get(plan['analysis_lock']['path'])!=plan['analysis_lock']['sha256']:
            raise ValueError('analysis lock was not bound before main training')
        if selected.get('evaluation_contract_sha256')!=digest(HERE/'evaluation_contract.py'):
            raise ValueError('selected checkpoint used a different evaluation contract')
    return value


def manifest(task_ids,tasks,tokenizer,veribench,*,purpose,arm,run_seed,boundary):
    ids=sorted(task_ids);cells=identities(ids,purpose,arm=arm,run_seed=run_seed,boundary=boundary)
    table={t.task_id:t for t in tasks}
    if len(table)!=len(tasks) or set(table)!=set(ids):raise ValueError('complete evaluation prompt population required')
    prompts={}
    for key in ids:
        value=render(table[key].instruction,tokenizer,veribench)
        prompts[key]={**{k:v for k,v in value.items() if k!='text'},'prompt_text':value['text'],
            'prompt_token_ids':list(tokenizer.encode(value['text']))}
    result={'condition':'v2-S2','purpose':purpose,'arm':arm,'run_seed':run_seed,'boundary':boundary,
            'cells':[{**cell,**prompts[cell['task_id']]} for cell in cells]}
    validate_manifest(result,ids);return result


def freeze(plan):
    learning=plan['learning'];lp,execution,config=learning_authority(learning);run=learning['run'];repository=run['repository']
    if run['phase']!='main':raise ValueError('held-out evaluation requires an admitted main run')
    scientific={b['path']:b['sha256'] for b in execution['bindings']}
    required=(Path(__file__).resolve(),HERE/'evaluation_contract.py',HERE/'evaluation_generation.py',
              HERE/'learning_report.py',HERE/'evaluation_selection.py')
    if any(scientific.get(str(p))!=digest(p) for p in required):raise ValueError('evaluation method was not frozen before main')
    main=published(plan['main_result'],repository)
    expected={'condition':'v2-S2','stage':'MAIN_TRAINING','status':'COMPLETE','arm':run['arm'],'run_seed':run['run_seed'],
              'L2_sha256':run['execution_lock']['sha256'],'boundaries_accounted':4,'cleanup_unresolved':0}
    if any(main.get(k)!=v for k,v in expected.items()):raise ValueError('complete clean main training publication required')
    boundary_ref=selection_authority(plan,main,execution,repository);boundary=read(boundary_ref)
    model_sha=checkpoint(boundary,config,scientific)
    if model_sha!=boundary_ref['model_binding_sha256']:raise ValueError('published main boundary model changed')
    evaluation=config['evaluation'];purpose=plan['purpose'];allow=evaluation['allowlists'][purpose]
    if scientific.get(allow['path'])!=allow['sha256']:raise ValueError('evaluation allowlist was not frozen before main')
    if digest(allow['path'])!=allow['sha256']:raise ValueError('evaluation task membership changed')
    from rl4cv.veribench.pack import read_task_ids,load_pack
    task_ids=read_task_ids(allow['path'])
    paths=[Path(evaluation['pack'])/key/'instruction.md' for key in task_ids]
    if any(scientific.get(str(p))!=digest(p) for p in paths):raise ValueError('evaluation prompt source was not bound before main')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(config['runtime']['tokenizer'],local_files_only=True)
    # No held-out prompt is loaded before main/selection/analysis authority above.
    prepared=manifest(task_ids,load_pack(evaluation['pack'],task_ids),tokenizer,evaluation['veribench'],purpose=purpose,
        arm=run['arm'],run_seed=run['run_seed'],boundary=plan['boundary'])
    root=Path(evaluation['root'])/run['arm']/str(run['run_seed'])/f"{purpose}_b{plan['boundary']}"
    destination=root/'freeze';destination.mkdir(parents=True,exist_ok=False)
    write_new(destination/'manifest.json',prepared)
    sources={Path(b['path']) for b in execution['bindings']}|set(paths)|{destination/'manifest.json',Path(boundary_ref['path']),Path(plan['main_result']['path'])}
    sources.update(Path(b['path']) for b in boundary['export_files'])
    if purpose=='test':sources.update(Path(plan[k]['path']) for k in ('selection','analysis_lock'))
    lock={'condition':'v2-S2','gate':'EVALUATION_SNAPSHOT','status':'FROZEN','purpose':purpose,
        'arm':run['arm'],'run_seed':run['run_seed'],'boundary':plan['boundary'],'declared':len(prepared['cells']),
        'LP_sha256':run['LP']['sha256'],'L2_sha256':run['execution_lock']['sha256'],
        'main_result':plan['main_result'],'selection':plan.get('selection'),'analysis_lock':plan.get('analysis_lock'),
        'model':boundary['model'],'model_binding_sha256':model_sha,'boundary_receipt_sha256':boundary_ref['sha256'],
        'evaluation_contract_sha256':digest(HERE/'evaluation_contract.py'),'bindings':bindings(sources),
        'configuration':{'root':str(root),'manifest':str(destination/'manifest.json'),'allowlist':allow['path'],
            'learning_configuration':learning['configuration']},'scientific_measurements':0,'model_calls':0}
    target=HERE.parent/'locks'/f"EVALUATION_S2_{run['arm']}_{run['run_seed']}_{purpose}_b{plan['boundary']}.json"
    write_new(target,lock)
    return {'status':'PREPARED_FOR_PUBLICATION','path':str(target),'sha256':digest(target),
            'purpose':purpose,'declared':len(prepared['cells']),'model_calls':0}
