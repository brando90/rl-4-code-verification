"""Supervise one exclusive historical-evaluation stage on its canonical main-run lease and retain cleanup."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from device_binding import launch_environment
from lp1 import cleanup
from anchor_lease import release
from a6_evaluation_authority import authorize as snapshot_authority
from technical_ledger import check_preflight
from training_checkpoint import digest,write_new


def authorize(plan):
    lp,execution,config,snapshot=snapshot_authority(plan);run=plan['learning']['run']
    stage=plan['stage'];key=plan['stage_key'];prefix=f"{snapshot['purpose']}_b{snapshot['boundary']}"
    if (stage not in ('evaluation_preflight','evaluation_generate') or
            (key!=prefix+'_preflight' if stage=='evaluation_preflight' else re.fullmatch(re.escape(prefix)+r'_s[0-9]{3}',key) is None)):
        raise ValueError('undeclared evaluation stage identity')
    runtime=json.loads(Path(plan['config']).read_text());settings=snapshot['configuration'];root=Path(settings['root'])
    expected={'condition':'v2-S2','stage':stage,'stage_key':key,'purpose':snapshot['purpose'],'arm':run['arm'],
        'run_seed':run['run_seed'],'boundary':snapshot['boundary'],'model':snapshot['model'],
        'model_binding_sha256':snapshot['model_binding_sha256'],'snapshot_sha256':plan['snapshot_lock']['sha256'],
        'manifest':settings['manifest'],'allowlist':settings['allowlist'],'stage_root':str(root/key/'output'),
        'attempt_root':str(root/key/'health')}
    if any(runtime.get(k)!=v for k,v in expected.items()):raise ValueError('evaluation runtime identity or paths changed')
    contract=lp['configuration']['evaluation_runtime_contract']
    if any(runtime.get(k)!=v for k,v in contract.items()):raise ValueError('evaluation numerical contract differs from LP')
    runtime_bindings={b['path']:b['sha256'] for b in runtime['bindings']}
    if len(runtime_bindings)!=len(runtime['bindings']):raise ValueError('duplicate evaluation runtime binding')
    if any(runtime_bindings.get(b['path'])!=b['sha256'] for b in snapshot['bindings']):
        raise ValueError('evaluation runtime omitted published snapshot inputs')
    reservation=Path(plan['reservation'])
    if reservation!=root/(key+'.json') or Path(plan['dispatch_root'])!=root/key/'dispatch':
        raise ValueError('exclusive evaluation reservation moved')
    record=json.loads(reservation.read_text())
    expected_record={'L2_sha256':run['execution_lock']['sha256'],'snapshot_sha256':plan['snapshot_lock']['sha256'],
        'stage':stage,'stage_key':key,'configuration_sha256':digest(plan['config'])}
    if any(record.get(k)!=v for k,v in expected_record.items()):raise ValueError('evaluation differs from its exclusive reservation')
    if stage=='evaluation_generate':
        prior=root/(prefix+'_preflight');health=prior/'health/preflight.json';closed=prior/'dispatch/result.json'
        if any(runtime_bindings.get(str(p))!=digest(p) for p in (health,closed)):
            raise ValueError('evaluation preflight evidence is unbound')
        check_preflight({'path':str(health),'sha256':digest(health)})
        result=json.loads(closed.read_text())
        if (result.get('status')!='RUNTIME_EXITED_ZERO' or result.get('cleanup_verified') is not True
                or result.get('snapshot_sha256')!=plan['snapshot_lock']['sha256']):
            raise ValueError('same-checkpoint evaluation preflight did not pass cleanly')
        if record.get('indexes')!=runtime.get('indexes'):raise ValueError('evaluation segment changed after reservation')
    lease=json.loads(Path(runtime['lease_path']).read_text())
    canonical=json.loads((Path(plan['lease_root'])/(lease['id']+'.json')).read_text())
    if (lease!=canonical or lease['phase']!='v2-S2-main' or lease['owner']!='e13v2' or lease['status']!='ACTIVE'
            or lease['id']!=runtime['lease_id'] or lease['host']!=socket.gethostname().split('.')[0]
            or lease['run_key']!=f"{run['arm']}/{run['run_seed']}/{snapshot['boundary']}/{key}"):
        raise ValueError('evaluation device is not its canonical local main-run allocation')
    maximum=plan['maximum_seconds']
    if not 90<maximum<=lease['expires_unix']-lease['started_unix']:raise ValueError('evaluation exceeds its lease')
    if record['lease_id']!=lease['id'] or record['maximum_seconds']!=maximum:raise ValueError('evaluation reservation budget changed')
    return runtime,lease,record


def launch_reserved(plan):
    config,lease,reservation=authorize(plan)
    root=Path(plan['dispatch_root']);root.mkdir(parents=True,exist_ok=False)
    run=plan['learning']['run']
    result={'condition':'v2-S2','phase':'main','arm':run['arm'],'run_seed':run['run_seed'],
        'purpose':config['purpose'],'boundary':config['boundary'],'stage':plan['stage'],'stage_key':plan['stage_key'],
        'lease_id':lease['id'],'automatic_retry':False,'status':'INCOMPLETE_INFRA',
        'snapshot_sha256':plan['snapshot_lock']['sha256'],'model_binding_sha256':config['model_binding_sha256']}
    try:
        env=launch_environment(lease,'main',{**os.environ,**plan['environment']})
        now=time.time();remaining=min(now+plan['maximum_seconds'],lease['expires_unix'])-now-90
        if remaining<=0:raise TimeoutError('evaluation lease expired before dispatch')
        write_new(root/'launch.json',{**result,'started_unix':now,'maximum_seconds':plan['maximum_seconds'],
            'visible_index':env['CUDA_VISIBLE_DEVICES'],'configuration_sha256':digest(plan['config']),
            'reservation_sha256':digest(plan['reservation']),'pid':os.getpid(),
            'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
        with (root/'execution.log').open('x') as log:
            child=subprocess.Popen([config['python'],str(HERE/'evaluation_runtime.py'),'--config',plan['config'],
                '--stage',plan['stage']],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            write_new(root/'process.json',{'pid':child.pid,'marker':lease['id'],
                'start_ticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],
                'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
            result['worker_exit_code']=child.wait(timeout=remaining)
        if result['worker_exit_code']:raise RuntimeError('evaluation runtime exited nonzero; preserve every completed output')
        result['status']='RUNTIME_EXITED_ZERO'
    except BaseException as exc:result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        cleaned=cleanup(lease['id']);write_new(root/'cleanup.json',cleaned)
        released=release(plan['lease_root'],lease['id'],cleanup_verified=cleaned['verified'])
        result.update(cleanup_verified=cleaned['verified'],released=released,ended_unix=time.time())
        if not cleaned['verified']:result['status']='CLEANUP_REQUIRED'
        write_new(root/'result.json',result)
    return result


def launch(plan):
    _,_,_,snapshot=snapshot_authority(plan)
    with (Path(snapshot['configuration']['root'])/'device_controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return launch_reserved(plan)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True,type=Path);a=p.parse_args()
    result=launch(json.loads(a.plan.read_text()));print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result['status']=='RUNTIME_EXITED_ZERO' else 1)
