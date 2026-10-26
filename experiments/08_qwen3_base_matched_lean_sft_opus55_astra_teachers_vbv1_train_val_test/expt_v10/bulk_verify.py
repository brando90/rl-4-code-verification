"""Check every previously unchecked Workbook proof with the frozen kernel inspector and retain all outcomes."""
from __future__ import annotations
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from dataclasses import asdict
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
ROOT=RUN/'lean_corpus_v10'
PRIOR=RUN/'lean_corpus_v9'
FROZEN=RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py'

def sha(data):return hashlib.sha256(data).hexdigest()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    temporary.replace(path)

def diagnostic_types(report):
    text=json.dumps(report.get('probe_errors',[]))+'\n'+report.get('stderr_tail','')
    lower=text.lower()
    if 'unexpected token' in lower or 'parser error' in lower:return 'syntax_compatibility'
    if any(s in lower for s in ['timeout','timed out','maximum recursion','deep recursion','maximum number of heartbeats','maxrecdepth','maxheartbeats']):return 'resource_limit'
    if 'unknown identifier' in lower or 'unknown constant' in lower:return 'library_identifier'
    if 'unsolved goals' in lower:return 'unsolved_goals'
    return 'other'

def prepare():
    ROOT.mkdir(parents=True,exist_ok=True)
    assert not (ROOT/'manifest.jsonl').exists(),'An existing frozen run must be resumed, not overwritten.'
    prior=list(csv.DictReader((PRIOR/'final/row_results.csv').open()))
    selections={r['task_id']:r for r in map(json.loads,(PRIOR/'selection.jsonl').read_text().splitlines())}
    rows=[]
    for row in prior:
        if row['kind']!='workbook' or row['format_check']!='PASS' or row['kernel_verified']=='True':continue
        tid=row['task_id'];selected=selections[tid];source=selected['lean'].encode()
        assert sha(source)==row['source_sha256'],tid
        path=ROOT/'sources'/tid/'Solution.lean';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(source)
        rows.append(dict(task_id=tid,source_sha256=sha(source),proof_index=int(row['proof_index'])))
    assert len(rows)==10995,len(rows)
    text=''.join(json.dumps(r)+'\n' for r in rows)
    (ROOT/'manifest.jsonl').write_text(text)
    unresolved=[]
    for row in prior:
        if row['review_decision']!='unresolved':continue
        folder=PRIOR/'review/cases'/row['task_id']
        checks=[json.loads(p.read_text()) for p in (folder/'checks').glob('*/result.json')]
        types=sorted({diagnostic_types(c['kernel_report']) for c in checks})
        unresolved.append(dict(task_id=row['task_id'],failure_types=types,checks=len(checks),rationale=row['rationale'],status='EXCLUDED_PENDING_RECOVERY'))
    write(ROOT/'unresolved_audit.json',dict(total=len(unresolved),overlapping_categories=dict(collections.Counter(t for r in unresolved for t in r['failure_types'])),rows=unresolved))
    write(ROOT/'freeze.json',dict(declared=len(rows),manifest_sha256=sha(text.encode()),frozen_inspector_sha256=sha(FROZEN.read_bytes()),prior_row_table_sha256=sha((PRIOR/'final/row_results.csv').read_bytes()),workers=48,timeout_per_compiler_operation_seconds=15,attempts_per_cell=1,host=socket.gethostname(),observed_unix=time.time()))
    print('Prepared',len(rows),'unchanged sources; audited',len(unresolved),'unresolved cases.',flush=True)

def load_kernel():
    spec=importlib.util.spec_from_file_location('bulk_frozen_kernel',FROZEN)
    kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
    return kernel

