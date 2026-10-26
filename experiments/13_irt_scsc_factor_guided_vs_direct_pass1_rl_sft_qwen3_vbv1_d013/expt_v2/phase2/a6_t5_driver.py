"""Evaluate adopted A6 T5 once on B own-reward receipts; A pilot lengths remain a separate token-budget input."""
from __future__ import annotations

import json
from pathlib import Path
import time
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'reproduction'))

from technical_ledger import published
from technical_driver import read
from a6_t5_measurement import evaluate as t5
from cell_worker import family_reward
from schedule import pilot_token_budget
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def validate_updates(entries,horizon):
    expected={(seed,update) for seed in (1301,) for update in range(1,horizon+1)}
    if len(entries)!=len(expected) or {(e['seed'],e['update']) for e in entries}!=expected:
        raise ValueError('complete fixed B pilot opportunity inventory required')
    rows=[];lengths=[]
    for entry in sorted(entries,key=lambda e:(e['seed'],e['update'])):
        row=read(entry['summary']);generation=read(entry['generation']);scoring=read(entry['scoring'])
        identity={'arm':'B','seed':entry['seed'],'update':entry['update'],'split':'train','declared':256}
        if any(row.get(k)!=v for k,v in identity.items()) or row.get('status')!='ACCOUNTED':
            raise ValueError('pilot summary identity changed')
        if row['scoring']!=entry['scoring'] or generation.get('status')!='COMPLETE' or generation.get('completed')!=256:
            raise ValueError('pilot generation or score receipt is incomplete')
        cells=scoring['rows'];files=entry['generation_files']
        if len(cells)!=256 or len(files)!=256 or len({r['cell_id'] for r in cells})!=256:
            raise ValueError('pilot full-slot denominator changed')
        if any(c.get('cleanup_verified') is not True for c in cells):raise ValueError('pilot scorer cleanup unresolved')
        table={r['cell_id']:r for r in cells};observed=[];current=[];seen=set()
        for reference in files:
            value=read(reference);key=value['cell_id'];tokens=value['output_token_ids']
            if key not in table or key in seen:raise ValueError('pilot generation cell inventory changed')
            seen.add(key);score=table[key]
            wanted={'arm':'B','run_seed':entry['seed'],'update':entry['update'],'split':'train'}
            if any(value.get(k)!=v or score.get(k)!=v for k,v in wanted.items()):raise ValueError('pilot cell belongs to another opportunity')
            if any(score.get(k)!=value.get(k) for k in ('task_id','sample','group_index')):raise ValueError('pilot score and response identity differ')
            if not 1<=len(tokens)<=8192:raise ValueError('pilot token length missing or invalid')
            current.append(len(tokens))
            if score['status']=='measured':
                if type(score.get('strict')) not in (int,bool) or score['strict'] not in (0,1):raise ValueError('measured pilot strict outcome is not binary')
                observed.append(score['strict'])
        if (row['measured']!=len(observed) or row['strict_successes']!=sum(observed)
                or row['generated_tokens']!=sum(current) or generation['generated_tokens']!=sum(current)):
            raise ValueError('pilot aggregate differs from retained cells')
        opportunity=read(entry['opportunity'])
        if (opportunity.get('status')!='ACCOUNTED' or opportunity.get('arm')!='B'
                or opportunity.get('run_seed')!=entry['seed'] or opportunity.get('update')!=entry['update']
                or opportunity.get('optimizer_updates') not in (0,1)):
            raise ValueError('pilot opportunity did not close')
        required={'generate','update'}|({'export'} if opportunity['optimizer_updates'] else set())
        if set(entry['closed_stages'])!=required:raise ValueError('pilot device stage inventory changed')
        for stage,ref in entry['closed_stages'].items():
            closed=read(ref)
            if (closed.get('status')!='RUNTIME_EXITED_ZERO' or closed.get('cleanup_verified') is not True
                    or closed.get('arm')!='B' or closed.get('run_seed')!=entry['seed'] or closed.get('update')!=entry['update']):
                raise ValueError('pilot device stage is not cleanly closed')
        own=read(row['groups']);flat=[r for group in own for r in group['rows']]
        if len(flat)!=256 or {r['cell_id']for r in flat}!=set(table):raise ValueError('B own reward slots changed')
        values=[]
        for r in flat:
            cell=table[r['cell_id']]
            if any(r.get(k)!=cell.get(k) for k in ('task_id','sample','group_index','arm','run_seed','update','split')):raise ValueError('B own reward identity changed')
            value=family_reward(cell,cell['strict'])if cell['status']=='measured'else None
            if r['reward']!=value or r['score_status']!=cell['status']:raise ValueError('B own reward differs from fixed reward function')
            values.append(value)
        rows.append({**row,'rewards':values});lengths.extend(current)
    return rows,lengths


