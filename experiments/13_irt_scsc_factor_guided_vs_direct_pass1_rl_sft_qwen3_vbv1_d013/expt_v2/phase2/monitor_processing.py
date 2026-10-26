"""Score the fixed generated monitor once, freeze independent hidden inputs, and retain bounded processor execution."""
from __future__ import annotations

import fcntl
import json
from pathlib import Path

from learning_driver import authorize as learning_authority
from monitor_runtime import validate
from monitor_cpu import prepare,run_cells
from score_training import score_batch
from technical_ledger import published
from technical_driver import bindings,read
from training_checkpoint import digest,write_new
from costs import snapshot as cost_snapshot,stage_cost

HERE=Path(__file__).resolve().parent


def retain(path,value):
    """Recover a completed parent write without overwriting or repeating a cell measurement."""
    if path.exists():
        if json.loads(path.read_text())!=value:raise ValueError('retained monitor processor artifact changed')
    else:write_new(path,value)


def authority(plan):
    learning=plan['learning'];lp,execution,config=learning_authority(learning);run=learning['run']
    value=published(plan['snapshot_lock'],run['repository'])
    if (value.get('condition'),value.get('gate'),value.get('status'))!=('v2-S2','PILOT_MONITOR_SNAPSHOT','FROZEN'):
        raise ValueError('published monitor snapshot required')
    if (run['phase']!='pilot' or value['execution_sha256']!=run['execution_lock']['sha256']
            or any(value[k]!=run[k] for k in ('arm','run_seed'))):raise ValueError('processor monitor belongs to another pilot')
    scientific={b['path']:b['sha256'] for b in execution['bindings']}
    for path in (Path(__file__).resolve(),HERE/'monitor_cpu.py',HERE/'score_training.py',HERE/'costs.py'):
        if scientific.get(str(path))!=digest(path):raise ValueError('monitor processor method not frozen before learning')
    bound={b['path']:b['sha256'] for b in value['bindings']}
    if len(bound)!=len(value['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):
        raise ValueError('monitor snapshot source changed')
    manifest=json.loads(Path(value['configuration']['snapshot']).read_text());validate(manifest,value)
    if manifest['cells']!=json.loads(Path(value['configuration']['cells_path']).read_text()):raise ValueError('monitor cells changed')
    return value,manifest,execution,config


def score(plan):
    lock,manifest,execution,config=authority(plan);root=Path(lock['configuration']['root']);generated=root/'monitor_generate/output'
    dispatch=json.loads((root/'monitor_generate/dispatch/result.json').read_text())
    terminal=json.loads((generated/'monitor_result.json').read_text())
    if (dispatch.get('status')!='RUNTIME_EXITED_ZERO' or dispatch.get('cleanup_verified') is not True
            or dispatch.get('snapshot_sha256')!=plan['snapshot_lock']['sha256']
            or terminal.get('status')!='COMPLETE' or terminal.get('declared')!=32 or terminal.get('completed')!=32
            or terminal.get('learning_rollout_tokens')!=0
            or json.loads((generated/'cells.json').read_text())!=manifest['cells']):
        raise ValueError('monitor generation is not complete under its own cleaned snapshot')
    output=root/'strict';output.mkdir(exist_ok=True)
    with (output/'controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX)
        if (output/'terminal.json').exists():
            report=json.loads((output/'terminal.json').read_text())
            if report['snapshot_sha256']!=plan['snapshot_lock']['sha256'] or report['scoring']['sha256']!=digest(report['scoring']['path']):
                raise ValueError('saved monitor scoring changed')
            inventory=read(report['generation_inventory'])
            if any(digest(b['path'])!=b['sha256'] for b in inventory['bindings']):raise ValueError('saved monitor generation changed')
            return report
        files=[generated/f'{i:05d}.generation.json' for i in range(32)]
        inputs={'snapshot_sha256':plan['snapshot_lock']['sha256'],'bindings':bindings(files+[generated/'monitor_result.json',generated/'cells.json',root/'monitor_generate/dispatch/result.json'])}
        inventory=output/'inputs.json';resumed=inventory.exists()
        if resumed:
            if json.loads(inventory.read_text())!=inputs:raise ValueError('monitor scoring inputs changed during recovery')
        else:write_new(inventory,inputs)
        before=cost_snapshot(output)
        scoring={**config['scoring'],'root':str(output/'cells'),'generation_root':str(generated)}
        Path(scoring['controller_fence']).parent.mkdir(parents=True,exist_ok=True)
        result=score_batch(manifest['cells'],scoring,{str(p):digest(p) for p in files},plan['snapshot_lock']['sha256'])
        cost=stage_cost(before,cost_snapshot(output),stage='pilot_monitor_strict')
        cost.update(cumulative_timing_complete=not resumed,timing_scope='this controller invocation only' if resumed else 'complete controller invocation')
        if not (output/'cost.json').exists():write_new(output/'cost.json',cost)
        report={'condition':'v2-S2','stage':'PILOT_MONITOR_STRICT','status':'ACCOUNTED',
                **{k:lock[k] for k in ('arm','run_seed','update','execution_sha256','model_binding_sha256')},
                'snapshot_sha256':plan['snapshot_lock']['sha256'],'declared':32,'accounted':len(result['rows']),
                'measured':result['measured'],'cleanup_unresolved':sum(r.get('cleanup_verified') is not True for r in result['rows']),
                'automatic_retries':0,'generation_inventory':{'path':str(inventory),'sha256':digest(inventory)},'scoring':{'path':str(output/'cells/result.json'),'sha256':digest(output/'cells/result.json')},
                'cost':{'path':str(output/'cost.json'),'sha256':digest(output/'cost.json')}}
        write_new(output/'terminal.json',report);return report


def prepare_hidden(plan):
    lock,manifest,execution,config=authority(plan);root=Path(lock['configuration']['root'])
    strict=json.loads((root/'strict/terminal.json').read_text())
    if strict['snapshot_sha256']!=plan['snapshot_lock']['sha256'] or strict['cleanup_unresolved']!=0:
        raise ValueError('monitor strict scoring is not cleanly accounted')
    scoring=read(strict['scoring']);monitor=config['monitor'];suites=read(monitor['hidden_suites'])
    suite_map={r['task_id']:r['suite'] for r in suites['rows']}
    controls=published(monitor['hidden_controls_result'],plan['learning']['run']['repository'])
    if controls.get('status')!='PASS' or controls.get('cleanup_verified') is not True:raise ValueError('hidden controls are not admitted')
    normalized=prepare(manifest,scoring,root/'strict/cells',suite_map,output=root/'hidden_inputs')
    hidden_config={'root':str(root/'hidden'),'controller_fence':str(root/'hidden_controller.lock'),
        'train_ids':config['runtime']['train_ids'],'lake':config['scoring']['lake'],'lake_bin':monitor['lake_bin'],
        'inputs':str(root/'hidden_inputs/inputs.json')}
    paths={Path(b['path']) for b in execution['bindings']+lock['bindings']}|{root/'strict/terminal.json',Path(strict['scoring']['path'])}
    paths.update((root/'hidden_inputs').iterdir())
    generation_inventory=read(strict['generation_inventory']);paths.add(Path(strict['generation_inventory']['path']))
    for b in generation_inventory['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('generation changed before hidden freeze')
        paths.add(Path(b['path']))
    for cell in normalized['cells']:
        value=read(cell['strict'])
        for ref in (cell.get('source'),cell['suite'],cell['strict'],value['strict_receipt'],value.get('oracle_receipt')):
            if ref:paths.add(Path(ref['path']))
    target=HERE.parent/'locks'/f"PILOT_MONITOR_CPU_S2_{lock['arm']}_{lock['run_seed']}_u{lock['update']}.json"
    frozen={'condition':'v2-S2','gate':'PILOT_MONITOR_CPU','status':'FROZEN','declared':32,
            **{k:lock[k] for k in ('arm','run_seed','update','execution_sha256','model_binding_sha256')},
            'snapshot_sha256':plan['snapshot_lock']['sha256'],'snapshot_lock':plan['snapshot_lock'],
            'pilot_execution_lock':plan['learning']['run']['execution_lock'],'hidden_controls_result':monitor['hidden_controls_result'],
            'configuration':hidden_config,'bindings':bindings(paths),'maximum_attempts_per_cell':1,
            'maximum_workers':8,'per_cell_timeout_seconds':3600,'model_calls':0}
    write_new(target,frozen);return {'status':'PREPARED_FOR_PUBLICATION','lock':str(target),'sha256':digest(target),'model_calls':0}


def hidden(plan):
    lock=published(plan['lock'],plan['repository'])
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('PILOT_MONITOR_CPU','v2-S2','FROZEN'):
        raise ValueError('published monitor hidden-execution lock required')
    pilot=published(lock['pilot_execution_lock'],plan['repository']);snapshot=published(lock['snapshot_lock'],plan['repository'])
    if (pilot.get('gate')!='LEARNING_PILOT' or pilot.get('status')!='FROZEN'
            or lock['execution_sha256']!=lock['pilot_execution_lock']['sha256']
            or snapshot['execution_sha256']!=lock['execution_sha256'] or lock['snapshot_sha256']!=lock['snapshot_lock']['sha256']):
        raise ValueError('monitor hidden execution belongs to another pilot or snapshot')
    controls=published(lock['hidden_controls_result'],plan['repository'])
    if controls.get('status')!='PASS' or controls.get('cleanup_verified') is not True:raise ValueError('hidden controls unavailable')
    scientific={b['path']:b['sha256'] for b in pilot['bindings']}
    for path in (Path(__file__).resolve(),HERE/'monitor_cpu.py',HERE/'hidden_runtime.py',HERE/'costs.py'):
        if scientific.get(str(path))!=digest(path):raise ValueError('hidden monitor source was not frozen before learning')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('hidden monitor input changed')
    config=lock['configuration'];inputs=json.loads(Path(config['inputs']).read_text())
    if bound.get(config['inputs'])!=digest(config['inputs']) or any(inputs[k]!=lock[k] or snapshot[k]!=lock[k] for k in ('arm','run_seed','update')):
        raise ValueError('hidden monitor source snapshot changed')
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    with (root/'parent_controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX)
        if (root/'terminal.json').exists():
            result=json.loads((root/'terminal.json').read_text())
            if result['execution_sha256']!=plan['lock']['sha256'] or result['rows_sha256']!=digest(root/'rows.json'):
                raise ValueError('completed monitor hidden result changed')
            return result
        attempt=root/'parent_attempt.json';resumed=attempt.exists()
        identity={'lock_sha256':plan['lock']['sha256'],'automatic_retries':False}
        if resumed:
            if json.loads(attempt.read_text())!=identity:raise ValueError('hidden monitor admission changed')
        else:write_new(attempt,identity)
        before=cost_snapshot(root);value=run_cells(inputs,config,plan['lock']['sha256'])
        retain(root/'rows.json',value['rows'])
        cost=stage_cost(before,cost_snapshot(root),stage='pilot_monitor_hidden');cost['cumulative_timing_complete']=not resumed
        if not (root/'cost.json').exists():write_new(root/'cost.json',cost)
        result={k:v for k,v in value.items() if k!='rows'}
        result.update(status='ACCOUNTED',snapshot_sha256=lock['snapshot_sha256'],rows_sha256=digest(root/'rows.json'),
            **{k:lock[k] for k in ('arm','run_seed','update','model_binding_sha256')},
            cost={'path':str(root/'cost.json'),'sha256':digest(root/'cost.json')})
        write_new(root/'terminal.json',result);return result
