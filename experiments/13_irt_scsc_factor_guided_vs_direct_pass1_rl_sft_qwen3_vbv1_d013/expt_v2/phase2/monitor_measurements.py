"""Join all fixed monitor measurements and retain physical per-cell evidence for the published stop decision."""
from __future__ import annotations

import json
from pathlib import Path

from monitor_preparation import reward_rows
from monitor_coverage import validate,IDENTITY
from audit_monitor import COVERAGE
from training_checkpoint import digest,write_new


def checked(reference):
    if digest(reference['path'])!=reference['sha256']:raise ValueError('monitor source receipt changed')
    return json.loads(Path(reference['path']).read_text())


def assemble(snapshot,inputs,*,scoring_ref,hidden_ref,hosted_ref,controls,hosted_cleanup_ref,output):
    """Caller binds the published snapshot/execution and controls; no scorer or judge is invoked here."""
    scoring=checked(scoring_ref);hidden=checked(hidden_ref);hosted=checked(hosted_ref);cleanup=checked(hosted_cleanup_ref)
    if (hidden.get('condition')!='v2-S2' or hidden.get('stage')!='PILOT_MONITOR_HIDDEN' or hidden.get('declared')!=32
            or hidden.get('accounted')!=32 or hosted.get('condition')!='v2-S2' or hosted.get('stage')!='PILOT_MONITOR_HOSTED'
            or hosted.get('declared')!=32):raise ValueError('complete monitor route accounting required')
    if set(controls)!=set(COVERAGE):raise ValueError('both independent monitor controls required')
    if any(c.get('condition')!='v2-S2' or c.get('status')!='PASS' for c in controls.values()):
        raise ValueError('independent monitor controls have not passed')
    identity={k:snapshot[k] for k in ('arm','run_seed','update')}
    if any(inputs.get(k)!=v for k,v in identity.items()):raise ValueError('normalized monitor snapshot changed')
    table=validate(inputs,hidden['rows'],[c['task_id'] for c in snapshot['cells']])
    formal={r['cell_id']:r for r in hosted['rows']}
    if len(formal)!=32 or set(formal)!=set(table):raise ValueError('hosted monitor denominator changed')
    expected={c['cell_id']:c for c in snapshot['cells']}
    normalized={c['cell_id']:c for c in inputs['cells']}
    if len(expected)!=32 or set(expected)!=set(table):raise ValueError('monitor source snapshot denominator changed')
    rows=reward_rows(snapshot,scoring['rows']);root=Path(output);root.mkdir(parents=True,exist_ok=False)
    route_clean=(cleanup.get('registered_processes_exited') is True and cleanup.get('port_free') is True
        and {r.get('operation') for r in cleanup.get('owned_remote_entries_removed',[])}=={'service','auth_secret'}
        and all(r.get('exit_code')==0 for r in cleanup['owned_remote_entries_removed']))
    # A zero-compiled-file pack has no service to deploy. Preserve that explicit
    # receipt instead of inventing remote deletion operations or model ratings.
    if hosted['declared_ratings']==0:
        route_clean=cleanup.get('status')=='NO_SERVICE_REQUIRED' and cleanup.get('model_calls')==0
    availability={metric:{'status':'ACCOUNTED','route_controls':'PASS','declared':32,'accounted':32,'cells':{},
        'cleanup_verified':route_clean if metric=='formal_specification_coverage' else hidden['cleanup_unresolved']==0}
        for metric in COVERAGE}
    retained={}
    for index,row in enumerate(rows):
        cell=expected[row['cell_id']];a=table[row['cell_id']];b=formal[row['cell_id']]
        if any(b.get(k)!=cell[k] for k in IDENTITY):raise ValueError('hosted monitor identity changed')
        row.update(hidden_test_coverage=a.get('hidden_test_coverage'),formal_specification_coverage=b['formal_specification_coverage'])
        candidate=normalized[row['cell_id']];strict=checked(candidate['strict'])
        references=[scoring_ref,hidden_ref,hosted_ref,hosted_cleanup_ref,candidate['strict'],strict['strict_receipt']]
        references += [ref for ref in (candidate.get('source'),strict.get('oracle_receipt'),a.get('hidden_receipt')) if ref]
        for ref in references:
            if digest(ref['path'])!=ref['sha256']:raise ValueError('monitor cell evidence changed during assembly')
        path=root/f'{index:03d}.json';write_new(path,{'measurement':row,'source_bindings':references})
        reference={'path':str(path),'sha256':digest(path)};retained[row['audit_id']]=reference
        for metric in COVERAGE:
            value=row[metric];gate=a.get('compile')
            if value is not None:
                failed=(gate is False) if metric=='formal_specification_coverage' else a.get('hidden_status')=='compile_failure'
                status='compile_failure' if failed else 'measured'
            elif metric=='hidden_test_coverage' and a.get('hidden_status') in ('not_applicable','no_tests'):status='not_applicable'
            else:status='incomplete'
            availability[metric]['cells'][row['audit_id']]={'status':status,'receipt_sha256':reference['sha256']}
    write_new(root/'rows.json',rows);write_new(root/'availability.json',availability)
    return {'condition':'v2-S2','gate':'PILOT_MONITOR_MEASUREMENTS','status':'ACCOUNTED',**identity,'declared':32,'accounted':32,
            'rows':{'path':str(root/'rows.json'),'sha256':digest(root/'rows.json')},
            'availability':{'path':str(root/'availability.json'),'sha256':digest(root/'availability.json')},
            'cell_receipts':retained,'new_model_calls':0,'new_strict_measurements':0,
            'required_publication_fields':['execution_sha256','model_binding_sha256','snapshot_lock']}
