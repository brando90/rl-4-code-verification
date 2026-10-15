"""Score complete train rollout slots with the frozen oracle, without relabeling them as anchors."""
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
from score_anchor import inspect_source,ADDRESS_SPACE
from score_anchor_ledger import MemorySlots,finish_attempt,check_identity
from panel import validate_generation
from training_checkpoint import digest,write_new


def score_one(row,root,config):
    from rl4cv.veribench.exp103 import extract_lean
    allowed=set(Path(config['train_ids']).read_text().splitlines())
    if row['split']!='train' or row['task_id'] not in allowed or row['arm'] not in ('A','B','C','P','technical'):
        raise ValueError('scoring requires a declared train-only rollout')
    root=Path(root);extraction=extract_lean(row['completion'],tuple(row['required_paths']),root=config['veribench'])
    source=root/'solution.lean'
    with source.open('x',encoding='utf-8') as out:out.write(extraction.lean or '')
    value=inspect_source(source,lake_dir=Path(config['lake']),scorer_root=Path(config['scorer']),
        evidence=root/'evidence',expected_sha256=digest(source),family='ladder',known=True,truncated=row['at_token_cap'])
    return {'status':'measured',**value,'extraction':extraction.method,'unmapped_paths':list(extraction.unmapped),
        'source_sha256':digest(source),'at_token_cap':row['at_token_cap']}


def worker(job_path):
    job=json.loads(Path(job_path).read_text());root=Path(job['root']);started=time.monotonic()
    if digest(job['generation'])!=job['generation_sha256']:raise ValueError('generation changed before worker read')
    row=json.loads(Path(job['generation']).read_text())
    for key,value in job['identity'].items():
        if row.get(key)!=value:raise ValueError('training scoring identity changed')
    validate_generation(job['cell'],row,job['contract'])
    row['required_paths']=job['cell']['required_paths'];result=dict(job['identity'])
    try:result.update(score_one(row,root,job['config']))
    except (subprocess.TimeoutExpired,MemoryError) as exc:
        result.update(status='deterministic_resource_limit',error_type=type(exc).__name__)
    except Exception as exc:
        result.update(status='unresolved_measurement',error_type=type(exc).__name__,error=str(exc))
    result['wall_seconds']=time.monotonic()-started
    write_new(root/'worker_result.json',result)
    return result


def execute(job,root,marker,slots):
    write_new(root/'job.json',job);code=None;error=None
    with slots:
        try:
            with (root/'execution.log').open('x') as log:
                child=subprocess.Popen(['prlimit',f'--as={ADDRESS_SPACE}','--',sys.executable,str(Path(__file__)),
                    '--job',str(root/'job.json')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                    env={**os.environ,'E13_EXECUTION_ID':marker})
                write_new(root/'process.json',{'pid':child.pid,'marker':marker,
                    'start_ticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],
                    'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
                code=child.wait(timeout=3600)
        except subprocess.TimeoutExpired:error='supervisor_timeout'
        except OSError as exc:error=type(exc).__name__
        return finish_attempt(root,job['identity'],marker,code,error)


def score_cell(cell,index,config,bound,execution_sha,slots,executor=execute):
    """Recover an existing receipt; never execute a second measurement attempt implicitly."""
    if cell['split']!='train' or cell['task_id'] not in set(Path(config['train_ids']).read_text().splitlines()):
        raise ValueError('held-out scoring forbidden')
    identity={k:cell[k] for k in ('cell_id','task_id','sample','split','arm','run_seed','update','group_index')}
    root=Path(config['root'])/f'{index:05d}';root.mkdir(parents=True,exist_ok=True)
    generation=Path(config['generation_root'])/f'{index:05d}.generation.json'
    if not generation.exists():
        if str(generation) in bound:raise ValueError('bound generation went missing')
        result={**identity,'status':'missing_generation','execution_sha256':execution_sha,'cleanup_verified':True}
    else:
        if bound.get(str(generation))!=digest(generation):raise ValueError('unbound or changed rollout')
        attempt=root/'attempt.json'
        if attempt.exists():
            prior=json.loads(attempt.read_text())
            if prior['identity']!=identity or prior['execution_sha256']!=execution_sha or prior['generation_sha256']!=digest(generation):
                raise ValueError('scoring execution binding changed')
            if (root/'result.json').exists():return check_identity(json.loads((root/'result.json').read_text()),identity)
            return finish_attempt(root,identity,prior['marker'])
        if (root/'result.json').exists():raise ValueError('previous missing generation cannot be replaced')
        marker='e13v2-training-score-'+uuid.uuid4().hex
        prior={'identity':identity,'execution_sha256':execution_sha,'generation_sha256':digest(generation),
            'marker':marker,'started_unix':time.time(),'automatic_retry':False}
        write_new(attempt,prior)
        job={'identity':identity,'generation':str(generation),'generation_sha256':digest(generation),
            'root':str(root),'cell':cell,'contract':{'max_model_len':15945,'terminal_token_ids':[151643,151645]},'config':config}
        return executor(job,root,marker,slots)
    if (root/'result.json').exists():
        old=json.loads((root/'result.json').read_text())
        if old!=result:raise ValueError('missing-generation receipt changed')
        return old
    write_new(root/'result.json',result);return result


def score_batch(cells,config,bound,execution_sha):
    """Called only after the parent driver verifies its published lock and durable generation inventory."""
    if not cells or len(cells)>256 or len({c['cell_id'] for c in cells})!=len(cells):raise ValueError('invalid rollout scoring cohort')
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    with Path(config['controller_fence']).open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX)
        slots=MemorySlots()
        with ThreadPoolExecutor(max_workers=48) as pool:
            rows=list(pool.map(lambda pair:score_cell(pair[1],pair[0],config,bound,execution_sha,slots),enumerate(cells)))
    receipt={'condition':'v2-S2','execution_sha256':execution_sha,'declared':len(cells),
        'measured':sum(r['status']=='measured' for r in rows),'automatic_retries':0,'rows':rows}
    path=root/'result.json'
    if path.exists():
        if json.loads(path.read_text())!=receipt:raise ValueError('scoring result changed')
    else:write_new(path,receipt)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--job',required=True,type=Path)
    worker(parser.parse_args().job)
