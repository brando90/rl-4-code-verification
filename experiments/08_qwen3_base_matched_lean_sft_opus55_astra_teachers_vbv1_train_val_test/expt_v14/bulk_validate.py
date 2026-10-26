"""Freeze and kernel-check all 729 unchanged public-source candidates with complete formal-only accounting."""
from __future__ import annotations
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor,as_completed
import csv
from dataclasses import asdict
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
ROOT=RUN/'public_gap_sources_v14'
BATCH=ROOT/'bulk_validation'
MATHLIB=Path('/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src/.lake/packages/mathlib')
FROZEN=RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py'
INSPECTOR_SHA='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'
PIN='79e94a093aff4a60fb1b1f92d9681e407124c2ca'
INPUTS={'mathlib_candidates.jsonl':('51c8991b689a5b27ee071dc787d33c086687f49fde6a748d0374f96c5b878e61',217),
        'deepseek_candidates.jsonl':('9538fcd310754eb54122d09a6c689403823fa78f79dce7cac7b2611b7c7f3d4d',512)}
RAW_SHA='a2cdac64d011eee00836ce1a2c5511dfa5567346afabe897c3309ac17771b92b'
WORKERS=8
TIMEOUT=60


def sha(data):return hashlib.sha256(data if isinstance(data,bytes) else data.encode()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n');tmp.replace(path)


def git(*args):
    return subprocess.check_output(['git','--no-optional-locks','-c','safe.directory='+str(MATHLIB),'-C',str(MATHLIB),*args])


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module;spec.loader.exec_module(module);return module


def extract_source(row):
    messages=row['messages'];assert [m['role'] for m in messages]==['system','user','assistant']
    answer=messages[2]['content'];path=f'/home/lean_project/Veribench/{row["task_id"]}.lean'
    opening=f'FILE: {path}\n```lean\n';assert answer.startswith(opening) and answer.endswith('```\n')
    source=answer[len(opening):-4];assert sha(source)==row['source_sha256'];assert sha(answer)==row['response_sha256']
    assert source.endswith('\n')
    return source


def prepare():
    BATCH.mkdir(parents=True,exist_ok=True)
    assert not (BATCH/'freeze.json').exists(),'Frozen batch already exists; resume it instead'
    assert sha(FROZEN.read_bytes())==INSPECTOR_SHA
    prep=load_module('v14_pinned_candidate_preparer',ROOT/'prepare_candidates.py')
    assert git('rev-parse','HEAD').decode().strip()==PIN
    raw_path=ROOT/'deepseek_v1.jsonl';assert sha(raw_path.read_bytes())==RAW_SHA
    deepseek=[json.loads(line) for line in raw_path.read_text().splitlines()];assert len(deepseek)==27503
    records=[];seen=set();input_hashes={}
    for filename,(digest,wanted) in INPUTS.items():
        data=(ROOT/filename).read_bytes();assert sha(data)==digest;input_hashes[filename]=digest
        rows=[json.loads(line) for line in data.splitlines()];assert len(rows)==wanted
        for row in rows:
            tid=row['task_id'];assert re.fullmatch(r'[a-z0-9_]+',tid) and tid not in seen;seen.add(tid)
            source=extract_source(row)
            if row['source']=='mathlib4':
                assert row['source_revision']==PIN
                original=git('show',PIN+':'+row['source_path'])
                assert original==(MATHLIB/row['source_path']).read_bytes()==source.encode(),tid
                code=prep.mask_comments_strings(source);target=list(prep.DECL.finditer(code))[-1]
                split=prep.assignment(code,target.end());prefix=source[:split+2]
                assert source[target.start():split].strip()==row['formal_statement']
                assert target.group(1)==row['theorem_name']
            else:
                assert row['source']=='deepseek_prover_v1' and row['source_revision']==prep.DEEPSEEK_REV
                upstream=deepseek[row['source_row']];assert upstream['split']==row['source_split']=='train'
                original=upstream['header']+'\n'+upstream['formal_statement']+'\n'+upstream['formal_proof']+'\n'
                assert original==source and upstream['name']==row['source_name'],tid
                assert upstream['formal_statement']==row['formal_statement']
                prefix=upstream['header']+'\n'+upstream['formal_statement']
            expected=prep.envelope(tid,source,row['formal_statement'],prefix)
            assert expected['messages']==row['messages'],tid
            path=BATCH/'sources'/tid/'Solution.lean';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(source.encode())
            records.append(dict(task_id=tid,source_family=row['source'],source_revision=row['source_revision'],
                source_path=row.get('source_path'),source_row=row.get('source_row'),license_status=row['license_status'],
                source_sha256=row['source_sha256'],input_record_sha256=sha(json.dumps(row,sort_keys=True,ensure_ascii=False)),
                exact_source_context_verified=True,semantic_review='NOT_REVIEWED',
                semantic_risk_flags=['possible_untyped_fractional_exponent'] if re.search(r'\^\s*\(\s*\d+\s*/\s*\d+\s*\)',prep.mask_comments_strings(source)) else [],
                training_admitted=False))
    assert len(records)==729
    text=''.join(json.dumps(row,sort_keys=True)+'\n' for row in records)
    (BATCH/'manifest.jsonl').write_text(text)
    version=subprocess.check_output([str(RUN/'bin/lake'),'env','lean','--version'],text=True).strip()
    write(BATCH/'freeze.json',dict(declared=729,source_counts=dict(collections.Counter(r['source_family'] for r in records)),
        manifest_sha256=sha(text),input_sha256=input_hashes,raw_deepseek_sha256=RAW_SHA,mathlib_revision=PIN,
        frozen_inspector_sha256=INSPECTOR_SHA,driver_sha256=sha(Path(__file__).read_bytes()),
        candidate_preparer_sha256=sha((ROOT/'prepare_candidates.py').read_bytes()),lean_version=version,
        workers=WORKERS,timeout_per_compiler_operation_seconds=TIMEOUT,measured_attempts_per_candidate=1,
        max_resumes=1,host=socket.gethostname(),observed_unix=time.time(),training_admitted=0))
    print('Frozen all 729 unchanged candidates and exact upstream contexts.',flush=True)


def reusable(kernel,result,row):
    assert result['source_sha256']==row['source_sha256']
    source=BATCH/'sources'/row['task_id']/'Solution.lean';assert sha(source.read_bytes())==row['source_sha256']
    if result['passed']:
        raw=json.loads(Path(result['kernel_report_path']).read_text());assert kernel.valid_report(raw)
        assert raw['source_sha256']==row['source_sha256'] and raw['n_theorems']>0 and raw['n_honest']==raw['n_theorems']
        compiled=Path(raw['evidence_dir'])/'original.olean';assert sha(compiled.read_bytes())==raw['compiled_module_sha256']
    return result


def outcome(raw):
    if raw.get('n_sorry_ax',0):return 'SORRY_REJECTED'
    if raw.get('n_declared_axiom',0) or raw.get('n_native_decide',0):return 'AXIOM_REJECTED'
    text=(json.dumps(raw.get('probe_errors',[]))+'\n'+raw.get('stderr_tail','')).lower()
    if any(s in text for s in ('timeout','timed out','maximum number of heartbeats','maximum recursion')):return 'RESOURCE_LIMIT'
    if 'unexpected token' in text or 'expected token' in text:return 'SYNTAX_COMPATIBILITY'
    if 'unknown identifier' in text or 'unknown constant' in text:return 'LIBRARY_IDENTIFIER'
    if 'unsolved goals' in text:return 'UNSOLVED_GOALS'
    if 'type mismatch' in text:return 'TYPE_MISMATCH'
    return 'FORMAL_CHECK_FAILED'


def check(kernel,row):
    tid=row['task_id'];folder=BATCH/'checks'/tid;receipt=folder/'result.json'
    if receipt.exists():return reusable(kernel,json.loads(receipt.read_text()),row)
    source=BATCH/'sources'/tid/'Solution.lean';assert sha(source.read_bytes())==row['source_sha256']
    attempt=1+len(list(folder.glob('attempt_*_started.json')));assert attempt<=2,'More than one interrupted resume'
    start=time.time();write(folder/f'attempt_{attempt}_started.json',dict(task_id=tid,attempt=attempt,pid=os.getpid(),started_unix=start))
    result=dict(row,passed=False,outcome='EXECUTOR_ERROR',host=socket.gethostname(),attempt=attempt,
                started_unix=start,training_admitted=False)
    try:
        raw=asdict(kernel.check_file(str(source),str(RUN/'grading'),timeout=TIMEOUT,allow_native_decide=False,
            keep_dir=str(folder/f'kernel_attempt_{attempt}')))
        kernel_path=folder/f'attempt_{attempt}_kernel_report.json';write(kernel_path,raw)
        passed=bool(kernel.valid_report(raw) and raw['source_sha256']==row['source_sha256']
            and raw['n_theorems']>0 and raw['n_honest']==raw['n_theorems'])
        assert sha(source.read_bytes())==row['source_sha256']
        if passed:assert sha((Path(raw['evidence_dir'])/'original.olean').read_bytes())==raw['compiled_module_sha256']
        result.update(passed=passed,outcome='FORMAL_PASS' if passed else outcome(raw),kernel_report_path=str(kernel_path),
            compile_rc=raw['compile_rc'],inspect_rc=raw['inspect_rc'],n_theorems=raw['n_theorems'],n_honest=raw['n_honest'],
            diagnostic=json.dumps(raw['probe_errors'],ensure_ascii=False)[:1500])
    except Exception as exc:result['diagnostic']=repr(exc)
    result.update(elapsed_seconds=time.time()-start,finished_unix=time.time());write(receipt,result);return result


def controls(kernel):
    values=[]
    for label,source,wanted in [('positive','import Mathlib\ntheorem publicSourceV14Control : True := by exact True.intro\n',True),
        ('sorry','import Mathlib\ntheorem publicSourceV14Control : False := by sorry\n',False),
        ('declared_axiom','import Mathlib\naxiom publicSourceV14Fake : False\ntheorem publicSourceV14Control : False := by exact publicSourceV14Fake\n',False)]:
        tid='control_'+label;path=BATCH/'sources'/tid/'Solution.lean';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
        row=dict(task_id=tid,source_family='control',source_sha256=sha(source),training_admitted=False)
        result=check(kernel,row);assert result['passed']==wanted,(label,result)
        if not wanted:assert result['outcome'] in ('SORRY_REJECTED','AXIOM_REJECTED'),(label,result)
        values.append(result)
    write(BATCH/'controls.json',dict(passed=True,declared=3,rows=values,observed_unix=time.time()))


def summarize(rows,completed,state,start):
    byid={r['task_id']:r for r in completed}
    allrows=[byid.get(row['task_id'],dict(row,passed=False,outcome='PENDING',training_admitted=False)) for row in rows]
    summary=dict(state=state,declared=len(rows),completed=len(completed),remaining=len(rows)-len(completed),
        passed=sum(r['passed'] for r in completed),outcomes=dict(collections.Counter(r['outcome'] for r in completed)),
        source_outcomes={family:dict(collections.Counter(r['outcome'] for r in completed if r['source_family']==family))
            for family in sorted(set(r['source_family'] for r in rows))},workers=WORKERS,pid=os.getpid(),host=socket.gethostname(),
        elapsed_seconds=time.time()-start,observed_unix=time.time(),training_admitted=0,
        interpretation='Formal correctness only; source semantics, comments, template, protected screens and global dedup pending')
    write(BATCH/'progress.json',summary)
    keys=['task_id','source_family','source_revision','source_path','source_row','license_status','source_sha256',
        'exact_source_context_verified','semantic_review','semantic_risk_flags','training_admitted','passed','outcome',
        'compile_rc','inspect_rc','n_theorems','n_honest','host','attempt','elapsed_seconds','diagnostic']
    with (BATCH/'row_results.csv.tmp').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(allrows)
    (BATCH/'row_results.csv.tmp').replace(BATCH/'row_results.csv')
    print(json.dumps(summary,sort_keys=True),flush=True);return summary


def run():
    with (BATCH/'owner.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        freeze=json.loads((BATCH/'freeze.json').read_text());assert freeze['driver_sha256']==sha(Path(__file__).read_bytes())
        assert sha(FROZEN.read_bytes())==INSPECTOR_SHA==freeze['frozen_inspector_sha256']
        data=(BATCH/'manifest.jsonl').read_bytes();assert sha(data)==freeze['manifest_sha256']
        rows=[json.loads(line) for line in data.splitlines()];assert len(rows)==729
        os.environ['PATH']=str(RUN/'bin')+':'+os.environ['PATH'];os.environ['CUDA_VISIBLE_DEVICES']=''
        kernel=load_module('public_source_v14_frozen_kernel',FROZEN);controls(kernel)
        start=time.time();last=start;results=[];summarize(rows,results,'RUNNING',start)
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures=[pool.submit(check,kernel,row) for row in rows]
            for future in as_completed(futures):
                results.append(future.result())
                if time.time()-last>=15 or len(results)==len(rows):summarize(rows,results,'RUNNING',start);last=time.time()
        summary=summarize(rows,results,'DONE',start);write(BATCH/'completion.json',summary)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);args=p.parse_args()
    prepare() if args.action=='prepare' else run()
