"""Serialize this experiment's GPU phases across hosts without altering any foreign or V17 job."""
import fcntl
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

LOCAL=Path('/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-v19-gpu-phase')
CONTROL=Path('/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control')
SNAP='/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v19'
GX='/home/lethan3/workspace/rl4cv-gx10/experiment-v19'

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)
def ssh(host):
    if host=='GX10':return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','cactushacks-gx10']
    if not CONTROL.exists():return None
    check=subprocess.run(['ssh','-S',str(CONTROL),'-O','check','eth127@skampere1.stanford.edu'],capture_output=True,timeout=5)
    if check.returncode:return None
    return ['ssh','-S',str(CONTROL),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ProxyCommand=/usr/bin/false','eth127@skampere1.stanford.edu']
def get(host,paths):
    route=ssh(host)
    if route is None:return {}
    root=GX if host=='GX10' else SNAP
    code='import json;from pathlib import Path;r=Path('+repr(root)+');names='+repr(paths)+';print(json.dumps({n:json.loads((r/n).read_text()) for n in names if (r/n).exists()}))'
    try:
        result=subprocess.run(route+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=45,check=True);return json.loads(result.stdout)
    except (subprocess.SubprocessError,json.JSONDecodeError):return {}
def put(host,name,obj):
    route=ssh(host);assert route is not None
    root=GX if host=='GX10' else SNAP
    text=json.dumps(obj,indent=2)+'\n'
    code='import json;from pathlib import Path;p=Path('+repr(root+'/'+name)+');s='+repr(text)+';p.parent.mkdir(parents=True,exist_ok=True);old=json.loads(p.read_text()) if p.exists() else None;assert old is None or old==json.loads(s);q=p.with_suffix(".tmp");q.write_text(s);q.replace(p)'
    subprocess.run(route+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=45,check=True)
def main():
    LOCAL.mkdir(parents=True,exist_ok=True);lock=(LOCAL/'owner.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    saved=LOCAL/'state.json';current=json.loads(saved.read_text()) if saved.exists() else dict(state='UNGRANTED')
    while True:
        snap=get('SNAP',['selection_ready.json','production_host.json','snap_phase_grant.json'])
        gx=get('GX10',['transfer_completion_initial.json','code/port_ready.json','gx10_gpu_phase_complete.json','gx10_smoke_grant.json'])
        write(LOCAL/'progress.json',dict(current,observed_unix=time.time(),snap_ready='selection_ready.json' in snap,gx_inputs_ready='transfer_completion_initial.json' in gx and 'code/port_ready.json' in gx,fresh_snap_login_attempts=0))
        if current['state']=='UNGRANTED' and 'snap_phase_grant.json' in snap:
            current=dict(state='SNAP_SELECTION_GRANTED',grant=snap['snap_phase_grant.json'])
            if 'gx10_gpu_phase_complete.json' in gx:current['gx10_phase_complete']=gx['gx10_gpu_phase_complete.json']
        elif current['state']=='UNGRANTED' and 'gx10_smoke_grant.json' in gx:
            current=dict(state='GX10_SMOKE_GRANTED',grant=gx['gx10_smoke_grant.json'])
        if current['state']=='UNGRANTED':
            if 'selection_ready.json' in snap:
                grant=dict(state='GRANTED',owner='SNAP_SELECTION',reason='SNAP final CPU cohort ready before GX disposable control start',granted_unix=time.time());put('SNAP','snap_phase_grant.json',grant);current=dict(state='SNAP_SELECTION_GRANTED',grant=grant)
            elif all(k in gx for k in ['transfer_completion_initial.json','code/port_ready.json']):
                grant=dict(state='GRANTED',owner='GX10_SMOKE',reason='Initial GX control inputs ready before SNAP final CPU cohort',granted_unix=time.time());put('GX10','gx10_smoke_grant.json',grant);current=dict(state='GX10_SMOKE_GRANTED',grant=grant)
        elif current['state']=='GX10_SMOKE_GRANTED':
            complete=gx.get('gx10_gpu_phase_complete.json')
            if complete and complete['state']=='COMPLETE' and ssh('SNAP') is not None:
                grant=dict(state='GRANTED',owner='SNAP_SELECTION',reason='GX10 disposable GPU phase completed; no V19 overlap',gx10_phase_complete=complete,granted_unix=time.time());put('SNAP','snap_phase_grant.json',grant);current=dict(state='SNAP_SELECTION_GRANTED',grant=grant,gx10_phase_complete=complete)
        elif current['state']=='SNAP_SELECTION_GRANTED':
            decision=snap.get('production_host.json')
            if decision:
                assert decision['state']=='FROZEN'
                if decision['host']=='GX10' and 'gx10_phase_complete' not in current:
                    grant=dict(state='GRANTED',owner='GX10_SMOKE',reason='SNAP chose GX10 without starting a GPU phase',granted_unix=time.time());put('GX10','gx10_smoke_grant.json',grant)
                current.update(state='COMPLETE',production_host=decision['host'],completed_unix=time.time());write(saved,current);return
        write(saved,current);time.sleep(30)
if __name__=='__main__':main()
