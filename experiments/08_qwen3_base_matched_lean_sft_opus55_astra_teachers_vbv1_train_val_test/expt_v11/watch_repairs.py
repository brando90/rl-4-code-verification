"""Observe repair processes, recover within native budgets, and finalize all 68 outcomes on the cluster."""
import collections
import fcntl
import json
from pathlib import Path
import os
import subprocess
import time
import repair_proofs as repair
from repair_proofs import base


def alive(pid):
    if not pid:return False
    try:
        os.kill(pid,0)
        return Path(f'/proc/{pid}/stat').read_text().split()[2]!='Z'
    except (OSError,IndexError):return False

def recover(folder):
    status=json.loads((folder/'status.json').read_text())
    if status['state'] not in ['RUNNING','CLAIMED','BLOCKED']:return
    if alive(status.get('driver_pid')) or alive(status.get('pid')):return
    attempts=status.get('attempts',0)
    if status.get('work'):
        output=folder/f'output_{max(0,attempts-1)}.json'
        try:
            result=repair.validate(folder,Path(status['work']),output)
            base.write(folder/'dead_driver_status.json',status)
            base.write(folder/'status.json',dict(status,state='DONE',decision=result['decision'],verified=result['verified'],recovered_by_watch=True));return
        except (FileNotFoundError,ValueError,KeyError,AssertionError):pass
    if status['state']=='BLOCKED' and attempts>=2:return
    base.write(folder/f'coordinator_recovery_{attempts}.json',dict(previous=status,observed_unix=time.time()))
    base.write(folder/'status.json',dict(status,state='PENDING' if attempts<2 else 'BLOCKED'))

def usage():
    total=collections.Counter()
    for p in (repair.ROOT/'cases').glob('*/cli_*.jsonl'):
        for line in p.read_text(errors='replace').splitlines():
            try:event=json.loads(line)
            except json.JSONDecodeError:continue
            if event.get('type')=='turn.completed':total.update(event.get('usage',{}))
    cost=((total['input_tokens']-total['cached_input_tokens'])*2+total['cached_input_tokens']*.1+total['output_tokens']*10)/1e6
    return dict(tokens=dict(total),configured_rate_estimate_usd=cost,estimate_not_invoice=True,unknown_cache_write_surcharges=True)

def cleanup():
    root=repair.ROOT
    prior=root/'cleanup.json'
    if prior.exists() and json.loads(prior.read_text()).get('state')=='DONE':return
    active=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:cwd=os.readlink(p/'cwd')
        except OSError:continue
        if cwd.startswith(str(root/'workers')+'/'):active.append(dict(pid=p.name,cwd=cwd))
    if active:
        base.write(root/'cleanup.json',dict(state='RETAINED_ACTIVE_CONSUMERS',active=active,owner='root repair coordinator',condition='Remove worker checkouts after these owned consumers exit; final sources are already central.'));return
    records=[]
    for work in sorted((root/'workers').iterdir()):
        if not work.is_dir():continue
        status=subprocess.check_output(['git','-C',str(work),'status','--porcelain','--ignored'],text=True).splitlines()
        if not all(s.startswith('?? ') for s in status):
            base.write(root/'cleanup.json',dict(state='RETAINED_TRACKED_CHANGES',work=str(work),status=status,owner='root repair coordinator'));return
        for p in work.rglob('*'):
            if not p.is_file() or p.name=='.git':continue
            rel=p.relative_to(work)
            if subprocess.run(['git','-C',str(work),'ls-files','--error-unmatch',str(rel)],capture_output=True).returncode==0:continue
            assert not p.is_symlink(),str(p)
            target=root/'worker_records'/work.name/rel;target.parent.mkdir(parents=True,exist_ok=True)
            data=p.read_bytes()
            if target.exists():assert target.read_bytes()==data
            else:target.write_bytes(data)
            assert target.read_bytes()==data;records.append(dict(path=str(target.relative_to(root)),sha256=base.sha(data)));p.unlink()
        subprocess.run(['git','-C',str(root/'worker_template'),'worktree','remove',str(work)],check=True)
    base.write(root/'cleanup.json',dict(state='DONE',removed_worktrees=16,preserved_records=records,observed_unix=time.time()))

def main():
    with (repair.ROOT/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            for p in (repair.ROOT/'cases').iterdir():recover(p)
            result=repair.summarize();base.write(repair.ROOT/'usage.json',usage());print(json.dumps(result),flush=True)
            if (repair.ROOT/'provider_hold.json').exists():
                base.write(repair.ROOT/'completion.json',dict(state='PROVIDER_HOLD',progress=result,observed_unix=time.time()));return
            pending=any(result['states'].get(s,0) for s in ['PENDING','CLAIMED','RUNNING'])
            if not pending:
                python='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
                with (repair.ROOT/'finalize.log').open('a') as stream:
                    process=subprocess.run([python,str(repair.HERE/'finalize_repairs.py')],stdout=stream,stderr=subprocess.STDOUT,timeout=900)
                cleanup()
                summary=json.loads((repair.ROOT/'final/summary.json').read_text()) if (repair.ROOT/'final/summary.json').exists() else {}
                clean=result['verified']==68 and summary.get('formatted')==68
                base.write(repair.ROOT/'completion.json',dict(state=('DONE' if clean else 'DONE_WITH_RECORDED_EXCLUSIONS') if process.returncode==0 else 'FINALIZATION_FAILED',finalizer_exit=process.returncode,progress=result,observed_unix=time.time()));return
            if result['states'].get('PENDING'):repair.launch()
            time.sleep(15)

if __name__=='__main__':main()
