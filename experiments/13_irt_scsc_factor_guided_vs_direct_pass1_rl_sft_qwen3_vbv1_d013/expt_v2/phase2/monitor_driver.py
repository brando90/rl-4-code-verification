"""Advance a published paused-pilot monitor through one-shot leased preflight and generation, retaining every interruption."""
from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path

from monitor_processing import authority
from monitor_snapshot import materialize
from monitor_supervisor import launch
from learning_resources import reserve
from technical_ledger import check_preflight
from training_checkpoint import digest,write_new
from resource_lease import release
from lp1 import cleanup


def run(plan):
    snapshot,manifest,execution,config=authority(plan)
    scientific={b['path']:b['sha256'] for b in execution['bindings']}
    if scientific.get(str(Path(__file__).resolve()))!=digest(__file__):
        raise ValueError('monitor coordinator was not frozen before learning')
    root=Path(snapshot['configuration']['root']);learning=plan['learning'];run=learning['run']
    resources={**learning['resources'],'run':run}
    with (root/'device_controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for stage in ('monitor_preflight','monitor_generate'):
            stage_root=root/stage;closed=stage_root/'dispatch/result.json'
            if closed.exists():
                result=json.loads(closed.read_text())
                if (result.get('snapshot_sha256')!=plan['snapshot_lock']['sha256']
                        or result.get('model_binding_sha256')!=snapshot['model_binding_sha256']):
                    raise ValueError('completed monitor belongs to another snapshot')
                if result.get('status')!='RUNTIME_EXITED_ZERO' or result.get('cleanup_verified') is not True:
                    return {'status':'HALTED','stage':stage,'result':result,'automatic_retry':False}
                if stage=='monitor_preflight':
                    health=stage_root/'health/preflight.json';check_preflight({'path':str(health),'sha256':digest(health)})
                continue
            if stage_root.exists() or (root/(stage+'.json')).exists():
                return {'status':'RECOVERY_REQUIRED','stage':stage,'automatic_retry':False}
            seconds=config['monitor']['stage_seconds'][stage]
            reserved=reserve(resources,update=snapshot['update'],stage_key=stage,seconds=seconds)
            if reserved['status']!='RESERVED':return reserved
            lease=reserved['lease']
            try:
                prepared=materialize(snapshot,config,stage,lease,plan['snapshot_lock']['sha256'])
                dispatch={'run':run,'snapshot_lock':plan['snapshot_lock'],'stage':stage,
                    'config':prepared['runtime'],'reservation':prepared['reservation'],
                    'lease_root':resources['lease_root'],'maximum_seconds':prepared['maximum_seconds'],
                    'dispatch_root':prepared['dispatch_root'],'environment':config['environment']}
                write_new(stage_root/'supervisor_plan.json',dispatch)
                result=launch(dispatch)
                if result.get('status')!='RUNTIME_EXITED_ZERO' or result.get('cleanup_verified') is not True:
                    return {'status':'HALTED','stage':stage,'result':result,'automatic_retry':False}
                if stage=='monitor_preflight':
                    health=stage_root/'health/preflight.json';check_preflight({'path':str(health),'sha256':digest(health)})
            finally:
                canonical=json.loads((Path(resources['lease_root'])/(lease['id']+'.json')).read_text())
                if canonical['status']!='RELEASED':
                    cleaned=cleanup(lease['id'])
                    released=release(resources['lease_root'],lease['id'],cleanup_verified=cleaned['verified'])
                    write_new(root/(stage+'_parent_cleanup.json'),{'cleanup':cleaned,'release':released})
        return {'condition':'v2-S2','status':'WAIT_FOR_PROCESSOR','snapshot_sha256':plan['snapshot_lock']['sha256'],
                'learning_rollout_tokens':0,'automatic_retry':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True,type=Path)
    args=p.parse_args();print(json.dumps(run(json.loads(args.plan.read_text())),sort_keys=True))
