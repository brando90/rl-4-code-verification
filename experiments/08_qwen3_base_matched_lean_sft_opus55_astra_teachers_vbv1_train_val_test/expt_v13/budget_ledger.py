"""Reserve and settle configured-price exposure for the authorized adaptive training campaign."""
from __future__ import annotations
import contextlib
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
PATH=RUN/'adaptive_1p7b_campaign/budget.json'
RATES={'input':2.0,'cached_input':0.2,'output':12.0}
CONSERVATIVE_RATES={'input':5.0,'cached_input':0.4,'output':18.0}

def estimate(usage):
    inp=usage.get('input_tokens',0);cached=usage.get('cached_input_tokens',0)
    return (max(0,inp-cached)*RATES['input']+cached*RATES['cached_input']+usage.get('output_tokens',0)*RATES['output'])/1_000_000

def charge_estimate(usage):
    """Upper configured-price charge includes long-context/cache-write uncertainty."""
    inp=usage.get('input_tokens',0);cached=usage.get('cached_input_tokens',0)
    return (max(0,inp-cached)*5.0+cached*0.4+usage.get('output_tokens',0)*18.0)/1_000_000

@contextlib.contextmanager
def transaction():
    PATH.parent.mkdir(parents=True,exist_ok=True)
    with PATH.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        data=json.loads(PATH.read_text()) if PATH.exists() else dict(total_initial=300,total_authorized=600,tranche2activated=False,rates_per_million=RATES,estimate_not_invoice=True,reservations={},charges={},events=[])
        yield data
        temp=PATH.with_name(PATH.name+f'.{os.getpid()}.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');os.replace(temp,PATH)

def reserve(identity,purpose,amount):
    assert purpose in ['cleanup','adaptation'] and amount>0
    with transaction() as d:
        assert identity not in d['charges'] and identity not in d['reservations']
        if d.get('hard_hold'):
            d['events'].append(dict(event='reserve_denied_hard_hold',identity=identity,time=time.time()));return False
        spent=sum(v['usd'] for v in d['charges'].values())
        held=sum(v['usd'] for v in d['reservations'].values())
        owned=sum(v['usd'] for k in ['charges','reservations'] for v in d[k].values() if v['purpose']==purpose)
        cap=480 if purpose=='cleanup' and d['tranche2activated'] else 240 if purpose=='cleanup' else 120 if d['tranche2activated'] else 60
        overall=600 if d['tranche2activated'] else 300
        if spent+held+amount>overall or owned+amount>cap:
            d['events'].append(dict(event='reserve_denied',identity=identity,purpose=purpose,usd=amount,time=time.time()));return False
        d['reservations'][identity]=dict(purpose=purpose,usd=amount,time=time.time())
        d['events'].append(dict(event='reserve',identity=identity,purpose=purpose,usd=amount,time=time.time()));return True

def settle(identity,usage=None,unknown=False):
    with transaction() as d:
        item=d['reservations'].pop(identity)
        cost=item['usd'] if unknown else charge_estimate(usage or {})
        d['charges'][identity]=dict(purpose=item['purpose'],usd=cost,base_rate_estimate_usd=estimate(usage or {}) if not unknown else None,usage=usage,unknown_usage=unknown,time=time.time())
        d['events'].append(dict(event='settle',identity=identity,purpose=item['purpose'],usd=cost,time=time.time()))
        if cost>item['usd']:
            d['hard_hold']=dict(reason='Actual conservative estimate exceeded reserved exposure',identity=identity,charge_usd=cost,reserved_usd=item['usd'],time=time.time())
            d['events'].append(dict(event='exposure_overrun_hard_hold',identity=identity,time=time.time()))

def release(identity,reason):
    with transaction() as d:
        item=d['reservations'].pop(identity)
        d['events'].append(dict(event='release',identity=identity,usd=item['usd'],reason=reason,time=time.time()))

def activate_second_tranche(reason):
    with transaction() as d:
        d['tranche2activated']=True
        d['events'].append(dict(event='activate_preapproved_second_tranche',reason=reason,time=time.time()))

def snapshot():
    with transaction() as d:return json.loads(json.dumps(d))

def session_usage(profile,started):
    total={};found=False;window=0
    for path in Path(profile).glob('sessions/**/*.jsonl'):
        if path.stat().st_mtime<started:continue
        last=None
        for line in path.read_text(errors='replace').splitlines():
            try:r=json.loads(line)
            except json.JSONDecodeError:continue
            p=r.get('payload',{})
            if r.get('type')=='event_msg' and p.get('type')=='token_count' and p.get('info'):
                last=p['info']['total_token_usage'];window=max(window,p['info'].get('model_context_window',0) or 0)
        if last:
            found=True
            for k,v in last.items():total[k]=total.get(k,0)+v
    return total if found else None,window

def run_cli(command,env,stdin,purpose,identity,profile,cwd,stdout_path,reservation=10.0,stop_at=1.2,timeout=900,on_start=None):
    """Run approved CLI with shared exposure reservation and actual session usage polling."""
    if not reserve(identity,purpose,reservation):return dict(state='BUDGET_HOLD',returncode=None)
    started=time.time();reason=None
    try:
        with Path(stdout_path).open('x') as stream:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,cwd=cwd,env=env,text=True,start_new_session=True)
            if on_start:on_start(proc.pid,started)
            proc.stdin.write(stdin);proc.stdin.close()
            while proc.poll() is None:
                used,window=session_usage(profile,started)
                if used and charge_estimate(used)>=stop_at:reason='conservative_configured_price_stop'
                if time.time()-started>timeout:reason='cli_timeout'
                if reason:
                    os.killpg(proc.pid,signal.SIGTERM)
                    try:proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                    break
                time.sleep(.2)
        used,window=session_usage(profile,started)
        settle(identity,used,unknown=used is None)
        return dict(state='EXITED',returncode=proc.returncode,usage=used,model_context_window=window,stop_reason=reason,base_rate_estimate_usd=estimate(used) if used else None,conservative_charge_usd=charge_estimate(used) if used else reservation,unknown_usage=used is None)
    except BaseException:
        # Unknown in-flight billing remains fully reserved/charged, never silently released.
        settle(identity,None,unknown=True)
        raise
