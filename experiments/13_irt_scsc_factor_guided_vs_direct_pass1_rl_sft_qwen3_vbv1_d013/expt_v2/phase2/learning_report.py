"""Retain terminal learning counts and exact checkpoint references without treating failed runs as completed evaluations."""
from __future__ import annotations

import fcntl
import json
from pathlib import Path

from learning_driver import authorize
from learning_steps import verify_export
from technical_driver import read,bindings
from training_checkpoint import digest,write_new


def checkpoint(boundary,config,scientific):
    model=Path(boundary['model']);files=boundary['export_files']
    if not files or any(digest(b['path'])!=b['sha256'] for b in files):raise ValueError('retained token-boundary model changed')
    actual={str(p) for p in model.rglob('*') if p.is_file()}
    if actual!={b['path'] for b in files}:raise ValueError('token-boundary model inventory changed')
    receipt=model/'export_receipt.json'
    if receipt.exists():verify_export(model,digest(receipt));return digest(receipt)
    if str(model)!=config['runtime']['initial_model'] or any(scientific.get(b['path'])!=b['sha256'] for b in files):
        raise ValueError('unupdated boundary differs from the frozen initial model')
    read(config['initial_model_manifest']);return config['initial_model_manifest']['sha256']


def summarize(root,state,config,execution_sha,scientific):
    root=Path(root);run={k:state[k] for k in ('arm','run_seed','phase')}
    if state['status'] not in ('COMPLETE','HALTED','RESOURCE_EXHAUSTED'):
        raise ValueError('learning report requires a terminal controller state')
    n=state['completed_updates'];trajectories=[];sources=[];boundaries={};optimized=0;generated=0
    if type(n) is not int or n<0:raise ValueError('invalid completed opportunity count')
    cleanup_unresolved=0
    for update in range(1,n+1):
        directory=root/f'update_{update:05d}'
        opportunity_path=directory/'opportunity.json';opportunity=json.loads(opportunity_path.read_text())
        score_path=directory/'score/result.json';score=json.loads(score_path.read_text());cells=read(score['scoring'])['rows']
        if (opportunity.get('status')!='ACCOUNTED' or opportunity.get('update')!=update
                or opportunity['state_after']['execution_sha256']!=execution_sha
                or any(opportunity.get(k)!=v for k,v in run.items())):
            raise ValueError('completed opportunity belongs to another learning run')
        if (score['arm']!=run['arm'] or score['seed']!=run['run_seed'] or score['update']!=update
                or len(cells)!=score['declared'] or len({c['cell_id'] for c in cells})!=len(cells)):
            raise ValueError('learning score denominator changed')
        known=[r for r in cells if r['status']=='measured']
        if len(known)!=score['measured'] or sum(r['strict'] for r in known)!=score['strict_successes']:
            raise ValueError('learning score summary differs from retained measurements')
        cleanup_unresolved+=sum(r.get('cleanup_verified') is not True for r in cells)
        count=opportunity['optimizer_updates']
        if count not in (0,1):raise ValueError('invalid optimizer opportunity count')
        stages=['generate','update']+(['export'] if count else [])
        for stage in stages:
            path=directory/stage/'dispatch/result.json';closed=json.loads(path.read_text());sources.append(path)
            cleanup_unresolved+=int(closed.get('cleanup_verified') is not True)
            if closed.get('status')!='RUNTIME_EXITED_ZERO':raise ValueError('completed opportunity has a failed device stage')
        optimized+=count;generated+=opportunity['generated_tokens']
        trajectories.append({'update':update,'declared':score['declared'],'measured':score['measured'],
            'missing':score['declared']-score['measured'],'strict_successes':score['strict_successes'],
            'generated_tokens':opportunity['generated_tokens'],'optimizer_updates':count,
            'complete_groups':opportunity['complete_groups'],'score_sha256':digest(score_path)})
        sources.extend([opportunity_path,score_path,Path(score['scoring']['path'])])
        path=directory/'boundary.json'
        if path.exists():
            value=json.loads(path.read_text());index=value['boundary']
            if (run['phase']!='main' or index not in (1,2,3,4) or str(index) in boundaries
                    or value['arm']!=run['arm'] or value['seed']!=run['run_seed']):
                raise ValueError('learning boundary identity changed')
            sha=checkpoint(value,config,scientific)
            boundaries[str(index)]={'path':str(path),'sha256':digest(path),'model_binding_sha256':sha,
                'model':value['model'],'generated_tokens':value['generated_tokens'],'target':value['target'],
                'overshoot':value['overshoot'],'completed_updates':value['completed_updates']}
            sources.append(path)
    if optimized!=state['optimizer_updates'] or generated!=state['generated_tokens']:
        raise ValueError('terminal learning counters differ from completed opportunities')
    if run['phase']=='main' and state['status']=='COMPLETE' and set(boundaries)!={'1','2','3','4'}:
        raise ValueError('complete main run lacks its four token boundaries')
    # Include partial failed-opportunity responses in separate total resource
    # accounting; they are never silently counted as completed learning updates.
    generation_files=sorted(root.glob('update_*/generate/output/*.generation.json'))
    all_tokens=sum(len(json.loads(path.read_text())['output_token_ids']) for path in generation_files)
    if all_tokens<generated:raise ValueError('completed rollout evidence went missing')
    sources.extend(generation_files)
    return {'condition':'v2-S2','stage':'MAIN_TRAINING' if run['phase']=='main' else 'LEARNING_PILOT_RESULT',
        **run,'status':state['status'],'completed_opportunities':n,'optimizer_updates':optimized,
        'completed_learning_tokens':generated,'all_retained_rollout_tokens':all_tokens,
        'partial_opportunity_tokens':all_tokens-generated,'retained_rollout_cells':len(generation_files),
        'cleanup_unresolved':cleanup_unresolved,'boundaries_accounted':len(boundaries),'boundaries':boundaries,
        'trajectories':trajectories,'failed_stage':state.get('failed_stage'),'error_type':state.get('error_type'),
        'evaluation_pending':True,'efficacy_claim':False},sources


def run(plan):
    learning=plan['learning'];lp,execution,config=authorize(learning);identity=learning['run']
    scientific={b['path']:b['sha256'] for b in execution['bindings']}
    if scientific.get(str(Path(__file__).resolve()))!=digest(__file__):raise ValueError('learning report method not frozen before training')
    root=Path(execution['configuration']['ledger'])/identity['phase']/identity['arm']/str(identity['run_seed'])
    with (root/'controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads((root/'terminal.json').read_text())
        if state!=json.loads((root/'state.json').read_text()):raise ValueError('terminal controller record differs from its state')
        if state['execution_sha256']!=identity['execution_lock']['sha256']:raise ValueError('terminal run belongs to another execution')
        result,sources=summarize(root,state,config,identity['execution_lock']['sha256'],scientific)
        inventory=root/'report_inventory.json';write_new(inventory,{'bindings':bindings(sources+[root/'terminal.json',root/'state.json'])})
        result.update(LP_sha256=identity['LP']['sha256'],execution_sha256=identity['execution_lock']['sha256'],
            source_inventory={'path':str(inventory),'sha256':digest(inventory)})
        if identity['phase']=='main':result['L2_sha256']=identity['execution_lock']['sha256']
        else:result['pilot_execution_sha256']=identity['execution_lock']['sha256']
        write_new(Path(plan['output']),result);return result
