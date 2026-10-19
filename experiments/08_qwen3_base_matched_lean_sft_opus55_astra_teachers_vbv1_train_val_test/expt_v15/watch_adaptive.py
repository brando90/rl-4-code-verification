"""Restart a dead adaptive coordinator within a bounded incident budget while preserving live child jobs."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training/adaptive_1p7b_campaign')

def write(path,data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'outer_watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        restarts=0
        while not (ROOT/'STOP').exists():
            with (ROOT/f'owner_restart_{restarts}.log').open('a') as log:
                child=subprocess.Popen([sys.executable,'-u',str(HERE/'supervise.py')],env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                while child.poll() is None:
                    write(ROOT/'outer_watch_heartbeat.json',dict(pid=os.getpid(),child_pid=child.pid,restarts=restarts,observed_unix=time.time()))
                    time.sleep(10)
            write(ROOT/f'owner_exit_{restarts}.json',dict(returncode=child.returncode,pid=child.pid,observed_unix=time.time()))
            if child.returncode==0:return
            restarts+=1
            if restarts>=3:
                write(ROOT/'outer_watch_hold.json',dict(reason='Three failed owner starts; bounded recovery exhausted. Healthy child jobs preserved.',observed_unix=time.time()));return
            time.sleep(10)

if __name__=='__main__':main()
