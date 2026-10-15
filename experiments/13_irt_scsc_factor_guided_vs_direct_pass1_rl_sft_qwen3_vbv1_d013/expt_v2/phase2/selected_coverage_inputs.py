"""Retain the preselected sample-zero test population and exact official evidence before independent coverage."""
from __future__ import annotations

import json
from pathlib import Path

from evaluation_contract import identities
from technical_ledger import published
from technical_driver import read,reference
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent
IDENTITY=('cell_id','task_id','sample_idx','split','arm','run_seed','boundary')


def authority(plan):
    """Require completed selected-test scoring and the independent sample choice frozen before main."""
    repo=plan['repository'];main=published(plan['L2'],repo);method=published(plan['method'],repo)
    selection=published(plan['selection'],repo);score=published(plan['score'],repo)
    lock=published(plan['score_lock'],repo)
    if (main.get('gate'),main.get('condition'),main.get('status'))!=('L2','v2-S2','FROZEN'):
        raise ValueError('published main execution required')
    if (method.get('gate'),method.get('condition'),method.get('status'))!=('SELECTED_TEST_ANALYSIS','v2-S2','FROZEN'):
        raise ValueError('pre-main selected-test analysis method required')
    bound={b['path']:b['sha256'] for b in main['bindings']}
    for ref in (plan['method'],reference(Path(__file__).resolve()),reference(HERE/'evaluation_contract.py')):
        if bound.get(ref['path'])!=ref['sha256']:raise ValueError('coverage method was not frozen before main')
    method_bound={b['path']:b['sha256'] for b in method['bindings']}
    if any(digest(p)!=sha for p,sha in method_bound.items()):raise ValueError('pre-main analysis binding changed')
    if method_bound.get(method['tasks']['path'])!=method['tasks']['sha256']:
        raise ValueError('test task metadata was not frozen before main')
    if method.get('independent_coverage',{}).get('sample_idx')!=0 or method['independent_coverage'].get('tasks_per_run')!=222:
        raise ValueError('independent coverage must retain the prospective sample zero')
    tasks=read(method['tasks']);names=[t['task_id'] for t in tasks]
    if len(names)!=222 or len(set(names))!=222:raise ValueError('complete 222-task test population required')
    expected={'condition':'v2-S2','L2_sha256':plan['L2']['sha256'],
        'evaluation_contract_sha256':digest(HERE/'evaluation_contract.py'),**plan['run']}
    if set(plan['run'])!={'arm','run_seed','boundary'}:raise ValueError('exact selected checkpoint identity required')
    if plan['run']['arm'] not in main['eligible_arms'] or plan['run']['run_seed'] not in main['main_seeds']:
        raise ValueError('selected checkpoint outside the frozen main population')
    if any(selection.get(k)!=v or score.get(k)!=v for k,v in expected.items()):
        raise ValueError('coverage belongs to another selected main checkpoint')
    if selection.get('gate')!='VALIDATION_SELECTION' or selection.get('status')!='SELECTED':
        raise ValueError('final selected checkpoint required')
    if score.get('stage')!='SELECTED_TEST_SCORE' or score.get('status') not in ('COMPLETE','INCOMPLETE') or score.get('cleanup_unresolved')!=0:
        raise ValueError('complete clean test scoring accounting required')
    for key in ('model_binding_sha256','boundary_receipt_sha256'):
        if score[key]!=selection[key]:raise ValueError('coverage model differs from selected checkpoint')
    if (lock.get('gate')!='EVALUATION_SCORE_INPUTS' or lock.get('status')!='FROZEN'
            or lock.get('purpose')!='test' or score['scoring_lock_sha256']!=plan['score_lock']['sha256']):
        raise ValueError('selected scoring input lock required')
    for key in ('condition','L2_sha256','arm','run_seed','boundary','model_binding_sha256','snapshot_sha256'):
        if lock.get(key)!=score.get(key):raise ValueError('coverage scoring source crosses checkpoints')
    if any(digest(b['path'])!=b['sha256'] for b in lock['bindings']):raise ValueError('selected scoring binding changed')
    if score['scoring_sha256']!=score['scoring']['sha256']:raise ValueError('test scoring digest changed')
    data=read(score['scoring'])
    return tasks,score,lock,data


