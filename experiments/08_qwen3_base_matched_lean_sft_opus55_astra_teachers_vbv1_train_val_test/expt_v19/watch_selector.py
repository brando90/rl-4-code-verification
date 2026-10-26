"""Supervise the SNAP selector and its child stages without killing healthy GPU work or resetting updates."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training/corpus_training_v19');HERE=Path(__file__).resolve().parent
os.environ.update(GX19_ROOT=str(ROOT),GX19_REPO='/lfs/skampere1/0/eth127/rl4cv_tiny_training/repo')
from common import write
from chain_gx10 import live

def read(path):return json.loads(path.read_text())
def main():
    ROOT.mkdir(parents=True,exist_ok=True);lock=(ROOT/'watch_selector.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);folder=ROOT/'watch';folder.mkdir(exist_ok=True)
    attempt=0
    while attempt<3:
        if (ROOT/'terminal.json').exists() and read(ROOT/'terminal.json').get('status')=='COMPLETE':return
        if (ROOT/'production_host.json').exists() and read(ROOT/'production_host.json')['host']=='GX10':return
        with (folder/f'selector_attempt_{attempt}.log').open('a') as log:
            process=subprocess.Popen([sys.executable,'-u',str(HERE/'select_and_run.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            while process.poll() is None:
                progress=ROOT/'conditions/final/run/progress.json'
                write(ROOT/'watch_progress.json',dict(state='MONITORING',attempt=attempt,owner_pid=process.pid,training_progress=read(progress) if progress.exists() else None,observed_unix=time.time()));time.sleep(30)
        if process.returncode==0:return
        if process.returncode==75:time.sleep(30);continue
        execution=ROOT/'execution/v19_final_cleaned_snap'
        children=[read(path) for path in execution.glob('*.json') if read(path).get('status')=='RUNNING']
        while any(live(record) for record in children):
            write(ROOT/'watch_progress.json',dict(state='MONITORING_PRESERVED_CHILD_AFTER_OWNER_DEATH',children=[r['pid'] for r in children if live(r)],observed_unix=time.time()));time.sleep(30)
        result=ROOT/'conditions/final/run/result.json'
        if (ROOT/'conditions/final/run/first_update.json').exists() and not (result.exists() and read(result).get('status')=='COMPLETE'):
            write(ROOT/'watch_progress.json',dict(state='PRESERVED_INTERRUPTED_OPTIMIZER_NEEDS_EXPLICIT_RECOVERY',observed_unix=time.time(),no_silent_optimizer_reset=True));return
        write(ROOT/'watch_progress.json',dict(state='BOUNDED_OWNER_RECOVERY',attempt=attempt,observed_unix=time.time()));attempt+=1;time.sleep(30)
    write(ROOT/'watch_progress.json',dict(state='FAILED_AFTER_BOUNDED_RECOVERY',observed_unix=time.time()))
if __name__=='__main__':main()
