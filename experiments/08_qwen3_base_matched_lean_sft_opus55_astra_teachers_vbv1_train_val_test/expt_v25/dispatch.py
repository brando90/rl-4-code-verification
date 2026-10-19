"""Wait for the strict freeze and atomically admitted free hardware, then supervise the complete V25 pipeline once."""
from contextlib import ExitStack
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from assemble import HERE,ROOT,RUN,REPO,EXP,write,digest

PY='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'

def main():
 owner=(ROOT/'dispatch.lock').open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
 while not (ROOT/'base/data/prepare_receipt.json').exists():
  write(ROOT/'dispatcher.json',dict(state='WAITING_FOR_STRICT_DATASET_FREEZE',pid=os.getpid(),observed_unix=time.time()));time.sleep(5)
 receipt=json.loads((ROOT/'base/data/prepare_receipt.json').read_text());assert receipt['status']=='PASS' and receipt['initial_model']=='Qwen/Qwen3-1.7B-Base' and not receipt['sft_weights_reused']
 for name,sha in receipt['v25_source_sha256'].items():assert digest(HERE/name)==sha,name
 os.environ['TINY_RUN_ROOT']=str(ROOT);spec=importlib.util.spec_from_file_location('v25_admission',REPO/EXP/'expt_v6/run_jobs.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
 attempt=0
 while True:
  devices,busy=runtime.device_inventory();free=[gpu for gpu in ['3','4','0','5','2'] if gpu in devices and devices[gpu]['uuid'] not in busy and devices[gpu]['used_mib']<64 and devices[gpu]['total_mib']>=79000]
  if not free:
   write(ROOT/'dispatcher.json',dict(state='WAITING_FOR_EMPTY_A100',pid=os.getpid(),devices=devices,observed_unix=time.time()));time.sleep(15);continue
  gpu=free[0];attempt+=1
  log=ROOT/f'pipeline_attempt_{attempt}.log';environment=dict(os.environ,CUDA_VISIBLE_DEVICES='')
  with log.open('x') as stream:
   process=subprocess.Popen([PY,str(HERE/'pipeline.py'),'--condition','base','--gpu',gpu],env=environment,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   write(ROOT/'dispatcher.json',dict(state='PIPELINE_STARTED',pid=os.getpid(),child_pid=process.pid,gpu=gpu,attempt=attempt,observed_unix=time.time(),base_revision=receipt['initial_revision'],training_sha256=receipt['training_sha256']))
   while process.poll() is None:
    progress=ROOT/'base/run/progress.json';first=ROOT/'base/run/first_update.json';write(ROOT/'watch_progress.json',dict(state='TRAINING_FIRST_UPDATE_VERIFIED' if first.exists() else 'PIPELINE_ACTIVE',owner_pid=os.getpid(),child_pid=process.pid,gpu=gpu,attempt=attempt,progress=json.loads(progress.read_text()) if progress.exists() else None,observed_unix=time.time()));time.sleep(15)
  if process.returncode==0:write(ROOT/'terminal.json',dict(status='COMPLETE',ended_unix=time.time(),test_split_evaluated=False));return
  if (ROOT/'base/run/first_update.json').exists():write(ROOT/'terminal.json',dict(status='FAILED_AFTER_UPDATES_PRESERVED',exit_code=process.returncode,ended_unix=time.time(),no_silent_optimizer_reset=True));return
  # Admission races may retry only before any stage has started; preserve every failed attempt.
  stage=ROOT/'execution/v25_base/smoke.json'
  if stage.exists() or attempt>=3:write(ROOT/'terminal.json',dict(status='FAILED_BEFORE_UPDATES',exit_code=process.returncode,ended_unix=time.time(),log=str(log)));return
  write(ROOT/'dispatcher.json',dict(state='PRE_UPDATE_ADMISSION_RETRY',attempt=attempt,gpu=gpu,observed_unix=time.time()));time.sleep(10)
if __name__=='__main__':
 try:main()
 except BaseException as exc:write(ROOT/'terminal.json',dict(status='FAILED',error=repr(exc),ended_unix=time.time()));raise
