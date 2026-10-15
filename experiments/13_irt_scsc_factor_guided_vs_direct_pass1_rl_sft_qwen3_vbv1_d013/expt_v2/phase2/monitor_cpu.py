"""Attach exact saved strict evidence and measure independent hidden coverage for every fixed monitor cell once."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from score_anchor_ledger import MemorySlots,finish_attempt
from score_anchor import ADDRESS_SPACE
from hidden_runtime import measure_cell
from training_checkpoint import digest,write_new
from audit_inputs import checked

IDENTITY=('cell_id','audit_id','task_id','group_id','split','arm','run_seed','update')


def prepare(snapshot,scoring,score_root,suites,*,output):
    """Normalize saved oracle compilation without rerunning strict scoring or inferring it from strict success."""
    if snapshot.get('condition')!='v2-S2' or snapshot.get('declared')!=32 or snapshot.get('frozen_before_generation') is not True:
        raise ValueError('frozen complete monitor snapshot required')
    rows=scoring['rows'];table={r['cell_id']:r for r in rows};cells=snapshot['cells']
    if len(table)!=32 or set(table)!={c['cell_id'] for c in cells}:raise ValueError('monitor strict denominator changed')
    root=Path(output);root.mkdir(parents=True,exist_ok=False);normalized=[]
    if set(suites)!={c['task_id'] for c in cells}:raise ValueError('complete fixed monitor hidden-suite inventory required')
    for index,cell in enumerate(cells):
        row=table[cell['cell_id']]
        if any(row.get(k)!=cell[k] for k in ('cell_id','task_id','sample','split','arm','run_seed','update','group_index')):
            raise ValueError('monitor strict evidence belongs to another snapshot')
        if row.get('cleanup_verified') is not True:raise ValueError('strict scorer cleanup unresolved')
        folder=Path(score_root)/f'{index:05d}';saved=folder/'result.json'
        if json.loads(saved.read_text())!=row:raise ValueError('monitor scoring summary differs from retained cell')
        source=folder/'solution.lean';compiled=None;oracle_ref=None
        if row['status']=='measured':
            if not source.exists() or digest(source)!=row['source_sha256']:raise ValueError('monitor candidate differs from strict source')
            oracle=folder/'evidence/oracle/oracle.json';value=json.loads(oracle.read_text())
            if type(value.get('compile')) is not bool:raise ValueError('official compile evidence missing')
            compiled=value['compile'];oracle_ref={'path':str(oracle),'sha256':digest(oracle)}
        strict={**row,'compile':compiled,'strict_receipt':{'path':str(saved),'sha256':digest(saved)},'oracle_receipt':oracle_ref}
        normalized_path=root/f'{index:03d}.strict.json';write_new(normalized_path,strict)
        checked(suites[cell['task_id']])
        normalized.append({**{k:cell[k] for k in IDENTITY},'source':{'path':str(source),'sha256':digest(source)} if source.exists() else None,
            'strict':{'path':str(normalized_path),'sha256':digest(normalized_path)},'suite':suites[cell['task_id']]})
    result={**{k:snapshot[k] for k in ('condition','arm','run_seed','update')},'declared':32,'cells':normalized,
            'new_strict_measurements':0,'new_hidden_measurements':0}
    write_new(root/'inputs.json',result);return result


def measure(job,hidden=measure_cell):
    cell=job['cell'];config=job['configuration'];root=Path(job['root'])
    if cell['split']!='train' or cell['task_id'] not in set(Path(config['train_ids']).read_text().splitlines()):
        raise ValueError('monitor hidden measurement is train-only')
    strict=json.loads(checked(cell['strict']).read_text());checked(strict['strict_receipt'])
    if strict['oracle_receipt']:checked(strict['oracle_receipt'])
    if any(strict.get(k)!=cell[k] for k in ('cell_id','task_id','split','arm','run_seed','update')):
        raise ValueError('monitor strict identity changed')
    result={**job['identity'],'condition':'v2-S2','status':'ACCOUNTED','compile':strict['compile'],
            'strict_receipt':cell['strict'],'source':cell['source'],'hidden_test_coverage':None,'new_strict_measurements':0}
    if cell['source'] is None:return {**result,'hidden_status':'missing_source'}
    source=checked(cell['source']);suite=checked(cell['suite'])
    hidden_cell={k:cell[k] for k in ('cell_id','task_id','split')};hidden_cell.update(source=str(source),suite=str(suite))
    bindings={str(source):cell['source']['sha256'],str(suite):cell['suite']['sha256'],config['train_ids']:digest(config['train_ids'])}
    try:value=hidden(hidden_cell,{**config,'root':str(root/'hidden')},bindings,job['execution_sha256'])
    except Exception as exc:value={'status':'unresolved_measurement','hidden_pass_rate':None,'error_type':type(exc).__name__,'error':str(exc)}
    write_new(root/'hidden_summary.json',value)
    result.update(hidden_status=value['status'],hidden_receipt={'path':str(root/'hidden_summary.json'),'sha256':digest(root/'hidden_summary.json')},
        hidden_test_coverage=value.get('hidden_pass_rate') if value.get('fully_applicable') or value['status']=='compile_failure' else None)
    return result


def worker(path):
    job=json.loads(Path(path).read_text());started=time.monotonic();result=measure(job)
    result['wall_seconds']=time.monotonic()-started;write_new(Path(job['root'])/'worker_result.json',result);return result


def execute(job,root,marker,slots):
    write_new(root/'job.json',job);code=None;error=None
    with slots:
        try:
            with (root/'execution.log').open('x') as log:
                child=subprocess.Popen(['prlimit',f'--as={ADDRESS_SPACE}','--',sys.executable,str(Path(__file__).resolve()),
                    '--job',str(root/'job.json')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                    env={**os.environ,'E13_EXECUTION_ID':marker})
                write_new(root/'process.json',{'pid':child.pid,'marker':marker,
                    'start_ticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],
                    'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
                code=child.wait(timeout=3600)
        except subprocess.TimeoutExpired:error='supervisor_timeout'
        except OSError as exc:error=type(exc).__name__
        return finish_attempt(root,job['identity'],marker,code,error)


def score_cell(cell,index,config,execution_sha,slots,executor=execute):
    root=Path(config['root'])/f'{index:03d}';root.mkdir(parents=True,exist_ok=True)
    identity={k:cell[k] for k in IDENTITY};expected={'identity':identity,'execution_sha256':execution_sha,'cell':cell}
    attempt=root/'attempt.json';final=root/'result.json'
    if attempt.exists():
        previous=json.loads(attempt.read_text())
        if any(previous.get(k)!=v for k,v in expected.items()):raise ValueError('monitor execution binding changed')
        value=json.loads(final.read_text()) if final.exists() else finish_attempt(root,identity,previous['marker'])
        if any(value.get(k)!=v for k,v in identity.items()):raise ValueError('monitor result identity changed')
        return value
    if final.exists():raise ValueError('monitor result lacks its attempt')
    marker='e13v2-monitor-hidden-'+uuid.uuid4().hex
    write_new(attempt,{**expected,'marker':marker,'automatic_retry':False,'started_unix':time.time()})
    return executor({**expected,'root':str(root),'configuration':config},root,marker,slots)


def run_cells(inputs,config,execution_sha):
    """Parent must verify the published snapshot/execution, controls and exact input bindings first."""
    cells=inputs['cells']
    if (inputs.get('condition')!='v2-S2' or inputs.get('declared')!=32 or len(cells)!=32
            or len({c['audit_id'] for c in cells})!=32 or len({c['task_id'] for c in cells})!=32):
        raise ValueError('fixed complete monitor population required')
    if any(c[k]!=inputs[k] for c in cells for k in ('arm','run_seed','update')):raise ValueError('monitor checkpoint changed')
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    Path(config['controller_fence']).parent.mkdir(parents=True,exist_ok=True)
    with Path(config['controller_fence']).open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX);slots=MemorySlots()
        with ThreadPoolExecutor(max_workers=8) as pool:
            rows=list(pool.map(lambda pair:score_cell(pair[1],pair[0],config,execution_sha,slots),enumerate(cells)))
        result={'condition':'v2-S2','stage':'PILOT_MONITOR_HIDDEN','execution_sha256':execution_sha,'declared':32,'accounted':len(rows),
                'rows':rows,'cleanup_unresolved':sum(r.get('cleanup_verified') is not True for r in rows),'automatic_retries':0}
        path=root/'result.json'
        if path.exists():
            if json.loads(path.read_text())!=result:raise ValueError('monitor hidden terminal changed')
        else:write_new(path,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job',required=True,type=Path);worker(p.parse_args().job)
