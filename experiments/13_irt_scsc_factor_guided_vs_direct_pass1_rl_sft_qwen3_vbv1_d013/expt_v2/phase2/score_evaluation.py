"""Score frozen evaluation cells with the historical strict oracle and bounded identical infrastructure recovery."""
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
from score_anchor_ledger import MemorySlots,finish_attempt,check_identity,retryable
from training_checkpoint import digest,write_new
from evaluation_generation import validate_manifest

IDENTITY=('cell_id','task_id','sample_idx','split','arm','run_seed','boundary')


def score_one(row,root,config):
    from rl4cv.veribench.exp103 import extract_lean
    allowed=set(Path(config['allowlist']).read_text().splitlines())
    if row['split']!=config['split'] or row['task_id'] not in allowed:
        raise ValueError('evaluation scoring cell outside its frozen split')
    if row['split'] not in ('validation','test') and not (row['split']=='train' and config['purpose']=='T4_train_cost'):
        raise ValueError('unregistered evaluation scoring purpose')
    root=Path(root);extraction=extract_lean(row['completion'],tuple(row['required_paths']),root=config['veribench'])
    source=root/'solution.lean'
    with source.open('x',encoding='utf-8') as out:out.write(extraction.lean or '')
    value=inspect_source(source,lake_dir=Path(config['lake']),scorer_root=Path(config['scorer']),
        evidence=root/'evidence',expected_sha256=digest(source),family='ladder',known=True,truncated=row['at_token_cap'])
    oracle=json.loads((root/'evidence/oracle/oracle.json').read_text())
    return {'status':'measured',**value,'compile':oracle['compile'],'extraction':extraction.method,
            'unmapped_paths':list(extraction.unmapped),'source_sha256':digest(source),'at_token_cap':row['at_token_cap']}


def worker(job_path):
    job=json.loads(Path(job_path).read_text());root=Path(job['root']);started=time.monotonic()
    if digest(job['generation'])!=job['generation_sha256']:raise ValueError('evaluation generation changed')
    row=json.loads(Path(job['generation']).read_text())
    if any(row.get(k)!=v for k,v in job['identity'].items()):raise ValueError('evaluation scoring identity changed')
    cell=job['cell']
    if row['prompt_token_ids']!=cell['prompt_token_ids'] or not isinstance(row.get('completion'),str):
        raise ValueError('evaluation generation prompt or text changed')
    if row['at_token_cap']!=(row['finish_reason']=='length') or not 0<len(row['output_token_ids'])<=12288:
        raise ValueError('evaluation token receipt changed')
    row['required_paths']=cell['required_paths'];result=dict(job['identity'])
    try:result.update(score_one(row,root,job['config']))
    except (subprocess.TimeoutExpired,MemoryError) as exc:
        result.update(status='deterministic_resource_limit',error_type=type(exc).__name__)
    except Exception as exc:result.update(status='unresolved_measurement',error_type=type(exc).__name__,error=str(exc))
    result['wall_seconds']=time.monotonic()-started;write_new(root/'worker_result.json',result);return result


def execute(job,root,attempt,slots):
    write_new(root/'job.json',job);code=None;error=None;marker=attempt['marker']
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


def score_cell(cell,index,config,generations,execution_sha,slots,executor=execute):
    expected={k:cell[k] for k in IDENTITY};root=Path(config['root'])/f'{index:05d}';root.mkdir(parents=True,exist_ok=True)
    final=root/'result.json';generation=generations.get(cell['cell_id'])
    if final.exists():
        old=check_identity(json.loads(final.read_text()),expected)
        if old['execution_sha256']!=execution_sha or old['generation']!=generation:raise ValueError('evaluation measurement binding changed')
        if generation and digest(generation['path'])!=generation['sha256']:raise ValueError('completed evaluation input changed')
        return old
    if generation is None:result={**expected,'status':'missing_generation','strict':None,'cleanup_verified':True,'attempts':0}
    else:
        if digest(generation['path'])!=generation['sha256']:raise ValueError('bound evaluation input changed')
        for number in (1,2):
            folder=root/f'attempt_{number}';folder.mkdir(exist_ok=True)
            path=folder/'attempt.json';binding={'identity':expected,'execution_sha256':execution_sha,'generation':generation,'number':number}
            if path.exists():
                attempt=json.loads(path.read_text())
                if any(attempt.get(k)!=v for k,v in binding.items()):raise ValueError('evaluation attempt binding changed')
                result=check_identity(json.loads((folder/'result.json').read_text()),expected) if (folder/'result.json').exists() else finish_attempt(folder,expected,attempt['marker'])
            else:
                attempt={**binding,'marker':'e13v2-evaluation-score-'+uuid.uuid4().hex,'started_unix':time.time()}
                write_new(path,attempt)
                job={'identity':expected,'cell':cell,'root':str(folder),'generation':generation['path'],
                     'generation_sha256':generation['sha256'],'config':config}
                result=check_identity(executor(job,folder,attempt,slots),expected)
            if not retryable(result):break
        result={**result,'attempts':number}
    result.update(condition='v2-S2',execution_sha256=execution_sha,generation=generation)
    if result['status']!='measured':result['strict']=None
    write_new(final,result);return result


def score_manifest(manifest,config,generations,execution_sha):
    """Parent must publish complete inputs and, for test, selection and analysis admission first."""
    cells=validate_manifest(manifest,Path(config['allowlist']).read_text().splitlines())
    if manifest['purpose']!=config['purpose'] or set(generations)!={c['cell_id'] for c in cells}:
        raise ValueError('evaluation scorer requires every declared generation status')
    if any(c['split']!=config['split'] for c in cells):raise ValueError('evaluation scorer split mismatch')
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    Path(config['controller_fence']).parent.mkdir(parents=True,exist_ok=True)
    with Path(config['controller_fence']).open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX);slots=MemorySlots()
        with ThreadPoolExecutor(max_workers=48) as pool:
            rows=list(pool.map(lambda pair:score_cell(pair[1],pair[0],config,generations,execution_sha,slots),enumerate(cells)))
        result={'condition':'v2-S2','purpose':manifest['purpose'],'execution_sha256':execution_sha,
                'declared':len(cells),'accounted':len(rows),'measured':sum(r['status']=='measured' for r in rows),
                'cleanup_unresolved':sum(r.get('cleanup_verified') is not True for r in rows),
                'identical_retries':sum(max(0,r['attempts']-1) for r in rows),'rows':rows}
        path=root/'result.json'
        if path.exists():
            if json.loads(path.read_text())!=result:raise ValueError('terminal evaluation scoring changed')
        else:write_new(path,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--job',type=Path,required=True)
    worker(parser.parse_args().job)
