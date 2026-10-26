"""Wait for bound cleanup completion, freeze matched replacements, then launch the second 1.7B pipeline on a free GPU."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from assemble import ROOT,RUN,HERE,write

def free_gpu(started):
    """Wait without a lease; the pipeline still performs atomic shared allocator admission."""
    while True:
        inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used','--format=csv,noheader,nounits'],text=True)
        devices={parts[0].strip():(parts[1].strip(),int(parts[2].strip())) for line in inventory.splitlines() if (parts:=line.split(','))}
        busy=set(subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True).split())
        eligible=['2']+(['1'] if (ROOT/'current/released.json').exists() else [])
        chosen=next((gpu for gpu in eligible if devices[gpu][1]<64 and devices[gpu][0] not in busy),None)
        if chosen:return chosen
        if time.time()-started>24*3600:raise TimeoutError('No authorized GPU became free in the declared waiting window')
        write(ROOT/'cleaned_dispatcher.json',dict(status='WAITING_FOR_FREE_GPU',observed_unix=time.time(),eligible=eligible));time.sleep(30)

def main():
    started=time.time();completion=RUN/'lean_corpus_v13/completion.json';write(ROOT/'cleaned_dispatcher.json',dict(status='WAITING_FOR_CLEANUP',pid=os.getpid(),started_unix=started))
    while not completion.exists() or not (ROOT/'current/data/prepare_receipt.json').exists():
        if time.time()-started>24*3600:
            write(ROOT/'cleaned_dispatcher.json',dict(status='CLEANUP_TIMEOUT',observed_unix=time.time()));return 1
        time.sleep(15)
    status=json.loads(completion.read_text());assert status['state'] in ('DONE','DONE_PARTIAL'),status
    for stage,command in [('prepare',[sys.executable,str(HERE/'assemble_cleaned.py')]),('pipeline',[sys.executable,str(HERE/'pipeline.py'),'--condition','cleaned','--gpu','2'])]:
        attempts=3 if stage=='pipeline' else 1
        for attempt in range(1,attempts+1):
            if stage=='pipeline':command[-1]=free_gpu(started)
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
            suffix='' if attempt==1 else f'_attempt_{attempt:02d}'
            with (ROOT/f'cleaned_{stage}{suffix}.log').open('x') as log:
                child=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                write(ROOT/'cleaned_dispatcher.json',dict(status=stage.upper()+'_RUNNING',pid=os.getpid(),child_pid=child.pid,attempt=attempt,observed_unix=time.time()))
                code=child.wait()
            if code==0:break
            # Only replay admission failures that created no smoke or training trajectory.
            # All scientific data/seed/settings remain identical and each attempt retains its log.
            untouched=not (ROOT/'execution/v12_cleaned/smoke.json').exists() and not (ROOT/'cleaned/smoke').exists()
            if stage!='pipeline' or not untouched or attempt==attempts:break
            write(ROOT/'cleaned_dispatcher.json',dict(status='EARLY_ADMISSION_RETRY',exit_code=code,attempt=attempt,observed_unix=time.time()));time.sleep(15)
        if code:
            write(ROOT/'cleaned_dispatcher.json',dict(status=stage.upper()+'_FAILED',exit_code=code,observed_unix=time.time()));return code
    write(ROOT/'cleaned_dispatcher.json',dict(status='COMPLETE',ended_unix=time.time()));return 0

if __name__=='__main__':
    try:code=main()
    except BaseException as exc:
        write(ROOT/'cleaned_dispatcher.json',dict(status='COORDINATOR_FAILED',error=repr(exc),pid=os.getpid(),observed_unix=time.time()));raise
    sys.exit(code)
