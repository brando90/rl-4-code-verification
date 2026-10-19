"""Supervise one admitted GPU continuation through full validation and CPU scoring with death and failure receipts."""
from __future__ import annotations
import argparse
import concurrent.futures
from contextlib import ExitStack
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from assemble import HERE,ROOT,REPO,RUN,digest,write

PYTHON='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
GEN_SITE='/lfs/skampere1/0/brando9/rl4cv_e08/venv_gen/lib/python3.12/site-packages'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--condition',default='base');parser.add_argument('--gpu',default='3');args=parser.parse_args()
    condition=args.condition;gpu=args.gpu;label='v25_'+condition;out=ROOT/condition
    os.environ['TINY_RUN_ROOT']=str(ROOT)
    spec=importlib.util.spec_from_file_location('v6_runtime',HERE.parent/'expt_v6/run_jobs.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
    data=out/'data';receipt=json.loads((data/'prepare_receipt.json').read_text());assert receipt['status']=='PASS'
    for n,h in receipt['v25_source_sha256'].items():assert digest(HERE/n)==h,n
    assert json.loads((RUN/'validation_preflight.json').read_text())['status']=='PASS'
    assert json.loads((RUN/'scoring_preflight.json').read_text())['status']=='PASS'
    lock=(RUN/f'device_{gpu}.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    gates=ExitStack()
    for path in [Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.lock'),Path('/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/lock')]:
        stream=gates.enter_context(path.open('rb'));deadline=time.monotonic()+180
        while True:
            try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                if time.monotonic()>deadline:raise RuntimeError('Admission lock busy: '+str(path))
                time.sleep(1)
    sys.path.insert(0,str(HERE.parent/'expt_v1/scripts'));import gpu_lease_e08
    assert not any(gpu in set(map(str,r['gpus'])) for r in gpu_lease_e08.live_leases().values()),'E08 active lease'
    leases=json.loads(Path('/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.json').read_text())['leases']
    assert not any(r.get('status')!='RELEASED' and r.get('host','').split('.')[0]=='skampere1' and str(r.get('index'))==gpu for r in leases),'E13 active lease'
    devices,busy=runtime.device_inventory();assert devices[gpu]['uuid'] not in busy and devices[gpu]['used_mib']<64 and devices[gpu]['total_mib']>=79000
    write(out/'allocation.json',dict(gpu=gpu,**devices[gpu],pid=os.getpid(),allocated_unix=time.time(),state='RUNNING'))
    env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES=gpu,PYTHONPATH=str(REPO/'src'),HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4')
    for key in list(env):
        if any(word in key for word in ('API_KEY','AUTH_TOKEN','ACCESS_TOKEN','BEARER_TOKEN')):env.pop(key)
    try:
        # Separate process; smoke weights are discarded before loading START again.
        runtime.run_stage(label,'smoke',[PYTHON,str(HERE/'entry.py'),'--condition',condition,'--smoke'],env,1200)
        assert json.loads((out/'smoke/result.json').read_text())['status']=='COMPLETE'
        # Preserve atomic allocator admission across the smoke-to-production reload gap.
        # Release shared gates as soon as the production process owns a real context.
        release_stop=threading.Event()
        def release_admission():
            while not release_stop.wait(1):
                stage=ROOT/'execution'/label/'training.json'
                if not stage.exists():continue
                info=json.loads(stage.read_text());devices_now,busy_now=runtime.device_inventory()
                if info.get('status')=='RUNNING' and devices_now[gpu]['uuid'] in busy_now:
                    gates.close();return
        release_thread=threading.Thread(target=release_admission,daemon=True);release_thread.start()
        runtime.run_stage(label,'training',[PYTHON,str(HERE/'entry.py'),'--condition',condition],env,12*3600)
        release_stop.set();release_thread.join(timeout=5);gates.close()
        preflight=json.loads((RUN/'validation_preflight.json').read_text());ids=HERE.parent/'expt_v1/results/split/vbv1_validation_task_ids.txt'
        env.update(PYTHONPATH=str(REPO/'src')+':'+str(ROOT/'generation_env/scipy_overlay')+':'+GEN_SITE,VERIBENCH_ROOT=str(REPO/'external/veribench'),VLLM_WORKER_MULTIPROC_METHOD='spawn',FLASHINFER_WORKSPACE_BASE=str(ROOT/'flashinfer'/label))
        cache_paths=dict(XDG_CACHE_HOME=ROOT/'cache',HF_HOME=ROOT/'cache/huggingface',TORCH_HOME=ROOT/'cache/torch',VLLM_CACHE_ROOT=ROOT/'cache/vllm',VLLM_CONFIG_ROOT=ROOT/'config/vllm',TORCHINDUCTOR_CACHE_DIR=ROOT/'cache/torchinductor',TRITON_CACHE_DIR=ROOT/'cache/triton',CUDA_CACHE_PATH=ROOT/'cache/cuda',PYTORCH_KERNEL_CACHE_PATH=ROOT/'cache/torchkernels',NUMBA_CACHE_DIR=ROOT/'cache/numba')
        for name,path in cache_paths.items():path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
        env.update(VLLM_NO_USAGE_STATS='1',DO_NOT_TRACK='1',HF_HUB_DISABLE_TELEMETRY='1')
        write(ROOT/'generation_env/cache_environment.json',dict(paths={name:str(path) for name,path in cache_paths.items()},home_unchanged=True,telemetry_disabled=True))
        raw=ROOT/'validation'/label/'raw.jsonl'
        cmd=['/usr/bin/python3','-m','rl4cv.veribench.generate','--pack',str(RUN/'validation_pack'),'--task-ids',str(ids),'--model',str(out/'run/hf'),'--label',label,'--samples','8','--thinking','on','--seed','91','--stop-token','<|im_end|>','--max-tokens','12288','--temperature','0.6','--top-p','0.95','--top-k','20','--batch','128','--tensor-parallel-size','1','--gpu-memory-utilization','0.85','--out',str(raw)]
        runtime.run_stage(label,'generation',cmd,env,8*3600)
        rows=[json.loads(s) for s in raw.read_text().splitlines()];expected={(tid,k) for tid in ids.read_text().splitlines() for k in range(8)}
        assert len(rows)==len({(r['task_id'],r['sample_idx']) for r in rows})==len(expected)==1080
        assert {(r['task_id'],r['sample_idx']) for r in rows}==expected
        for row in rows:assert all(row[k]==v for k,v in preflight['prompts'][row['task_id']].items())
        write(raw.parent/'generation_verified.json',dict(status='PASS',cells=1080,raw_sha256=digest(raw),test_split_opened=False))
    except BaseException as exc:
        write(out/'terminal.json',dict(status='FAILED',error=repr(exc),ended_unix=time.time()));raise
    finally:
        gates.close();lock.close();write(out/'released.json',dict(gpu=gpu,released_unix=time.time()))
    cpu=dict(env,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(REPO/'src'),PATH=str(RUN/'bin')+':'+env['PATH'])
    try:
        runtime.run_stage(label,'materialize',[PYTHON,'-m','rl4cv.veribench.jobs','--gen',str(raw),'--out-root',str(ROOT/'validation'/label/'jobs'),'--name',label],cpu,300)
        score_root=ROOT/'scoring_parallel_v1';score_root.mkdir(exist_ok=True)
        assert not (score_root/'partition.json').exists(),'Immutable scoring partition already exists'
        scorer=REPO/'external/veribench_scorer/experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py'
        spec=importlib.util.spec_from_file_location('v25_partition_frozen_cli',scorer);cli=importlib.util.module_from_spec(spec);sys.modules[spec.name]=cli;spec.loader.exec_module(cli)
        gold=cli.S.discover_gold_files(str(REPO/'external/veribench_scorer/veribench_dataset/lean_src/veribench'));idx=cli.build_gold_index(gold);cells=[]
        import shutil
        for sample in range(8):
            job=ROOT/'validation'/label/'jobs'/f'{label}_s{sample}';tasks=cli.S.discover_agent_tasks(str(job));assert len(tasks)==135
            for td,source in sorted(tasks.items()):
                task=cli.trial_task_id(job/td);gk=cli.task_id_to_gold_key(task,idx);assert gk
                key=f's{sample}_{len(cells):04d}';view=score_root/'jobs'/key;view.mkdir(parents=True)
                shutil.copytree(job/td,view/td);relative=Path(source).relative_to(job/td);assert digest(view/td/relative)==digest(source)
                cells.append(dict(key=key,sample=sample,task_id=task,td=td,gold_key=gk,job=str(view),source_sha256=digest(source),source_size=Path(source).stat().st_size))
        assert len(cells)==1080
        write(score_root/'partition.json',dict(legacy=[],cells=cells,sentinels=[],owner_pid=os.getpid(),owner_fenced=False,all_generated_cells=1080,observed_unix=time.time(),selection='Every generated cell; largest-source-first scheduling, no scoring outcomes used'))
        logged=HERE.parent/'expt_v24/future_logging/parallel_scoring_logged.py'
        assert digest(logged)==receipt['future_logged_entry_sha256']
        write(score_root/'prospective.json',dict(driver_sha256=digest(logged),logged_diagnostics_mandatory=True,compile_timeout_seconds=600,kernel_timeout_seconds=900,max_total_workers=32,training_restarted=False,observed_unix=time.time()))
        runtime.run_stage(label,'scoring_parallel',[PYTHON,str(logged),'--version','25'],cpu,8*3600)
        final=json.loads((ROOT/'analysis'/f'{label}_summary.json').read_text());assert final['status']=='COMPLETE' and final['scored_cells']==1080
        write(out/'terminal.json',dict(status='COMPLETE',ended_unix=time.time(),test_split_opened=False))
    except BaseException as exc:
        write(out/'terminal.json',dict(status='SCORING_FAILED',error=repr(exc),ended_unix=time.time()));raise

if __name__=='__main__':main()
