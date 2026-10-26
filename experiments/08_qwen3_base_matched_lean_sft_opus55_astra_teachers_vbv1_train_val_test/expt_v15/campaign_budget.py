"""Enforce the extended shared campaign budget with model-specific conservative charges and in-flight reservations."""
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
# Sol support authorized for the separate V22 review; verified official pricing
# 2026-10-19: https://developers.openai.com/api/docs/pricing
RATES={'gpt-5.6-terra':dict(input=2.,cached_input=.2,output=12.),'gpt-6-astra':dict(input=10.,cached_input=1.,output=50.),'gpt-6.1-sol':dict(input=2.,cached_input=.1,output=10.)}
UPPER={'gpt-5.6-terra':dict(input=5.,cached_input=.4,output=18.),'gpt-6-astra':dict(input=25.,cached_input=2.,output=75.),'gpt-6.1-sol':dict(input=5.,cached_input=.2,output=15.)}

def estimate(usage,model='gpt-5.6-terra',conservative=False):
    rate=(UPPER if conservative else RATES)[model];usage=usage or {}
    inp=usage.get('input_tokens',0);cached=usage.get('cached_input_tokens',0)
    return (max(0,inp-cached)*rate['input']+cached*rate['cached_input']+usage.get('output_tokens',0)*rate['output'])/1e6

def charge_estimate(usage,model='gpt-5.6-terra'):return estimate(usage,model,True)

@contextlib.contextmanager
def transaction():
    PATH.parent.mkdir(parents=True,exist_ok=True)
    with PATH.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        data=json.loads(PATH.read_text())
        yield data
        temp=PATH.with_name(PATH.name+f'.{os.getpid()}.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(PATH)

def authorize_extension():
    with transaction() as d:
        if d.get('total_authorized',0)<900:
            d['total_authorized']=900;d['purpose_caps_authorized']={'cleanup':780,'adaptation':120}
            d['events'].append(dict(event='user_authorized_conditional_third_300',total_maximum_usd=900,reason='User explicitly authorized another$300 if needed to finish proof cleanup and second training run.',time=time.time()))

def snapshot():
    with transaction() as d:return json.loads(json.dumps(d))

def activate_second_tranche(reason):
    with transaction() as d:
        d['tranche2activated']=True;d['events'].append(dict(event='activate_preapproved_second_tranche',reason=reason,time=time.time()))

def activate_third_tranche(reason):
    with transaction() as d:
        assert d.get('total_authorized',0)>=900,'Additional tranche not authorized'
        if not d.get('tranche3activated'):
            d['tranche3activated']=True
            d['events'].append(dict(event='activate_preapproved_third_tranche',reason=reason,time=time.time()))

def reserve(identity,purpose,amount,model='gpt-5.6-terra'):
    assert purpose in ['cleanup','adaptation'] and amount>0 and model in RATES
    with transaction() as d:
        if d.get('hard_hold'):return False
        assert identity not in d['charges'] and identity not in d['reservations'],identity
        spent=sum(v['usd'] for v in d['charges'].values());held=sum(v['usd'] for v in d['reservations'].values())
        own=sum(v['usd'] for k in ['charges','reservations'] for v in d[k].values() if v['purpose']==purpose)
        if d.get('tranche3activated'):
            total=900;cap=780 if purpose=='cleanup' else 120
        else:
            total=600 if d.get('tranche2activated') else 300;cap=(480 if d.get('tranche2activated') else 240) if purpose=='cleanup' else (120 if d.get('tranche2activated') else 60)
        if (spent+held+amount>total or own+amount>cap) and d.get('total_authorized',0)>=900 and not d.get('tranche3activated'):
            d['tranche3activated']=True;total=900;cap=780 if purpose=='cleanup' else 120
            d['events'].append(dict(event='activate_preapproved_third_tranche',reason='Requested bounded work plus in-flight exposure exceeds the earlier allocation; user authorized additional$300.',time=time.time()))
        if spent+held+amount>total or own+amount>cap:
            d['events'].append(dict(event='reserve_denied',identity=identity,purpose=purpose,usd=amount,time=time.time()));return False
        d['reservations'][identity]=dict(purpose=purpose,usd=amount,model=model,time=time.time())
        d['events'].append(dict(event='reserve',identity=identity,purpose=purpose,usd=amount,model=model,time=time.time()));return True

def settle(identity,usage=None,unknown=False):
    with transaction() as d:
        item=d['reservations'].pop(identity,None);prior=d['charges'].get(identity)
        if item is None and prior is None:raise KeyError(identity)
        if item is None and unknown:return prior
        item=item or prior;model=item.get('model','gpt-5.6-terra')
        cost=item['usd'] if unknown else charge_estimate(usage or {},model)
        d['charges'][identity]=dict(purpose=item['purpose'],model=model,usd=cost,base_rate_estimate_usd=None if unknown else estimate(usage or {},model),usage=usage,unknown_usage=unknown,time=time.time())
        d['events'].append(dict(event='settle_reconciled' if prior else 'settle',identity=identity,purpose=item['purpose'],model=model,usd=cost,time=time.time()))
        if cost>item['usd']+1e-9:d['hard_hold']=dict(reason='Measured conservative charge exceeded reserved exposure; stop new calls and investigate.',identity=identity,time=time.time())
        return d['charges'][identity]

def release(identity,reason):
    with transaction() as d:
        item=d['reservations'].pop(identity);d['events'].append(dict(event='release',identity=identity,usd=item['usd'],reason=reason,time=time.time()))

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
    return (total if found else None),window

def stop(process):
    if process.poll() is not None:return
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()

def run_cli(command,env,stdin,purpose,identity,profile,cwd,stdout_path,reservation=10.,stop_at=1.2,timeout=900,on_start=None,model='gpt-5.6-terra'):
    if not reserve(identity,purpose,reservation,model):return dict(state='BUDGET_HOLD',returncode=None)
    started=time.time();reason=None;proc=None
    try:
        with Path(stdout_path).open('x') as stream:
            proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,cwd=cwd,env=env,text=True,start_new_session=True)
            if on_start:on_start(proc.pid,started)
            proc.stdin.write(stdin);proc.stdin.close()
            while proc.poll() is None:
                used,window=session_usage(profile,started)
                if used and charge_estimate(used,model)>=stop_at:reason='conservative_configured_price_stop'
                if time.time()-started>timeout:reason='cli_timeout'
                if reason:stop(proc);break
                time.sleep(.5)
        used,window=session_usage(profile,started);charge=settle(identity,used,unknown=used is None)
        return dict(state='EXITED',returncode=proc.returncode,usage=used,model=model,model_context_window=window,stop_reason=reason,base_rate_estimate_usd=charge.get('base_rate_estimate_usd'),conservative_charge_usd=charge['usd'],unknown_usage=used is None)
    except BaseException:
        if proc is not None:stop(proc)
        settle(identity,None,unknown=True);raise
