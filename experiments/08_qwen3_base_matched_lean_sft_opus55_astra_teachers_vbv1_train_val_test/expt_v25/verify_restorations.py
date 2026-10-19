"""Verify composed original proofs; failed rows remain exact V20 examples."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import sys
import threading
import time

from audit_counterparts import RUN, ROOT, EXP, read, sha, module
sys.path.insert(0,str(EXP/'expt_v24/future_logging'))
from durable_capture import DurableCapture, atomic, clone


def main(workers):
    os.environ['PATH']=str(RUN/'bin')+':/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin:'+os.environ['PATH']
    os.environ['CUDA_VISIBLE_DEVICES']=''
    kernel=module('restore_verify_frozen_kernel',RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py')
    assert sha(Path(kernel.__file__).read_bytes())=='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'
    cases=read(ROOT/'restoration_candidates/pending.jsonl')
    cached={row['index']:row for row in json.loads((ROOT/'counterpart_audit/cached_receipts.json').read_text())['rows']}
    out=ROOT/'restoration_verification';out.mkdir(exist_ok=True)
    freeze=dict(declared=len(cases),candidate_manifest_sha256=sha((ROOT/'restoration_candidates/pending.jsonl').read_bytes()),
        kernel_sha256=sha(Path(kernel.__file__).read_bytes()),driver_sha256=sha(Path(__file__).read_bytes()),workers=workers,
        timeout_seconds=900,created_unix=time.time(),selection='All composed candidates; large sources first; no outcome-based retries')
    if (out/'freeze.json').exists():assert json.loads((out/'freeze.json').read_text())['candidate_manifest_sha256']==freeze['candidate_manifest_sha256']
    else:atomic(out/'freeze.json',freeze)
    active={};done=[];lock=threading.Lock()
    def check(case):
        index=case['index'];source=Path(case['source_path']);folder=out/f'{index:04d}';folder.mkdir(exist_ok=True)
        receipt=folder/'result.json'
        if receipt.exists():
            old=json.loads(receipt.read_text());assert old['source_sha256']==sha(source.read_bytes())==case['candidate_sha256'];return old
        with lock:active[index]=time.time()
        result=dict(index=index,uid=case['uid'],pool=case['pool'],source_path=str(source),source_sha256=sha(source.read_bytes()),passed=False)
        try:
            assert result['source_sha256']==case['candidate_sha256']
            code=kernel.strip_comments(source.read_text(),keep_literals=True)
            for previous in cached.get(index,{}).get('matching_receipts',[]):
                if not previous.get('valid_frozen_kernel_report') or not previous.get('retained_compiled_artifact_verified'):continue
                prior_source=Path(previous['checked_source_path']);report_path=Path(previous['kernel_report_path']);artifact=Path(previous['compiled_module_path'])
                if sha(prior_source.read_bytes())!=previous['checked_source_sha256'] or sha(report_path.read_bytes())!=previous['kernel_report_sha256'] or sha(artifact.read_bytes())!=previous['compiled_module_sha256']:continue
                report=json.loads(report_path.read_text());report=report.get('kernel_report',report)
                if not kernel.valid_report(report):continue
                if report['source_sha256']!=previous['checked_source_sha256']:continue
                if re.search(r'\b(?:__LINE__|__FILE__|elab|elab_rules|macro|macro_rules|syntax)\b|^\s*#(?:eval|check)',code,re.M):continue
                if code.split()!=kernel.strip_comments(prior_source.read_text(),keep_literals=True).split():continue
                result.update(passed=True,basis='cached_frozen_kernel_comment_equivalence',cached_receipt=previous,
                    comment_binding=dict(checked_source_sha256=previous['checked_source_sha256'],candidate_source_sha256=result['source_sha256'],noncomment_tokens_identical=True,source_position_metaprogramming_absent=True))
                break
            if not result['passed']:
                capture=DurableCapture(folder/'compiler_diagnostics','/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin/lean',
                    dict(scope='V25 training counterpart verification, not validation',evaluated_source_sha256=result['source_sha256'],uid=case['uid']))
                probe=clone(kernel.run_probe,subprocess=capture)
                checking=clone(kernel.check_file,run_probe=probe)
                report=checking(str(source),str(RUN/'grading'),timeout=900,keep_dir=str(folder/'kernel')).to_dict()
                atomic(folder/'kernel_report.json',report)
                result.update(passed=kernel.valid_report(report) and report['source_sha256']==result['source_sha256'] and report['n_theorems']==report['n_honest'] and report['n_theorems']>0,
                    basis='new_frozen_kernel_full_source',kernel_report_path=str(folder/'kernel_report.json'),kernel_report_sha256=sha((folder/'kernel_report.json').read_bytes()),
                    compile_rc=report['compile_rc'],inspect_rc=report['inspect_rc'],n_honest=report['n_honest'],n_theorems=report['n_theorems'])
        except Exception as error:result['error']=repr(error)
        result.update(ended_unix=time.time(),failed_candidate_keeps_baseline=not result['passed'])
        atomic(receipt,result)
        with lock:active.pop(index,None)
        return result
    started=time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(check,c) for c in sorted(cases,key=lambda c:-Path(c['source_path']).stat().st_size)]
        for future in as_completed(futures):
            done.append(future.result())
            with lock:running=dict(active)
            atomic(out/'progress.json',dict(state='VERIFYING',declared=len(cases),completed=len(done),passed=sum(r['passed'] for r in done),active=len(running),workers=workers,oldest_active_seconds=time.time()-min(running.values()) if running else None,observed_unix=time.time()))
    (out/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in sorted(done,key=lambda r:r['index'])))
    atomic(out/'completion.json',dict(state='DONE',declared=len(cases),completed=len(done),passed=sum(r['passed'] for r in done),
        passed_by_pool=dict(Counter(r['pool'] for r in done if r['passed'])),basis_counts=dict(Counter(r.get('basis','error') for r in done)),
        failure_reasons=dict(Counter(r.get('error',str(r.get('compile_rc'))) for r in done if not r['passed'])),
        all_failed_candidates_keep_exact_baseline=True,elapsed_seconds=time.time()-started,rows_sha256=sha((out/'rows.jsonl').read_bytes()),observed_unix=time.time()))
    print((out/'completion.json').read_text(),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=96);main(parser.parse_args().workers)
