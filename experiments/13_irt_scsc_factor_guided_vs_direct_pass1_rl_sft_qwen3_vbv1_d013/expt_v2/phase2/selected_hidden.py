"""Run the validated hidden adapter once on every fixed selected-test sample under published authority."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl,hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from hidden_runtime import Runtime,ADDRESS_SPACE
from score_anchor_ledger import MemorySlots,finish_attempt
from selected_coverage_inputs import authority,IDENTITY,verify_evidence
from selected_coverage import validate
from technical_driver import read,reference
from technical_ledger import published
from training_checkpoint import digest,write_new
from costs import snapshot as cost_snapshot,stage_cost


def measure(job,runtime_class=Runtime):
    cell=job['cell'];config=job['configuration'];strict=read(cell['strict']);read(strict['strict_receipt'])
    if strict.get('oracle_receipt'):read(strict['oracle_receipt'])
    if cell['split']!='test' or cell['sample_idx']!=0 or cell['task_id'] not in Path(config['test_ids']).read_text().splitlines():
        raise ValueError('fixed declared selected-test sample required')
    if any(strict.get(k)!=cell[k] for k in IDENTITY):raise ValueError('selected-test hidden source identity changed')
    result={'condition':'v2-S2',**job['identity'],'status':'ACCOUNTED','compile':strict['compile'],
        'strict_receipt':cell['strict'],'source':cell['source'],'hidden_test_coverage':None,'new_strict_measurements':0}
    if cell['source'] is None:return {**result,'hidden_status':'missing_source'}
    if digest(cell['source']['path'])!=cell['source']['sha256']:raise ValueError('selected-test hidden candidate changed')
    suite=read(cell['suite']);source=Path(cell['source']['path']).read_text()
    key=hashlib.sha256((job['execution_sha256']+'\0'+cell['cell_id']).encode()).hexdigest()[:24]
    root=Path(job['root'])/'hidden';root.mkdir(exist_ok=False)
    runtime=runtime_class(root,config['lake'],config['lake_bin'])
    try:value=runtime.evaluate(suite,source,'E13Hidden'+key)
    except Exception as exc:value={'status':'unresolved_measurement','hidden_pass_rate':None,'error_type':type(exc).__name__,'error':str(exc)}
    write_new(Path(job['root'])/'hidden_summary.json',value)
    result.update(hidden_status=value['status'],hidden_receipt=reference(Path(job['root'])/'hidden_summary.json'),
        hidden_test_coverage=value.get('hidden_pass_rate') if value.get('fully_applicable') or value['status']=='compile_failure' else None)
    return result


def worker(path):
    job=json.loads(Path(path).read_text());started=time.monotonic();value=measure(job)
    value['wall_seconds']=time.monotonic()-started;write_new(Path(job['root'])/'worker_result.json',value);return value


def execute(job,root,marker,slots):
    write_new(root/'job.json',job);code=None;error=None
    with slots:
        try:
            with (root/'execution.log').open('x') as log:
                child=subprocess.Popen(['prlimit',f'--as={ADDRESS_SPACE}','--',sys.executable,str(Path(__file__).resolve()),'--job',str(root/'job.json')],
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'E13_EXECUTION_ID':marker})
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
        if any(previous.get(k)!=v for k,v in expected.items()):raise ValueError('selected-test hidden attempt changed')
        value=json.loads(final.read_text()) if final.exists() else finish_attempt(root,identity,previous['marker'])
        if any(value.get(k)!=v for k,v in identity.items()):raise ValueError('selected-test hidden result identity changed')
        return value
    if final.exists():raise ValueError('hidden result lacks its attempt')
    marker='e13v2-selected-hidden-'+uuid.uuid4().hex
    write_new(attempt,{**expected,'marker':marker,'automatic_retry':False,'started_unix':time.time()})
    return executor({**expected,'root':str(root),'configuration':config},root,marker,slots)


def run(plan):
    lock=published(plan['lock'],plan['repository'])
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('SELECTED_TEST_COVERAGE_CPU','v2-S2','FROZEN'):
        raise ValueError('published selected-test independent coverage inputs required')
    selection=lock['selection_plan'];tasks,score,score_lock,data=authority(selection)
    main=published(selection['L2'],plan['repository']);bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('selected-test hidden binding changed')
    science={b['path']:b['sha256'] for b in main['bindings']}
    sources=[Path(__file__).resolve(),HERE/'hidden_runtime.py',HERE/'selected_coverage.py',HERE/'selected_coverage_inputs.py',HERE/'costs.py',HERE.parent/'phase1/score_anchor_ledger.py']
    if any(science.get(str(p))!=digest(p) for p in sources):raise ValueError('hidden test method was not frozen before main')
    controls=published(lock['hidden_controls_result'],plan['repository'])
    if controls.get('status')!='PASS' or controls.get('cleanup_verified') is not True:raise ValueError('independent hidden controls unavailable')
    config=lock['configuration'];inputs=read(lock['inputs']);allowed=Path(config['test_ids']).read_text().splitlines()
    validate(inputs,allowed)
    if set(allowed)!={t['task_id'] for t in tasks} or any(inputs[k]!=selection['run'][k] for k in ('arm','run_seed','boundary')):
        raise ValueError('hidden coverage population differs from selected checkpoint')
    verify_evidence(inputs,tasks,data,score_lock['configuration']['root'],selection['run'])
    refs=[lock['inputs'],reference(Path(config['test_ids']))]
    for cell in inputs['cells']:
        strict=read(cell['strict'])
        refs += [cell['strict'],cell['suite'],strict['strict_receipt']]
        refs += [ref for ref in (cell.get('source'),strict.get('oracle_receipt')) if ref]
    if any(bound.get(ref['path'])!=ref['sha256'] for ref in refs):raise ValueError('hidden coverage physical input unbound')
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    with (root/'controller.lock').open('a') as controller:
        fcntl.flock(controller,fcntl.LOCK_EX)
        final=root/'terminal.json'
        if final.exists():
            result=json.loads(final.read_text())
            if result['execution_sha256']!=plan['lock']['sha256'] or result['rows_sha256']!=digest(root/'rows.json'):
                raise ValueError('completed selected-test hidden result changed')
            return result
        attempt=root/'parent_attempt.json';resumed=attempt.exists();identity={'lock':plan['lock'],'automatic_retry':False}
        if resumed:
            if json.loads(attempt.read_text())!=identity:raise ValueError('selected-test hidden parent changed')
        else:write_new(attempt,identity)
        before=cost_snapshot(root);Path(config['controller_fence']).parent.mkdir(parents=True,exist_ok=True)
        with Path(config['controller_fence']).open('a') as fence:
            fcntl.flock(fence,fcntl.LOCK_EX);slots=MemorySlots()
            with ThreadPoolExecutor(max_workers=8) as pool:
                rows=list(pool.map(lambda pair:score_cell(pair[1],pair[0],config,plan['lock']['sha256'],slots),enumerate(inputs['cells'])))
        if (root/'rows.json').exists():
            if json.loads((root/'rows.json').read_text())!=rows:raise ValueError('retained hidden rows changed')
        else:write_new(root/'rows.json',rows)
        cost=stage_cost(before,cost_snapshot(root),stage='selected_test_hidden');cost['cumulative_timing_complete']=not resumed
        if not (root/'cost.json').exists():write_new(root/'cost.json',cost)
        result={'condition':'v2-S2','stage':'SELECTED_TEST_HIDDEN','status':'ACCOUNTED',**selection['run'],
            'L2_sha256':selection['L2']['sha256'],'model_binding_sha256':score['model_binding_sha256'],
            'execution_sha256':plan['lock']['sha256'],'declared':222,'accounted':len(rows),'rows_sha256':digest(root/'rows.json'),
            'cleanup_unresolved':sum(r.get('cleanup_verified') is not True for r in rows),'automatic_retries':0,
            'rows':reference(root/'rows.json'),'cost':reference(root/'cost.json')}
        write_new(final,result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job',required=True,type=Path);worker(p.parse_args().job)
