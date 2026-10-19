"""Run the authorized fixed 100-function diagnostic persistently, preserving every stage receipt."""
from __future__ import annotations
from contextlib import ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
RUN=Path(os.environ.get('TINY_RUN_ROOT','/lfs/skampere1/0/eth127/rl4cv_tiny_training'))
ROOT=RUN/'diagnostic_seen_fresh_v7'
os.environ['TINY_RUN_ROOT']=str(RUN)
sys.path.insert(0,str(HERE.parent/'expt_v6'))
import run_jobs as jobs

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    status=ROOT/'status.json'
    label='diagnostic_seen_fresh_v7'
    def record(phase,**kwargs):
        jobs.write(status,dict(phase=phase,run_id=label,updated_unix=time.time(),pid=os.getpid(),**kwargs))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',TINY_RUN_ROOT=str(RUN),
        PYTHONPATH=str(jobs.REPO/'src'),TINY_REPO_ROOT=str(jobs.REPO),
        TINY_ROOT=str(RUN/'curriculum'),HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false',
        OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',
        PATH=str(RUN/'bin')+':'+os.environ['PATH'])
    for key in list(env):
        if any(word in key for word in ('API_KEY','AUTH_TOKEN','ACCESS_TOKEN','BEARER_TOKEN')):env.pop(key)
    record('ADMISSION')
    try:
        if not (ROOT/'admission.json').exists():
            jobs.run_stage(label,'admission',[jobs.PYTHON,str(HERE/'build_diagnostic.py')],env,600)
        admission=json.loads((ROOT/'admission.json').read_text())
        assert admission['status']=='PASS' and admission['tasks']==100
        assert digest(ROOT/'manifest.jsonl')==admission['manifest_sha256']
        assert digest(HERE/'PROTOCOL.md')==admission['protocol_sha256']
        assert digest(HERE/'build_diagnostic.py')==admission['source_code_sha256']
        record('CHECKER_CONTROLS')
        jobs.run_stage(label,'controls',[jobs.PYTHON,str(HERE/'check_diagnostic.py'),'--controls'],env,900)
        model=RUN/'onep7/runs/mixed/hf'
        expected=json.loads((model.parent/'weights_manifest.json').read_text())
        for name,want in expected.items():assert digest(model/name)==want,name
        jobs.write(ROOT/'model_identity.json',dict(model=str(model),weights_manifest=expected,
            exported_training_result=json.loads((model.parent/'result.json').read_text()),
            source_hashes={p.name:digest(p) for p in HERE.glob('*.py')},
            generation_source_sha256=digest(jobs.REPO/'src/rl4cv/veribench/generate.py')))
        record('WAITING_FOR_DEVICE',gpu='1')
        gpu='1'
        with ExitStack() as gates:
            for path in ['/lfs/skampere1/0/brando9/rl4cv_e13v2/leases/registry.lock',
                         '/lfs/skampere1/0/brando9/rl4cv_e08/pipeline/lock']:
                stream=gates.enter_context(open(path,'rb'))
                fcntl.flock(stream,fcntl.LOCK_EX)
            with (RUN/f'device_{gpu}.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                devices,busy=jobs.device_inventory()
                assert devices[gpu]['uuid'] not in busy and devices[gpu]['used_mib']<64
                jobs.write(ROOT/'allocation.json',dict(gpu=gpu,**devices[gpu],observed_unix=time.time(),owner='eth127'))
                gen_env=dict(env,CUDA_VISIBLE_DEVICES=gpu,
                    PYTHONPATH=str(jobs.REPO/'src')+':'+jobs.GEN_SITE,
                    VERIBENCH_ROOT=str(jobs.REPO/'external/veribench'),
                    VLLM_WORKER_MULTIPROC_METHOD='spawn',
                    FLASHINFER_WORKSPACE_BASE=str(ROOT/'flashinfer'))
                command=['/usr/bin/python3','-m','rl4cv.veribench.generate',
                    '--pack',str(ROOT/'pack'),'--task-ids',str(ROOT/'task_ids.txt'),
                    '--model',str(model),'--label',label,'--samples','1','--thinking','on',
                    '--seed','20261019','--stop-token','<|im_end|>',
                    '--max-tokens','4096','--max-model-len','8192','--temperature','0',
                    '--top-p','1','--top-k','-1','--batch','100','--tensor-parallel-size','1',
                    '--gpu-memory-utilization','0.45','--out',str(ROOT/'raw.jsonl')]
                record('GENERATION',gpu=gpu)
                # Gate release observes the actual CUDA context, without model calls.
                import threading
                done=threading.Event()
                def release_when_loaded():
                    while not done.wait(1):
                        _,contexts=jobs.device_inventory()
                        if devices[gpu]['uuid'] in contexts:
                            gates.close()
                            return
                watcher=threading.Thread(target=release_when_loaded,daemon=True)
                watcher.start()
                try:
                    jobs.run_stage(label,'generation',command,gen_env,3600)
                finally:
                    done.set();watcher.join(timeout=10);gates.close()
                    jobs.write(ROOT/'released.json',dict(gpu=gpu,observed_unix=time.time()))
        generations=[json.loads(s) for s in (ROOT/'raw.jsonl').read_text().splitlines()]
        assert len(generations)==100
        want={(d['task_id'],d['sample_idx']) for d in json.loads((ROOT/'cells.json').read_text())}
        assert len({(d['task_id'],d['sample_idx']) for d in generations})==100
        assert want=={(d['task_id'],d['sample_idx']) for d in generations}
        record('CHECKING',generated=100)
        jobs.run_stage(label,'checking',[jobs.PYTHON,str(HERE/'check_diagnostic.py')],env,7200)
        summary=json.loads((ROOT/'summary.json').read_text())
        record(summary['status'],generated=100,summary=str(ROOT/'summary.json'))
    except BaseException as exc:
        record('FAILED',error=repr(exc))
        raise

if __name__=='__main__':
    main()
