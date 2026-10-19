"""Wait remotely for V18, prepare final data, atomically prefer a free leased A100, then run the complete SNAP chain or freeze GX10 selection."""
from contextlib import ExitStack
import concurrent.futures
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training');ROOT=RUN/'corpus_training_v19';REPO=RUN/'repo'
EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test');HERE=REPO/EXP/'expt_v19';V18=RUN/'lean_corpus_v18'
os.environ.update(GX19_ROOT=str(ROOT),GX19_REPO=str(REPO),TINY_RUN_ROOT=str(ROOT))
from common import digest,write,run_stage,FROZEN
from chain_gx10 import live
PY='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
GEN_SITE='/lfs/skampere1/0/brando9/rl4cv_e08/venv_gen/lib/python3.12/site-packages'
LABEL='v19_final_cleaned_snap'

def read(path):return json.loads(path.read_text())
def progress(state,**detail):write(ROOT/'chain_progress.json',dict(state=state,observed_unix=time.time(),pid=os.getpid(),**detail))
def env(gpu):
    out=os.environ.copy();out.update(CUDA_VISIBLE_DEVICES=gpu,PYTHONPATH=str(REPO/'src'),HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',PATH=str(RUN/'bin')+':'+out['PATH'])
    for key in list(out):
        if any(s in key for s in ['API_KEY','AUTH_TOKEN','ACCESS_TOKEN','BEARER_TOKEN']):out.pop(key)
    return out

def run(name,cmd,environment,timeout):
    folder=ROOT/'execution'/LABEL;path=folder/(name+'.json')
    if path.exists():
        prior=read(path)
        while prior['status']=='RUNNING' and live(prior):
            progress('MONITORING_PRESERVED_'+name.upper(),child_pid=prior['pid']);time.sleep(30);prior=read(path)
        if prior['status']=='DONE':return prior
        result={'training':ROOT/'conditions/final/run/result.json','full_model_smoke':ROOT/'conditions/final/smoke/result.json'}.get(name)
        if result and result.exists() and read(result).get('status')=='COMPLETE':
            prior.update(status='DONE',reconciled_after_owner_death=True,ended_unix=time.time());write(path,prior);return prior
        if name=='training' and (ROOT/'conditions/final/run/first_update.json').exists():raise RuntimeError('Interrupted optimizer must be recovered explicitly, never reset')
        archive=folder/'attempts';archive.mkdir(parents=True,exist_ok=True);count=len(list(archive.glob(name+'.*.json')));assert count<1,'Bounded retry limit reached'
        for suffix in ['.json','.log']:
            source=folder/(name+suffix)
            if source.exists():source.rename(archive/(name+f'.{count}'+suffix))
        output={'training':ROOT/'conditions/final/run','full_model_smoke':ROOT/'conditions/final/smoke'}.get(name)
        if output and output.exists():output.rename(archive/(name+f'.{count}.artifacts'))
    progress('RUNNING_'+name.upper());return run_stage(LABEL,name,cmd,environment,timeout)

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def freeze(host,completion,gpu=None,evidence=None):
    path=ROOT/'production_host.json'
    if path.exists():
        previous=read(path);assert previous['host']==host and previous['gpu']==gpu and previous['v18_completion_sha256']==digest(V18/'completion.json');return previous
    decision=dict(state='FROZEN',condition='v19_final_cleaned',host=host,gpu=gpu,v18_completion_sha256=digest(V18/'completion.json'),accepted_originals=completion['accepted'],excluded_originals=completion['excluded'],selected_unix=time.time(),selection_rule='Prefer genuinely empty adequate SNAP A100 under all shared locks, otherwise GX10 before any production optimizer updates',selection_evidence=evidence,test_split_evaluated=False)
    write(path,decision);return decision

def main():
    ROOT.mkdir(parents=True,exist_ok=True);owner=(ROOT/'selector.lock').open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    while not (V18/'completion.json').exists():progress('WAITING_FOR_FULL_V18_COMPLETION');time.sleep(30)
    completion=read(V18/'completion.json');assert completion['state'] in ['DONE','DONE_WITH_EXCLUSIONS'] and completion['no_automated_fallbacks'] is True and completion['declared']==completion['accounted']==2585
    data=ROOT/'conditions/final/data';cpu=env('')
    if not (data/'prepare_receipt.json').exists():
        run('assemble_final',[PY,str(HERE/'assemble_final_data.py'),'--base-data',str(RUN/'corpus_training_v12/cleaned/data'),'--v18-root',str(V18),'--receipt-root',str(V18/'final/proof_receipts'),'--initial',str(RUN/'onep7/runs/mixed/hf'),'--frozen-source',str(REPO/EXP/'expt_v12'),'--repo',str(REPO),'--kernel',str(REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py'),'--output',str(data)],cpu,7200)
    receipt=read(data/'prepare_receipt.json');assert receipt['status']=='PASS' and receipt['v18_completion_sha256']==digest(V18/'completion.json') and receipt['preparation_code_sha256']==digest(HERE/'assemble_final_data.py')
    for relative,h in FROZEN.items():assert digest(REPO/'external/veribench_scorer'/relative)==h
    assert read(RUN/'validation_preflight.json')['status']=='PASS' and read(RUN/'scoring_preflight.json')['status']=='PASS'
    write(ROOT/'selection_ready.json',dict(state='READY',prepare_receipt_sha256=digest(data/'prepare_receipt.json'),v18_completion_sha256=digest(V18/'completion.json'),observed_unix=time.time()))
    while not (ROOT/'snap_phase_grant.json').exists():progress('WAITING_FOR_CROSS_HOST_GPU_PHASE_GRANT');time.sleep(15)
    grant=read(ROOT/'snap_phase_grant.json');assert grant['state']=='GRANTED' and grant['owner']=='SNAP_SELECTION'
    runtime=load('v19_original_runtime',REPO/EXP/'expt_v6/run_jobs.py')
    gates=ExitStack()
    try:
        for path in ['/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.lock','/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/lock']:
            stream=gates.enter_context(Path(path).open('rb'));fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        gates.close()
        if (ROOT/'production_host.json').exists() and read(ROOT/'production_host.json')['host']=='SNAP':progress('WAITING_FOR_SELECTED_HOST_ADMISSION');raise SystemExit(75)
        freeze('GX10',completion,evidence={'admission':'Shared admission lock busy; no foreign work touched'});progress('GX10_SELECTED');return
    sys.path.insert(0,str(REPO/EXP/'expt_v1/scripts'));import gpu_lease_e08
    leases8=gpu_lease_e08.live_leases();leases13=read(Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.json'))['leases'];devices,busy=runtime.device_inventory();chosen=None;device_lock=None
    existing_decision=read(ROOT/'production_host.json') if (ROOT/'production_host.json').exists() else None
    if existing_decision and existing_decision['host']=='GX10':gates.close();progress('GX10_ALREADY_SELECTED');return
    candidates=[existing_decision['gpu']] if existing_decision else ['1','2','0']
    for gpu in candidates:
        if any(gpu in set(map(str,r['gpus'])) for r in leases8.values()):continue
        if any(r.get('status')!='RELEASED' and r.get('host','').split('.')[0]=='skampere1' and str(r.get('index'))==gpu for r in leases13):continue
        if gpu not in devices or devices[gpu]['uuid'] in busy or devices[gpu]['used_mib']>=64 or devices[gpu]['total_mib']<79000:continue
        stream=(RUN/f'device_{gpu}.lock').open('a')
        try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:stream.close();continue
        chosen=gpu;device_lock=stream;break
    if chosen is None and existing_decision:
        gates.close();progress('WAITING_FOR_SELECTED_SNAP_GPU',gpu=existing_decision['gpu']);raise SystemExit(75)
    if chosen is None:
        gates.close();freeze('GX10',completion,evidence={'devices':devices,'busy_uuids':sorted(busy),'admission':'No eligible empty unleased 80GB GPU1/2/0'});progress('GX10_SELECTED');return
    decision=freeze('SNAP',completion,chosen,dict(devices[chosen],foreign_work_preserved=True));write(ROOT/'allocation.json',dict(decision,pid=os.getpid()))
    gpuenv=env(chosen);write(ROOT/'production_freeze.json',dict(state='FROZEN',host_decision_sha256=digest(ROOT/'production_host.json'),prepare_receipt_sha256=digest(data/'prepare_receipt.json'),training_wrapper_sha256=digest(HERE/'train_snap.py'),source_sha256=receipt['source_sha256'],execution_source_sha256={name:digest(HERE/name) for name in ['common.py','select_and_run.py','train_snap.py','summarize_snap.py','assemble_final_data.py']},runtime='Original SNAP PyTorch2.7.1 runtime; observed identity in first_update',observed_unix=time.time()))
    try:
        # Keep atomic shared admission across discarded smoke and production reload.
        run('full_model_smoke',[PY,str(HERE/'train_snap.py'),'--smoke'],gpuenv,1800)
        assert read(ROOT/'conditions/final/smoke/result.json')['status']=='COMPLETE'
        stop=threading.Event()
        def release_when_context():
            while not stop.wait(1):
                path=ROOT/'execution'/LABEL/'training.json'
                if path.exists():
                    d,b=runtime.device_inventory()
                    if read(path).get('status')=='RUNNING' and d[chosen]['uuid'] in b:gates.close();return
        thread=threading.Thread(target=release_when_context,daemon=True);thread.start()
        run('training',[PY,str(HERE/'train_snap.py')],gpuenv,24*3600);stop.set();thread.join(5);gates.close()
        preflight=read(RUN/'validation_preflight.json');ids=REPO/EXP/'expt_v1/results/split/vbv1_validation_task_ids.txt';raw=ROOT/'validation'/LABEL/'raw.jsonl'
        gpuenv.update(PYTHONPATH=str(REPO/'src')+':'+GEN_SITE,VERIBENCH_ROOT=str(REPO/'external/veribench'),VLLM_WORKER_MULTIPROC_METHOD='spawn',FLASHINFER_WORKSPACE_BASE=str(ROOT/'flashinfer'/LABEL))
        command=['/usr/bin/python3','-m','rl4cv.veribench.generate','--pack',str(RUN/'validation_pack'),'--task-ids',str(ids),'--model',str(ROOT/'conditions/final/run/hf'),'--label',LABEL,'--samples','8','--thinking','on','--seed','91','--stop-token','<|im_end|>','--max-tokens','12288','--temperature','0.6','--top-p','0.95','--top-k','20','--batch','128','--tensor-parallel-size','1','--gpu-memory-utilization','0.85','--out',str(raw)]
        run('generation',command,gpuenv,12*3600)
        rows=[json.loads(line) for line in raw.read_text().splitlines()];expected={(tid,k) for tid in ids.read_text().splitlines() for k in range(8)}
        assert len(rows)==len({(r['task_id'],r['sample_idx']) for r in rows})==1080 and {(r['task_id'],r['sample_idx']) for r in rows}==expected
        for row in rows:assert all(row[k]==v for k,v in preflight['prompts'][row['task_id']].items())
        write(raw.parent/'generation_verified.json',dict(status='PASS',cells=1080,raw_sha256=digest(raw),test_split_evaluated=False))
    finally:gates.close();device_lock.close();write(ROOT/'released.json',dict(gpu=chosen,released_unix=time.time()))
    run('materialize',[PY,'-m','rl4cv.veribench.jobs','--gen',str(raw),'--out-root',str(ROOT/'validation'/LABEL/'jobs'),'--name',LABEL],cpu,600)
    def score(k):
        command=[PY,str(REPO/'external/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py'),'--job-dir',str(ROOT/'validation'/LABEL/'jobs'/f'{LABEL}_s{k}'),'--pack',str(RUN/'validation_pack'),'--name',f'{LABEL}_s{k}','--gold-dir',str(REPO/'external/veribench_scorer/veribench_dataset/lean_src/veribench'),'--lake-dir',str(RUN/'grading'),'--skip-tc','--out-dir',str(ROOT/'validation'/LABEL/'scores'/f'{LABEL}_s{k}')]
        return run(f'score_{k}',command,cpu,12*3600)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(score,range(8)))
    run('summarize',[PY,str(HERE/'summarize_snap.py')],cpu,900)
    result=read(ROOT/'analysis'/f'{LABEL}_summary.json');write(ROOT/'terminal.json',dict(status='COMPLETE',summary=result,ended_unix=time.time(),test_split_evaluated=False));progress('COMPLETE',summary=result)

if __name__=='__main__':
    try:main()
    except SystemExit as exc:
        if exc.code==75:write(ROOT/'waiting_admission.json',dict(state='WAITING',observed_unix=time.time(),no_gpu_held=True))
        raise
    except BaseException as exc:write(ROOT/'terminal.json',dict(status='FAILED',error=repr(exc),ended_unix=time.time()));raise
