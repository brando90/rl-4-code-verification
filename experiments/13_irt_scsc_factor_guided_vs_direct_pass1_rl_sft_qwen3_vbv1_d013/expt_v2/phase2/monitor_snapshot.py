"""Freeze the exact paused pilot checkpoint and fixed diagnostic inputs before any monitor response."""
from __future__ import annotations

import copy
import fcntl
import json
from pathlib import Path

from learning_driver import authorize as learning_authority
from learning_steps import verify_export
from monitor_preparation import prepare
from technical_driver import bindings,read
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent
SOURCES=('monitor_snapshot.py','monitor_supervisor.py','monitor_runtime.py','monitor_preparation.py',
         'monitor_cpu.py','monitor_coverage.py','monitor_hosted.py','hosted_coverage.py','coverage_pack.py','audit_monitor.py',
         'monitor_measurements.py','monitor_decision.py','monitor_processing.py','monitor_driver.py','monitor_publication.py')


def freeze(plan):
    """Prepare a lock for publication; this function neither claims devices nor measures outputs."""
    learning=plan['learning'];lp,execution,config=learning_authority(learning);run=learning['run']
    if run['phase']!='pilot' or run['arm'] not in ('B','C') or run['run_seed']!=1301:
        raise ValueError('fixed B/C learning pilot required')
    scientific={b['path']:b['sha256'] for b in execution['bindings']}
    for name in SOURCES:
        if scientific.get(str(HERE/name))!=digest(HERE/name):raise ValueError('monitor implementation was not frozen before learning')
    monitoring=config['monitor']
    for key in ('cohort','hidden_suites'):
        ref=monitoring[key]
        if scientific.get(ref['path'])!=ref['sha256']:raise ValueError('monitor cohort or hidden tests were not frozen before learning')
        read(ref)
    root=Path(execution['configuration']['ledger'])/'pilot'/run['arm']/str(run['run_seed'])
    with (root/'controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state_path=root/'state.json';state=json.loads(state_path.read_text());update=state['completed_updates']
        admission=json.loads((root/'admission.json').read_text())
        if ((root/'terminal.json').exists() or admission.get('status')!='ADMITTED'
                or admission.get('execution_lock_sha256')!=run['execution_lock']['sha256']):
            raise ValueError('pilot is not actively admitted')
        if (state['status']!='WAIT_FOR_MONITOR' or state['next_stage']!='monitor' or update not in (0,10,20,30)
                or state['execution_sha256']!=run['execution_lock']['sha256']
                or state['configuration_sha256']!=digest(learning['configuration'])):
            raise ValueError('pilot is not paused at its declared checkpoint')
        model_sha=state.get('model_receipt_sha256') or config['initial_model_manifest']['sha256']
        if state.get('model_receipt_sha256'):verify_export(state['model'],model_sha)
        elif state['model']!=config['runtime']['initial_model']:
            raise ValueError('unupdated pilot model differs from the frozen initial weights')
        model_files=[p for p in Path(state['model']).rglob('*') if p.is_file()]
        if not model_files:raise ValueError('empty monitor model')
        model_inventory=bindings(model_files)
        if not state.get('model_receipt_sha256'):
            if any(scientific.get(b['path'])!=b['sha256'] for b in model_inventory):raise ValueError('initial model changed')
        cohort=read(monitoring['cohort']);prompts=read(config['train_prompts'])
        snapshot=prepare(cohort,prompts,Path(config['runtime']['train_ids']).read_text().splitlines(),
            arm=run['arm'],run_seed=run['run_seed'],update=update,
            models=read(config['marginal_models']) if run['arm']=='C' else None,abilities=state.get('abilities'))
        destination=root/'monitors'/f'update_{update:05d}'/'freeze';destination.mkdir(parents=True,exist_ok=False)
        # Keep an immutable copy: the live controller state legitimately changes
        # after a published decision, and must not invalidate earlier evidence.
        (destination/'controller_state.json').write_bytes(state_path.read_bytes())
        write_new(destination/'snapshot.json',snapshot);write_new(destination/'cells.json',snapshot['cells'])
        write_new(destination/'model_inventory.json',model_inventory)
        required={Path(b['path']) for b in execution['bindings']}|set(destination.iterdir())|set(model_files)
        lock={'condition':'v2-S2','gate':'PILOT_MONITOR_SNAPSHOT','status':'FROZEN','arm':run['arm'],
              'run_seed':run['run_seed'],'update':update,'declared':32,'split':'train',
              'execution_sha256':run['execution_lock']['sha256'],'model':state['model'],'model_binding_sha256':model_sha,
              'controller_state_sha256':digest(state_path),'bindings':bindings(required),
              'configuration':{'snapshot':str(destination/'snapshot.json'),'cells_path':str(destination/'cells.json'),
                               'root':str(destination.parent),'learning_configuration':learning['configuration']},
              'learning_rollout_tokens':0,'model_calls':0,'snapshot_automatic_retries':0}
        target=HERE.parent/'locks'/f"PILOT_MONITOR_S2_{run['arm']}_{run['run_seed']}_u{update}.json"
        write_new(target,lock)
        return {'status':'PREPARED_FOR_PUBLICATION','lock':str(target),'sha256':digest(target),'model_calls':0}


def materialize(snapshot,learning_config,stage,lease,snapshot_sha):
    """Parent verifies publication first; freeze one leased runtime and its exclusive reservation."""
    if stage not in ('monitor_preflight','monitor_generate'):raise ValueError('undeclared monitor stage')
    if snapshot.get('status')!='FROZEN' or snapshot.get('gate')!='PILOT_MONITOR_SNAPSHOT':raise ValueError('frozen snapshot required')
    root=Path(snapshot['configuration']['root']);stage_root=root/stage
    runtime=copy.deepcopy(learning_config['runtime'])
    paths={Path(b['path']) for b in runtime['bindings']}|{Path(b['path']) for b in snapshot['bindings']}
    for b in runtime['bindings']+snapshot['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('monitor binding changed before materialization')
    if stage=='monitor_generate':paths.update((root/'monitor_preflight'/p for p in ('health/preflight.json','dispatch/result.json')))
    runtime.update(condition='v2-S2',learning_phase='pilot',stage=stage,model=snapshot['model'],
        model_binding_sha256=snapshot['model_binding_sha256'],arm=snapshot['arm'],run_seed=snapshot['run_seed'],update=snapshot['update'],
        snapshot=snapshot['configuration']['snapshot'],cells_path=snapshot['configuration']['cells_path'],
        stage_root=str(stage_root/'output'),attempt_root=str(stage_root/'health'),ray_temp=str(stage_root/'ray'),
        lease_id=lease['id'],lease_path=str(stage_root/'lease.json'),bindings=bindings(paths))
    stage_root.mkdir(parents=True,exist_ok=False);(stage_root/'health').mkdir()
    write_new(stage_root/'lease.json',lease);write_new(stage_root/'runtime.json',runtime)
    seconds=learning_config['monitor']['stage_seconds'][stage]
    record={'condition':'v2-S2','execution_sha256':snapshot['execution_sha256'],'snapshot_sha256':snapshot_sha,
            'stage':stage,'configuration_sha256':digest(stage_root/'runtime.json'),'lease_id':lease['id'],
            'maximum_seconds':seconds,'automatic_retry':False}
    write_new(root/(stage+'.json'),record)
    return {'runtime':str(stage_root/'runtime.json'),'reservation':str(root/(stage+'.json')),
            'dispatch_root':str(stage_root/'dispatch'),'maximum_seconds':seconds}
