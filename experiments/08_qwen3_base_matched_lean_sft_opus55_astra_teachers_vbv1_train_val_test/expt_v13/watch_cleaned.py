"""Supervise Terra cleanup workers, bounded death recovery, budget tranches and final matched-run publication."""
from __future__ import annotations
import csv
import fcntl
import json
import os
import signal
import subprocess
import time
import clean_existing as clean
import budget_ledger as budget
from clean_existing import base

def alive(pid):
    try:
        os.kill(int(pid),0)
        return clean.Path(f'/proc/{pid}/stat').read_text().split()[2]!='Z'
    except (OSError,ValueError,TypeError):return False

def snapshot():
    rows=[]
    for p in sorted((clean.ROOT/'cases').glob('*/status.json')):
        r=json.loads(p.read_text());r['task_id']=p.parent.name;rows.append(r)
    data=clean.summarize();ledger=budget.snapshot()
    data.update(conservative_charge_usd=sum(v['usd'] for v in ledger['charges'].values() if v['purpose']=='cleanup'),base_rate_estimate_usd=sum(v.get('base_rate_estimate_usd') or 0 for v in ledger['charges'].values() if v['purpose']=='cleanup'),reserved_usd=sum(v['usd'] for v in ledger['reservations'].values() if v['purpose']=='cleanup'),tranche2activated=ledger['tranche2activated'])
    base.write(clean.ROOT/'progress.json',data)
    keys=['task_id','state','decision','verified','attempts','lane','model','effort','reason','error']
    with (clean.ROOT/'row_progress.csv').open('w') as stream:
        w=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(rows)
    base.write(clean.ROOT/'watch_heartbeat.json',dict(pid=os.getpid(),state='RUNNING',observed_unix=time.time()))
    return rows,data,ledger

def recover(rows):
    for row in rows:
        if row['state'] not in ['RUNNING','CLAIMED']:continue
        if alive(row.get('driver_pid')):continue
        if alive(row.get('pid')):
            try:os.killpg(row['pid'],signal.SIGTERM)
            except OSError:pass
            time.sleep(.2)
            if alive(row.get('pid')):
                try:os.killpg(row['pid'],signal.SIGKILL)
                except OSError:pass
        identity=row.get('budget_identity')
        ledger=budget.snapshot()
        if identity in ledger['reservations']:
            profile=clean.ROOT/'runtime'/f'lane_{row["lane"]:02d}'
            used,_=budget.session_usage(profile,row.get('started_unix',time.time()))
            budget.settle(identity,used,unknown=used is None)
        folder=clean.ROOT/'cases'/row['task_id'];state='PENDING' if row.get('attempts',0)<2 else 'FALLBACK'
        base.write(folder/'status.json',dict(row,state=state,reason='Driver died; fenced old CLI, settled reserved exposure, preserved artifacts and bounded remaining attempts.'))

