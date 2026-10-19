"""Resume compact read-only receipts after an existing authenticated master returns."""
from __future__ import annotations
import fcntl
import json
from pathlib import Path
import stat
import subprocess
import time

HERE=Path(__file__).resolve().parent
RESULTS=HERE/'results'
CONTROL=Path('/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control')
HOST='eth127@skampere1.stanford.edu'
REMOTE='''from pathlib import Path
import hashlib,json
run=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
out={}
for phase in ['v21','v22']:
 root=run/('lean_corpus_'+phase);files={}
 for name in ['progress.json','completion.json','cohort_closed.json','watch_heartbeat.json','provider_hold.json','budget_hold.json','coordinator_attention.json','runtime_manifest.json','pricing_controls.json','final/row_results.csv','final/proof_receipts_manifest.json','final/protected_screen.json']:
  p=root/name
  if p.exists():
   raw=p.read_bytes();files[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),text=raw.decode())
 out[phase]=files
print(json.dumps(out))
'''

def write(path,data):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(path)

def main():
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS/'visibility.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        deadline=time.time()+12*3600
        while time.time()<deadline:
            try:ready=stat.S_ISSOCK(CONTROL.stat().st_mode)
            except FileNotFoundError:ready=False
            if not ready:
                write(RESULTS/'visibility_status.json',dict(state='WAITING_FOR_EXISTING_AUTHENTICATED_SOCKET',observed_unix=time.time(),no_fresh_gateway_login=True));time.sleep(10);continue
            check=subprocess.run(['ssh','-S',str(CONTROL),'-O','check',HOST],capture_output=True,timeout=5)
            if check.returncode:time.sleep(10);continue
            # Multiplex an existing authenticated transport only. If it disappears
            # between the check and this read, false ProxyCommand prevents fallback
            # gateway authentication or SSH-agent key attempts.
            args=['ssh','-S',str(CONTROL),'-o','ControlMaster=no','-o','ProxyCommand=false','-o','ProxyJump=none','-o','BatchMode=yes','-o','IdentityAgent=none','-o','IdentitiesOnly=yes',HOST,'python3 -']
            try:
                read=subprocess.run(args,input=REMOTE,text=True,capture_output=True,timeout=30)
                if read.returncode:raise RuntimeError('Existing-master-only receipt read failed with code '+str(read.returncode))
                snapshot=json.loads(read.stdout)
                for phase,files in snapshot.items():
                    for name,record in files.items():
                        label=phase+'_'+name.replace('/','_')
                        target=RESULTS/('observed_'+label)
                        target.write_text(record['text'])
                done=all('completion.json' in snapshot.get(phase,{}) for phase in ['v21','v22'])
                write(RESULTS/'visibility_status.json',dict(state='BOTH_COMPLETIONS_OBSERVED' if done else 'OBSERVING_EXISTING_MASTER',file_sha256={phase:{name:r['sha256'] for name,r in files.items()} for phase,files in snapshot.items()},observed_unix=time.time(),no_fresh_gateway_login=True))
                if done:return
            except Exception as exc:write(RESULTS/'visibility_status.json',dict(state='EXISTING_MASTER_READ_UNAVAILABLE',error=repr(exc),observed_unix=time.time(),no_fresh_gateway_login=True))
            time.sleep(30)

if __name__=='__main__':main()
