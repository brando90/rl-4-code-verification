"""Materialize immutable learning prefixes and join real stage results without changing frozen scientific settings."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from arm_rewards import plan_group
from training_checkpoint import digest,write_new,verify_files
from technical_driver import bindings,reference,read
from score_training import score_batch
from rollout_groups import assemble
from online_ability import refit


def verify_export(root,receipt_sha):
    root=Path(root);path=root/'export_receipt.json'
    if digest(path)!=receipt_sha:raise ValueError('generator export receipt changed')
    receipt=json.loads(path.read_text())
    if receipt.get('status')!='COMPLETE' or receipt.get('condition')!='v2-S2':raise ValueError('incomplete generator export')
    verify_files(root,receipt['bindings'])
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    if actual!={b['relative_path'] for b in receipt['bindings']}|{'export_receipt.json'}:
        raise ValueError('generator export file inventory changed')
    return receipt


def prefix(config,state,run,root):
    """Freeze the maximum 32-group prefix and all placebo/C values before any response."""
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    templates=read(config['train_prompts'])
    if set(templates)!=set(Path(config['runtime']['train_ids']).read_text().splitlines()):
        raise ValueError('training prompt inventory differs from the frozen train allowlist')
    tasks=sorted(templates)
    models=read(config['marginal_models']) if run['arm']=='C' else None
    placebo=read(config['placebo_distribution']) if run['arm']=='P' else None
    plans=[];cells=[]
    for group in range(state['group_index'],state['group_index']+32):
        planned=plan_group(run['arm'],seed=run['run_seed'],update=state['update'],group_index=group,tasks=tasks,
            models=models,abilities=state.get('abilities'),placebo_distribution=placebo)
        for cell in planned['cells']:
            template=templates[cell['task_id']]
            if template['task_id']!=cell['task_id'] or template['split']!='train':raise ValueError('prompt template identity changed')
            cells.append({**template,**cell,'arm':run['arm'],'run_seed':run['run_seed'],
                          'update':state['update'],'group_index':group})
        plans.append(planned)
    write_new(root/'plans.json',plans);write_new(root/'cells.json',cells)
    if run['phase']=='main':
        targets=config['token_budget']['targets']
        boundary=state['boundary_index']
        if not 0<=boundary<4 or len(targets)!=4:raise ValueError('invalid main token boundary')
        budget={'generated_tokens':state['generated_tokens'],'next_target':targets[boundary],
                'group_index':state['group_index'],'update_groups':0}
        write_new(root/'budget.json',budget)
    return {'status':'PREPARED','plans':reference(root/'plans.json'),'cells':reference(root/'cells.json'),
            'group_index':state['group_index'],'maximum_groups':32}


def materialize(config,state,run,update_root,key,lease):
    """Bind actual predecessor bytes after completion; never inject future checkpoints into a prospective lock."""
    update_root=Path(update_root);root=update_root/key
    value=copy.deepcopy(config['runtime'])
    if any(digest(b['path'])!=b['sha256'] for b in value['bindings']):raise ValueError('static learning runtime binding changed')
    value.update(stage=key,learning_phase=run['phase'],arm=run['arm'],run_seed=run['run_seed'],update=state['update'],
                 stage_root=str(root/'output'),attempt_root=str(root/'health'),lease_path=str(root/'lease.json'),
                 lease_id=lease['id'],ray_temp=str(root/'ray'),model=state['model'])
    value['provenance']={'condition':'v2-S2','phase':run['phase'],'arm':run['arm'],'run_seed':run['run_seed'],
                         'update':state['update'],'execution_sha256':run['execution_lock']['sha256']}
    if state.get('model_receipt_sha256'):verify_export(state['model'],state['model_receipt_sha256'])
    paths={Path(b['path']) for b in value['bindings']}
    value['cells_path']=str(update_root/'prefix/cells.json') if key!='preflight' else config['health_cells']['path']
    paths.add(Path(value['cells_path']))
    if key=='generate' and run['phase']=='main':
        value['budget_state']=str(update_root/'prefix/budget.json');paths.add(Path(value['budget_state']))
    if key=='update':
        value['groups_path']=str(update_root/'score/groups.json');paths.add(Path(value['groups_path']))
        if state.get('checkpoint'):value['checkpoint']=state['checkpoint']
    if key=='export':value['checkpoint']=str(update_root/'update/output/after')
    for directory in [Path(value['model'])]+([Path(value['checkpoint'])] if value.get('checkpoint') else []):
        paths.update(p for p in directory.rglob('*') if p.is_file())
    value['bindings']=bindings(paths)
    root.mkdir(parents=True,exist_ok=False);(root/'health').mkdir()
    write_new(root/'lease.json',lease);write_new(root/'runtime.json',value)
    return root/'runtime.json'


def score(config,run,update_root):
    root=Path(update_root);generated=root/'generate/output'
    terminal=json.loads((generated/'result.json').read_text())
    cells=json.loads((generated/'cells.json').read_text())
    plans=json.loads((root/'prefix/plans.json').read_text())[:len(cells)//8]
    maximum=json.loads((root/'prefix/cells.json').read_text())
    if (terminal['status']!='COMPLETE' or terminal['completed']!=len(cells) or terminal['declared']!=len(cells)
            or cells!=maximum[:len(cells)] or not len(cells) or len(cells)%8):
        raise ValueError('learning generation is not a complete declared prefix')
    if run['phase']=='pilot' and len(cells)!=256:raise ValueError('pilot update requires all 256 slots')
    paths=[generated/f'{i:05d}.generation.json' for i in range(len(cells))]
    rows=[json.loads(p.read_text()) for p in paths]
    score_config={**config['scoring'],'root':str(root/'score/cells'),'generation_root':str(generated)}
    Path(score_config['controller_fence']).parent.mkdir(parents=True,exist_ok=True)
    scored=score_batch(cells,score_config,{str(p):digest(p) for p in paths},run['execution_lock']['sha256'])
    if any(r.get('cleanup_verified') is not True for r in scored['rows']):raise ValueError('training scorer cleanup unresolved')
    groups=assemble(cells,rows,scored['rows'],train_ids=Path(config['runtime']['train_ids']).read_text().splitlines(),plans=plans)
    write_new(root/'score/groups.json',groups)
    measured=[r for r in scored['rows'] if r['status']=='measured']
    result={'condition':'v2-S2','status':'ACCOUNTED','arm':run['arm'],'seed':run['run_seed'],'split':'train',
            'update':cells[0]['update'],'declared':len(cells),'measured':len(measured),
            'strict_successes':sum(r['strict'] for r in measured),'generated_tokens':terminal['generated_tokens'],
            'complete_groups':len(groups),'groups':reference(root/'score/groups.json'),
            'scoring':reference(Path(score_config['root'])/'result.json')}
    write_new(root/'score/result.json',result);return result


def ability(config,state,run,run_root,update_root):
    if run['arm']!='C':raise ValueError('ability refits apply only to C')
    root=Path(update_root)/'ability';root.mkdir(parents=True,exist_ok=False)
    paths=[Path(run_root)/f'update_{i:05d}/score/cells/result.json' for i in range(1,state['update'])]
    rows=[]
    for path in paths:
        previous=json.loads(path.read_text())
        if previous['execution_sha256']!=run['execution_lock']['sha256']:raise ValueError('earlier C scorer binding changed')
        rows.extend(previous['rows'])
    if any(r['run_seed']!=run['run_seed'] for r in rows):raise ValueError('ability refit crossed run seeds')
    write_new(root/'inputs.json',{'prior_scores':bindings(paths),'current_update':state['update'],
                                'model':config['marginal_models'],'automatic_retry':False})
    models=read(config['marginal_models']);tasks=sorted(read(config['train_prompts']))
    result=refit(rows,tasks,models,current_update=state['update'],save=lambda name,value:write_new(root/(name+'.json'),value))
    write_new(root/'result.json',result);return result


def finish(state,run,update_root):
    """Advance opportunity counters once, retaining token-boundary overshoot and wholly missing updates."""
    state=copy.deepcopy(state);root=Path(update_root)
    generation=json.loads((root/'generate/output/result.json').read_text())
    update=json.loads((root/'update/output/result.json').read_text())
    if generation.get('condition')!='v2-S2' or generation.get('status')!='COMPLETE':raise ValueError('generation is not complete')
    if update.get('condition')!='v2-S2' or update.get('status') not in ('MEASURED','UNMEASURED'):
        raise ValueError('learning update lacks a terminal measured/missing receipt')
    measured=update['status']=='MEASURED'
    if update.get('optimizer_updates')!=int(measured):raise ValueError('optimizer opportunity accounting changed')
    if measured:
        after=root/'update/output/after/receipt.json'
        if digest(after)!=update['after_receipt_sha256']:raise ValueError('updated checkpoint changed')
        export=root/'export/output/export_receipt.json'
        if not export.exists():raise ValueError('updated generator export missing')
        exported=verify_export(export.parent,digest(export))
        if exported['native_receipt_sha256']!=digest(after):raise ValueError('export belongs to another native checkpoint')
        state.update(checkpoint=str(after.parent),model=str(export.parent),model_receipt_sha256=digest(export))
    state['optimizer_updates']+=int(measured)
    state['completed_updates']=state['update']
    state['generated_tokens']+=generation['generated_tokens']
    state['group_index']+=generation['complete_groups']
    state['boundary_crossed']=False
    if run['phase']=='main':
        budget=generation['budget_state_after']
        if (budget['generated_tokens']!=state['generated_tokens'] or budget['group_index']!=state['group_index']
                or budget['update_groups']!=generation['complete_groups'] or not budget['update_due']):
            raise ValueError('main token accounting diverged from the complete generated prefix')
        if budget['boundary_crossed']:
            state['boundary_crossed']=True;state['boundary_index']+=1
            write_new(root/'boundary.json',{'condition':'v2-S2','arm':run['arm'],'seed':run['run_seed'],
                'boundary':state['boundary_index'],'target':budget['next_target'],'generated_tokens':state['generated_tokens'],
                'overshoot':budget['overshoot'],'model':state['model'],'checkpoint':state.get('checkpoint'),
                'export_files':bindings(p for p in Path(state['model']).iterdir() if p.is_file()),
                'completed_updates':state['completed_updates'],'optimizer_updates':state['optimizer_updates']})
    result={'condition':'v2-S2','status':'ACCOUNTED','phase':run['phase'],'arm':run['arm'],'run_seed':run['run_seed'],
            'update':state['update'],'optimizer_updates':int(measured),'generated_tokens':generation['generated_tokens'],
            'complete_groups':generation['complete_groups'],'state_after':state}
    write_new(root/'opportunity.json',result);return state
