"""Retry unresolved supplied proofs with explicit legacy-notation support or a recorded larger resource bound."""
from __future__ import annotations
import collections
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import time
import bulk_verify as bulk

ROOT=bulk.ROOT/'unresolved_recovery'
LEGACY='''
macro "∑ " i:ident " in " s:term ", " f:term : term =>
  `(Finset.sum $s (fun $i => $f))
macro "∏ " i:ident " in " s:term ", " f:term : term =>
  `(Finset.prod $s (fun $i => $f))
'''

def assemble(row,index,legacy):
    statement=re.sub(r'\s*:=\s*by\s+sorry\s*$','',row['formal_statement'])
    assert statement!=row['formal_statement']
    proof=row['all_proof_alternatives'][index]
    return 'import Mathlib\nopen BigOperators Nat Real Rat\n'+(LEGACY if legacy else '')+'\n'+statement+' := by\n'+''.join('  '+line+'\n' for line in proof.splitlines())

def check(kernel,tid,index,source,timeout):
    folder=ROOT/'checks'/tid/f'proof_{index:02d}';receipt=folder/'result.json'
    if receipt.exists():return json.loads(receipt.read_text())
    folder.mkdir(parents=True,exist_ok=True);path=folder/'Solution.lean';path.write_text(source)
    result=dict(task_id=tid,proof_index=index,source_sha256=bulk.sha(source.encode()),timeout_per_operation=timeout,passed=False)
    started=time.time()
    try:
        r=kernel.check_file(str(path),str(bulk.RUN/'grading'),timeout=timeout,allow_native_decide=False,keep_dir=str(folder/'kernel'))
        raw=asdict(r);bulk.write(folder/'kernel_report.json',raw)
        result.update(passed=bool(kernel.valid_report(raw) and r.n_theorems>=1 and r.n_honest==r.n_theorems and r.source_sha256==result['source_sha256']),compile_rc=r.compile_rc,inspect_rc=r.inspect_rc,diagnostic=json.dumps(raw['probe_errors'],ensure_ascii=False)[:1800])
    except Exception as exc:result['error']=repr(exc)
    result['elapsed_seconds']=time.time()-started;bulk.write(receipt,result);return result

def recover(kernel,item):
    tid=item['task_id'];row=json.loads((bulk.PRIOR/'review/cases'/tid/'input.json').read_text())
    types=item['failure_types'];legacy='syntax_compatibility' in types
    eligible=legacy or 'resource_limit' in types
    if not eligible:
        return dict(task_id=tid,state='EXCLUDED_NEEDS_PROOF_OR_LIBRARY_REPAIR',failure_types=types,passed=False)
    indices=list(dict.fromkeys([row['proof_index'],0]))[:2]
    outcomes=[]
    for index in indices:
        result=check(kernel,tid,index,assemble(row,index,legacy),60 if 'resource_limit' in types else 15)
        outcomes.append(result)
        if result['passed']:
            answer=dict(task_id=tid,state='RECOVERED_REQUIRES_ANNOTATION_REASSEMBLY',passed=True,proof_index=index,legacy_notation=legacy,source_sha256=result['source_sha256'],checks=outcomes)
            bulk.write(ROOT/'decisions'/f'{tid}.json',answer);return answer
    answer=dict(task_id=tid,state='EXCLUDED_UNRESOLVED',passed=False,legacy_notation=legacy,checks=outcomes)
    bulk.write(ROOT/'decisions'/f'{tid}.json',answer);return answer

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    os.environ['PATH']=str(bulk.RUN/'bin')+':'+os.environ['PATH'];os.environ['CUDA_VISIBLE_DEVICES']=''
    kernel=bulk.load_kernel()
    source='import Mathlib\n'+LEGACY+'\ntheorem legacySumV10Control : (∑ k in Finset.range 3, k) = 3 := by decide\n'
    control=check(kernel,'control',0,source,15);assert control['passed'],control
    bulk.write(ROOT/'control.json',control)
    rows=json.loads((bulk.ROOT/'unresolved_audit.json').read_text())['rows'];results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(recover,kernel,row) for row in rows]):
            results.append(future.result())
            summary=dict(declared=len(rows),completed=len(results),workers=4,states=dict(collections.Counter(r['state'] for r in results)),rows=results,observed_unix=time.time())
            bulk.write(ROOT/'progress.json',summary)
            print(json.dumps({k:v for k,v in summary.items() if k!='rows'}),flush=True)
    bulk.write(ROOT/'completion.json',dict(declared=len(rows),completed=len(results),recovered=sum(r['passed'] for r in results),states=dict(collections.Counter(r['state'] for r in results)),observed_unix=time.time()))

if __name__=='__main__':main()
