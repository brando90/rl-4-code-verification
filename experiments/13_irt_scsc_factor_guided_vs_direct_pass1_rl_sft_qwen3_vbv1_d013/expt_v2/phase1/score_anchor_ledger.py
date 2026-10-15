"""Resume frozen anchor scoring by cell, preserving completed measurements and one identical infrastructure retry."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid

import psutil
from panel import digest,validate_manifest,validate_generation
from anchor_storage import write_new,mkdir,sync_directory
from lp1 import cleanup
from g1_driver import verify_publication
import score_anchor as scorer

HERE=Path(__file__).resolve().parent
TRANSIENT_ERRORS={'OSError','ConnectionError','BrokenPipeError','InterruptedError','ProcessLookupError'}


def identity(cell,batch):
    return {'cell_id':cell['cell_id'],'task_id':cell['task_id'],'sample_idx':cell['sample'],
            'policy':scorer.POLICIES[batch],'batch':batch,'split':'train'}


def check_identity(result,expected):
    if any(result.get(k)!=v for k,v in expected.items()):raise ValueError('scoring receipt identity changed')
    if result['status']=='measured' and result.get('strict') not in (False,True,0,1):
        raise ValueError('nonbinary scored strict outcome')
    return result


def retryable(result):
    return bool(result.get('cleanup_verified') and result['status']=='unresolved_measurement'
        and (result.get('error_type') in TRANSIENT_ERRORS or result.get('missing_worker_receipt') is True))


class MemorySlots:
    """One complete scoring controller at a time; admit at most the frozen aggregate memory allowance."""
    def __init__(self):self.condition=threading.Condition();self.active=0
    def __enter__(self):
        with self.condition:
            while True:
                mem=psutil.virtual_memory();ceiling=min(48,int(.5*mem.available/scorer.P99_PEAK))
                if self.active<ceiling and mem.available>=.25*mem.total:
                    self.active+=1;break
                self.condition.wait(1)
    def __exit__(self,*exc):
        with self.condition:self.active-=1;self.condition.notify_all()


def finish_attempt(root,expected,marker,code=None,error=None):
    """Recover a durable worker result before considering any retry after controller loss."""
    root=Path(root);cleaned=cleanup(marker)
    worker=root/'worker_result.json'
    if worker.exists():
        result=check_identity(json.loads(worker.read_text()),expected)
        if code not in (None,0) and result['status']=='measured':
            result.update(status='unresolved_measurement',error_type='nonzero_worker_after_receipt')
    else:
        result={**expected,'status':'unresolved_measurement','missing_worker_receipt':True,
                'error_type':error or 'missing_worker_receipt'}
    if error=='supervisor_timeout':result.update(status='deterministic_resource_limit',error_type=error)
    if not cleaned['verified']:result.update(status='unresolved_cleanup')
    result.update(cleanup_verified=cleaned['verified'],worker_exit_code=code)
    cleanup_path=root/'cleanup.json'
    if cleanup_path.exists():cleanup_path=root/('cleanup_recovery_'+uuid.uuid4().hex+'.json')
    write_new(cleanup_path,cleaned)
    write_new(root/'result.json',result)
    return result


def execute(job,root,attempt,slots):
    """Call the unchanged worker with the unchanged source, adapter and resource cap."""
    root=Path(root);write_new(root/'job.json',job)
    marker=attempt['marker'];code=None;error=None
    with slots:
        try:
            with (root/'execution.log').open('x') as log:
                child=subprocess.Popen(['prlimit',f'--as={scorer.ADDRESS_SPACE}','--',sys.executable,
                    str(HERE/'score_anchor.py'),'--job',str(root/'job.json')],stdout=log,stderr=subprocess.STDOUT,
                    start_new_session=True,env={**os.environ,'E13_EXECUTION_ID':marker})
                write_new(root/'process.json',{'pid':child.pid,'marker':marker,
                    'start_ticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],
                    'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
                code=child.wait(timeout=3600)
        except subprocess.TimeoutExpired:error='supervisor_timeout'
        except OSError as exc:error=type(exc).__name__
        return finish_attempt(root,job['identity'],marker,code,error)


def score_cell(cell,index,config,manifest,bound,lock_sha,slots,executor=execute):
    expected=identity(cell,manifest['batch']);root=Path(config['root'])/f'{index:05d}';mkdir(root)
    final=root/'result.json'
    if final.exists():
        result=check_identity(json.loads(final.read_text()),expected)
        if result.get('lock_sha256')!=lock_sha:raise ValueError('completed scoring cell belongs to another lock')
        return result
    generation=Path(config['generation_root'])/f'{index:05d}.generation.json'
    result=None
    if not generation.exists():
        result={**expected,'status':'missing_generation','cleanup_verified':True,'attempts':0}
    else:
        if bound.get(str(generation))!=digest(generation):raise ValueError('unbound or changed generation receipt')
        row=json.loads(generation.read_text())
        if any(row.get(k)!=cell[k] for k in ('cell_id','task_id','sample','split')):
            raise ValueError('generation identity differs from declared scoring cell')
        validate_generation(cell,row,manifest)
        job={'identity':expected,'cell':cell,'batch':manifest['batch'],'generation':str(generation),
             'manifest_contract':{k:manifest[k] for k in ('terminal_token_ids','max_model_len')},
             'bindings':[{'path':str(generation),'sha256':digest(generation)}],'config':config}
        for number in (1,2):
            attempt_root=root/f'attempt_{number}';attempt_path=attempt_root/'attempt.json'
            if attempt_path.exists():
                attempt=json.loads(attempt_path.read_text())
                if (attempt['identity']!=expected or attempt['lock_sha256']!=lock_sha
                        or attempt['generation_sha256']!=digest(generation) or attempt['number']!=number):
                    raise ValueError('persisted scoring attempt changed')
                saved=attempt_root/'result.json'
                result=check_identity(json.loads(saved.read_text()),expected) if saved.exists() else finish_attempt(
                    attempt_root,expected,attempt['marker'])
            else:
                mkdir(attempt_root)
                attempt={'identity':expected,'number':number,'marker':'e13v2-score-'+uuid.uuid4().hex,
                    'lock_sha256':lock_sha,'generation_sha256':digest(generation),'started_unix':time.time()}
                write_new(attempt_path,attempt)
                result=check_identity(executor({**job,'root':str(attempt_root)},attempt_root,attempt,slots),expected)
            if not retryable(result):break
        result={**result,'attempts':number}
    result.update(condition='v2-S2',lock_sha256=lock_sha)
    write_new(final,result)
    return result


def verify(plan):
    lock=verify_publication(plan['lock'],plan['repository'],plan['published_revision'])
    if lock.get('gate')!='ANCHOR_SCORE_S2' or lock.get('condition')!='v2-S2' or lock.get('status')!='FROZEN':
        raise ValueError('published S2 scoring lock required')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    for path,sha in bound.items():
        if digest(path)!=sha:raise ValueError('scoring binding changed: '+path)
    config=lock['configuration']
    required={str(HERE/'score_anchor_ledger.py'),str(HERE/'score_anchor.py'),str(HERE/'panel.py'),
        str(HERE/'lp1.py'),str(HERE/'anchor_storage.py'),str(HERE/'g1_driver.py'),
        str(HERE.parent/'R0_attempt_2/declaration_adapter_v2.py'),str(HERE.parent/'R0_attempt_2/DeclarationProbe_v2.lean'),
        str(HERE.parent/'historical_oracle_v2.py'),config['manifest'],config['train_ids'],config['LP1_result'],
        config['generation_report'],config['generation_lock']}
    if not required<=set(bound):raise ValueError('scoring execution or provenance is unbound')
    lp1=verify_publication(config['LP1_result'],plan['repository'],config['LP1_revision'])
    if lp1.get('status')!='PASS' or lp1.get('condition')!='v2-S2':raise ValueError('S2 probability admission missing')
    report=verify_publication(config['generation_report'],plan['repository'],config['generation_revision'])
    manifest=json.loads(Path(config['manifest']).read_text())
    cells=validate_manifest(manifest,Path(config['train_ids']).read_text().splitlines())
    if (manifest['batch'] not in scorer.POLICIES or len(cells)!=4312 or report.get('batch')!=manifest['batch']
            or report.get('condition')!='v2-S2' or report.get('declared')!=len(cells)
            or report.get('accounted')!=len(cells) or report.get('status') not in ('COMPLETE','INCOMPLETE')
            or report.get('generation_lock_sha256')!=digest(config['generation_lock'])):
        raise ValueError('full generation manifest has not closed')
    if manifest['batch']=='full2':
        if config['calibration'] not in bound:raise ValueError('batch-2 calibration is unbound')
        if report.get('calibration_sha256')!=digest(config['calibration']):raise ValueError('batch-2 chronology changed')
    return lock,config,bound,manifest,cells


def run(plan_path):
    plan=json.loads(Path(plan_path).read_text());lock,config,bound,manifest,cells=verify(plan)
    root=Path(config['root']);mkdir(root);mkdir(Path(config['controller_fence']).parent)
    with Path(config['controller_fence']).open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX)
        if (root/'terminal.json').exists():
            terminal=json.loads((root/'terminal.json').read_text())
            if terminal.get('cells_sha256')!=digest(root/'results.jsonl') or terminal.get('scoring_lock_sha256')!=digest(plan['lock']):
                raise ValueError('completed scoring ledger differs from terminal receipt')
            return terminal
        subprocess.run([sys.executable,str(HERE.parent/'watchdog_e13v2.py'),'--root',plan['watchdog_root'],
            '--run',plan['watchdog_run'],'register','--role','score-'+manifest['batch'],'--pid',str(os.getpid())],check=True)
        slots=MemorySlots();lock_sha=digest(plan['lock'])
        def score(pair):
            index,cell=pair
            try:return score_cell(cell,index,config,manifest,bound,lock_sha,slots)
            except Exception as exc:
                # A defect is an explicit missing cell, never a fabricated zero or a resampled generation.
                result={**identity(cell,manifest['batch']),'status':'integrity_defect','condition':'v2-S2',
                    'error_type':type(exc).__name__,'error':str(exc),'lock_sha256':lock_sha,'attempts':0}
                failure=root/f'{index:05d}.integrity.json'
                if not failure.exists():write_new(failure,result)
                return result
        with ThreadPoolExecutor(max_workers=48) as pool:rows=list(pool.map(score,enumerate(cells)))
        target=root/'results.jsonl'
        content=''.join(json.dumps(row,sort_keys=True,allow_nan=False)+'\n' for row in rows)
        if target.exists():
            if target.read_text()!=content:raise ValueError('completed scoring ledger changed')
        else:
            with target.open('x') as out:out.write(content);out.flush();os.fsync(out.fileno())
            sync_directory(root)
        result={**scorer.summarize(rows,len(cells)),'condition':'v2-S2','batch':manifest['batch'],
            'accounted':len(cells),'cells_sha256':digest(target),'scoring_lock_sha256':lock_sha,
            'generation_lock_sha256':digest(config['generation_lock']),
            'retried_cells':sum(r['attempts']==2 for r in rows),'retries':sum(max(0,r['attempts']-1) for r in rows),
            'integrity_defects':sum(r['status']=='integrity_defect' for r in rows),
            'cleanup_unresolved':sum(r['status']=='unresolved_cleanup' for r in rows)}
        if manifest['batch']=='full2':result['calibration_sha256']=digest(config['calibration'])
        write_new(root/'terminal.json',result)
        return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',required=True,type=Path)
    print(json.dumps(run(parser.parse_args().plan),sort_keys=True))
