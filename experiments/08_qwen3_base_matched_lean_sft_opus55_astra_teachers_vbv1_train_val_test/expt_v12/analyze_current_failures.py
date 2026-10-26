"""Diagnose the complete first-run validation cohort without changing scores or exposing held-out source to teachers."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from assemble import ROOT,RUN,write,digest

def read(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
def classify(text):
    flags=[]
    for name,pattern in [
        ('unsolved_goals',r'unsolved goals'),
        ('type_mismatch',r'type mismatch|application type mismatch|has type[\s\S]*?but is expected to have type'),
        ('unknown_identifier_or_constant',r'unknown (?:identifier|constant)|unknown tactic'),
        ('parser_or_syntax',r'unexpected token|unexpected identifier|expected token|unterminated|invalid field notation|invalid constructor'),
        ('failed_tactic',r'tactic[^\n]*failed|simp made no progress|no goals to be solved|omega could not prove|failed to prove'),
        ('instance_or_inference',r'failed to synthesize|typeclass instance problem|cannot synthesize|failed to infer|don.t know how to synthesize'),
        ('recursion_or_heartbeats',r'maximum (?:recursion|number of heartbeats)|maxRecDepth|maxHeartbeats|deep recursion'),
        ('termination_or_definition',r'fail to show termination|termination_by|structural recursion|invalid mutual|invalid recursive'),
    ]:
        if re.search(pattern,text,re.I):flags.append(name)
    return flags or ['other_compiler_diagnostic']

def main():
    os.environ['CUDA_VISIBLE_DEVICES']=''
    import numpy as np
    folder=ROOT/'analysis/failure_diagnostics_current';folder.mkdir(parents=True,exist_ok=True)
    pinned=json.loads((RUN/'scoring_preflight.json').read_text());assert digest(RUN/'bin/lake')==pinned['lake_adapter_sha256']
    write(folder/'progress.json',dict(completed=0,declared=851,state='RUNNING',observed_unix=time.time()))
    raw=read(ROOT/'validation/v12_current/raw.jsonl');scores=read(ROOT/'validation/v12_current/scored.jsonl')
    assert len(raw)==len(scores)==1080
    ri={(r['task_id'],r['sample_idx']):r for r in raw};si={(r['task_id'],r['sample_idx']):r for r in scores};assert set(ri)==set(si)
    failures=[k for k,r in si.items() if not r['compiles'] and bool((ri[k].get('lean') or '').strip())]
    assert len(failures)==851
    env={**os.environ,'CUDA_VISIBLE_DEVICES':'','PATH':str(RUN/'bin')+':'+os.environ['PATH']}
    def check(key):
        tid,sample=key;out=folder/'cells'/f's{sample}'/tid;receipt=out/'diagnostic.json'
        if receipt.exists():return json.loads(receipt.read_text())
        path=ROOT/'validation/v12_current/jobs'/f'v12_current_s{sample}'/tid/'verifier/solution.lean'
        source_sha=digest(path);started=time.time();record=dict(task_id=tid,sample_idx=sample,source_sha256=source_sha,original_compiles=False,diagnostic_only=True)
        try:
            result=subprocess.run([str(RUN/'bin/lake'),'env','lean',str(path)],cwd=RUN/'grading',env=env,capture_output=True,text=True,timeout=20)
            text=result.stdout+'\n'+result.stderr;record.update(returncode=result.returncode,categories=classify(text) if result.returncode else ['diagnostic_recompile_passed'])
        except subprocess.TimeoutExpired as exc:
            text=(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout,bytes) else exc.stdout or ''
            text+='\nDIAGNOSTIC_TIMEOUT_20_SECONDS';record.update(returncode=124,categories=['diagnostic_timeout'])
        out.mkdir(parents=True,exist_ok=True);(out/'compile.log').write_text(text)
        # Keep source-dependent messages in this protected analysis directory, never teacher inputs.
        error_lines=re.findall(r'^.*?:\d+:\d+: error:.*$',text,re.M)
        record.update(error_count=len(error_lines),elapsed_seconds=time.time()-started,log_sha256=hashlib.sha256(text.encode()).hexdigest())
        write(receipt,record);return record
    diagnostics=[]
    with ThreadPoolExecutor(max_workers=16) as pool:
        for future in as_completed([pool.submit(check,k) for k in failures]):
            diagnostics.append(future.result())
            if len(diagnostics)%50==0:write(folder/'progress.json',dict(completed=len(diagnostics),declared=851,observed_unix=time.time()))
    bykey={(r['task_id'],r['sample_idx']):r for r in diagnostics};rows=[]
    for key,r in si.items():
        original=ri[key];d=bykey.get(key);status='success' if r['compiles'] else 'extracted_compile_failure' if (original.get('lean') or '').strip() else 'no_extracted_lean'
        rows.append(dict(task_id=key[0],sample_idx=key[1],status=status,extracted=bool((original.get('lean') or '').strip()),compiles=r['compiles'],truncated=original['truncated'],generated_tokens=original['generated_tokens'],extraction=original['extraction'],diagnostic_categories=';'.join(d['categories']) if d else '',diagnostic_returncode=d.get('returncode') if d else '',diagnostic_source_sha256=d.get('source_sha256','') if d else ''))
    with (folder/'all_cells.csv').open('w') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['task_id'],r['sample_idx'])))
    def taskvector(path):
        tasks=list(csv.DictReader(path.open()));return {r['task_id']:float(r['success_rate']) for r in tasks}
    current=taskvector(ROOT/'analysis/v12_current_tasks.csv');ids=sorted(current);a=np.array([current[k] for k in ids]);draws=np.random.default_rng(0).integers(0,135,(10000,135));comparisons={}
    for condition in ['1p7_control','1p7_mixed']:
        old=taskvector(RUN/'analysis'/f'{condition}_tasks.csv');assert set(old)==set(current)
        b=np.array([old[k] for k in ids]);delta=a-b
        comparisons[condition]=dict(old_successes=round(float(b.sum()*8)),old_rate=float(b.mean()),current_successes=120,current_rate=float(a.mean()),difference=float(delta.mean()),difference_ci95=np.quantile(delta[draws].mean(axis=1),[.025,.975]).tolist(),bootstrap_unit='paired validation task retaining all eight samples',bootstrap_draws=10000,seed=0,p_value=None,interpretation='Descriptive difference on the same validation cohort; additional data, training tokens and continuation differ, so no causal attribution to one change.')
    category_counts=dict(collections.Counter(t for r in diagnostics for t in r['categories']))
    representatives={}
    for row in sorted(diagnostics,key=lambda r:(r['task_id'],r['sample_idx'])):
        for category in row['categories']:
            representatives.setdefault(category,dict(task_id=row['task_id'],sample_idx=row['sample_idx'],diagnostic_source_sha256=row['source_sha256'],analysis_only_log=str(folder/'cells'/f's{row["sample_idx"]}'/row['task_id']/'compile.log')))
    summary=dict(state='DONE',declared_cells=1080,extracted=971,compiled=120,extracted_compile_failures=851,no_extracted_lean=109,capped=110,capped_with_extracted_lean=sum(r['truncated'] and r['extracted'] for r in rows),extraction_counts=dict(collections.Counter(r['extraction'] for r in rows)),status_counts=dict(collections.Counter(r['status'] for r in rows)),diagnostic_checked=len(diagnostics),overlapping_diagnostic_categories=category_counts,representatives_analysis_only=representatives,comparisons=comparisons,diagnostics_timeout_seconds=20,diagnostic_workers=16,official_scores_changed=False,validation_sources_sent_to_teachers=False,observed_unix=time.time())
    write(folder/'summary.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
