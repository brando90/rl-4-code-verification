"""Reconcile the published unadmitted trainer-to-generator handoff failure without replacing any evidence."""
from __future__ import annotations
import argparse,fcntl,json
from pathlib import Path
from a6_technical_driver import authorize,dynamic_config,ORDER,reference
from technical_ledger import published,admit,check_preflight
from technical_resources import reserve
from technical_stage import prepare,launch_local
from training_checkpoint import digest,write_new
from anchor_storage import atomic_json
from costs import snapshot,stage_cost


def verify_failure(root,receipt):
    """Require the exact published pre-admission failure and retained successful model check."""
    root=Path(root)
    if (receipt.get('status')!='INCOMPLETE_INFRA_PRE_ADMISSION'
            or receipt.get('numbered_attempt_3_admitted') is not False
            or receipt.get('admission_statistics_computed') is not False
            or receipt.get('generated_experiment_responses')!=0 or receipt.get('optimizer_updates')!=0
            or receipt.get('cleanup_verified') is not True
            or receipt.get('error_type')!='PermissionError'
            or receipt.get('offloaded_state_preflight',{}).get('status')!='PASS'):
        raise ValueError('not the published unadmitted shutdown handoff failure')
    bindings=receipt['evidence']
    if not bindings or any(digest(row['path'])!=row['sha256'] for row in bindings):
        raise ValueError('preflight failure evidence changed')
    if (root/'generate_update').exists() or (root/'preflight/health/preflight.json').exists():
        raise ValueError('preflight already generated or admitted an engine')
    return True


def verify_unadmitted(state,root,ledger,plan,recovery):
    """Keep the original two numbered failures, pending third attempt and old state identity exact."""
    root=Path(root);ledger=Path(ledger)
    attempts=sorted(ledger.glob('attempt_*/attempt.json'))
    if (plan['gate']!='T2' or plan['attempt']!=3 or len(attempts)!=2
            or 'admission'in state or state.get('status')!='HALTED' or state.get('next_stage')!='preflight'
            or state.get('LP_sha256')!=recovery['previous_preflight_LP']['sha256']
            or state.get('configuration_sha256')!=recovery['previous_configuration_sha256']
            or (ledger/'attempt_3').exists()):
        raise ValueError('only the exact unadmitted third-attempt preflight may be reconciled')
    for number,path in enumerate(attempts,1):
        a=json.loads(path.read_text());result=json.loads((path.parent/'result.json').read_text())
        if (a.get('attempt')!=number or result.get('status')!='INCOMPLETE_INFRA'
                or result.get('admission_statistics_computed') is not False
                or (path.parent/'evaluation_attempt.json').exists()):
            raise ValueError('numbered gate history is not two infrastructure-only failures')


def tick(plan):
    lock,config,science=authorize(plan)
    fix=published(plan['successor'],plan['repository']);recovery=fix['preflight_recovery']
    if (fix.get('gate')!='A4_TECHNICAL_FIX' or fix.get('status')!='FROZEN'
            or fix.get('science_sha256')!=science or fix.get('successor_LP')!=plan['LP']):
        raise ValueError('published same-science recovery successor required')
    bound={x['path']:x['sha256']for x in lock['bindings']}
    if bound.get(str(Path(__file__).resolve()))!=digest(__file__):raise ValueError('reconciliation implementation unbound')
    failed=published(recovery['failed_preflight'],plan['repository'])
    gate=plan['gate'];root=Path(config['work_root'])/gate/f"attempt_{plan['attempt']}"
    with (root/'controller.lock').open('a')as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=root/'state.json';state=json.loads(path.read_text())
        verify_failure(root,failed)
        verify_unadmitted(state,root,Path(lock['configuration']['technical_ledger'])/gate,plan,recovery)
        polls=root/'preflight_handoff';polls.mkdir(exist_ok=True)
        for folder in polls.glob('poll_*'):
            terminal=folder/'terminal.json'
            if not terminal.exists() or json.loads(terminal.read_text()).get('status')!='WAIT_FOR_IDLE_DEVICE':
                raise RuntimeError('prior handoff launch is not replayable')
        number=len(list(polls.glob('poll_*')));folder=polls/f'poll_{number:04d}';folder.mkdir()
        write_new(folder/'before.json',state)
        seconds=config['stage_seconds'][gate]['preflight']
        resource={**plan['resource_plan'],'LP':plan['LP'],'repository':plan['repository']}
        reserved=reserve(resource,gate=gate,attempt=plan['attempt'],stage_key=f'preflight_handoff_{number:04d}',seconds=seconds)
        write_new(folder/'reservation.json',reserved)
        if reserved['status']in ('WAIT_FOR_IDLE_DEVICE','DEVICE_CHANGED_BEFORE_LAUNCH'):
            result={'status':'WAIT_FOR_IDLE_DEVICE','numbered_attempt_admitted':False}
            write_new(folder/'terminal.json',result);return result
        if reserved['status']!='RESERVED':
            write_new(folder/'terminal.json',reserved);return reserved
        lease=reserved['lease'];before=snapshot(root)
        try:
            runtime=dynamic_config(config,gate,'preflight',folder,lease)
            stage_plan=prepare(LP=plan['LP'],repository=plan['repository'],gate=gate,stage_key='preflight',
                config_path=runtime,maximum_seconds=seconds,preparation_root=folder/'preflight/dispatch')
            result=launch_local(stage_plan,lease_root=resource['lease_root'],route_environment=config['environment'])
        finally:
            from resource_lease import release
            from lp1 import cleanup
            canonical_path=Path(resource['lease_root'])/(lease['id']+'.json');canonical=json.loads(canonical_path.read_text())
            if canonical['status']!='RELEASED':
                cleaned=cleanup(lease['id']);release(resource['lease_root'],lease['id'],cleanup_verified=cleaned['verified'])
            else:
                cp=folder/'preflight/dispatch/dispatch_cleanup.json';cleaned=json.loads(cp.read_text())if cp.exists()else None
            canonical=json.loads(canonical_path.read_text())
            write_new(root/'costs'/f'preflight_handoff_{number:04d}.json',stage_cost(before,snapshot(root),stage='preflight',lease=canonical,cleanup=cleaned))
        if result['status']!='RUNTIME_FINISHED':
            write_new(folder/'terminal.json',result);return result
        h=folder/'preflight/health';health=reference(h/'preflight.json');check_preflight(health)
        actual=json.loads((h/'dtensor_state_preflight.json').read_text())
        if actual.get('status')!='PASS' or actual.get('shutdown',{}).get('status')!='PASS':
            raise ValueError('real model hashing and completed worker shutdown required')
        attempt_root,admitted=admit(lock['configuration']['technical_ledger'],gate,LP=plan['LP'],
            repository=plan['repository'],preflight=health,prerequisites=plan['prerequisites'],successor=plan['successor'])
        if admitted['attempt']!=3:raise ValueError('prospective third admission changed')
        state.update(status='READY',next_stage=ORDER[gate][0],last_stage='preflight',preflight=health,
            admission=str(attempt_root/'attempt.json'),LP_sha256=plan['LP']['sha256'],
            configuration_sha256=digest(plan['configuration']),preflight_handoff_lock=plan['successor'])
        state.pop('stage_result',None);atomic_json(path,state)
        result={'status':'PREFLIGHT_RECOVERED','numbered_attempt_admitted':True,'admission':state['admission']}
        write_new(folder/'terminal.json',result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',required=True,type=Path)
    print(json.dumps(tick(json.loads(parser.parse_args().plan.read_text()))))
