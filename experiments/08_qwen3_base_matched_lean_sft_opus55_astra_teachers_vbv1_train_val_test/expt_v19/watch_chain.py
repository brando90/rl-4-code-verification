"""Run the remote chain across chat idleness; reconcile owner death without restarting a live optimizer."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from common import ROOT,HERE,write
from chain_gx10 import live

def read(path):return json.loads(path.read_text())
def main():
    ROOT.mkdir(parents=True,exist_ok=True);lock=(ROOT/'watch_chain.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    folder=ROOT/'watch';folder.mkdir(exist_ok=True)
    for attempt in range(3):
        terminal=ROOT/'terminal.json'
        if terminal.exists() and read(terminal).get('status')=='COMPLETE':return
        with (folder/f'chain_attempt_{attempt}.log').open('a') as log:
            process=subprocess.Popen([sys.executable,str(HERE/'chain_gx10.py')],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            while process.poll() is None:
                heartbeat=ROOT/'chain_heartbeat.json';progress=read(heartbeat) if heartbeat.exists() else {}
                age=time.time()-progress.get('observed_unix',time.time())
                write(ROOT/'watch_progress.json',dict(state='MONITORING',attempt=attempt,chain_pid=process.pid,heartbeat_age_seconds=age,stale_warning=age>180,observed_unix=time.time(),healthy_child_killed=False));time.sleep(30)
        if process.returncode==0:return
        # Never perform a fresh optimizer run after an interrupted first update.
        training=ROOT/'execution/v19_final_cleaned_gx10/training.json'
        result=ROOT/'conditions/final/run/result.json'
        if (ROOT/'conditions/final/run/first_update.json').exists() and not (result.exists() and read(result).get('status')=='COMPLETE'):
            while training.exists() and live(read(training)):
                write(ROOT/'watch_progress.json',dict(state='MONITORING_PRESERVED_OPTIMIZER_AFTER_OWNER_DEATH',attempt=attempt,child_pid=read(training)['pid'],observed_unix=time.time()));time.sleep(30)
            if not (result.exists() and read(result).get('status')=='COMPLETE'):
                write(ROOT/'watch_progress.json',dict(state='PRESERVED_INTERRUPTED_OPTIMIZER_NEEDS_EXPLICIT_RECOVERY',attempt=attempt,observed_unix=time.time(),error='No silent optimizer reset'));return
        write(ROOT/'watch_progress.json',dict(state='BOUNDED_OWNER_RECOVERY',attempt=attempt,exit_code=process.returncode,observed_unix=time.time()));time.sleep(30)
    write(ROOT/'watch_progress.json',dict(state='FAILED_AFTER_BOUNDED_RECOVERY',observed_unix=time.time()))
if __name__=='__main__':main()