def normalize(tasks,scoring,score_root,run,*,output):
    """Use every fixed sample zero, including unavailable responses; never choose by observed correctness."""
    if len(tasks)!=222 or len({t['task_id'] for t in tasks})!=222 or any(t.get('split')!='test' for t in tasks):
        raise ValueError('complete unique test metadata required')
    population=identities(sorted(t['task_id'] for t in tasks),'test',**run)
    rows=scoring['rows'];table={r['cell_id']:r for r in rows}
    if len(rows)!=3552 or len(table)!=3552 or set(table)!={c['cell_id'] for c in population}:
        raise ValueError('full selected-test scoring population required')
    metadata={t['task_id']:t for t in tasks};normalized=[];pending=[]
    for index,cell in enumerate(population):
        row=table[cell['cell_id']]
        if any(row.get(k)!=cell[k] for k in IDENTITY):raise ValueError('selected-test scoring identity changed')
        if row.get('cleanup_verified') is not True:raise ValueError('selected-test cleanup unresolved')
        if cell['sample_idx']!=0:continue
        folder=Path(score_root)/f'{index:05d}';saved=folder/'result.json'
        if json.loads(saved.read_text())!=row:raise ValueError('test cell differs from its saved scoring result')
        source=None;oracle=None;compiled=None;frontend=None
        if row.get('attempts',0):
            attempt=folder/f"attempt_{row['attempts']}";candidate=attempt/'solution.lean'
            if candidate.exists():source=reference(candidate)
            if row['status']=='measured':
                if source is None or source['sha256']!=row['source_sha256']:raise ValueError('official test candidate changed')
                oracle=reference(attempt/'evidence/oracle/oracle.json');raw=read(oracle)
                if type(raw.get('compile')) is not bool or raw['compile'] is not row['compile']:
                    raise ValueError('official test compilation evidence changed')
                compiled=raw['compile']
                path=attempt/'evidence/components/frontend.json'
                if path.exists():frontend=reference(path)
        if row['status']=='measured' and compiled is None:raise ValueError('measured test cell lacks its attempt evidence')
        strict={**row,'compile':compiled,'strict_receipt':reference(saved),'oracle_receipt':oracle,'frontend':frontend}
        pending.append(strict)
        normalized.append({**cell,'group_id':metadata[cell['task_id']]['group_id'],'source':source})
    if len(normalized)!=222:raise ValueError('fixed independent sample population changed')
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    for index,(cell,strict) in enumerate(zip(normalized,pending)):
        path=root/f'{index:03d}.strict.json';write_new(path,strict);cell['strict']=reference(path)
    result={'condition':'v2-S2','stage':'SELECTED_TEST_COVERAGE_INPUTS',**run,'split':'test',
        'declared':222,'sample_idx':0,'cells':normalized,'new_strict_measurements':0,'model_calls':0,
        'missing_sample_replacement':False}
    write_new(root/'inputs.json',result);return result


def prepare(plan):
    tasks,score,lock,data=authority(plan)
    result=normalize(tasks,data,lock['configuration']['root'],plan['run'],output=plan['output'])
    provenance={key:plan[key] for key in ('L2','method','selection','score','score_lock')}
    provenance.update(model_binding_sha256=score['model_binding_sha256'],scoring=score['scoring'],
        inputs=reference(Path(plan['output'])/'inputs.json'),required_next='publish independent coverage input lock before any hidden-test or hosted-judge measurement')
    write_new(Path(plan['output'])/'provenance.json',provenance)
    return result
