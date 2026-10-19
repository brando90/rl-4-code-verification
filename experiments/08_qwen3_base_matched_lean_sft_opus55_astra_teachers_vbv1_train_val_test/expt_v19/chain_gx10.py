"""Persistently own the final GX10 condition from immutable artifact handoff through full frozen validation."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
from common import ROOT,REPO,HERE,clean_env,digest,write,run_stage

LABEL='v19_final_cleaned_gx10'

def read(path):return json.loads(Path(path).read_text())
def live(record):
    try:
        stat=Path(f"/proc/{record['pid']}/stat").read_text().rsplit(') ',1)[1].split()
        return stat[0]!='Z' and stat[19]==str(record['start_ticks']) and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==record['boot_id']
    except (OSError,KeyError):return False

def state(value,**kwargs):write(ROOT/'chain_progress.json',dict(state=value,observed_unix=time.time(),owner_pid=os.getpid(),host=socket.gethostname(),**kwargs))
def wait_ready(path):
    while not path.exists():state('WAITING_FOR_'+path.stem.upper(),artifact=str(path));time.sleep(30)
    record=read(path);assert record.get('state')=='READY' and record.get('all_files_hash_checked') is True,path
    manifest=ROOT/f"transfer_manifest_{record['identity']}.json";assert digest(manifest)==record['manifest_sha256']
    for entry in read(manifest)['entries']:assert digest(ROOT/entry['destination'])==entry['sha256'],entry['destination']
    return record

def stage(name,command,env,timeout,retries=0):
    folder=ROOT/'execution'/LABEL;receipt=folder/(name+'.json')
    if receipt.exists():
        prior=read(receipt)
        while prior['status']=='RUNNING' and live(prior):
            state('MONITORING_PRESERVED_'+name.upper(),child_pid=prior['pid']);time.sleep(30)
            if receipt.exists():prior=read(receipt)
        if prior['status']=='DONE':return prior
        completed={'training':ROOT/'conditions/final/run/result.json','full_model_smoke':ROOT/'conditions/partial818/smoke/result.json'}.get(name)
        if completed and completed.exists() and read(completed).get('status')=='COMPLETE':
            prior.update(status='DONE',reconciled_after_owner_death=True,ended_unix=time.time());write(receipt,prior);return prior
        if name=='training' and (ROOT/'conditions/final/run/first_update.json').exists():
            raise RuntimeError('Preserve interrupted optimizer trajectory: explicit checkpoint recovery required; no silent restart')
        archives=folder/'attempts';archives.mkdir(parents=True,exist_ok=True)
        previous=len(list(archives.glob(name+'.*.json')))
        if previous>=retries:raise RuntimeError('Stage failed/dead with declared retry limit: '+name)
        for suffix in ('.json','.log'):
            source=folder/(name+suffix)
            if source.exists():source.rename(archives/(name+f'.{previous}'+suffix))
    state('RUNNING_'+name.upper(),command=command)
    return run_stage(LABEL,name,command,env,timeout)

def idle_gpu():
    while True:
        output=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True)
        if not [line for line in output.splitlines() if line.strip()]:return
        state('WAITING_FOR_FOREIGN_GPU_CONTEXT',foreign_pids=output.splitlines());time.sleep(45)

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    owner=(ROOT/'chain.lock').open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state('ARMED_WAITING_FOR_IMMUTABLE_INPUTS')
    def heartbeat():
        while True:
            detail={}
            for name in ['chain_progress.json','conditions/final/run/progress.json']:
                path=ROOT/name
                if path.exists():detail[name]=read(path)
            write(ROOT/'chain_heartbeat.json',dict(owner_pid=os.getpid(),observed_unix=time.time(),details=detail));time.sleep(30)
    threading.Thread(target=heartbeat,daemon=True).start()
    wait_ready(ROOT/'transfer_completion_initial.json')
    wrapper=ROOT/'code/train_gx10.py';ready=ROOT/'code/port_ready.json'
    while not ready.exists():state('WAITING_FOR_ASTRA_WRAPPER');time.sleep(30)
    assert read(ready)['state']=='READY_FOR_SMOKE' and digest(wrapper)==read(ready)['train_wrapper_sha256']
    env=clean_env('0');env.update(GX19_INFERENCE_DTYPE='float16')
    # One cross-host phase grant prevents a disposable control overlapping SNAP's V19 GPU work.
    while not (ROOT/'gx10_smoke_grant.json').exists():
        decision_path=ROOT/'production_host.json'
        if decision_path.exists() and read(decision_path)['host']=='SNAP':state('FENCED_PENDING_GX10_CONTROL');return
        state('WAITING_FOR_CROSS_HOST_GPU_PHASE_GRANT');time.sleep(15)
    grant=read(ROOT/'gx10_smoke_grant.json');assert grant['state']=='GRANTED' and grant['owner']=='GX10_SMOKE'
    gpu=(ROOT/'gpu.lock').open('a');fcntl.flock(gpu,fcntl.LOCK_EX);idle_gpu()
    frozen=ROOT/'code/expt_v12_frozen'
    trainer=[sys.executable,str(wrapper),'--root',str(ROOT),'--condition','partial818','--frozen-source-dir',str(frozen),'--smoke']
    stage('full_model_smoke',trainer,env,2*3600)
    smoke=read(ROOT/'conditions/partial818/smoke/result.json');update=read(ROOT/'conditions/partial818/smoke/first_update.json')
    assert smoke['status']=='COMPLETE' and update['status']=='PASS' and update['grad_norm']>0
    write(ROOT/'controls/full_model_control.json',dict(status='PASS',result_sha256=digest(ROOT/'conditions/partial818/smoke/result.json'),first_update_sha256=digest(ROOT/'conditions/partial818/smoke/first_update.json'),disposable=True,smoke_weights_reused=False,observed_unix=time.time()))
    gpu.close()
    wait_ready(ROOT/'transfer_completion_evaluation.json')
    gpu=(ROOT/'gpu.lock').open('a');fcntl.flock(gpu,fcntl.LOCK_EX);idle_gpu()
    stage('sampling_controls',[sys.executable,str(HERE/'inference_controls.py')],env,300);gpu.close()
    write(ROOT/'gx10_gpu_phase_complete.json',dict(state='COMPLETE',grant_sha256=digest(ROOT/'gx10_smoke_grant.json'),full_model_control_sha256=digest(ROOT/'controls/full_model_control.json'),sampling_control_sha256=digest(ROOT/'controls/inference_controls.json'),observed_unix=time.time()))
    wait_ready(ROOT/'transfer_completion_final.json')
    while not (ROOT/'production_host.json').exists():state('WAITING_FOR_SINGLE_PRODUCTION_HOST_DECISION');time.sleep(30)
    decision=read(ROOT/'production_host.json');assert decision['state']=='FROZEN' and decision['condition']=='v19_final_cleaned'
    if decision['host']!='GX10':state('FENCED_PRODUCTION_ON_SNAP',decision=decision);return
    assert decision['v18_completion_sha256']==digest(ROOT/'sources/v18/completion.json')
    cpu=clean_env('')
    finaldata=ROOT/'conditions/final/data';prepare=finaldata/'prepare_receipt.json'
    if not prepare.exists():
        stage('assemble_final',[sys.executable,str(HERE/'assemble_final_data.py'),'--base-data',str(ROOT/'conditions/partial818/data'),'--v18-root',str(ROOT/'sources/v18'),'--receipt-root',str(ROOT/'sources/v18/final/proof_receipts'),'--initial',str(ROOT/'initial_hf'),'--frozen-source',str(frozen),'--repo',str(REPO),'--kernel',str(REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py'),'--output',str(finaldata)],cpu,2*3600)
    prepared=read(prepare);assert prepared['status']=='PASS' and prepared['preparation_code_sha256']==digest(HERE/'assemble_final_data.py') and prepared['v18_completion_sha256']==decision['v18_completion_sha256']
    freeze=dict(state='FROZEN',host_decision_sha256=digest(ROOT/'production_host.json'),prepare_receipt_sha256=digest(prepare),wrapper_sha256=digest(wrapper),chain_sha256=digest(Path(__file__)),execution_source_sha256={name:digest(HERE/name) for name in ['common.py','chain_gx10.py','watch_chain.py','generate_gx10.py','score_gx10.py','assemble_final_data.py','inference_controls.py']},inference_dtype='float16',inference_backend='transformers_gpu_per_cell_rng_v19',generation_batch=16,v12_numeric_equivalence_claimed=False,observed_unix=time.time())
    freeze_path=ROOT/'production_freeze.json'
    if freeze_path.exists():
        prior_freeze=read(freeze_path);assert all(prior_freeze[key]==value for key,value in freeze.items() if key!='observed_unix')
    else:write(freeze_path,freeze)
    stage('kernel_controls',[sys.executable,str(HERE/'score_gx10.py'),'controls'],cpu,600)
    gpu=(ROOT/'gpu.lock').open('a');fcntl.flock(gpu,fcntl.LOCK_EX);idle_gpu()
    stage('training',[sys.executable,str(wrapper),'--root',str(ROOT),'--condition','final','--frozen-source-dir',str(frozen)],env,72*3600)
    assert read(ROOT/'conditions/final/run/result.json')['status']=='COMPLETE'
    raw=ROOT/'validation'/LABEL/'raw.jsonl';ids=REPO/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_validation_task_ids.txt'
    cmd=[sys.executable,str(HERE/'generate_gx10.py'),'--pack',str(ROOT/'validation_pack'),'--task-ids',str(ids),'--model',str(ROOT/'conditions/final/run/hf'),'--label',LABEL,'--samples','8','--thinking','on','--seed','91','--stop-token','<|im_end|>','--max-tokens','12288','--temperature','0.6','--top-p','0.95','--top-k','20','--batch','16','--out',str(raw)]
    stage('generation',cmd,env,7*24*3600,retries=1)
    gpu.close()
    # Reuse exact scorer functions while allowing recovery of complete component stages.
    import score_gx10 as scoring
    scoring.run_stage=lambda label,name,command,environment,timeout:stage(name,command,environment,timeout,retries=1)
    state('RUNNING_FROZEN_SCORING');scoring.score(LABEL)
    result=read(ROOT/'analysis'/f'{LABEL}_summary.json');write(ROOT/'terminal.json',dict(status='COMPLETE',summary=result,ended_unix=time.time(),test_split_evaluated=False));state('COMPLETE',summary=result)

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        write(ROOT/'terminal.json',dict(status='FAILED',error=repr(exc),ended_unix=time.time(),no_silent_optimizer_restart=True));state('FAILED',error=repr(exc));raise
