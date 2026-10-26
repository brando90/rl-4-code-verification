"""Provide portable GX10 paths, atomic receipts, hashes and bounded subprocess supervision."""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

ROOT=Path(os.environ.get('GX19_ROOT','/home/lethan3/workspace/rl4cv-gx10/experiment-v19')).resolve()
REPO=Path(os.environ.get('GX19_REPO',ROOT/'repo')).resolve()
EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test')
HERE=Path(__file__).resolve().parent
NATIVE=Path('/home/lethan3/workspace/rl4cv-gx10/lean-v4.22.0')
LAKE_BIN=Path('/home/lethan3/workspace/rl4cv-gx10/verification-v10/bin')
FROZEN={'scripts/scsc/run_real_eval.py':'6e82b3d1cd6d3686aaec3d45f273cd902b03b962c0c2eca48f2c2b4f25f41fa9','scripts/scsc/kernel_axioms.py':'5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287','experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py':'b3713c48e0fdb24adec93b77be8785d20e48897ee8d1fd8ce31fdf37101e81d6'}

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)

def clean_env(cuda):
    env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES=cuda,HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',GX19_ROOT=str(ROOT),GX19_REPO=str(REPO),PYTHONPATH=str(REPO/'src'),VERIBENCH_ROOT=str(REPO/'external/veribench'),PATH=str(LAKE_BIN)+':'+env['PATH'])
    for key in list(env):
        if any(word in key for word in ['API_KEY','AUTH_TOKEN','ACCESS_TOKEN','BEARER_TOKEN']):env.pop(key)
    return env

def run_stage(label,stage,command,env,timeout):
    folder=ROOT/'execution'/label;folder.mkdir(parents=True,exist_ok=True);path=folder/(stage+'.json');assert not path.exists(),'Existing attempt must be reconciled explicitly: '+str(path)
    record=dict(label=label,stage=stage,command=command,status='RUNNING',host=socket.gethostname(),started_unix=time.time(),cuda_visible_devices=env['CUDA_VISIBLE_DEVICES'])
    with (folder/(stage+'.log')).open('x') as log:
        process=subprocess.Popen(command,env=env,cwd=REPO,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);record['pid']=process.pid
        record['boot_id']=Path('/proc/sys/kernel/random/boot_id').read_text().strip();record['start_ticks']=Path(f'/proc/{process.pid}/stat').read_text().rsplit(') ',1)[1].split()[19];write(path,record)
        try:code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            record['stop_reason']='Declared stage boundary';os.killpg(process.pid,signal.SIGTERM)
            try:process.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            code=124
    record.update(exit_code=code,ended_unix=time.time(),status='DONE' if code==0 else 'FAILED');write(path,record)
    if code:raise RuntimeError(f'{label}/{stage} exited{code}; see '+str(folder/(stage+'.log')))
    return record
