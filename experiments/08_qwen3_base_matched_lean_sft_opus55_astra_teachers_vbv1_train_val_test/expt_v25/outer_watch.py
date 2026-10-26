"""Observe frozen V25 owners/stages without changing data or restarting an optimizer."""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import time

DEFAULT_ROOT=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v25')

def read(path):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return None

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(tmp,path)

def identity(pid,expected=None):
    try:
        root=Path('/proc')/str(int(pid));raw=(root/'stat').read_text()
        fields=raw[raw.rfind(')')+2:].split();start=fields[19]
        command=(root/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        return dict(pid=int(pid),alive=fields[0]!='Z',start_ticks=start,
                    identity_matches=expected is None or str(expected)==start,command=command)
    except (OSError,ValueError,TypeError):return dict(pid=pid,alive=False,identity_matches=False)

def classify(snapshot):
    terminal=snapshot.get('terminal') or snapshot.get('base_terminal')
    summary=snapshot.get('summary')
    if terminal and terminal.get('status')=='COMPLETE':
        return 'COMPLETE' if summary else 'COMPLETE_RECEIPT_MISSING_SUMMARY'
    if terminal and terminal.get('status') not in ('RUNNING',None):return 'FAILURE_RECORDED'
    if snapshot['pipeline_alive']:return 'PIPELINE_ACTIVE'
    if snapshot['active_children']:return 'OWNER_MISSING_CHILD_ACTIVE_PRESERVED'
    if snapshot['dispatcher_alive']:return 'DISPATCHER_ACTIVE'
    return 'OWNERS_DEAD_RECOVERY_REQUIRED'

def snapshot(root):
    now=time.time();dispatch=read(root/'dispatcher.json') or {}
    owner=identity(dispatch.get('pid'));pipeline=identity(dispatch.get('child_pid'))
    pipeline_ok=pipeline['alive'] and pipeline['identity_matches'] and 'expt_v25/pipeline.py' in pipeline.get('command','')
    owner_ok=owner['alive'] and owner['identity_matches'] and 'expt_v25/dispatch.py' in owner.get('command','')
    stages=[];children=[]
    for path in sorted((root/'execution/v25_base').glob('*.json')):
        row=read(path)
        if not row:continue
        item=dict(path=str(path),**row)
        if row.get('status')=='RUNNING':
            proc=identity(row.get('pid'),row.get('start_ticks'))
            boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            proc['boot_matches']=not row.get('boot_id') or boot==row['boot_id']
            item['actual_process']=proc
            if proc['alive'] and proc['identity_matches'] and proc['boot_matches']:children.append(proc)
        stages.append(item)
    progress=read(root/'base/run/progress.json');age=None
    if progress and progress.get('observed_unix'):age=now-progress['observed_unix']
    result=dict(observer_pid=os.getpid(),observed_unix=now,root=str(root),dispatcher=owner,
        pipeline=pipeline,dispatcher_alive=owner_ok,pipeline_alive=pipeline_ok,
        active_children=children,stages=stages,progress=progress,
        progress_age_seconds=age,stale_training_warning=bool(age and age>900 and any(x.get('stage')=='training' and x.get('status')=='RUNNING' for x in stages)),
        first_optimizer_update=read(root/'base/run/first_update.json'),
        terminal=read(root/'terminal.json'),base_terminal=read(root/'base/terminal.json'),
        summary=read(root/'analysis/v25_base_summary.json'),
        policy='Observe only; preserve healthy descendants; never reset optimizer after updates.',
        test_split_opened=False)
    result['state']=classify(result);return result

def controls():
    base=dict(terminal=None,base_terminal=None,summary=None,pipeline_alive=False,
              dispatcher_alive=False,active_children=[])
    cases=[({},'OWNERS_DEAD_RECOVERY_REQUIRED'),({'pipeline_alive':True},'PIPELINE_ACTIVE'),
      ({'active_children':[{'pid':42}]},'OWNER_MISSING_CHILD_ACTIVE_PRESERVED'),
      ({'dispatcher_alive':True},'DISPATCHER_ACTIVE'),
      ({'terminal':{'status':'FAILED_AFTER_UPDATES_PRESERVED'}},'FAILURE_RECORDED'),
      ({'base_terminal':{'status':'COMPLETE'}},'COMPLETE_RECEIPT_MISSING_SUMMARY'),
      ({'terminal':{'status':'COMPLETE'},'summary':{'total':1080}},'COMPLETE')]
    for delta,expected in cases:assert classify(dict(base,**delta))==expected
    assert not identity(-987654321)['alive']
    proc_available=Path('/proc/self/stat').exists()
    if proc_available:
        assert identity(os.getpid())['alive']
        assert not identity(os.getpid(),'wrong')['identity_matches']
    return dict(status='PASS',proc_identity_controls_run=proc_available,controls=len(cases)+(3 if proc_available else 1),scope='harmless CPU routing and /proc PID identity controls; no model updates')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--once',action='store_true');parser.add_argument('--selftest',action='store_true');args=parser.parse_args()
    if args.selftest:print(json.dumps(controls()));return
    root=args.root;root.mkdir(parents=True,exist_ok=True)
    lock=(root/'outer_watch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    write(root/'outer_watch_controls.json',dict(**controls(),observed_unix=time.time()))
    while True:
        result=snapshot(root);write(root/'outer_watch.json',result)
        if result['state'] in ('COMPLETE','COMPLETE_RECEIPT_MISSING_SUMMARY','FAILURE_RECORDED','OWNERS_DEAD_RECOVERY_REQUIRED'):
            write(root/'outer_watch_terminal.json',result)
            return
        if args.once:return
        time.sleep(30)
if __name__=='__main__':main()
