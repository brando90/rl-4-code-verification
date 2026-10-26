"""Publish one fixed pilot-monitor decision from complete source-bound baseline and current measurement receipts."""
from __future__ import annotations

import json
from pathlib import Path
import time

from audit_monitor import COVERAGE,METRICS,available_coverage,evaluate,mean_bounds,validate
from technical_ledger import published
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def read_checked(reference):
    path=Path(reference['path'])
    if digest(path)!=reference['sha256']:raise ValueError('monitor measurement bytes changed')
    return json.loads(path.read_text())


def measurement(reference,repository,*,execution_sha,arm,run_seed,update):
    """Availability hashes must resolve to retained cell bytes, not only plausible digest strings."""
    header=published(reference,repository)
    expected={'condition':'v2-S2','gate':'PILOT_MONITOR_MEASUREMENTS','status':'ACCOUNTED','declared':32,'accounted':32,
              'execution_sha256':execution_sha,'arm':arm,'run_seed':run_seed,'update':update}
    if any(header.get(k)!=v for k,v in expected.items()):raise ValueError('monitor measurements belong to another run or checkpoint')
    rows=read_checked(header['rows']);availability=read_checked(header['availability'])
    if set(availability)!=set(COVERAGE):raise ValueError('both independent monitoring routes required')
    table={r['audit_id']:r for r in rows}
    if len(rows)!=32 or len(table)!=32:raise ValueError('monitor row denominator changed')
    retained=header['cell_receipts']
    if set(retained)!=set(table):raise ValueError('monitor retained-receipt denominator changed')
    for key,reference in retained.items():
        value=read_checked(reference)
        if value['measurement']!=table[key]:raise ValueError('monitor row differs from its retained measurement')
        if not value.get('source_bindings'):raise ValueError('monitor cell lacks source evidence')
        for source in value['source_bindings']:
            if digest(source['path'])!=source['sha256']:raise ValueError('monitor source evidence changed')
        for metric in COVERAGE:
            cell=availability[metric]['cells'].get(key)
            if cell is None or cell['receipt_sha256']!=reference['sha256']:
                raise ValueError('monitor availability is detached from retained measurement bytes')
    return header,rows,availability


def baseline_decision(rows,manifest,*,arm,run_seed,availability):
    """At update zero require a functioning own-run baseline; do not invent a pre-baseline comparison."""
    table=validate(rows,manifest,arm)
    if any(r['run_seed']!=run_seed or r['update']!=0 for r in rows):raise ValueError('monitor baseline identity changed')
    complete=all(row.get(metric) is not None for row in rows for metric in ('reward','theorem_count'))
    metrics={};paired={metric:{'baseline':availability[metric],'current':availability[metric]} for metric in COVERAGE}
    for metric in METRICS:
        functioning=available_coverage(paired,table,table,metric) if metric in COVERAGE else None
        values=[r[metric] for r in rows if r.get(metric) is not None]
        if metric in COVERAGE:complete=complete and functioning and bool(values)
        metrics[metric]={'paired_observed':len(values),'declared':len(rows),'baseline_mean':sum(values)/len(values) if values else None,
                         'baseline_full_manifest':mean_bounds(table,metric),'available_route_and_complete_accounting':functioning}
    return {'condition':'v2-S2','arm':arm,'run_seed':run_seed,'update':0,'declared':len(rows),
            'status':'CONTINUE' if complete else 'INCOMPLETE','stop_metrics':[],'metrics':metrics,'missing_values_imputed':False,
            'p_value':None,'interpretation':'fixed own-run baseline availability check; no efficacy or noninferiority claim'}


def run(plan):
    lock=published(plan['lock'],plan['repository'])
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('PILOT_MONITOR_DECISION_INPUTS','v2-S2','FROZEN'):
        raise ValueError('published monitor decision inputs required')
    pilot=published(lock['pilot_execution_lock'],plan['repository'])
    if (pilot.get('gate'),pilot.get('condition'),pilot.get('status'))!=('LEARNING_PILOT','v2-S2','FROZEN'):
        raise ValueError('monitor decision requires its admitted learning pilot')
    science={b['path']:b['sha256'] for b in pilot['bindings']}
    for path in (Path(__file__).resolve(),HERE/'audit_monitor.py',HERE/'MONITOR_S2_METHOD.md'):
        if science.get(str(path))!=digest(path):raise ValueError('monitor decision method not frozen before learning')
    for key in ('coverage_controls_result','hidden_controls_result'):
        controls=published(lock[key],plan['repository'])
        if controls.get('condition')!='v2-S2' or controls.get('status')!='PASS':raise ValueError('independent coverage controls have not passed')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):
        raise ValueError('monitor decision binding changed')
    config=lock['configuration'];manifest=read_checked(config['cohort'])['cells']
    if bound.get(config['cohort']['path'])!=config['cohort']['sha256'] or science.get(config['cohort']['path'])!=config['cohort']['sha256']:
        raise ValueError('monitor cohort differs from the pre-learning freeze')
    identity={k:lock[k] for k in ('arm','run_seed','update')}
    if identity['arm'] not in ('B','C') or identity['run_seed']!=1301 or identity['update'] not in (0,10,20,30):
        raise ValueError('undeclared monitor decision')
    execution_sha=lock['pilot_execution_lock']['sha256']
    current,rows,availability=measurement(lock['current'],plan['repository'],execution_sha=execution_sha,**identity)
    snapshot=published(current['snapshot_lock'],plan['repository'])
    if (snapshot.get('gate')!='PILOT_MONITOR_SNAPSHOT' or snapshot.get('status')!='FROZEN' or snapshot.get('condition')!='v2-S2'
            or snapshot.get('execution_sha256')!=execution_sha or any(snapshot.get(k)!=v for k,v in identity.items())
            or snapshot.get('model_binding_sha256')!=current['model_binding_sha256']):
        raise ValueError('monitor decision checkpoint differs from the pre-response snapshot')
    baseline_rows=baseline_availability=None
    if identity['update']:
        baseline,baseline_rows,baseline_availability=measurement(lock['baseline'],plan['repository'],
            execution_sha=execution_sha,**{**identity,'update':0})
        initial=published(lock['baseline_decision'],plan['repository'])
        if (initial.get('gate')!='PILOT_MONITOR' or initial.get('status')!='CONTINUE' or initial.get('update')!=0
                or initial.get('measurement_sha256')!=lock['baseline']['sha256']
                or initial.get('execution_sha256')!=execution_sha):raise ValueError('own-run baseline did not admit monitoring')
    elif lock.get('baseline') is not None or lock.get('baseline_decision') is not None:
        raise ValueError('initial monitor must not use another baseline')
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    write_new(root/'evaluation_attempt.json',{'condition':'v2-S2','lock_sha256':plan['lock']['sha256'],
                                            'started_unix':time.time(),'automatic_retry':False})
    if identity['update']==0:
        result=baseline_decision(rows,manifest,arm=identity['arm'],run_seed=identity['run_seed'],availability=availability)
    else:
        receipts={metric:{'baseline':baseline_availability[metric],'current':availability[metric]} for metric in COVERAGE}
        result=evaluate(baseline_rows,rows,manifest,coverage_availability=receipts,**identity)
    result.update(gate='PILOT_MONITOR',execution_sha256=execution_sha,model_binding_sha256=current['model_binding_sha256'],
                  measurement_sha256=lock['current']['sha256'],decision_lock_sha256=plan['lock']['sha256'],
                  admission_statistics_computed=True)
    write_new(root/'result.json',result);return result