def check(kernel,row,timeout=15):
    tid=row['task_id'];folder=ROOT/'checks'/tid;receipt=folder/'result.json'
    if receipt.exists():
        old=json.loads(receipt.read_text());assert old['source_sha256']==row['source_sha256'];return old
    source=ROOT/'sources'/tid/'Solution.lean'
    assert sha(source.read_bytes())==row['source_sha256']
    started=time.time();write(folder/'started.json',dict(task_id=tid,pid=os.getpid(),host=socket.gethostname(),started_unix=started))
    result=dict(row,host=socket.gethostname(),passed=False,started_unix=started)
    try:
        report=kernel.check_file(str(source),str(RUN/'grading'),timeout=timeout,allow_native_decide=False,keep_dir=str(folder/'kernel'))
        raw=asdict(report);write(folder/'kernel_report.json',raw)
        result.update(compile_rc=report.compile_rc,inspect_rc=report.inspect_rc,n_theorems=report.n_theorems,n_honest=report.n_honest,
            passed=bool(kernel.valid_report(raw) and report.n_theorems>=1 and report.n_honest==report.n_theorems and report.source_sha256==row['source_sha256']))
        result['outcome']='PASS' if result['passed'] else diagnostic_types(raw)
        result['diagnostic']=json.dumps(raw['probe_errors'],ensure_ascii=False)[:1500]
    except Exception as exc:result.update(outcome='EXECUTOR_ERROR',diagnostic=repr(exc))
    result.update(elapsed_seconds=time.time()-started,finished_unix=time.time())
    write(receipt,result);return result

def controls(kernel):
    results=[]
    for name,source,wanted in [('positive','import Mathlib\ntheorem bulkWorkbookV10Preflight : True := by exact True.intro\n',True),('sorry','import Mathlib\ntheorem bulkWorkbookV10Preflight : False := by sorry\n',False),('axiom','import Mathlib\naxiom bulkWorkbookV10Fake : False\ntheorem bulkWorkbookV10Preflight : False := by exact bulkWorkbookV10Fake\n',False)]:
        path=ROOT/'sources'/('control_v2_'+name)/'Solution.lean';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
        result=check(kernel,dict(task_id='control_v2_'+name,source_sha256=sha(source.encode()),proof_index=-1))
        assert result['passed']==wanted,(name,result)
        results.append(result)
    write(ROOT/'controls.json',dict(passed=True,rows=results));print('Positive/sorry/declared-axiom controls passed.',flush=True)

def summarize(rows,results,started,workers,state):
    counts=dict(collections.Counter(r['outcome'] for r in results))
    write(ROOT/'progress.json',dict(state=state,declared=len(rows),completed=len(results),remaining=len(rows)-len(results),outcomes=counts,workers=workers,pid=os.getpid(),host=socket.gethostname(),elapsed_seconds=time.time()-started,observed_unix=time.time()))
    keys=['task_id','proof_index','source_sha256','host','passed','outcome','compile_rc','inspect_rc','n_theorems','n_honest','elapsed_seconds','diagnostic']
    with (ROOT/'row_results.csv.tmp').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(sorted(results,key=lambda r:r['task_id']))
    (ROOT/'row_results.csv.tmp').replace(ROOT/'row_results.csv')
    print(json.dumps(dict(state=state,completed=len(results),declared=len(rows),outcomes=counts)),flush=True)

def run(workers):
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'owner.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        os.environ['PATH']=str(RUN/'bin')+':'+os.environ['PATH'];os.environ['CUDA_VISIBLE_DEVICES']=''
        kernel=load_kernel();freeze=json.loads((ROOT/'freeze.json').read_text())
        assert sha(FROZEN.read_bytes())==freeze['frozen_inspector_sha256']
        text=(ROOT/'manifest.jsonl').read_bytes();assert sha(text)==freeze['manifest_sha256']
        rows=[json.loads(x) for x in text.splitlines()];controls(kernel)
        results=[];started=time.time();last=started;summarize(rows,results,started,workers,'RUNNING')
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(check,kernel,row) for row in rows]
            for future in as_completed(futures):
                results.append(future.result())
                if time.time()-last>=15 or len(results)==len(rows):
                    summarize(rows,results,started,workers,'RUNNING');last=time.time()
        summarize(rows,results,started,workers,'DONE')
        write(ROOT/'completion.json',dict(state='DONE',declared=len(rows),completed=len(results),passed=sum(r['passed'] for r in results),observed_unix=time.time()))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);parser.add_argument('--workers',type=int,default=48);args=parser.parse_args()
    prepare() if args.action=='prepare' else run(args.workers)
