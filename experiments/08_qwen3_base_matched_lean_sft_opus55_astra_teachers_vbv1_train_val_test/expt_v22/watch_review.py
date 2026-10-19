"""Supervise a separate dynamic Sol review cohort without changing V21 outcomes."""
from __future__ import annotations
import csv
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import time
import review_failures as repair
from review_failures import ROOT,RUN,HERE,MODEL,budget,read,write

def alive(pid):
    if not pid:return False
    try:os.kill(int(pid),0);return Path(f'/proc/{pid}/stat').read_text().split()[2]!='Z'
    except (OSError,ValueError,IndexError):return False

def stop(pid):
    if not alive(pid):return
    try:os.killpg(pid,signal.SIGTERM)
    except OSError:return
    time.sleep(.2)
    if alive(pid):
        try:os.killpg(pid,signal.SIGKILL)
        except OSError:pass

def recover(folder):
    state=read(folder/'status.json')
    if state['state'] not in ['CLAIMED','RUNNING'] or alive(state.get('driver_pid')):return
    profile=ROOT/'runtime'/f'lane_{state.get("lane",0):02d}'
    usage,_=budget.session_usage(profile,state.get('started_unix',time.time()))
    if alive(state.get('pid')):
        if time.time()-state.get('started_unix',time.time())<900 and (not usage or budget.charge_estimate(usage,MODEL)<1.2):
            write(folder/'orphan_adoption.json',dict(state='HEALTHY_SOL_CLI_ADOPTED',previous=state,observed_unix=time.time()));return
        stop(state['pid'])
    identity=state.get('budget_identity');ledger=budget.snapshot()
    if identity in ledger['reservations'] or ledger['charges'].get(identity,{}).get('unknown_usage'):budget.settle(identity,usage,unknown=usage is None)
    work=Path(state.get('work',str(ROOT/'workers'/f'lane_{state.get("lane",0):02d}'/folder.name)))
    try:repair.salvage(folder.name,work);return
    except Exception:pass
    retry=state.get('attempts',0)<2
    write(folder/'recovery.json',dict(previous=state,retry=retry,observed_unix=time.time()))
    write(folder/'status.json',dict(state,state='PENDING' if retry else 'EXCLUDED_BOUNDED_REPAIR',verified=False,reason='Bounded Sol child recovery retained actual checked artifacts; no proof established yet.'))

def snapshot():
    result=repair.summarize();ledger=budget.snapshot();own={k:v for k,v in ledger['charges'].items() if k.startswith('v22/')}
    result.update(v22_conservative_charge_usd=sum(v['usd'] for v in own.values()),v22_base_estimate_usd=sum(v.get('base_rate_estimate_usd') or 0 for v in own.values()),cleanup_reserved_usd=sum(v['usd'] for v in ledger['reservations'].values() if v['purpose']=='cleanup'))
    write(ROOT/'progress.json',result)
    with (ROOT/'row_progress.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=['task_id','state','verified','source_sha256','attempts','reason'],extrasaction='ignore',lineterminator='\n');writer.writeheader()
        for path in sorted((ROOT/'cases').glob('*/status.json')):writer.writerow(dict(task_id=path.parent.name,**read(path)))
    write(ROOT/'watch_heartbeat.json',dict(state='RUNNING',pid=os.getpid(),observed_unix=time.time(),progress=result));return result,ledger

def finalize():
    script=HERE/'finalize_review.py'
    if not script.exists():write(ROOT/'coordinator_attention.json',dict(reason='Sol reviews terminal; finalizer source pending deployment.',observed_unix=time.time()));return False
    python='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
    for n in range(2):
        with (ROOT/f'finalizer_{n}.log').open('a') as stream:
            process=subprocess.run([python,str(script),'--baseline',str(RUN/'corpus_training_v20/base/data/training.jsonl')],stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
        if process.returncode==0:return True
    write(ROOT/'finalizer_hold.json',dict(reason='Sol delta admission failed twice; no unchecked dataset fabricated.',observed_unix=time.time()));return False

def main():
    with (ROOT/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while not (ROOT/'completion.json').exists():
            repair.sync_failures()
            for folder in (ROOT/'cases').iterdir():recover(folder)
            result,ledger=snapshot()
            pending=any(result['states'].get(k,0) for k in ['PENDING','CLAIMED','RUNNING','BUDGET_HOLD'])
            if (ROOT/'finalizer_hold.json').exists():write(ROOT/'coordinator_attention.json',read(ROOT/'finalizer_hold.json'))
            elif result['cohort_closed'] and not pending:
                if finalize():return
            elif ledger.get('hard_hold') or (ROOT/'provider_hold.json').exists():
                write(ROOT/'coordinator_attention.json',dict(reason='Shared budget or requested Sol provider/model hold; no alternate model/key.',observed_unix=time.time()))
            else:
                own=sum(v['usd'] for group in ['charges','reservations'] for v in ledger[group].values() if v['purpose']=='cleanup')
                total=sum(v['usd'] for group in ['charges','reservations'] for v in ledger[group].values())
                if min(780-own,900-total)<10 and not result['states'].get('RUNNING'):
                    write(ROOT/'budget_hold.json',dict(reason='Authorized900sharedexposure cannot reserve another Sol request; preserve pending cases honestly.',observed_unix=time.time()))
                    write(ROOT/'coordinator_attention.json',read(ROOT/'budget_hold.json'))
                elif pending:
                    for path in (ROOT/'cases').glob('*/status.json'):
                        state=read(path)
                        if state['state']=='BUDGET_HOLD':write(path,dict(state,state='PENDING'))
                    repair.launch()
            time.sleep(15)

if __name__=='__main__':main()
