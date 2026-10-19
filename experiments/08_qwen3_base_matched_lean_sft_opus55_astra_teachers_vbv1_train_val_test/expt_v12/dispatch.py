"""Wait for CPU preparation, then own the current-run pipeline and preserve terminal or dead-process evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from assemble import ROOT,HERE,write

def main():
    receipt=ROOT/'current/data/prepare_receipt.json';deadline=time.monotonic()+3600
    write(ROOT/'dispatcher.json',dict(status='WAITING_FOR_PREPARATION',pid=os.getpid(),started_unix=time.time()))
    while not receipt.exists():
        process=subprocess.run(['pgrep','-f',str(HERE/'assemble.py')],capture_output=True,text=True)
        if process.returncode or time.monotonic()>deadline:
            write(ROOT/'dispatcher.json',dict(status='PREPARATION_DEAD_OR_TIMEOUT',observed_unix=time.time(),log=str(ROOT/'assembly.log')));return 1
        time.sleep(10)
    assert json.loads(receipt.read_text())['status']=='PASS'
    command=[sys.executable,str(HERE/'pipeline.py'),'--condition','current','--gpu','1']
    with (ROOT/'pipeline_current.log').open('x') as log:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(ROOT/'dispatcher.json',dict(status='PIPELINE_RUNNING',pid=os.getpid(),pipeline_pid=child.pid,started_unix=time.time(),command=command))
        code=child.wait()
    write(ROOT/'dispatcher.json',dict(status='PIPELINE_COMPLETE' if code==0 else 'PIPELINE_FAILED',exit_code=code,ended_unix=time.time(),pipeline_pid=child.pid))
    return code

if __name__=='__main__':sys.exit(main())
