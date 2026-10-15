"""Supervise one bounded S2 anchor generation segment and verify all owned process cleanup."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from anchor_runtime import check_bindings
from runtime import check_lease
from lp1 import cleanup
from anchor_storage import write_new,mkdir


def run(config_path):
    config=json.loads(Path(config_path).read_text());check_bindings(config);check_lease(config)
    marker=os.environ['E13_EXECUTION_ID'];lease=json.loads(Path(config['lease_path']).read_text())
    if marker!=lease['id']:raise ValueError('execution marker differs from claimed device lease')
    root=Path(config['attempt_root']);mkdir(root)
    launch={'condition':'v2-S2','batch':config['batch'],'segment_id':config['segment_id'],
            'lease_id':marker,'started_unix':time.time(),'maximum_seconds':config['maximum_seconds'],
            'numerical_dtype':'float16','optimizer_updates':0,'pid':os.getpid(),'pgid':os.getpgid(os.getpid()),
            'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    write_new(root/'launch.json',launch)
    result={**launch,'status':'INCOMPLETE_INFRA'};checks=[]
    deadline=min(time.time()+config['maximum_seconds'],lease['expires_unix'])
    def interrupted(signum,frame):raise TimeoutError('anchor segment interrupted')
    previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGTERM,signal.SIGHUP)}
    try:
        for stage in ('preflight','generate'):
            if stage=='generate' and json.loads((root/'preflight.json').read_text())['status']!='PASS':
                raise RuntimeError('anchor preflight did not pass')
            check_lease(config);remaining=deadline-time.time()-90
            if remaining<=0:raise TimeoutError('anchor segment allocation exhausted')
            with (root/(stage+'.log')).open('x') as log:
                child=subprocess.run([config['python'],str(Path(__file__).with_name('anchor_runtime.py')),
                    '--config',str(config_path),'--stage',stage],stdout=log,stderr=subprocess.STDOUT,
                    start_new_session=True,timeout=remaining,check=False)
            cleaned=cleanup(marker);checks.append(cleaned)
            if child.returncode or not cleaned['verified']:
                raise RuntimeError(stage+' failed or left an owned process')
        result.update(json.loads((root/'generation_segment.json').read_text()))
    except BaseException as exc:
        result.update(error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        checks.append(cleanup(marker));result['cleanup_verified']=all(c['verified'] for c in checks)
        if not result['cleanup_verified']:result['status']='CLEANUP_REQUIRED'
        result['ended_unix']=time.time();write_new(root/'cleanup.json',checks);write_new(root/'result.json',result)
        for sig,handler in previous.items():signal.signal(sig,handler)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True)
    print(json.dumps(run(parser.parse_args().config),sort_keys=True))
