"""Ordinary 15-second supervision for the 25 statically assigned tiny repair lanes."""
from __future__ import annotations
import csv
import fcntl
import importlib.util
import os
from pathlib import Path
import subprocess
import time
import repair_batches as repair
from repair_batches import ROOT,HERE,RUN,read,write,budget

spec=importlib.util.spec_from_file_location('tiny_v21_recovery',HERE.parent/'expt_v18/watch_batches.py')
recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)

def snapshot():
    result=repair.summarize();ledger=budget.snapshot()
    own={k:v for k,v in ledger['charges'].items() if k.startswith('v21/')}
    result.update(v21_conservative_charge_usd=sum(v['usd'] for v in own.values()),v21_base_estimate_usd=sum(v.get('base_rate_estimate_usd') or 0 for v in own.values()),cleanup_reserved_usd=sum(v['usd'] for v in ledger['reservations'].values() if v['purpose']=='cleanup'))
    write(ROOT/'progress.json',result)
    keys=['task_id','state','verified','source_sha256','batch','attempts','reason','rationale']
    with (ROOT/'row_progress.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader()
        for path in sorted((ROOT/'cases').glob('*/status.json')):writer.writerow(dict(task_id=path.parent.name,**read(path)))
    write(ROOT/'watch_heartbeat.json',dict(state='RUNNING',pid=os.getpid(),observed_unix=time.time(),progress=result))
    return result,ledger

def relaunch():
    if (ROOT/'provider_hold.json').exists() or (ROOT/'user_stop_paid_generation.json').exists():return
    for lane in range(25):
        batches=[p for p in (ROOT/'batches').iterdir() if read(p/'input.json')['lane']==lane]
        for batch in batches:
            status=read(batch/'status.json')
            if status['state']=='BUDGET_HOLD':write(batch/'status.json',dict(status,state='PENDING'))
        if not any(read(p/'status.json')['state']=='PENDING' for p in batches):continue
        name=f'codex-rl4cv-terra-tiny-v21-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        # The single shared ledger reserves every CLI request before provider work;
        # process presence never bypasses either global or purpose exposure caps.
        subprocess.run(['tmux','new-session','-d','-s',name,f'python3 -u {HERE}/repair_batches.py worker --lane {lane} >> {ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'],check=True)

def finalize():
    script=HERE/'finalize_tiny.py'
    if not script.exists():write(ROOT/'coordinator_attention.json',dict(reason='All repairs terminal; finalizer source awaiting deployment.',observed_unix=time.time()));return False
    python='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
    for n in range(2):
        with (ROOT/f'finalizer_{n}.log').open('a') as stream:
            proc=subprocess.run([python,str(script),'--baseline',str(RUN/'corpus_training_v20/base/data/training.jsonl')],stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
        if proc.returncode==0:return True
    write(ROOT/'finalizer_hold.json',dict(reason='Finalizer failed twice; no unchecked dataset fabricated.',observed_unix=time.time()))
    write(ROOT/'coordinator_attention.json',read(ROOT/'finalizer_hold.json'));return False

def main():
    with (ROOT/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while not (ROOT/'completion.json').exists():
            for batch in (ROOT/'batches').iterdir():recovery.recover(batch)
            progress,ledger=snapshot()
            if (ROOT/'finalizer_hold.json').exists():
                write(ROOT/'coordinator_attention.json',read(ROOT/'finalizer_hold.json'))
            elif progress['batches'].get('DONE',0)==125:
                if finalize():return
            elif ledger.get('hard_hold') or (ROOT/'provider_hold.json').exists():
                write(ROOT/'coordinator_attention.json',dict(reason='Shared budget or provider hold; keep unattempted proofs honest.',progress=progress,observed_unix=time.time()))
            else:
                used=sum(v['usd'] for group in ['charges','reservations'] for v in ledger[group].values() if v['purpose']=='cleanup')
                global_used=sum(v['usd'] for group in ['charges','reservations'] for v in ledger[group].values())
                headroom=min(780-used,900-global_used)
                if headroom<10 and not progress['batches'].get('RUNNING'):
                    write(ROOT/'budget_hold.json',dict(reason='Authorized shared exposure cannot reserve another bounded tiny proof call; no automatic ceiling increase.',cleanup_remaining_usd=780-used,global_remaining_usd=900-global_used,progress=progress,observed_unix=time.time()))
                    write(ROOT/'coordinator_attention.json',read(ROOT/'budget_hold.json'))
                else:relaunch()
            time.sleep(15)

if __name__=='__main__':main()
