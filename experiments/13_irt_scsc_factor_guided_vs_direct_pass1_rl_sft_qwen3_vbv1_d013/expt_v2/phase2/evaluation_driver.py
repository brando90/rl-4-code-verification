"""Execute the complete frozen evaluation population with bounded identical infrastructure recovery and retained costs."""
from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path

from evaluation_authority import authorize
from evaluation_stage import materialize
from evaluation_supervisor import launch
from evaluation_ledger import scan
from learning_resources import reserve
from technical_ledger import check_preflight
from training_checkpoint import digest,write_new
from resource_lease import release
from lp1 import cleanup
from costs import snapshot as cost_snapshot,stage_cost


def execute(plan,lp,config,snapshot,stage,key,indexes):
    learning=plan['learning'];resources={**learning['resources'],'run':learning['run']}
    root=Path(snapshot['configuration']['root']);directory=root/key
    if directory.exists() or (root/(key+'.json')).exists():return {'status':'RECOVERY_REQUIRED','stage_key':key}
    seconds=config['evaluation']['stage_seconds'][stage]
    reserved=reserve(resources,update=snapshot['boundary'],stage_key=key,seconds=seconds)
    if reserved['status']!='RESERVED':return reserved
    lease=reserved['lease'];before=cost_snapshot(root)
    try:
        prepared=materialize(snapshot,config,lp['configuration']['evaluation_runtime_contract'],stage,key,indexes,lease,plan['snapshot_lock']['sha256'])
        dispatch={**plan,**prepared,'lease_root':resources['lease_root'],'environment':config['environment']}
        write_new(directory/'supervisor_plan.json',dispatch)
        result=launch(dispatch)
    finally:
        canonical=json.loads((Path(resources['lease_root'])/(lease['id']+'.json')).read_text())
        if canonical['status']!='RELEASED':
            cleaned=cleanup(lease['id']);released=release(resources['lease_root'],lease['id'],cleanup_verified=cleaned['verified'])
            write_new(root/(key+'_parent_cleanup.json'),{'cleanup':cleaned,'release':released})
        canonical=json.loads((Path(resources['lease_root'])/(lease['id']+'.json')).read_text())
        cp=directory/'dispatch/cleanup.json';parent=root/(key+'_parent_cleanup.json')
        cleaned=json.loads(cp.read_text()) if cp.exists() else json.loads(parent.read_text())['cleanup'] if parent.exists() else {}
        cost=stage_cost(before,cost_snapshot(root),stage=key,lease=canonical,cleanup=cleaned)
        # Preparation failure may precede stage-directory creation; keep its
        # resource receipt beside the snapshot instead of losing the charge.
        write_new(directory/'cost.json' if directory.exists() else root/(key+'_cost.json'),cost)
    return result


def finish(root,value,snapshot_sha,*,reason=None):
    value={**value,'snapshot_sha256':snapshot_sha,'learning_rollout_tokens':0,'stop_reason':reason}
    if reason:value['status']='INCOMPLETE'
    write_new(root/'generation_terminal.json',value);return value


def run(plan):
    lp,execution,config,snapshot=authorize(plan)
    science={b['path']:b['sha256'] for b in execution['bindings']}
    for name in ('evaluation_driver.py','evaluation_ledger.py','evaluation_stage.py','costs.py'):
        path=Path(__file__).resolve().parent/name
        if science.get(str(path))!=digest(path):raise ValueError('evaluation coordination was not frozen before main')
    root=Path(snapshot['configuration']['root']);sha=plan['snapshot_lock']['sha256']
    manifest=json.loads(Path(snapshot['configuration']['manifest']).read_text())
    allowed=Path(snapshot['configuration']['allowlist']).read_text().splitlines()
    prefix=f"{snapshot['purpose']}_b{snapshot['boundary']}";health_key=prefix+'_preflight'
    with (root/'evaluation_controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        terminal=root/'generation_terminal.json'
        if terminal.exists():
            old=json.loads(terminal.read_text());current=scan(root,manifest,allowed,sha)
            if old['snapshot_sha256']!=sha or old['generation']!=current['generation']:
                raise ValueError('completed evaluation input or output evidence changed')
            return old
        closed=root/health_key/'dispatch/result.json'
        if closed.exists():
            result=json.loads(closed.read_text())
            if (result.get('snapshot_sha256')!=sha or result.get('model_binding_sha256')!=snapshot['model_binding_sha256']):
                raise ValueError('evaluation health result belongs to another checkpoint')
        else:result=execute(plan,lp,config,snapshot,'evaluation_preflight',health_key,None)
        if result['status'] in ('WAIT_FOR_IDLE_DEVICE','DEVICE_CHANGED_BEFORE_LAUNCH','RECOVERY_REQUIRED'):return result
        if result.get('status')!='RUNTIME_EXITED_ZERO' or result.get('cleanup_verified') is not True:
            value=scan(root,manifest,allowed,sha)
            value['cleanup_unresolved']+=int(result.get('cleanup_verified') is not True and result['status']!='RESOURCE_EXHAUSTED')
            return finish(root,value,sha,reason='evaluation_preflight_'+result['status'])
        health=root/health_key/'health/preflight.json';check_preflight({'path':str(health),'sha256':digest(health)})
        while True:
            value=scan(root,manifest,allowed,sha)
            if value['status'] in ('RECOVERY_REQUIRED','CLEANUP_REQUIRED'):return value
            if value['status'] in ('COMPLETE','INCOMPLETE'):return finish(root,value,sha)
            key=f"{prefix}_s{value['next_segment']:03d}"
            result=execute(plan,lp,config,snapshot,'evaluation_generate',key,value['pending_indexes'][:256])
            if result['status'] in ('WAIT_FOR_IDLE_DEVICE','DEVICE_CHANGED_BEFORE_LAUNCH','RECOVERY_REQUIRED'):return result
            if result['status']=='RESOURCE_EXHAUSTED':return finish(root,value,sha,reason='RESOURCE_EXHAUSTED')
            # Every closed segment, including failures, is reconciled against its
            # immutable response files before another segment is considered.


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True,type=Path);a=p.parse_args()
    print(json.dumps(run(json.loads(a.plan.read_text())),sort_keys=True))
