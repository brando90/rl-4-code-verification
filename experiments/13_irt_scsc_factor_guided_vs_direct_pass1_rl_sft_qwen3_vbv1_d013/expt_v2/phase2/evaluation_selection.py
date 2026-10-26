"""Bind all four published validation reports to one main run before selecting any test checkpoint."""
from __future__ import annotations

import json
from pathlib import Path

from evaluation_contract import select
from technical_ledger import published
from training_checkpoint import digest,write_new


def evaluate(reports,*,arm,run_seed,LP_sha256,L2_sha256,contract_sha256):
    if arm not in ('A','B','C','P') or run_seed not in (13011,13012,13013):raise ValueError('undeclared main run')
    if len(reports)!=4 or {r['boundary'] for r in reports}!={1,2,3,4}:raise ValueError('four complete validation reports required')
    for report in reports:
        expected={'condition':'v2-S2','stage':'VALIDATION_SCORE','arm':arm,'run_seed':run_seed,
                  'LP_sha256':LP_sha256,'L2_sha256':L2_sha256,'evaluation_contract_sha256':contract_sha256}
        if any(report.get(k)!=v for k,v in expected.items()):raise ValueError('validation reports cross runs or frozen settings')
        if report.get('cleanup_unresolved')!=0:raise ValueError('validation cleanup unresolved')
        for key in ('generation_sha256','scoring_sha256','model_binding_sha256','boundary_receipt_sha256'):
            value=report.get(key)
            if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('validation measurement provenance missing')
    result=select([{'boundary':r['boundary'],'summary':r['summary']} for r in reports])
    chosen=next((r for r in reports if r['boundary']==result['boundary']),None)
    return {**result,'gate':'VALIDATION_SELECTION','arm':arm,'run_seed':run_seed,
            'LP_sha256':LP_sha256,'L2_sha256':L2_sha256,'evaluation_contract_sha256':contract_sha256,
            'model_binding_sha256':chosen['model_binding_sha256'] if chosen else None,
            'boundary_receipt_sha256':chosen['boundary_receipt_sha256'] if chosen else None,
            'all_four_validation_summaries':[{'boundary':r['boundary'],'summary':r['summary']} for r in sorted(reports,key=lambda x:x['boundary'])],
            'test_admitted':False,'required_next':'publish selection, then bind selected checkpoint and pre-main analysis lock to the separate test execution manifest'}


def run(plan):
    repo=plan['repository'];lock=published(plan['lock'],repo)
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('VALIDATION_SELECTION_METHOD','v2-S2','FROZEN'):
        raise ValueError('selection method must be frozen before validation outcomes')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    for path,sha in bound.items():
        if digest(path)!=sha:raise ValueError('selection method binding changed')
    here=Path(__file__).resolve().parent
    if any(bound.get(str(p))!=digest(p) for p in (Path(__file__).resolve(),here/'evaluation_contract.py',here/'technical_ledger.py',here/'training_checkpoint.py')):
        raise ValueError('selection executable is unbound')
    main_lock=published(plan['L2'],repo)
    if (plan['L2']['sha256']!=lock['L2_sha256'] or main_lock.get('gate')!='L2'
            or main_lock.get('status')!='FROZEN' or main_lock.get('condition')!='v2-S2'
            or main_lock.get('LP_sha256')!=lock['LP_sha256']):
        raise ValueError('selection method is detached from the frozen main execution')
    main_bindings={b['path']:b['sha256'] for b in main_lock['bindings']}
    for path in (Path(__file__).resolve(),here/'evaluation_contract.py'):
        if main_bindings.get(str(path))!=digest(path):raise ValueError('selection implementation was not frozen before main')
    if lock['evaluation_contract_sha256']!=digest(here/'evaluation_contract.py'):
        raise ValueError('selection contract identity changed')
    run=plan['run'];main=published(plan['main_result'],repo)
    if any(main.get(k)!=v for k,v in {'condition':'v2-S2','stage':'MAIN_TRAINING','status':'COMPLETE','arm':run['arm'],'run_seed':run['run_seed'],'L2_sha256':lock['L2_sha256']}.items()):
        raise ValueError('complete main training receipt required')
    if main.get('boundaries_accounted')!=4:raise ValueError('all four main token checkpoints required')
    reports=[published(ref,repo) for ref in plan['validation_results']]
    for report in reports:
        key=str(report['boundary']);boundary=main['boundaries'][key]
        if report['boundary_receipt_sha256']!=boundary['sha256'] or report['model_binding_sha256']!=boundary['model_binding_sha256']:
            raise ValueError('validation model is detached from the admitted main run')
    root=Path(plan['output']);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'attempt.json',{'condition':'v2-S2','method':plan['lock'],'main':plan['main_result'],
        'validation_results':plan['validation_results'],'automatic_retry':False})
    result=evaluate(reports,arm=run['arm'],run_seed=run['run_seed'],LP_sha256=lock['LP_sha256'],
        L2_sha256=lock['L2_sha256'],contract_sha256=lock['evaluation_contract_sha256'])
    result.update(method_lock_sha256=plan['lock']['sha256'],validation_results=plan['validation_results'])
    write_new(root/'result.json',result);return result
