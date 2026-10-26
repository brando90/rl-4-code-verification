"""Persistent CPU handoff from complete counterpart checks to the one dataset freeze."""
import fcntl
import json
import os
import subprocess
import sys
import time
from assemble import ROOT,HERE,write,digest

def main():
    lock=(ROOT/'preparation.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    target=ROOT/'base/data/prepare_receipt.json'
    if target.exists():assert json.loads(target.read_text())['status']=='PASS';return
    while not (ROOT/'restoration_verification/completion.json').exists():
        write(ROOT/'preparation.json',dict(state='WAITING_FOR_ALL_COUNTERPART_CHECKS',pid=os.getpid(),observed_unix=time.time()));time.sleep(1)
    completion=json.loads((ROOT/'restoration_verification/completion.json').read_text());assert completion['state']=='DONE'
    command=[sys.executable,str(HERE/'assemble.py')]
    write(ROOT/'preparation.json',dict(state='ASSEMBLING_MATCHED_COHORT',pid=os.getpid(),command=command,assemble_sha256=digest(HERE/'assemble.py'),observed_unix=time.time()))
    with (ROOT/'assembly.log').open('x') as log:
        result=subprocess.run(command,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''),stdout=log,stderr=subprocess.STDOUT,check=False,timeout=1800)
    assert result.returncode==0,result.returncode
    receipt=json.loads(target.read_text());assert receipt['status']=='PASS'
    write(ROOT/'preparation.json',dict(state='DATASET_FROZEN_DISPATCHER_CAN_ADMIT',pid=os.getpid(),rows=receipt['rows'],restored=receipt['restored_rows'],training_sha256=receipt['training_sha256'],observed_unix=time.time()))

if __name__=='__main__':
    try:main()
    except BaseException as error:write(ROOT/'preparation.json',dict(state='FAILED',pid=os.getpid(),error=repr(error),observed_unix=time.time()));raise
