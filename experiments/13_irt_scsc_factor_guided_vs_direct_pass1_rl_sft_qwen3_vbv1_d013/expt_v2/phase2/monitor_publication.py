"""Prepare source-bound hosted-monitor and decision publication locks without making judge calls or decisions."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from monitor_processing import authority
from monitor_coverage import build,helper,SUITE
from monitor_measurements import assemble
from coverage_controls import CONFIGS
from technical_ledger import published
from technical_driver import bindings,read
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def context(plan):
    snapshot,manifest,pilot,config=authority(plan)
    science={b['path']:b['sha256'] for b in pilot['bindings']}
    if science.get(str(Path(__file__).resolve()))!=digest(__file__):
        raise ValueError('monitor publication method was not frozen before learning')
    repository=plan['learning']['run']['repository']
    cpu_lock=published(plan['cpu_lock'],repository);cpu=published(plan['cpu_result'],repository)
    if (cpu_lock.get('gate')!='PILOT_MONITOR_CPU' or cpu_lock.get('snapshot_sha256')!=plan['snapshot_lock']['sha256']
            or cpu.get('stage')!='PILOT_MONITOR_HIDDEN' or cpu.get('condition')!='v2-S2'
            or cpu.get('execution_sha256')!=plan['cpu_lock']['sha256']
            or cpu.get('snapshot_sha256')!=plan['snapshot_lock']['sha256']
            or cpu.get('accounted')!=32 or cpu.get('cleanup_unresolved')!=0
            or any(cpu[k]!=snapshot[k] for k in ('arm','run_seed','update','model_binding_sha256'))):
        raise ValueError('monitor processor evidence belongs to another snapshot or is unclean')
    for b in cpu_lock['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('monitor processor input changed')
    root=Path(snapshot['configuration']['root']);rows=root/'hidden/rows.json'
    if digest(rows)!=cpu['rows_sha256']:raise ValueError('monitor processor rows changed')
    return snapshot,manifest,pilot,config,cpu_lock,cpu,root,repository


def prepare_hosted(plan):
    snapshot,manifest,pilot,learning,cpu_lock,cpu,root,repository=context(plan)
    controls=published(plan['coverage_controls_result'],repository)
    controls_lock=published(plan['coverage_controls_lock'],repository)
    if controls.get('status')!='PASS' or controls.get('actual_bundle_verified') is not True:
        raise ValueError('hosted controls have not passed')
    original=read(plan['validated_configuration'])
    if original!=controls_lock['configuration']:raise ValueError('hosted configuration differs from validated controls')
    config=copy.deepcopy(original);work=root/'hosted';work.mkdir(exist_ok=False)
    name=f"{snapshot['arm'].lower()}-{snapshot['run_seed']}-u{snapshot['update']}"
    config.update(work=str(work),snapshot_name=name,private_namespace='rl4cv_e13v2_S2_monitor_'+name.replace('-','_'),
        prepared=str(work/'prepared.json'),inputs=str(root/'hidden_inputs/inputs.json'),cpu_rows=str(root/'hidden/rows.json'))
    config_path=work/'configuration.json';write_new(config_path,config)
    pack=build(config,json.loads(Path(config['inputs']).read_text()),json.loads(Path(config['cpu_rows']).read_text()))
    module=helper(config);catalog=json.loads(Path(config['registry_catalog']).read_text())['models'];estimates={}
    for member in CONFIGS:
        cfg=module.judge_config(member);model=catalog[cfg['selector']]
        if model.get('provider_properties',{}).get('fallback_models'):raise ValueError('judge selector has fallback')
        estimates[member]=sum(module.judge_run.worst_cost(model,c['instruction_bytes'],cfg['max_tokens']) for c in pack['cells'])
    paths={Path(b['path']) for previous in (pilot,snapshot,cpu_lock,controls_lock) for b in previous['bindings']}
    paths.update(Path(plan[k]['path']) for k in ('snapshot_lock','cpu_lock','cpu_result','coverage_controls_result','coverage_controls_lock','validated_configuration'))
    paths.update(Path(config[k]) for k in ('inputs','cpu_rows','train_ids','route_identity','registry_catalog','migration_provenance'))
    paths.add(config_path);paths.update(Path(b['path']) for b in pack['source_bindings'])
    paths.update(p for folder in (module.PRIVATE,module.RESULTS) for p in folder.rglob('*') if p.is_file())
    paths.update(Path(config['bundle'])/n for n in ('judge_call.py','setup.sh','contract.yaml'))
    prepared={'condition':'v2-S2','status':'PREPARED_NOT_ADMITTED','configuration':config,
        'pack_sha256':digest(module.suite_spec(SUITE)['pack_receipt']),'bindings':bindings(paths),
        'declared_ratings':pack['n_declared_ratings'],'declared_cells':32,'compiled_files':pack['compiled_files'],
        'estimated_maximum_single_attempt_usd_by_member':estimates,'estimated_maximum_two_attempt_usd':2*sum(estimates.values()),
        'model_calls':0,'model_funding':'validated Vals-managed hosted route; reverify before admission'}
    write_new(work/'prepared.json',prepared);paths.add(work/'prepared.json')
    lock={'condition':'v2-S2','gate':'PILOT_MONITOR_HOSTED','status':'FROZEN','configuration':config,
        **{k:snapshot[k] for k in ('arm','run_seed','update','execution_sha256','model_binding_sha256')},
        'snapshot_lock':plan['snapshot_lock'],'pilot_execution_lock':plan['learning']['run']['execution_lock'],
        'cpu_execution_lock':plan['cpu_lock'],'cpu_result':plan['cpu_result'],
        'coverage_controls_result':plan['coverage_controls_result'],'coverage_controls_lock':plan['coverage_controls_lock'],
        'members':list(CONFIGS),'concurrency':5,'declared_ratings':pack['n_declared_ratings'],
        'declared_cells':32,'repeats_per_member':3,'request_attempts_per_rating':2,'one_admission_per_member':True,
        'estimated_maximum_single_attempt_usd_by_member':estimates,'estimated_maximum_two_attempt_usd':2*sum(estimates.values()),
        'bindings':bindings(paths)}
    target=HERE.parent/'locks'/f"PILOT_MONITOR_HOSTED_S2_{snapshot['arm']}_{snapshot['run_seed']}_u{snapshot['update']}.json"
    write_new(target,lock)
    return {'status':'PREPARED_FOR_PUBLICATION','lock':str(target),'sha256':digest(target),'model_calls':0,
            'estimated_maximum_two_attempt_usd':prepared['estimated_maximum_two_attempt_usd']}


def prepare_decision(plan):
    snapshot,manifest,pilot,config,cpu_lock,cpu,root,repository=context(plan)
    hosted_lock=published(plan['hosted_lock'],repository);hosted=published(plan['hosted_result'],repository)
    cleanup=published(plan['hosted_cleanup'],repository)
    if (hosted_lock.get('gate')!='PILOT_MONITOR_HOSTED' or hosted_lock.get('snapshot_lock')!=plan['snapshot_lock']
            or hosted.get('stage')!='PILOT_MONITOR_HOSTED' or hosted.get('lock_sha256')!=plan['hosted_lock']['sha256']):
        raise ValueError('hosted monitor belongs to another snapshot')
    raw_ref=hosted['private_result'];raw=read(raw_ref)
    if any(raw.get(k)!=v for k,v in hosted.items() if k!='private_result'):
        raise ValueError('published hosted result differs from retained full receipt')
    controls={'formal_specification_coverage':published(plan['coverage_controls_result'],repository),
              'hidden_test_coverage':published(plan['hidden_controls_result'],repository)}
    strict=json.loads((root/'strict/terminal.json').read_text())
    if strict['snapshot_sha256']!=plan['snapshot_lock']['sha256'] or strict['cleanup_unresolved']!=0:
        raise ValueError('monitor strict scoring is not cleanly accounted')
    inputs=json.loads(Path(cpu_lock['configuration']['inputs']).read_text())
    hidden_path=root/'hidden/assembled_input.json'
    write_new(hidden_path,{**cpu,'rows':json.loads((root/'hidden/rows.json').read_text())})
    result=assemble(manifest,inputs,scoring_ref=strict['scoring'],hidden_ref={'path':str(hidden_path),'sha256':digest(hidden_path)},
        hosted_ref=raw_ref,controls=controls,hosted_cleanup_ref=plan['hosted_cleanup'],output=root/'measurements')
    result.update(**{k:snapshot[k] for k in ('execution_sha256','model_binding_sha256')},snapshot_lock=plan['snapshot_lock'])
    public=HERE/f"monitor_measurements_S2_{snapshot['arm']}_{snapshot['run_seed']}_u{snapshot['update']}.json"
    write_new(public,result)
    # This result must be published first; a later call binds its actual revision
    # in the decision input lock. No statistic is computed by this preparation.
    return {'status':'MEASUREMENTS_PREPARED_FOR_PUBLICATION','path':str(public),'sha256':digest(public),
            'admission_statistics_computed':False,'model_calls':0}


def freeze_decision(plan):
    snapshot,manifest,pilot,config,cpu_lock,cpu,root,repository=context(plan)
    current=published(plan['current'],repository)
    if (current.get('gate')!='PILOT_MONITOR_MEASUREMENTS' or current.get('status')!='ACCOUNTED'
            or current.get('snapshot_lock')!=plan['snapshot_lock']
            or any(current.get(k)!=snapshot[k] for k in ('arm','run_seed','update','execution_sha256','model_binding_sha256'))):
        raise ValueError('monitor measurement publication belongs to another checkpoint')
    from monitor_decision import measurement
    measurement(plan['current'],repository,execution_sha=snapshot['execution_sha256'],
        **{k:snapshot[k] for k in ('arm','run_seed','update')})
    paths={Path(b['path']) for b in pilot['bindings']+snapshot['bindings']}
    refs=[plan['current'],plan['snapshot_lock'],config['monitor']['cohort'],
          plan['coverage_controls_result'],plan['hidden_controls_result']]
    refs += [current[k] for k in ('rows','availability')]+list(current['cell_receipts'].values())
    for ref in current['cell_receipts'].values():
        refs.extend(read(ref)['source_bindings'])
    baseline=plan.get('baseline');initial=plan.get('baseline_decision')
    if snapshot['update']:
        if not baseline or not initial:raise ValueError('later monitor requires its own published initial baseline')
        first=published(initial,repository);base=published(baseline,repository)
        if (first.get('gate')!='PILOT_MONITOR' or first.get('status')!='CONTINUE'
                or first.get('measurement_sha256')!=baseline['sha256'] or first.get('update')!=0
                or any(base.get(k)!=snapshot[k] for k in ('arm','run_seed','execution_sha256'))):
            raise ValueError('monitor baseline belongs to another pilot or was not admitted')
        refs.extend([baseline,initial,base['rows'],base['availability'],*base['cell_receipts'].values()])
        for ref in base['cell_receipts'].values():refs.extend(read(ref)['source_bindings'])
    elif baseline or initial:raise ValueError('initial monitor cannot use another baseline')
    for ref in refs:
        if digest(ref['path'])!=ref['sha256']:raise ValueError('decision input changed before publication')
        paths.add(Path(ref['path']))
    lock={'condition':'v2-S2','gate':'PILOT_MONITOR_DECISION_INPUTS','status':'FROZEN',
        **{k:snapshot[k] for k in ('arm','run_seed','update')},
        'pilot_execution_lock':plan['learning']['run']['execution_lock'],'current':plan['current'],
        'baseline':baseline,'baseline_decision':initial,
        'coverage_controls_result':plan['coverage_controls_result'],'hidden_controls_result':plan['hidden_controls_result'],
        'configuration':{'root':str(root/'decision'),'cohort':config['monitor']['cohort']},'bindings':bindings(paths),
        'admission_statistics_computed':False,'model_calls':0}
    target=HERE.parent/'locks'/f"PILOT_MONITOR_DECISION_S2_{snapshot['arm']}_{snapshot['run_seed']}_u{snapshot['update']}.json"
    write_new(target,lock)
    return {'status':'PREPARED_FOR_PUBLICATION','path':str(target),'sha256':digest(target),'admission_statistics_computed':False}
