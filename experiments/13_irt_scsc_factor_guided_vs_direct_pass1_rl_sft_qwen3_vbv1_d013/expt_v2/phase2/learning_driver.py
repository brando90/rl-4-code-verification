"""Advance immutable pilot/main learning opportunities with published monitor decisions and no automatic replay."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from anchor_storage import atomic_json
from learning_ledger import verify_learning,admit,reserve_stage
from learning_resources import reserve
from learning_supervisor import launch
from learning_steps import prefix,materialize,score,ability,finish
from technical_ledger import published,check_preflight
from technical_driver import reference,read
from training_checkpoint import digest,write_new
from costs import snapshot,stage_cost
from checkpoint_retention import retire

DEVICE={'preflight','generate','update','export'}
FINAL={'HALTED','RESOURCE_EXHAUSTED','COMPLETE'}


def authorize(plan):
    run=plan['run'];lp,execution,science=verify_learning(run)
    bound={b['path']:b['sha256'] for b in execution['bindings']}
    required=[Path(plan['configuration']).resolve(),Path(__file__).resolve()]
    required.extend(HERE/name for name in ['learning_steps.py','learning_resources.py','learning_supervisor.py',
        'learning_ledger.py','checkpoint_retention.py','score_training.py','arm_rewards.py','online_ability.py','costs.py'])
    required.append(HERE.parent/'watchdog_e13v2.py')
    if any(bound.get(str(p))!=digest(p) for p in required):raise ValueError('learning controller configuration or implementation unbound')
    config=json.loads(Path(plan['configuration']).read_text())
    if config['condition']!='v2-S2' or config['host']!=socket.gethostname().split('.')[0]:raise ValueError('learning route is not local S2')
    if config['LP_sha256']!=run['LP']['sha256']:raise ValueError('learning runtime differs from pilot lock')
    contract=lp['configuration']['training_runtime_contract']
    keys={'policy_config','initial_model','tokenizer','python','numerical_dtype','batch_size','terminal_token_ids',
          'runtime_versions','loss_config','gpu_memory_utilization'}
    if set(contract)!=keys or any(config['runtime'].get(k)!=v for k,v in contract.items()):
        raise ValueError('learning optimizer, sampler or numerical runtime differs from LP')
    from resource_lease import verify_allocation
    allocation,sha=verify_allocation(plan['resources']['allocation_plan'])
    if sha!=execution['allocation_sha256'] or set(allocation['routes'])!={config['host']}:
        raise ValueError('learning controller needs its published local allocation')
    for key in ['train_prompts','initial_model_manifest','health_cells']:
        ref=config[key]
        if bound.get(ref['path'])!=ref['sha256']:raise ValueError('learning input not bound')
        read(ref)
    if run['arm']=='C':
        for key in ['marginal_models','initial_abilities']:
            if bound.get(config[key]['path'])!=config[key]['sha256']:raise ValueError('C fit input unbound')
            read(config[key])
    if run['arm']=='P':
        if bound.get(config['placebo_distribution']['path'])!=config['placebo_distribution']['sha256']:
            raise ValueError('placebo distribution unbound')
        read(config['placebo_distribution'])
    if run['phase']=='main' and config['token_budget']!=execution['token_budget']:
        raise ValueError('main token budget differs from L2')
    if any(k in config['runtime'] for k in ('checkpoint','generation_root','source_update','groups_path','budget_state')):
        raise ValueError('prospective learning runtime cannot inject future state')
    return lp,execution,config


def monitor(plan,config,state):
    """A missing external measurement is a wait; its published stop/incomplete verdict is retained."""
    run=plan['run'];key=str(state['completed_updates'])
    ref=plan.get('monitor_results',{}).get(key)
    if ref is None:return {'status':'WAIT_FOR_MONITOR','update':state['completed_updates']}
    value=published(ref,run['repository'])
    expected={'condition':'v2-S2','gate':'PILOT_MONITOR','arm':run['arm'],'run_seed':run['run_seed'],
              'update':state['completed_updates'],'execution_sha256':run['execution_lock']['sha256'],
              'model_binding_sha256':state.get('model_receipt_sha256') or config['initial_model_manifest']['sha256']}
    if any(value.get(k)!=v for k,v in expected.items()):raise ValueError('published monitor belongs to another checkpoint or run')
    if value.get('status') not in ('CONTINUE','STOP_ARM','INCOMPLETE'):raise ValueError('monitor decision not terminal')
    return {'status':value['status'],'receipt':ref}


def next_opportunity(state,run):
    state=dict(state);state['update']=state['completed_updates']+1
    state['next_stage']='ability' if run['arm']=='C' and state['update']>1 and (state['update']-1)%10==0 else 'prefix'
    state['status']='READY';return state


def after_finish(state,run):
    state=dict(state)
    if run['phase']=='pilot':
        if run['arm'] in ('B','C') and state['completed_updates']%10==0:
            state.update(next_stage='monitor',status='READY');return state
        if state['completed_updates'] in (30,60):
            state.update(next_stage='pilot_decision',status='READY');return state
    elif state['boundary_index']==4:
        state.update(status='COMPLETE',next_stage='evaluation_pending');return state
    return next_opportunity(state,run)


def pilot_decision(plan,state):
    run=plan['run'];horizon=state['completed_updates']
    if run['arm']!='A':return {**state,'status':'COMPLETE','next_stage':'pilot_report_pending'}
    ref=plan.get('T5_results',{}).get(str(horizon))
    if ref is None:return {**state,'status':'WAIT_FOR_T5'}
    result=published(ref,run['repository'])
    if (result.get('condition')!='v2-S2' or result.get('gate')!='T5' or result.get('horizon')!=horizon
            or result.get('pilot_execution_sha256')!=run['execution_lock']['sha256']
            or result.get('admission_statistics_computed') is not True):raise ValueError('T5 does not bind this fixed pilot')
    if result['status']=='EXTEND_TO_60' and horizon==30:
        state=next_opportunity(state,run);state['T5_extension']=ref;return state
    if result['status'] not in ('PASS','FAIL','INCONCLUSIVE'):raise ValueError('invalid final pilot decision')
    return {**state,'status':'COMPLETE','next_stage':'pilot_report_pending','T5_final':ref}


def tick(plan):
    lp,execution,config=authorize(plan);run=plan['run'];admit(run)
    root=Path(execution['configuration']['ledger'])/run['phase']/run['arm']/str(run['run_seed'])
    with (root/'controller.lock').open('a') as fence:
        try:fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'ALREADY_SUPERVISED'}
        path=root/'state.json'
        state=json.loads(path.read_text()) if path.exists() else {
            'condition':'v2-S2','phase':run['phase'],'arm':run['arm'],'run_seed':run['run_seed'],
            'execution_sha256':run['execution_lock']['sha256'],'configuration_sha256':digest(plan['configuration']),
            'status':'READY','next_stage':'preflight','update':0,'completed_updates':0,'group_index':0,
            'generated_tokens':0,'optimizer_updates':0,'boundary_index':0,'model':config['runtime']['initial_model'],
            'checkpoint':None,'abilities':read(config['initial_abilities']) if run['arm']=='C' else None}
        if state['execution_sha256']!=run['execution_lock']['sha256'] or state['configuration_sha256']!=digest(plan['configuration']):
            raise ValueError('learning execution changed while resuming')
        if state['status'] in FINAL:return state
        if state['status']=='RUNNING':return {**state,'status':'RECOVERY_REQUIRED','reason':'adopt exact existing receipts; never replay a learning stage'}
        if state['status']=='DEVICE_CHANGED_BEFORE_LAUNCH':return state
        subprocess.run([sys.executable,str(HERE.parent/'watchdog_e13v2.py'),'--root',plan['watchdog_root'],
            '--run',plan['watchdog_run'],'register','--role',f"learning-{run['phase']}-{run['arm']}-{run['run_seed']}",
            '--pid',str(os.getpid())],check=True)
        while True:
            key=state['next_stage'];update_root=root/f"update_{state['update']:05d}"
            update_root.mkdir(parents=True,exist_ok=True);(update_root/'costs').mkdir(exist_ok=True)
            if key=='monitor':
                result=monitor(plan,config,state)
                if result['status']=='WAIT_FOR_MONITOR':state['status']='WAIT_FOR_MONITOR';atomic_json(path,state);return state
                if result['status']!='CONTINUE':
                    state.update(status='HALTED',monitor_result=result);atomic_json(path,state);write_new(root/'terminal.json',state);return state
                state.setdefault('monitor_receipts',{})[str(state['completed_updates'])]=result['receipt']
                if state['completed_updates']==30:state.update(next_stage='pilot_decision',status='READY')
                else:state=next_opportunity(state,run)
                atomic_json(path,state);continue
            if key=='pilot_decision':
                state=pilot_decision(plan,state);atomic_json(path,state)
                if state['status']=='WAIT_FOR_T5':return state
                if state['status']=='COMPLETE':write_new(root/'terminal.json',state);return state
                continue
            lease=None
            if key in DEVICE:
                seconds=config['stage_seconds'][key]
                resource_plan={**plan['resources'],'run':run}
                reserved=reserve(resource_plan,update=state['update'],stage_key=key,seconds=seconds)
                if reserved['status']!='RESERVED':
                    state['status']=reserved['status'];atomic_json(path,state);return state
                lease=reserved['lease']
            state['status']='RUNNING';atomic_json(path,state);before=snapshot(root)
            try:
                if lease is not None:
                    runtime=materialize(config,state,run,update_root,key,lease)
                    reservation=reserve_stage(root,update=state['update'],stage=key,execution_sha=run['execution_lock']['sha256'],
                        inputs={'configuration_sha256':digest(runtime),'lease_id':lease['id'],'maximum_seconds':seconds})
                    result=launch({'run':run,'stage':key,'config':str(runtime),'reservation':str(reservation),
                        'lease_root':resource_plan['lease_root'],'maximum_seconds':seconds,'dispatch_root':str(update_root/key/'dispatch'),
                        'environment':config['environment']})
                    if result['status']!='RUNTIME_EXITED_ZERO' or result.get('cleanup_verified') is not True:raise RuntimeError('learning runtime failed; automatic replay is prohibited')
                    if key=='preflight':
                        health=update_root/'preflight/health/preflight.json';check_preflight(reference(health))
                        state['preflight']=reference(health)
                        state.update(next_stage='monitor' if run['phase']=='pilot' and run['arm'] in ('B','C') else 'prefix',update=0 if run['phase']=='pilot' and run['arm'] in ('B','C') else 1)
                    elif key=='generate':state['next_stage']='score'
                    elif key=='update':
                        receipt=json.loads((update_root/'update/output/result.json').read_text())
                        state['next_stage']='export' if receipt['status']=='MEASURED' else 'finish'
                    else:state['next_stage']='finish'
                else:
                    # Exclusive local stage marker, including pure prefix/final bookkeeping.
                    write_new(update_root/(key+'_controller_attempt.json'),{'execution_sha256':run['execution_lock']['sha256'],
                        'configuration_sha256':digest(plan['configuration']),'automatic_retry':False})
                    if key=='prefix':prefix(config,state,run,update_root/'prefix');state['next_stage']='generate'
                    elif key=='score':score(config,run,update_root);state['next_stage']='update'
                    elif key=='ability':
                        result=ability(config,state,run,root,update_root)
                        if result['admitted'] is not True:
                            state.update(status='HALTED',reason='C ability refit failed; no fallback');atomic_json(path,state);write_new(root/'terminal.json',state);return state
                        state['abilities']=result['abilities'];state['next_stage']='prefix'
                    elif key=='finish':
                        state=finish(state,run,update_root);state['next_stage']='retention'
                    elif key=='retention':
                        retire(root,state,root/'retention'/f"after_{state['completed_updates']:05d}.json",controller_fence=fence)
                        state=after_finish(state,run)
                    else:raise ValueError('unknown learning sequence stage')
                if state['status']=='RUNNING':state['status']='READY'
            except BaseException as exc:
                state.update(status='HALTED',error_type=type(exc).__name__,error=str(exc),failed_stage=key)
                atomic_json(path,state);write_new(root/'terminal.json',state);return state
            finally:
                if lease is not None:
                    from resource_lease import release
                    from lp1 import cleanup
                    canonical=json.loads((Path(resource_plan['lease_root'])/(lease['id']+'.json')).read_text())
                    if canonical['status']!='RELEASED':
                        cleaned=cleanup(lease['id']);release(resource_plan['lease_root'],lease['id'],cleanup_verified=cleaned['verified'])
                        write_new(update_root/(key+'_parent_cleanup.json'),cleaned)
                    else:
                        cp=update_root/key/'dispatch/cleanup.json';cleaned=json.loads(cp.read_text()) if cp.exists() else None
                    canonical=json.loads((Path(resource_plan['lease_root'])/(lease['id']+'.json')).read_text())
                    write_new(update_root/'costs'/(key+'.json'),stage_cost(before,snapshot(root),stage=key,lease=canonical,cleanup=cleaned))
                else:write_new(update_root/'costs'/(key+'.json'),stage_cost(before,snapshot(root),stage=key))
            atomic_json(path,state)
            if state['status']=='COMPLETE':write_new(root/'terminal.json',state);return state


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,required=True)
    args=parser.parse_args();result=tick(json.loads(args.plan.read_text()))
    print(json.dumps({k:v for k,v in result.items() if k not in ('abilities','monitor_receipts')},sort_keys=True))
