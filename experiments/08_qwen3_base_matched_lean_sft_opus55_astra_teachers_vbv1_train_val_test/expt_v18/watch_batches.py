"""Supervise every cleanup batch and original audit, recover bounded failures, and freeze accepted-only training data."""
from __future__ import annotations
import csv
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import repair_batches as repair
from repair_batches import budget,read,write,ROOT,HERE,RUN,MODEL

def alive(pid):
    if not pid:return False
    try:os.kill(int(pid),0);return Path(f'/proc/{pid}/stat').read_text().split()[2]!='Z'
    except (OSError,ValueError,IndexError):return False

def stop_pid(pid):
    if not alive(pid):return
    try:os.killpg(pid,signal.SIGTERM)
    except OSError:return
    time.sleep(.2)
    if alive(pid):
        try:os.killpg(pid,signal.SIGKILL)
        except OSError:pass

def recover(batch):
    state=read(batch/'status.json')
    if state['state'] not in ['RUNNING','CLAIMED']:return
    if alive(state.get('driver_pid')):return
    profile=ROOT/'runtime'/f'lane_{state.get("lane",0):02d}'
    used,_=budget.session_usage(profile,state.get('started_unix',time.time()))
    if alive(state.get('pid')):
        if time.time()-state.get('started_unix',time.time())<900 and (not used or budget.charge_estimate(used,MODEL)<1.2):
            write(batch/'orphan_adoption.json',dict(state='HEALTHY_CLI_ADOPTED',previous=state,observed_unix=time.time()));return
        stop_pid(state['pid'])
    identity=state.get('budget_identity');ledger=budget.snapshot()
    if identity in ledger['reservations'] or ledger['charges'].get(identity,{}).get('unknown_usage'):
        budget.settle(identity,used,unknown=used is None)
    ids=read(batch/'input.json')['tasks'];work=Path(state.get('work','/missing'))
    for tid in ids:
        case=ROOT/'cases'/tid
        if read(case/'status.json')['state'].startswith('ACCEPTED'):continue
        try:repair.salvage(tid,work/tid)
        except Exception:pass
    missing=[tid for tid in ids if not read(ROOT/'cases'/tid/'status.json')['state'].startswith('ACCEPTED')]
    retry=bool(missing and state.get('attempts',0)<2)
    if not retry:
        for tid in missing:write(ROOT/'cases'/tid/'status.json',dict(state='EXCLUDED_BOUNDED_REPAIR',verified=False,reason='V18 bounded attempts ended without an explicit verified proof.',prior=read(ROOT/'cases'/tid/'status.json')))
    write(batch/'recovery.json',dict(previous=state,retry=retry,observed_unix=time.time()))
    write(batch/'status.json',dict(state,state='PENDING' if retry else 'DONE'))

