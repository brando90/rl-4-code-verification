"""Bound an admitted technical stage by its owned lease and retain failure and cleanup evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from runtime import check_lease
from lp1 import cleanup
from g1_driver import verify_publication
from training_checkpoint import digest,write_new

STAGES=('preflight','generate','probabilities','update','replay','export')


def authorize(plan_path):
    plan=json.loads(Path(plan_path).read_text())
    lock=verify_publication(plan['lock'],plan['repository'],plan['published_revision'])
    if lock.get('condition')!='v2-S2' or lock.get('gate')!='LP' or lock.get('status')!='FROZEN':
        raise ValueError('published S2 pilot lock required')
    sources={b['path']:b['sha256'] for b in lock['bindings']}
    required=[HERE/'technical_supervisor.py',HERE/'technical_runtime.py',HERE.parent/'phase1/lp1.py',
        HERE.parent/'phase1/runtime.py',HERE.parent/'phase1/g1_driver.py',HERE/'training_checkpoint.py']
    for path in required:
        if sources.get(str(path))!=digest(path):raise ValueError('unbound or changed stage supervisor')
    execution=Path(plan['execution']);record=json.loads(execution.read_text())
    stage=plan['stage']
    wanted_status='PREFLIGHT_RESERVED' if stage=='preflight' else 'ADMITTED'
    if record.get('LP_sha256')!=digest(plan['lock']) or record.get('status')!=wanted_status:
        raise ValueError('technical execution is not admitted under this pilot lock')
    config_path=Path(plan['config']);config=json.loads(config_path.read_text())
    if stage not in STAGES or config['stage']!=stage or config.get('condition')!='v2-S2':raise ValueError('unregistered technical stage')
    entry=record['stages'][plan['stage_key']]
    if entry['stage']!=stage or entry['config_sha256']!=digest(config_path):raise ValueError('stage differs from admitted execution')
    valid_attempt=(record['attempt']==0) if stage=='preflight' else (1<=record['attempt']<=3)
    if record['gate'] not in ('T1','T2','T3','T4') or not valid_attempt:
        raise ValueError('technical attempt is outside the A4 gate scope')
    if record.get('admission_statistics_computed'):raise ValueError('a measured gate cannot launch another stage')
    if entry['maximum_seconds']!=plan['maximum_seconds'] or entry['lease_id']!=config['lease_id']:
        raise ValueError('resource envelope changed')
    # The parent admission driver freezes stage dependencies before dispatch.
    # Its receipt is durably reserved before any child process can execute.
    if stage!='preflight':
        preflight=Path(entry['preflight'])
        p=json.loads(preflight.read_text())
        if digest(preflight)!=entry['preflight_sha256'] or p.get('status')!='PASS' or p.get('admission_statistics_computed') is not False:
            raise ValueError('non-probe preflight admission missing')
    return plan,config


def run(plan_path):
    plan,config=authorize(plan_path);check_lease(config)
    lease=json.loads(Path(config['lease_path']).read_text());marker=os.environ['E13_EXECUTION_ID']
    if marker!=lease['id'] or marker!=config['lease_id']:raise ValueError('execution marker differs from owned lease')
    maximum=plan['maximum_seconds']
    if not isinstance(maximum,(int,float)) or maximum<=90 or maximum>lease['expires_unix']-lease['started_unix']:
        raise ValueError('stage cap exceeds leased allocation')
    root=Path(plan['supervisor_root']);root.mkdir(parents=True,exist_ok=False)
    started=time.time();deadline=min(started+maximum,lease['expires_unix']);remaining=deadline-started-90
    launch={'condition':'v2-S2','stage':plan['stage'],'lease_id':marker,'started_unix':started,
        'maximum_seconds':maximum,'plan_sha256':digest(plan_path),'execution_sha256':digest(plan['execution']),
        'config_sha256':digest(plan['config']),'admission_statistics_computed':False,
        'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
        'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    write_new(root/'launch.json',launch);result={**launch,'status':'INCOMPLETE_INFRA'}
    def interrupted(signum,frame):raise TimeoutError('technical stage interrupted')
    previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGTERM,signal.SIGHUP)}
    try:
        if remaining<=0:raise TimeoutError('technical allocation exhausted before launch')
        with (root/'execution.log').open('x') as log:
            child=subprocess.run([config['python'],str(HERE/'technical_runtime.py'),'--config',plan['config'],
                '--stage',plan['stage']],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,timeout=remaining)
        result['worker_exit_code']=child.returncode
        if child.returncode:raise RuntimeError('technical runtime exited nonzero; no implicit retry')
        # A zero exit alone is not proof of a complete scientific artifact. The
        # admission driver verifies all bound stage receipts before comparing statistics.
        result['status']='RUNTIME_EXITED_ZERO'
    except BaseException as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
    finally:
        cleaned=cleanup(marker);result['cleanup_verified']=cleaned['verified']
        if not cleaned['verified']:result['status']='CLEANUP_REQUIRED'
        result['ended_unix']=time.time();result['device_hours']=(result['ended_unix']-started)/3600
        write_new(root/'cleanup.json',cleaned);write_new(root/'result.json',result)
        for sig,handler in previous.items():signal.signal(sig,handler)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,required=True)
    result=run(parser.parse_args().plan);print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result['status']=='RUNTIME_EXITED_ZERO' else 1)
