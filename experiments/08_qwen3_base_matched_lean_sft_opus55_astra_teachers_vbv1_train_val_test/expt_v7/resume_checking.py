"""Continue the exact saved diagnostic with two CPU workers and the original deadline."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent/'expt_v6')]
import run_jobs as jobs
import check_diagnostic as checker

def main():
    root=checker.ROOT
    prior=json.loads((jobs.RUN/'execution/diagnostic_seen_fresh_v7/checking.json').read_text())
    identity=json.loads((root/'model_identity.json').read_text())
    original_hash=identity['source_hashes']['check_diagnostic.py']
    assert hashlib.sha256((HERE/'check_diagnostic.py').read_bytes()).hexdigest()==original_hash
    assert prior['status']=='FAILED' and prior['exit_code']==-15
    records=list((root/'checks').glob('*/result.json'))
    jobs.write(root/'cpu_admission_continuation.json',dict(
        observed_unix=time.time(),preserved_results=len(records),
        verifier_source_sha256=original_hash,
        raw_sha256=hashlib.sha256((root/'raw.jsonl').read_bytes()).hexdigest(),
        diagnostic_workers=2,combined_own_compiler_maximum=10,
        original_deadline_unix=prior['started_unix']+7200,
        original_stage=prior,policy='resource admission only; no changed scoring or regeneration'))
    if '--worker' in sys.argv:
        checker.await_capacity=lambda:None
        sys.argv=[sys.argv[0]]
        checker.main()
        return
    old=json.loads((root/'status.json').read_text())
    jobs.write(root/'original_coordinator_terminal.json',old)
    jobs.write(root/'status.json',dict(phase='CHECKING',run_id='diagnostic_seen_fresh_v7',
        updated_unix=time.time(),pid=os.getpid(),preserved_results=len(records),
        continuation='cpu_admission_continuation.json'))
    remaining=prior['started_unix']+7200-time.time()
    assert remaining>0
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',TINY_RUN_ROOT=str(jobs.RUN),
             PATH=str(jobs.RUN/'bin')+':'+os.environ['PATH'])
    try:
        jobs.run_stage('diagnostic_seen_fresh_v7','checking_cpu_admission',
            [jobs.PYTHON,str(HERE/'resume_checking.py'),'--worker'],env,remaining)
        summary=json.loads((root/'summary.json').read_text())
        jobs.write(root/'status.json',dict(phase=summary['status'],run_id='diagnostic_seen_fresh_v7',
            updated_unix=time.time(),pid=os.getpid(),generated=100,summary=str(root/'summary.json'),
            continuation='cpu_admission_continuation.json'))
    except BaseException as exc:
        jobs.write(root/'status.json',dict(phase='FAILED',run_id='diagnostic_seen_fresh_v7',
            updated_unix=time.time(),error=repr(exc)))
        raise

if __name__=='__main__':main()
