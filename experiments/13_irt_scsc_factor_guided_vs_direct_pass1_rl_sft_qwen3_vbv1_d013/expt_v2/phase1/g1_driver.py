"""Run G1 once after publication, fixed Phase 1 prerequisites and complete input verification."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import importlib.metadata
import platform
from pathlib import Path
import subprocess
import time
import traceback

from panel import digest, write_new
from g1_inputs import load, verify_bindings
from nested_a3 import run_forecast


def verify_publication(path, repository, revision):
    path, repository = Path(path).resolve(), Path(repository).resolve()
    subprocess.run(['git','merge-base','--is-ancestor',revision,'origin/main'],
                   cwd=repository,check=True,capture_output=True)
    blob=subprocess.check_output(['git','show',revision+':'+str(path.relative_to(repository))],cwd=repository)
    if hashlib.sha256(blob).hexdigest()!=digest(path):
        raise ValueError('fit lock differs from its published bytes')
    return json.loads(blob)


def verify_fit_lock(path, repository, revision):
    lock=verify_publication(path,repository,revision)
    if lock.get('gate')!='G1' or lock.get('status')!='FROZEN':
        raise ValueError('G1 final lock required before any fit')
    if lock.get('completion_refits') is not False or lock['bootstrap']['draws']!=10000:
        raise ValueError('G1 fixed-forecast/bootstrap contract changed')
    for name,version in lock['library_versions'].items():
        actual=platform.python_version() if name=='python' else importlib.metadata.version(name)
        if actual!=version:raise ValueError('frozen fitting library changed: '+name)
    bound={}
    for b in lock['bindings']:
        p=Path(b['path']);p=p if p.is_absolute() else Path(repository)/p
        if digest(p)!=b['sha256']:raise ValueError('G1 implementation hash mismatch: '+str(p))
        bound[str(p.resolve())]=b['sha256']
    required={Path(__file__).resolve(),Path(__file__).with_name('g1_inputs.py').resolve(),
              Path(__file__).with_name('nested_a3.py').resolve(),Path(__file__).with_name('g1_bounds.py').resolve()}
    if not required <= {Path(p) for p in bound}:raise ValueError('G1 execution bindings absent')
    paths=verify_bindings(lock['input_bindings'])
    # These are non-test local source inputs already prepared before outcomes.
    for b in json.loads(paths['source_features'].read_text()):
        if digest(b['path'])!=b['sha256']:raise ValueError('feature source changed')
    return lock,paths


def check_order(prerequisites, lock):
    """Later results can be produced after the method freeze; bind them before fitting."""
    if set(prerequisites)!={'lp1','calibration','batch2'}:
        raise ValueError('G1 requires LP-1, frozen calibration and independent batch 2')
    values={}
    for name,b in prerequisites.items():
        if digest(b['path'])!=b['sha256']:raise ValueError('prerequisite hash mismatch: '+name)
        values[name]=json.loads(Path(b['path']).read_text())
    if (values['lp1'].get('status')!='PASS' or
            values['lp1'].get('admission_statistics_computed') is not True):
        raise ValueError('LP-1 did not pass its statistics')
    calibration=values['calibration'];batch2=values['batch2']
    if calibration.get('status')!='FROZEN' or 'F2' not in calibration:
        raise ValueError('calibration/items/F2 not frozen')
    if calibration.get('g1_lock_sha256')!=lock['self_sha256']:
        raise ValueError('calibration fit did not follow this published G1 method')
    if (batch2.get('status') not in ('COMPLETE','INCOMPLETE') or batch2.get('batch')!='full2'
            or batch2.get('declared')!=539*8 or batch2.get('accounted')!=539*8):
        raise ValueError('independent full batch 2 is not fully accounted')
    if batch2.get('calibration_sha256')!=prerequisites['calibration']['sha256']:
        raise ValueError('batch 2 did not bind the calibration freeze')
    return values


def json_safe(value):
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [json_safe(v) for v in value]
    if hasattr(value,'tolist'):return json_safe(value.tolist())
    if isinstance(value,float) and not math.isfinite(value):return None
    return value


def combined_status(outputs):
    required={'grouped_tasks','full_schedule_policies'}
    if set(outputs)!=required:raise ValueError('both frozen G1 holdout schemes required')
    statuses=[o['evaluation']['status'] for o in outputs.values()]
    if 'FAIL' in statuses:return 'FAIL'
    return 'PASS' if statuses==['PASS','PASS'] else 'INCONCLUSIVE'


def run(lock_path, repository, revision, prerequisites_path, root):
    lock,paths=verify_fit_lock(lock_path,repository,revision)
    lock['self_sha256']=digest(lock_path)
    prerequisites=json.loads(Path(prerequisites_path).read_text())
    for b in prerequisites.values():
        verify_publication(b['path'],repository,b['published_revision'])
    check_order(prerequisites,lock)
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    write_new(root/'attempt.json',{'started_unix':time.time(),'lock_sha256':lock['self_sha256'],
              'revision':revision,'prerequisites':prerequisites,'retries':0,'completion_refits':False})
    result={'gate':'G1','status':'INCONCLUSIVE','disable_arm_C':True,'retries':0,'completion_refits':False}
    try:
        systems=json.loads(paths['policy_metadata'].read_text())['systems']
        rows,excluded,groups=load(lock['input_bindings'],systems)
        source=json.loads(paths['validation_features'].read_text())
        if set(source)!=set(groups) or any(source[t]['group_id']!=groups[t] for t in groups):
            raise ValueError('feature task/group denominator differs from prediction grid')
        features={t:source[t]['features'] for t in source}
        def sink(forecasts):
            write_new(root/(forecasts['scheme']+'.forecasts.json'),json_safe(forecasts))
        outputs=run_forecast(rows,systems,features,groups,excluded_ids=excluded,
                             draws=lock['bootstrap']['draws'],forecast_sink=sink)
        status=combined_status(outputs)
        write_new(root/'outputs.json',json_safe(outputs))
        result.update(status=status,disable_arm_C=status!='PASS',declared_historical_cells=len(rows),
                      excluded_alias_cells=len(excluded),tasks=len(groups),
                      schemes={name:data['evaluation'] for name,data in outputs.items()},
                      outputs_sha256=digest(root/'outputs.json'))
    except BaseException as exc:
        (root/'error.txt').write_text(traceback.format_exc())
        result.update(error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        write_new(root/'result.json',json_safe(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('lock','repository','prerequisites','root'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--published-revision',required=True)
    args=p.parse_args()
    print(json.dumps(run(args.lock,args.repository,args.published_revision,args.prerequisites,args.root),allow_nan=False))