def launch_available(ledger):
    if (clean.ROOT/'freeze_for_comparison.json').exists():return
    spent=sum(v['usd'] for v in ledger['charges'].values() if v['purpose']=='cleanup')
    reserved=sum(v['usd'] for v in ledger['reservations'].values() if v['purpose']=='cleanup')
    cap=480 if ledger['tranche2activated'] else 240
    capacity=max(0,int((cap-spent-reserved)//clean.RESERVE))
    if capacity==0:return
    for lane in range(clean.LANES):
        name=f'codex-rl4cv-terra-clean-v13-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        if capacity<=0:break
        command=f'python3 -u {clean.HERE}/clean_existing.py worker --lane {lane} >> {clean.ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'
        subprocess.run(['tmux','new-session','-d','-s',name,command],check=True);capacity-=1

def finish_frozen_active(row):
    """Adopt the one already admitted CLI while preventing its old driver from retrying."""
    folder=clean.ROOT/'cases'/row['task_id'];handoff=folder/'comparison_freeze_handoff.json'
    if not handoff.exists():
        # Stop only the ordinary coordinator. Its independently grouped CLI stays healthy.
        if alive(row.get('driver_pid')):os.kill(row['driver_pid'],signal.SIGSTOP)
        base.write(handoff,dict(previous=row,old_driver_suspended=True,existing_cli_preserved=True,no_new_attempts=True,observed_unix=time.time()))
    profile=clean.ROOT/'runtime'/f'lane_{row["lane"]:02d}'
    used,_=budget.session_usage(profile,row.get('started_unix',time.time()))
    expired=time.time()-row.get('started_unix',time.time())>900
    cost_stop=bool(used and budget.charge_estimate(used)>=clean.STOP_ESTIMATE)
    if alive(row.get('pid')) and not expired and not cost_stop:return False
    if alive(row.get('pid')):
        try:os.killpg(row['pid'],signal.SIGTERM)
        except OSError:pass
        time.sleep(.5)
        if alive(row.get('pid')):
            try:os.killpg(row['pid'],signal.SIGKILL)
            except OSError:pass
    if alive(row.get('driver_pid')):
        try:os.kill(row['driver_pid'],signal.SIGKILL)
        except OSError:pass
    identity=row.get('budget_identity');ledger=budget.snapshot()
    if identity in ledger['reservations']:budget.settle(identity,used,unknown=used is None)
    try:
        assert not expired and not cost_stop,'Already-admitted native CLI time/cost bound reached.'
        result=json.loads((folder/f'output_{row.get("attempt",0)}.json').read_text())
        assert result['task_id']==folder.name
        if result['decision']=='cleaned':
            source=clean.assemble(folder,clean.Path(row['work']));digest=base.sha(source)
            receipt=json.loads((folder/'checks'/digest/'result.json').read_text())
            assert receipt['passed'] and clean.kernel_module().valid_report(receipt['kernel_report'])
            assert receipt['kernel_report']['source_sha256']==digest
            (folder/'Solution.lean').write_text(source);result.update(verified=True,source_sha256=digest)
        else:result['verified']=False
        base.write(folder/'decision.json',result)
        base.write(folder/'status.json',dict(row,state='DONE',decision=result['decision'],verified=result['verified'],comparison_freeze=True,finished_unix=time.time()))
    except Exception as exc:
        base.write(folder/'status.json',dict(row,state='FALLBACK',comparison_freeze=True,reason='Already-admitted case finished without an accepted frozen result',error=repr(exc),finished_unix=time.time()))
    return True

def finish(reason):
    for p in (clean.ROOT/'cases').glob('*/status.json'):
        r=json.loads(p.read_text())
        if r['state'] in ['PENDING','BUDGET_HOLD','CLAIMED']:
            base.write(p,dict(r,state='FALLBACK',reason=reason))
    python='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
    for attempt in range(2):
        try:
            result=subprocess.run([str(python),str(clean.HERE/'finalize_cleaned.py')],capture_output=True,text=True,timeout=1800)
            (clean.ROOT/f'finalizer_{attempt}.log').write_text(result.stdout+result.stderr)
            if result.returncode==0:
                base.write(clean.ROOT/'watch_heartbeat.json',dict(pid=os.getpid(),state='DONE',reason=reason,observed_unix=time.time()));return 0
            error=dict(error='Finalizer failed',returncode=result.returncode,reason=reason,attempt=attempt,observed_unix=time.time())
        except subprocess.TimeoutExpired:
            error=dict(error='Finalizer1800second timeout',reason=reason,attempt=attempt,observed_unix=time.time())
        base.write(clean.ROOT/f'finalizer_error_{attempt}.json',error)
    # Deterministic fallback cannot admit any unchecked changed source. V12 independently
    # already froze and checked every original row and will reapply its own gates.
    final=clean.ROOT/'final';final.mkdir(exist_ok=True)
    (final/'replacements.jsonl').write_text('')
    alltext=''.join(json.dumps(dict(r,proof_cleanup_v13=dict(original_fallback=True,reason='Finalizer failed twice; no replacement admitted')),ensure_ascii=False)+'\n' for r in base.read_rows(clean.SOURCE))
    (final/'cleaned_existing_training.jsonl').write_text(alltext)
    summary=dict(state='DONE_PARTIAL',declared=2585,accounted=2585,replacements=0,original_fallbacks=2585,replacements_sha256=base.sha(''),training_sha256=base.sha(alltext),source_sha256=clean.SOURCE_SHA,finalizer_failure=error,observed_unix=time.time())
    base.write(final/'summary.json',summary);base.write(clean.ROOT/'completion.json',summary)
    base.write(clean.ROOT/'watch_error.json',error);return 1

def main():
    with (clean.ROOT/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        deadline=time.time()+24*3600
        while True:
            rows,data,ledger=snapshot()
            freeze=clean.ROOT/'freeze_for_comparison.json'
            if freeze.exists():
                active=[r for r in rows if r['state'] in ['RUNNING','CLAIMED']]
                if not active:return finish(json.loads(freeze.read_text())['reason'])
                for row in active:finish_frozen_active(row)
                time.sleep(2);continue
            recover(rows)
            active=any(r['state'] in ['RUNNING','CLAIMED'] for r in rows)
            pending=any(r['state'] in ['PENDING','BUDGET_HOLD'] for r in rows)
            if not active and not pending:return finish('All declared rewrite cases reached a terminal result.')
            held=(clean.ROOT/'provider_hold.json').exists() or bool(ledger.get('hard_hold'))
            spent=sum(v['usd'] for v in ledger['charges'].values() if v['purpose']=='cleanup')
            reserved=sum(v['usd'] for v in ledger['reservations'].values() if v['purpose']=='cleanup')
            cap=480 if ledger['tranche2activated'] else 240
            if (held or time.time()>deadline) and not active:return finish('Provider hold or declared24hour watchdog deadline; original fallbacks retained.')
            if not active and pending and cap-spent-reserved<clean.RESERVE:
                if not ledger['tranche2activated']:
                    budget.activate_second_tranche('Initial cleanup allocation insufficient for remaining declared cases; user explicitly preapproved another300total.');ledger=budget.snapshot()
                else:return finish('Authorized configured-price cleanup allocation exhausted; original fallbacks retained.')
            if not held and time.time()<=deadline:
                # A denied reservation while other lanes are active is a temporary hold.
                for p in (clean.ROOT/'cases').glob('*/status.json'):
                    r=json.loads(p.read_text())
                    if r['state']=='BUDGET_HOLD':base.write(p,dict(r,state='PENDING'))
                launch_available(ledger)
            time.sleep(20)

if __name__=='__main__':raise SystemExit(main())
