"""Deploy the unattended SNAP host selector only through an existing authenticated SSH master."""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
CONTROL=Path('/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control')
LOCAL=Path('/Users/lethan3/Documents/veribench-projects/tmp/rl4cv-final-selector-v19')
RUN='/lfs/skampere1/0/eth127/rl4cv_tiny_training'
REMOTE=RUN+'/repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v19'
SESSION='rl4cv-final-host-selector-v19'
FILES=['common.py','assemble_final_data.py','prepare_final_transfer.py','select_and_run.py','train_snap.py','summarize_snap.py','chain_gx10.py','watch_selector.py']

def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)
def main():
    LOCAL.mkdir(parents=True,exist_ok=True)
    if (LOCAL/'deployed.json').exists():return
    while True:
        write(LOCAL/'progress.json',dict(state='WAITING_FOR_EXISTING_AUTHENTICATED_MASTER',observed_unix=time.time(),fresh_login_attempts=0))
        if CONTROL.exists():
            check=subprocess.run(['ssh','-S',str(CONTROL),'-O','check','eth127@skampere1.stanford.edu'],capture_output=True,timeout=5)
            if check.returncode==0:break
        time.sleep(15)
    ssh=['ssh','-S',str(CONTROL),'-o','BatchMode=yes','-o','ProxyCommand=/usr/bin/false','eth127@skampere1.stanford.edu']
    def remote(command):return subprocess.run(ssh+[command],text=True,capture_output=True,timeout=90,check=True)
    remote('mkdir -p '+shlex.quote(REMOTE))
    subprocess.run(['scp','-q','-o','ControlPath='+str(CONTROL),'-o','ProxyCommand=/usr/bin/false','-o','BatchMode=yes',*[str(HERE/n) for n in FILES],'eth127@skampere1.stanford.edu:'+REMOTE+'/'],check=True,timeout=60)
    expected={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in FILES}
    code='import hashlib,json;from pathlib import Path;r=Path('+repr(REMOTE)+');d=json.loads('+repr(json.dumps(expected))+');assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in d.items());print("SOURCE_HASH_PASS")'
    remote('python3 -c '+shlex.quote(code))
    command='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python -u '+shlex.quote(REMOTE+'/watch_selector.py')+' > '+shlex.quote(RUN+'/v19_selector.log')+' 2>&1'
    remote('tmux new-session -d -s '+shlex.quote(SESSION)+' '+shlex.quote('bash -c '+shlex.quote(command)))
    write(LOCAL/'deployed.json',dict(state='ARMED',session=SESSION,source_sha256=expected,observed_unix=time.time(),production_started=False))
if __name__=='__main__':main()