def run(plan):
    repository=plan['repository'];lock=published(plan['lock'],repository)
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('T5_INPUTS','v2-S2','FROZEN'):
        raise ValueError('published learning-pilot gate input lock required')
    pilot=published(lock['pilot_execution_lock'],repository)
    if (pilot.get('gate'),pilot.get('condition'),pilot.get('status'))!=('LEARNING_PILOT','v2-S2','FROZEN'):
        raise ValueError('fixed learning pilot was not admitted')
    science={b['path']:b['sha256'] for b in pilot['bindings']}
    for path in (Path(__file__).resolve(),HERE/'a6_t5_measurement.py',HERE/'schedule.py',HERE.parent/'reproduction/cell_worker.py'):
        if science.get(str(path))!=digest(path):raise ValueError('T5 method was not frozen before learning')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('T5 input binding changed')
    config=lock['configuration'];horizon=config['horizon']
    if horizon not in (30,60):raise ValueError('undeclared pilot horizon')
    if horizon==60:
        previous=published(lock['extension_admission'],repository)
        if (previous.get('gate')!='T5' or previous.get('status')!='EXTEND_TO_60' or previous.get('horizon')!=30
                or previous.get('pilot_execution_sha256')!=lock['pilot_execution_lock']['sha256']
                or previous.get('arm')!='B' or previous.get('seeds')!=[1301] or previous.get('metric')!='own train reward'):
            raise ValueError('B pilot extension was not admitted by its final 30-update result')
    elif lock.get('extension_admission') is not None:raise ValueError('initial T5 cannot import an extension')
    inputs=read(config['inputs'])
    if bound.get(config['inputs']['path'])!=config['inputs']['sha256']:raise ValueError('T5 full input inventory is unbound')
    if set(inputs['states'])!={'1301'}:raise ValueError('both fixed B pilot states required')
    for seed,ref in inputs['states'].items():
        if bound.get(ref['path'])!=ref['sha256']:raise ValueError('pilot state copy is unbound')
        state=read(ref)
        expected={'condition':'v2-S2','arm':'B','run_seed':int(seed),'phase':'pilot','status':'WAIT_FOR_T5',
                  'completed_updates':horizon,'execution_sha256':lock['pilot_execution_lock']['sha256']}
        if any(state.get(k)!=v for k,v in expected.items()):raise ValueError('pilot is not paused at its fixed T5 horizon')
    for entry in inputs['updates']:
        for ref in [entry[k] for k in ('summary','generation','scoring','opportunity')]+entry['generation_files']+list(entry['closed_stages'].values()):
            if bound.get(ref['path'])!=ref['sha256']:raise ValueError('pilot measurement source is unbound')
    for entry in inputs['updates']:
        summary=read(entry['summary']);ref=summary['groups']
        if bound.get(ref['path'])!=ref['sha256']:raise ValueError('B own reward groups unbound')
    rows,lengths=validate_updates(inputs['updates'],horizon)
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    write_new(root/'evaluation_attempt.json',{'condition':'v2-S2','lock_sha256':plan['lock']['sha256'],
        'started_unix':time.time(),'automatic_retry':False})
    result=t5(rows,horizon=horizon)
    result.update(pilot_execution_sha256=lock['pilot_execution_lock']['sha256'],input_lock_sha256=plan['lock']['sha256'],
        LP_sha256=pilot['LP_sha256'],pilot_slots=len(lengths),pilot_generated_tokens=sum(lengths),
        token_budget=None,token_budget_required='separately bound full A pilot lengths, unchanged rule')
    write_new(root/'result.json',result);return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(run(json.loads(args.plan.read_text())),sort_keys=True))
