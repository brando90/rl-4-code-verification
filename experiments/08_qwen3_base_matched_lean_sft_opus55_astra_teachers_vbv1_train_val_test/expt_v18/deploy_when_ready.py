"""Deploy the authorized full cleanup after an existing SSH control socket is restored, without gateway polling."""
from __future__ import annotations
import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import signal
import socket
import stat
import subprocess
import time

HERE=Path(__file__).resolve().parent
CONTROL=Path('/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control')
HOST='eth127@skampere1.stanford.edu'
REMOTE='/lfs/skampere1/0/eth127/rl4cv_tiny_training/repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v18'
RUN='/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v18'
FILES=['repair_batches.py','watch_batches.py','finalize_full.py','controls.py','PROTOCOL.md','README.md','results.md','CKPT_full_cleanup.md']

def record(state,**fields):
    path=HERE/'results/deployment_receipt.json';path.parent.mkdir(exist_ok=True)
    data=dict(state=state,control=str(CONTROL),observed_unix=time.time(),**fields)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)
    print(json.dumps(data),flush=True)

def command(args,timeout=60):
    process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    try:out,err=process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGTERM)
        try:out,err=process.communicate(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);out,err=process.communicate()
        raise RuntimeError('Bounded transport operation timed out: '+args[0])
    if process.returncode:raise RuntimeError(f'{args[0]} returned {process.returncode}: '+err[-1500:]+out[-1500:])
    return out

def ssh(text,timeout=60):
    return command(['ssh','-S',str(CONTROL),'-o','BatchMode=yes','-o','ConnectTimeout=10',HOST,text],timeout)

def deploy():
    record('UPLOADING')
    ssh('mkdir -p '+shlex.quote(REMOTE))
    command(['scp','-o','ControlPath='+str(CONTROL),'-o','BatchMode=yes',*[str(HERE/f) for f in FILES],HOST+':'+REMOTE+'/'],60)
    record('PREPARING_REMOTE')
    # Source preparation may be resumed only before dispatch exists; published inputs stay fixed.
    code=f'import pathlib,subprocess; p=pathlib.Path({RUN!r}); print("existing dispatch" if (p/"dispatch.json").exists() else "prepare"); subprocess.run(["python3",{REMOTE+"/repair_batches.py"!r},"prepare"],check=True) if not (p/"dispatch.json").exists() else None'
    prepared=ssh('python3 -c '+shlex.quote(code),900)
    record('RUNNING_DETERMINISTIC_CONTROLS',prepare_output=prepared[-2000:])
    controls=ssh('python3 '+shlex.quote(REMOTE+'/controls.py'),300)
    record('LAUNCHING_FIRST_REAL_BATCH',controls_output=controls[-2000:])
    launch=ssh('python3 '+shlex.quote(REMOTE+'/repair_batches.py')+' launch --first')
    code=f'''import pathlib,subprocess,json,time,hashlib
root=pathlib.Path({RUN!r});here=pathlib.Path({REMOTE!r})
name="rl4cv-v18-full-watch"
if subprocess.run(["tmux","has-session","-t",name],capture_output=True).returncode:
 subprocess.run(["tmux","new-session","-d","-s",name,f"python3 -u {{here}}/watch_batches.py >> {{root}}/watch.log 2>&1"],check=True)
manifest={{f:hashlib.sha256((here/f).read_bytes()).hexdigest() for f in {FILES!r}}}
(root/"runtime_manifest.json").write_text(json.dumps(dict(source_sha256=manifest,observed_unix=time.time()),indent=2)+"\\n")
print(json.dumps(dict(watch_session=name,first_batch=json.loads((root/"batches/batch_0000/status.json").read_text()),runtime_manifest=str(root/"runtime_manifest.json"))))
'''
    receipt=ssh('python3 -c '+shlex.quote(code),60)
    record('REMOTE_DISPATCHED',receipt=json.loads(receipt),launch_output=launch[-1000:])

def main():
    with (HERE/'results/deploy.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        record('WAITING_FOR_EXISTING_CONTROL_SOCKET')
        deadline=time.time()+12*3600;attempts=0;last_failure_identity=None
        while time.time()<deadline:
            try:
                info=CONTROL.stat()
                identity=(info.st_ino,info.st_mtime_ns)
                ready=stat.S_ISSOCK(info.st_mode)
            except FileNotFoundError:ready=False;identity=None
            if ready and identity!=last_failure_identity:
                try:
                    # This command checks the existing LOCAL master only, without a gateway login.
                    command(['ssh','-S',str(CONTROL),'-O','check',HOST],5)
                    attempts+=1;deploy();return
                except Exception as exc:
                    last_failure_identity=identity;record('TRANSPORT_FAILED_WAITING_FOR_RESTORED_SOCKET',attempts=attempts,error=repr(exc))
                    if attempts>=2:return
            time.sleep(5)
        record('WAITING_DEADLINE_REACHED',reason='No existing authenticated SSH master returned; no gateway login was attempted.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',type=Path);a=p.parse_args()
    if a.control:CONTROL=a.control
    main()
