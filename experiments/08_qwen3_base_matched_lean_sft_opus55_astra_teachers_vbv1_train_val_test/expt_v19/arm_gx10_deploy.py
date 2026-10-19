"""Wait locally for the existing authenticated SNAP socket, then launch one Astra port and one artifact relay."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
CONTROL=Path('/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control')
LOCAL=Path('/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-gx10-transfer-v19')
REMOTE='/lfs/skampere1/0/eth127/rl4cv_tiny_training/gx10_port_v19'
GX='/home/lethan3/workspace/rl4cv-gx10/experiment-v19'
SSH=['ssh','-S',str(CONTROL),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ProxyCommand=/usr/bin/false','eth127@skampere1.stanford.edu']


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');tmp.replace(path)


def remote(code):return subprocess.run(SSH+[code],capture_output=True,text=True,timeout=120,check=True)


def main():
    LOCAL.mkdir(parents=True,exist_ok=True);started=time.time()
    assert not (LOCAL/'deploy_launched.json').exists(),'Deployment already launched; inspect existing receipts'
    while True:
        write(LOCAL/'deploy_watch.json',dict(state='WAITING_FOR_EXISTING_AUTHENTICATED_SOCKET',observed_unix=time.time(),
            elapsed_seconds=time.time()-started,fresh_network_login_attempts=0))
        if CONTROL.exists():
            # An OpenSSH control command addresses the local master only; it cannot start a fresh network login.
            check=subprocess.run(['ssh','-S',str(CONTROL),'-O','check','eth127@skampere1.stanford.edu'],capture_output=True,timeout=5)
            if check.returncode==0:break
        time.sleep(15)
    write(LOCAL/'deploy_watch.json',dict(state='AUTHENTICATED_MASTER_FOUND',observed_unix=time.time()))
    remote('mkdir -p '+shlex.quote(REMOTE))
    files=[HERE/name for name in ('run_astra_port.py','astra_port_prompt.md','prepare_transfer.py','stream_artifacts.py')]
    subprocess.run(['scp','-q','-o','ControlPath='+str(CONTROL),'-o','ProxyCommand=/usr/bin/false','-o','BatchMode=yes',
        *map(str,files),'eth127@skampere1.stanford.edu:'+REMOTE+'/'],check=True,timeout=60)
    command='/usr/bin/python3 -u '+shlex.quote(REMOTE+'/run_astra_port.py')+' > '+shlex.quote(REMOTE+'/astra_driver.log')+' 2>&1'
    remote('tmux new-session -d -s codex-rl4cv-astra-gx10-port-v19 '+shlex.quote('bash -c '+shlex.quote(command)))
    write(LOCAL/'deploy_launched.json',dict(astra_session='codex-rl4cv-astra-gx10-port-v19',astra_root=REMOTE+'/astra',
        started_unix=time.time(),model='gpt-6-astra',effort='high',single_artifact_writer=True))
    prepared=remote('/usr/bin/python3 '+shlex.quote(REMOTE+'/prepare_transfer.py')+' --output '+shlex.quote(REMOTE+'/transfer_manifest_initial.json'))
    (LOCAL/'prepare_transfer.log').write_text(prepared.stdout+prepared.stderr)
    with (LOCAL/'relay_driver.log').open('a') as log:
        relay=subprocess.Popen([sys.executable,str(HERE/'relay_artifacts.py')],stdout=log,stderr=subprocess.STDOUT)
        write(LOCAL/'deploy_watch.json',dict(state='RELAY_RUNNING_ASTRA_LAUNCHED',relay_pid=relay.pid,observed_unix=time.time()))
        code=relay.wait()
    write(LOCAL/'deploy_completion.json',dict(state='RELAY_DONE' if code==0 else 'RELAY_FAILED',relay_exit=code,
        observed_unix=time.time(),astra_completion_remote=REMOTE+'/astra/completion.json'))
    raise SystemExit(code)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        write(LOCAL/'deploy_failure.json',dict(error=repr(exc),observed_unix=time.time(),fresh_network_login_attempts=0))
        raise