def snapshot():
    result=repair.summarize();ledger=budget.snapshot()
    entries=list(ledger['charges'].items())
    result.update(v18_conservative_charge_usd=sum(v['usd'] for k,v in entries if k.startswith('v18/')),v18_base_estimate_usd=sum(v.get('base_rate_estimate_usd') or 0 for k,v in entries if k.startswith('v18/')),cleanup_total_conservative_usd=sum(v['usd'] for _,v in entries if v['purpose']=='cleanup'),cleanup_reserved_usd=sum(v['usd'] for v in ledger['reservations'].values() if v['purpose']=='cleanup'),tranche3activated=ledger.get('tranche3activated',False))
    write(ROOT/'progress.json',result)
    keys=['task_id','state','verified','source_sha256','batch','attempts','reason','rationale']
    with (ROOT/'row_progress.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader()
        for p in sorted((ROOT/'cases').glob('*/status.json')):writer.writerow(dict(task_id=p.parent.name,**read(p)))
    write(ROOT/'watch_heartbeat.json',dict(state='RUNNING',pid=os.getpid(),observed_unix=time.time(),progress=result))
    return result,ledger

def audit_watch():
    pending=[tid for tid in read(ROOT/'unchanged_manifest.json') if read(ROOT/'cases'/tid/'status.json')['state']=='UNCHANGED_CHECK_PENDING']
    if not pending:return
    name='rl4cv-v18-unchanged-audit'
    if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:return
    prior=read(ROOT/'audit_launch.json') if (ROOT/'audit_launch.json').exists() else dict(launches=0)
    if prior['launches']>=2:
        for tid in pending:write(ROOT/'cases'/tid/'status.json',dict(state='EXCLUDED_CHECK_INFRASTRUCTURE',verified=False,reason='Original-source kernel audit could not complete in two ordinary-code audit launches.'))
        return
    subprocess.run(['tmux','new-session','-d','-s',name,f'python3 -u {HERE}/repair_batches.py audit >> {ROOT}/audit.log 2>&1'],check=True)
    write(ROOT/'audit_launch.json',dict(launches=prior['launches']+1,observed_unix=time.time()))

def launch_available(ledger):
    if (ROOT/'provider_hold.json').exists() or ledger.get('hard_hold'):return
    own=sum(v['usd'] for k in ['charges','reservations'] for v in ledger[k].values() if v['purpose']=='cleanup')
    global_owned=sum(v['usd'] for k in ['charges','reservations'] for v in ledger[k].values())
    # Use the explicit900authorization for scheduling. Reserving beyond earlier480
    # activates the third tranche, rather than silently shrinking to one worker.
    if not ledger.get('tranche3activated') and 480-own<40 and ledger.get('total_authorized',0)>=900:
        budget.activate_third_tranche('V18 has remaining declared repairs; earlier cleanup headroom cannot sustain four bounded lanes. User preapproved additional300 to finish.');ledger=budget.snapshot()
    capacity=max(0,min(32,int(min(780-own,900-global_owned)//10)))
    if capacity<=0:return
    pending=[p for p in (ROOT/'batches').glob('*/status.json') if read(p)['state'] in ['PENDING','BUDGET_HOLD']]
    if not pending:return
    for p in pending:
        state=read(p)
        if state['state']=='BUDGET_HOLD':write(p,dict(state,state='PENDING'))
    for lane in range(32):
        if capacity<=0:break
        name=f'codex-rl4cv-terra-full-v18-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        subprocess.run(['tmux','new-session','-d','-s',name,f'python3 -u {HERE}/repair_batches.py worker --lane {lane} >> {ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'],check=True);capacity-=1

def finalize():
    python='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
    for n in range(2):
        with (ROOT/f'finalizer_{n}.log').open('a') as stream:
            process=subprocess.run([python,str(HERE/'finalize_full.py')],stdout=stream,stderr=subprocess.STDOUT,timeout=1800)
        if process.returncode==0:return True
    write(ROOT/'coordinator_attention.json',dict(reason='Finalizer failed twice; no accepted-pool replacement/fallback fabricated.',observed_unix=time.time()));return False

def main():
    with (ROOT/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while True:
            for batch in (ROOT/'batches').iterdir():recover(batch)
            audit_watch();progress,ledger=snapshot()
            first=read(ROOT/'batches/batch_0000/status.json')
            if not (ROOT/'calibration_ok.json').exists():
                if first['state']=='PENDING':repair.launch(first=True)
                if first['state']=='DONE':
                    accepted=[tid for tid in read(ROOT/'batches/batch_0000/input.json')['tasks'] if read(ROOT/'cases'/tid/'status.json')['state'].startswith('ACCEPTED')]
                    write(ROOT/'calibration_ok.json',dict(state='PASS' if accepted else 'ZERO_ACCEPTED_REVIEW',accepted=accepted,progress=progress,observed_unix=time.time()))
                    if not accepted:
                        write(ROOT/'coordinator_attention.json',dict(reason='First real four-file calibration produced no verified replacement; inspect before scaling.',observed_unix=time.time()));time.sleep(15);continue
                else:time.sleep(15);continue
            if read(ROOT/'calibration_ok.json')['state']!='PASS':time.sleep(15);continue
            remaining=any(progress['batches'].get(k,0) for k in ['PENDING','CLAIMED','RUNNING','BUDGET_HOLD'])
            audit_pending=progress['states'].get('UNCHANGED_CHECK_PENDING',0)
            if not remaining and not audit_pending:
                ok=finalize();write(ROOT/'watch_heartbeat.json',dict(state='DONE' if ok else 'FINALIZER_HOLD',pid=os.getpid(),observed_unix=time.time()));return
            launch_available(ledger)
            if (ROOT/'provider_hold.json').exists() or ledger.get('hard_hold'):
                write(ROOT/'coordinator_attention.json',dict(reason='Funding/authentication or reserved-exposure hold; preserve healthy admitted jobs and all unattempted rows.',progress=progress,observed_unix=time.time()))
            elif progress['batches'].get('BUDGET_HOLD') and not progress['batches'].get('RUNNING'):
                write(ROOT/'coordinator_attention.json',dict(reason='Authorized900sharedbudget cannot reserve another bounded cleanup request; unattempted proofs remain explicitly unresolved.',progress=progress,observed_unix=time.time()))
            time.sleep(15)

if __name__=='__main__':main()
