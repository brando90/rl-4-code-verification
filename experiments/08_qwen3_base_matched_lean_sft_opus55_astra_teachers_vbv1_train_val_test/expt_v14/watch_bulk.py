"""Watch the bounded public-source CPU batch and record completion or one interrupted-driver resume."""
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess
import time
from bulk_validate import BATCH,write


def main():
    BATCH.mkdir(parents=True,exist_ok=True)
    with (BATCH/'watcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        history=[]
        for launch in range(2):
            completed=BATCH/'completion.json'
            if completed.exists() and json.loads(completed.read_text()).get('state')=='DONE':break
            with (BATCH/f'driver_launch_{launch}.log').open('a') as log:
                child=subprocess.Popen(['/usr/bin/python3','-u',str(Path(__file__).with_name('bulk_validate.py')),'run'],stdout=log,stderr=subprocess.STDOUT)
                while child.poll() is None:
                    write(BATCH/'watch_status.json',dict(state='WATCHING',pid=os.getpid(),driver_pid=child.pid,
                        launch=launch,host=socket.gethostname(),observed_unix=time.time(),model_calls=0))
                    time.sleep(15)
                history.append(dict(launch=launch,pid=child.pid,exit_code=child.returncode,finished_unix=time.time()))
            write(BATCH/'driver_history.json',history)
            if child.returncode==0:break
            # Only resume a terminated driver; deterministic assertion/freeze/control failures stop.
            if child.returncode not in (-9,-15,137,143):break
        valid=completed.exists() and json.loads(completed.read_text()).get('state')=='DONE'
        write(BATCH/'watch_completion.json',dict(state='DONE' if valid else 'FAILED',history=history,
            observed_unix=time.time(),pid=os.getpid(),host=socket.gethostname(),model_calls=0))
        raise SystemExit(0 if valid else 1)


if __name__=='__main__':main()
