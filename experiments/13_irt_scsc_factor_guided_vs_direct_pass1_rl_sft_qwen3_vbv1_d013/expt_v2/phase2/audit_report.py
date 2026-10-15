"""Bind the fixed train mutation report to actual independent route evidence and the pre-audit analysis method."""
from __future__ import annotations

import json
from pathlib import Path

from audit_analysis import evaluate
from audit_coverage import validate
from technical_ledger import published
from technical_driver import read
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def cleanup_verified(hosted,cleanup):
    if hosted['declared_ratings']==0:
        return cleanup.get('status')=='NO_SERVICE_REQUIRED' and cleanup.get('model_calls')==0
    operations=cleanup.get('owned_remote_entries_removed',[])
    return (cleanup.get('registered_processes_exited') is True and cleanup.get('port_free') is True
        and {r.get('operation') for r in operations}=={'service','auth_secret'}
        and all(r.get('exit_code')==0 for r in operations))


def assemble(inputs,cpu,hosted,controls,cleanup,*,train,C_weights=None):
    if set(controls)!={'hidden','formal'} or any(v.get('condition')!='v2-S2' or v.get('status')!='PASS' for v in controls.values()):
        raise ValueError('both independent audit routes require their published controls')
    if (cpu.get('stage')!='TRAIN_AUDIT_CPU' or cpu.get('condition')!='v2-S2' or cpu.get('status')!='ACCOUNTED'
            or cpu.get('declared')!=128 or cpu.get('accounted')!=128
            or hosted.get('stage')!='TRAIN_AUDIT_HOSTED' or hosted.get('condition')!='v2-S2' or hosted.get('declared')!=128):
        raise ValueError('complete declared audit route accounting required')
    if hosted['declared_ratings'] and (hosted.get('actual_bundle_verified') is not True or hosted.get('requested_identity_verified') is not True):
        raise ValueError('actual hosted executable and requested judge identities must match')
    table=validate(inputs,cpu['rows'],train)
    formal={r['cell_id']:r for r in hosted['rows']}
    if len(formal)!=128 or set(formal)!=set(table):raise ValueError('hosted audit population changed')
    for cell in inputs['cells']:
        row=table[cell['cell_id']];coverage=formal[cell['cell_id']]
        if coverage['compile']!=row['compile']:raise ValueError('hosted coverage compile gate differs from its source')
        if row.get('strict_receipt'):
            strict=read(row['strict_receipt'])
            if strict['status']!=row.get('strict_status'):raise ValueError('audit strict status differs from its physical receipt')
            if strict['status']=='measured' and (strict.get('strict')!=row.get('strict') or strict!=row.get('components')):
                raise ValueError('audit components differ from the frozen oracle/probe receipt')
        if row.get('hidden_receipt'):
            hidden=read(row['hidden_receipt'])
            expected=hidden.get('hidden_pass_rate') if hidden.get('fully_applicable') or hidden['status']=='compile_failure' else None
            if hidden['status']!=row.get('hidden_status') or expected!=row.get('hidden_test_coverage'):
                raise ValueError('audit hidden score differs from its independent receipt')
        elif row.get('hidden_test_coverage') is not None:raise ValueError('audit hidden score lacks independent source evidence')
    result=evaluate(inputs,cpu['rows'],hosted['rows'],C_weights=C_weights)
    clean=cpu.get('cleanup_unresolved')==0 and cleanup_verified(hosted,cleanup)
    known={'hidden':sum(r['hidden_test_coverage'] is not None for r in result['rows']),
        'formal':sum(r['formal_specification_coverage'] is not None for r in result['rows'])}
    result.update(status='ACCOUNTED' if clean else 'CLEANUP_REQUIRED',independent_checks_functioning=clean and all(known.values()),
        independent_coverage_known=known,hosted_cleanup_verified=cleanup_verified(hosted,cleanup),
        declared_mutation_comparisons=96,accounted_mutation_comparisons=len(result['comparisons']))
    return result


def run(plan):
    repo=plan['repository'];lock=published(plan['lock'],repo)
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('TRAIN_AUDIT_ANALYSIS_INPUTS','v2-S2','FROZEN'):
        raise ValueError('published train audit analysis inputs required')
    sources={b['path']:b['sha256'] for b in lock['bindings']}
    if len(sources)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in sources.items()):raise ValueError('audit analysis input changed')
    cpu_lock=published(lock['cpu_lock'],repo);hosted_lock=published(lock['hosted_lock'],repo)
    method={b['path']:b['sha256'] for b in cpu_lock['bindings']}
    for path in (Path(__file__).resolve(),HERE/'audit_analysis.py',HERE/'audit_coverage.py',HERE/'arm_rewards.py'):
        if method.get(str(path))!=digest(path):raise ValueError('audit analysis method was not bound before mutation measurements')
    controls={key:published(ref,repo) for key,ref in lock['controls'].items()}
    monitor=published(lock['monitor_method'],repo)
    if monitor.get('condition')!='v2-S2' or monitor.get('status')!='FROZEN':raise ValueError('prospective pilot monitoring method required')
    cpu=published(lock['cpu_result'],repo);published_hosted=published(lock['hosted_result'],repo)
    config=lock['configuration'];hosted=read(config['hosted_full']);rows=read(config['cpu_rows']);inputs=read(config['inputs'])
    if (cpu['execution_sha256']!=lock['cpu_lock']['sha256'] or cpu['rows_sha256']!=config['cpu_rows']['sha256']
            or hosted['lock_sha256']!=lock['hosted_lock']['sha256']
            or hosted_lock['cpu_execution_lock']['sha256']!=lock['cpu_lock']['sha256']):
        raise ValueError('audit measurements belong to another execution')
    if published_hosted.get('private_result')!=config['hosted_full'] or any(hosted.get(k)!=v for k,v in published_hosted.items() if k!='private_result'):
        raise ValueError('published hosted audit differs from retained measurements')
    if digest(cpu_lock['configuration']['inputs'])!=config['inputs']['sha256']:raise ValueError('audit task/variant input changed')
    weights_ref=cpu_lock['analysis']['C_weights']
    if config.get('C_weights')!=weights_ref:raise ValueError('audit C weighting changed after mutation measurements')
    weights=read(weights_ref) if weights_ref else None
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'attempt.json',{'analysis_lock':plan['lock'],'automatic_retry':False})
    value=assemble(inputs,{**cpu,'rows':rows},hosted,controls,read(config['hosted_cleanup']),
        train=Path(config['train_ids']).read_text().splitlines(),C_weights=weights)
    write_new(root/'private_result.json',value)
    public={k:v for k,v in value.items() if k not in ('rows','comparisons','required_next')}
    public.update(analysis_lock_sha256=plan['lock']['sha256'],cpu_lock_sha256=lock['cpu_lock']['sha256'],
        hosted_lock_sha256=lock['hosted_lock']['sha256'],controls=lock['controls'],monitor_method=lock['monitor_method'],
        private_result={'path':str(root/'private_result.json'),'sha256':digest(root/'private_result.json')},
        learning_admitted=False,required_next='published technical gates and learning execution lock; retain every reward-increasing mutation')
    write_new(root/'result.json',public);return public
