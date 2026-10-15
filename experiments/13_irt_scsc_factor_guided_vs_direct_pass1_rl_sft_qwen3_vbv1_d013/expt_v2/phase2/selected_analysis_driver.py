"""Join every frozen main arm and seed to its selected-test evidence before the single exploratory analysis."""
from __future__ import annotations

import json
from pathlib import Path

from selected_test_analysis import evaluate,validate,SEEDS
from evaluation_contract import identities
from technical_ledger import published
from technical_driver import read
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def missing(tasks,arm,seed,reason,*,boundary=None):
    if not isinstance(reason,str) or not reason:raise ValueError('unmeasured run needs its retained reason')
    return [{'condition':'v2-S2','arm':arm,'run_seed':seed,'task_id':t['task_id'],'split':'test',
        'sample_idx':sample,'boundary':boundary,'strict':None,'status':'not_evaluated','reason':reason}
        for t in tasks for sample in range(16)]


def collect(runs,tasks,arms,L2_sha,contract_sha,repository):
    expected={(arm,seed) for arm in arms for seed in SEEDS}
    if len(runs)!=len(expected) or {(r['arm'],r['run_seed']) for r in runs}!=expected:
        raise ValueError('all declared paired main arm/seed blocks must remain accounted')
    rows=[];sources=[];availability=[]
    for run in runs:
        arm=run['arm'];seed=run['run_seed'];main=published(run['main_result'],repository)
        if any(main.get(k)!=v for k,v in {'condition':'v2-S2','stage':'MAIN_TRAINING','arm':arm,'run_seed':seed,'L2_sha256':L2_sha}.items()):
            raise ValueError('main report belongs to another declared execution')
        sources.append(run['main_result']);reason=None;boundary=None
        if main['status']!='COMPLETE':
            if main['status'] not in ('HALTED','RESOURCE_EXHAUSTED','NOT_STARTED'):
                raise ValueError('main run is not terminal')
            if run.get('selection') or run.get('test_score'):raise ValueError('failed main run cannot supply a selected test checkpoint')
            if main['status']=='NOT_STARTED':
                stop=published(main['blocked_by'],repository)
                if stop.get('L2_sha256')!=L2_sha or stop.get('status') not in ('HALTED','RESOURCE_EXHAUSTED','FAIL','INCONCLUSIVE'):
                    raise ValueError('unstarted main run lacks its published same-execution stop')
                sources.append(main['blocked_by'])
            reason='main '+main['status']
        else:
            if main.get('cleanup_unresolved')!=0:raise ValueError('completed main run has unresolved cleanup')
            selected=published(run['selection'],repository);sources.append(run['selection'])
            if any(selected.get(k)!=v for k,v in {'gate':'VALIDATION_SELECTION','condition':'v2-S2','arm':arm,'run_seed':seed,
                    'L2_sha256':L2_sha,'evaluation_contract_sha256':contract_sha}.items()):
                raise ValueError('selected test checkpoint belongs to another main run')
            if selected['status']=='INCONCLUSIVE':
                if run.get('test_score'):raise ValueError('unresolved selection cannot supply test scores')
                reason='validation checkpoint selection INCONCLUSIVE'
            elif selected['status']!='SELECTED':raise ValueError('validation selection is not final')
            else:
                boundary=selected['boundary'];model=main['boundaries'][str(boundary)]
                if selected['model_binding_sha256']!=model['model_binding_sha256'] or selected['boundary_receipt_sha256']!=model['sha256']:
                    raise ValueError('selected checkpoint differs from its retained main boundary')
                if run.get('test_score') is None:
                    unavailable=published(run['unavailable'],repository);sources.append(run['unavailable'])
                    if any(unavailable.get(k)!=v for k,v in {'stage':'SELECTED_TEST_UNAVAILABLE','condition':'v2-S2','status':'NOT_EVALUATED',
                            'arm':arm,'run_seed':seed,'boundary':boundary,'L2_sha256':L2_sha}.items()):
                        raise ValueError('selected test unavailable receipt belongs to another checkpoint')
                    reason=unavailable['reason']
                else:
                    score=published(run['test_score'],repository);sources.append(run['test_score'])
                    expected_score={'stage':'SELECTED_TEST_SCORE','condition':'v2-S2','arm':arm,'run_seed':seed,'boundary':boundary,
                        'L2_sha256':L2_sha,'evaluation_contract_sha256':contract_sha,'model_binding_sha256':model['model_binding_sha256'],
                        'boundary_receipt_sha256':model['sha256'],'cleanup_unresolved':0}
                    if any(score.get(k)!=v for k,v in expected_score.items()) or score.get('status') not in ('COMPLETE','INCOMPLETE'):
                        raise ValueError('selected-test score differs from its clean selected checkpoint')
                    data=read(score['scoring']);sources.append(score['scoring'])
                    if digest(score['scoring']['path'])!=score['scoring_sha256']:raise ValueError('selected-test raw scoring changed')
                    population=identities(sorted(t['task_id'] for t in tasks),'test',arm=arm,run_seed=seed,boundary=boundary)
                    table={r['cell_id']:r for r in data['rows']}
                    if len(table)!=3552 or len(data['rows'])!=3552 or set(table)!={c['cell_id'] for c in population}:
                        raise ValueError('selected-test raw scoring omitted declared cells')
                    known=successes=0
                    for cell in population:
                        row=table[cell['cell_id']]
                        if any(row.get(k)!=cell[k] for k in ('cell_id','task_id','sample_idx','split','arm','run_seed','boundary')):
                            raise ValueError('selected-test raw cell crossed its run or checkpoint')
                        strict=row.get('strict')
                        if row['status']!='measured' and strict is not None:raise ValueError('unmeasured selected-test cell has an imputed outcome')
                        known+=strict is not None;successes+=strict or 0
                        rows.append({**row,'condition':'v2-S2'})
                    summary=score['summary']
                    if (summary['declared'],summary['measured'],summary['missing'],summary['successes'],summary['task_count'],summary['samples_per_task'])!=(3552,known,3552-known,successes,222,16):
                        raise ValueError('selected-test summary differs from retained cells')
        if reason:rows.extend(missing(tasks,arm,seed,reason,boundary=boundary))
        availability.append({'arm':arm,'run_seed':seed,'boundary':boundary,'not_evaluated_reason':reason})
    validate(rows,tasks,arms);return rows,sources,availability


