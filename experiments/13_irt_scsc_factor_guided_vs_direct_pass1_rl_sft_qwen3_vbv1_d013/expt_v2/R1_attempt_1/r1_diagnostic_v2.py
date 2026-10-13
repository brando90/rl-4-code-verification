#!/usr/bin/env python3
"""Freeze train-only diagnostic identifiers and observe the entire unchanged version-1 cell path."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE.parent/'R0_attempt_2'))
sys.path.insert(0,str(HERE))
from historical_oracle_v2 import load, digest, E08


def prepare(*, root, split_path, sealed_dir):
    """Only train metadata and statuses leave this filtering process; no held-out source is opened."""
    r0=json.loads((root/'R0_attempt_2/receipt.json').read_text())
    if r0['status']!='PASS': raise ValueError('R0 has not passed; R1 not admitted')
    with split_path.open() as f:
        split={r['task_id']:r for r in csv.DictReader(f)}
    train={t for t,r in split.items() if r['split']=='train'}
    if len(train)!=539:raise ValueError('train denominator mismatch')
    manifest=sealed_dir/'sealed_manifest.jsonl'
    if digest(manifest)!='06fcbcda0d7406156f99754d69814a699fe4dbf29fee40e377fa190ccd03f1b6':
        raise ValueError('frozen base manifest mismatch')
    old_results=sealed_dir/'sealed_results.jsonl'
    if digest(old_results)!='8b5914819a098a749293494ee8db74ecbefca5c8ea0eebd493a6980a84edd85c':
        raise ValueError('frozen version-1 terminal ledger mismatch')
    allow={}
    for line in manifest.open():
        r=json.loads(line)
        if r['task_id'] not in train:continue
        if r['split']!='train' or r['group_id']!=split[r['task_id']]['group_id']:
            raise ValueError('train membership disagreement')
        allow[r['cell_id']]=r
    if len(allow)!=12936:raise ValueError('train-cell denominator mismatch')
    buckets={'rejected':[],'measured':[]}
    for line in old_results.open():
        r=json.loads(line)
        if r['cell_id'] not in allow:continue
        if r['status']=='measured':buckets['measured'].append(r['cell_id'])
        elif r.get('failure_class')=='source_or_pinned_probe_rejected':buckets['rejected'].append(r['cell_id'])
    rng=random.Random(1302001)
    selected=[]
    for category,size in [('rejected',300),('measured',100)]:
        ids=sorted(buckets[category])
        selected.extend({**allow[cell],'original_category':category} for cell in rng.sample(ids,min(size,len(ids))))
    out=root/'R1_attempt_1'
    out.mkdir(exist_ok=False)
    (out/'train_allowlist.json').write_text(json.dumps(sorted(allow),indent=2)+'\n')
    (out/'sample.json').write_text(json.dumps(selected,indent=2)+'\n')
    lock={'created':datetime.now(timezone.utc).isoformat(),'seed':1302001,'split_sha256':digest(split_path),
          'allowlist_sha256':digest(out/'train_allowlist.json'),'sample_sha256':digest(out/'sample.json'),
          'population_counts':{k:len(v) for k,v in buckets.items()},'sample_counts':{k:sum(r['original_category']==k for r in selected) for k in buckets},
          'held_out_content_read':False,'cause_denominator':'selected rejected train cells only',
          'source_manifest_sha256':digest(manifest),'old_status_ledger_sha256':digest(old_results)}
    (out/'selection_lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    return lock


def observe_v1(row, *, output, lake_dir, scorer_root):
    """Call reproduce itself on a one-cell train manifest; trace exceptions without replacing its logic."""
    if row['split']!='train':raise ValueError('development harness rejects held-out cells before source access')
    output.mkdir(parents=True,exist_ok=False)
    fields={'cell_id','model','task_id','sample_idx','group_id','split','source_path','source_sha256','truncated','old_kernel_binary'}
    manifest=output/'sealed_manifest.jsonl'
    manifest.write_text(json.dumps({k:row[k] for k in fields})+'\n')
    (output/'manifest_binding.json').write_text(json.dumps({'manifest_sha256':digest(manifest),'input_sha256':{}})+'\n')
    sys.path.insert(0,str(HERE.parent.parent/'expt_v1'))
    old=load('e13v2_observed_complete_v1',HERE.parent.parent/'expt_v1/opaque_base_audit.py')
    exceptions=[];calls=[]
    prior_trace=sys.gettrace();original_run=subprocess.run;prior_tmp=tempfile.tempdir

    def trace(frame,event,arg):
        if event=='exception' and frame.f_code.co_filename in {
            str(HERE.parent.parent/'expt_v1/opaque_base_audit.py'),str(HERE.parent.parent/'expt_v1/declaration_adapter.py'),
            str(HERE.parents[3]/'src/rl4cv/e13.py')}:
            kind,error,_=arg
            exceptions.append({'file':frame.f_code.co_filename,'function':frame.f_code.co_name,
                               'line':frame.f_lineno,'exception':kind.__name__,'message':str(error)})
        return trace

    def run(*args,**kwargs):
        index=len(calls);calls.append({'argv':args[0] if args else kwargs.get('args')})
        try:r=original_run(*args,**kwargs)
        except subprocess.TimeoutExpired as e:
            calls[index]['timeout']=True
            for stream in ('stdout','stderr'):
                data=getattr(e,stream) or b''
                (output/f'{index}.{stream}').write_bytes(data.encode() if isinstance(data,str) else data)
            raise
        calls[index]['returncode']=r.returncode
        for stream in ('stdout','stderr'):
            data=getattr(r,stream) or b''
            (output/f'{index}.{stream}').write_bytes(data.encode() if isinstance(data,str) else data)
        return r
    sys.settrace(trace);subprocess.run=run;tempfile.tempdir=str(output)
    try:
        exit_code=old.reproduce(private_dir=output,scorer_root=scorer_root,lake_dir=lake_dir,
            vacuity_source=E08/'score_teacher_files.py',public_path=output/'receipt.json',
            state_path=output/'state.json',binding_sha256=digest(manifest),heartbeat_every=1)
    finally:
        sys.settrace(prior_trace);subprocess.run=original_run;tempfile.tempdir=prior_tmp
        (output/'trace.json').write_text(json.dumps({'exceptions':exceptions,'subprocesses':calls},indent=2)+'\n')
    result=json.loads((output/'sealed_results.jsonl').read_text())
    return {'exit_code':exit_code,'result':result,'exceptions':exceptions}