def run(plan):
    repo=plan['repository'];inputs=published(plan['inputs'],repo);method=published(inputs['method'],repo);main=published(inputs['L2'],repo)
    if (inputs.get('gate'),inputs.get('condition'),inputs.get('status'))!=('SELECTED_TEST_ANALYSIS_INPUTS','v2-S2','FROZEN'):
        raise ValueError('published selected-test analysis input lock required')
    if (method.get('gate'),method.get('condition'),method.get('status'))!=('SELECTED_TEST_ANALYSIS','v2-S2','FROZEN'):
        raise ValueError('published pre-main test-analysis method required')
    bound={b['path']:b['sha256'] for b in inputs['bindings']};science={b['path']:b['sha256'] for b in main['bindings']}
    method_bound={b['path']:b['sha256'] for b in method['bindings']}
    if len(method_bound)!=len(method['bindings']) or any(digest(p)!=sha for p,sha in method_bound.items()):
        raise ValueError('pre-main test-analysis binding changed')
    if method_bound.get(method['tasks']['path'])!=method['tasks']['sha256']:
        raise ValueError('test population metadata must be bound before main')
    if len(bound)!=len(inputs['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('selected-test input changed')
    if science.get(inputs['method']['path'])!=inputs['method']['sha256']:raise ValueError('test-analysis method was not frozen before main')
    for path in (Path(__file__).resolve(),HERE/'selected_test_analysis.py',HERE/'evaluation_contract.py'):
        if science.get(str(path))!=digest(path) or method_bound.get(str(path))!=digest(path):raise ValueError('test-analysis implementation changed after main')
    if (main.get('gate'),main.get('condition'),main.get('status'))!=('L2','v2-S2','FROZEN'):
        raise ValueError('main execution is not frozen')
    if method['arms']!=main['eligible_arms'] or method['seeds']!=list(SEEDS) or main['main_seeds']!=list(SEEDS) or method['bootstrap_seed']!=1302301:
        raise ValueError('pre-main paired analysis population or randomness changed')
    tasks=read(method['tasks']);rows,sources,availability=collect(inputs['runs'],tasks,method['arms'],inputs['L2']['sha256'],digest(HERE/'evaluation_contract.py'),repo)
    if any(bound.get(ref['path'])!=ref['sha256'] for ref in sources):raise ValueError('analysis omitted published or raw outcome bindings')
    root=Path(plan['output']);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'attempt.json',{'condition':'v2-S2','method':inputs['method'],'inputs':plan['inputs'],'automatic_retry':False})
    write_new(root/'rows.json',rows)
    result=evaluate(rows,tasks,method['arms'],bootstrap_seed=method['bootstrap_seed'])
    result.update(stage='SELECTED_TEST_ANALYSIS',method_sha256=inputs['method']['sha256'],inputs_sha256=plan['inputs']['sha256'],
        L2_sha256=inputs['L2']['sha256'],run_availability=availability,rows_sha256=digest(root/'rows.json'))
    write_new(root/'result.json',result);return result
