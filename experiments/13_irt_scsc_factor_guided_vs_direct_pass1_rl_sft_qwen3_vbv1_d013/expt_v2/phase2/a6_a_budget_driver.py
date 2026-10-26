"""Evaluate the unchanged A-pilot token budget once from published complete opportunity and token receipts."""
from __future__ import annotations

import json
from pathlib import Path
import time

from technical_ledger import published
from technical_driver import read
from t5_driver import validate_updates
from schedule import pilot_token_budget
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def run(plan):
    repository=plan['repository'];lock=published(plan['lock'],repository)
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('A6_A_BUDGET_INPUTS','v2-S2','FROZEN'):
        raise ValueError('published learning-pilot gate input lock required')
    pilot=published(lock['pilot_execution_lock'],repository)
    if (pilot.get('gate'),pilot.get('condition'),pilot.get('status'))!=('LEARNING_PILOT','v2-S2','FROZEN'):
        raise ValueError('fixed learning pilot was not admitted')
    science={b['path']:b['sha256'] for b in pilot['bindings']}
    for path in (Path(__file__).resolve(),HERE/'t5_driver.py',HERE/'schedule.py'):
        if science.get(str(path))!=digest(path):raise ValueError('A-budget method was not frozen before learning')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('A-budget input binding changed')
    config=lock['configuration'];horizon=config['horizon']
    if horizon!=30 or lock.get('extension_admission') is not None:raise ValueError('A6 preserves both 30-update A pilots without extension')
    inputs=read(config['inputs'])
    if bound.get(config['inputs']['path'])!=config['inputs']['sha256']:raise ValueError('A-budget full input inventory is unbound')
    if set(inputs['states'])!={'1301','1302'}:raise ValueError('both fixed A pilot states required')
    for seed,ref in inputs['states'].items():
        if bound.get(ref['path'])!=ref['sha256']:raise ValueError('pilot state copy is unbound')
        state=read(ref)
        expected={'condition':'v2-S2','arm':'A','run_seed':int(seed),'phase':'pilot','status':'COMPLETE',
                  'completed_updates':horizon,'execution_sha256':lock['pilot_execution_lock']['sha256']}
        if any(state.get(k)!=v for k,v in expected.items()):raise ValueError('pilot is not paused at its fixed A horizon')
    for entry in inputs['updates']:
        for ref in [entry[k] for k in ('summary','generation','scoring','opportunity')]+entry['generation_files']+list(entry['closed_stages'].values()):
            if bound.get(ref['path'])!=ref['sha256']:raise ValueError('pilot measurement source is unbound')
    rows,lengths=validate_updates(inputs['updates'],horizon)
    root=Path(config['root']);root.mkdir(parents=True,exist_ok=True)
    write_new(root/'evaluation_attempt.json',{'condition':'v2-S2','lock_sha256':plan['lock']['sha256'],
        'started_unix':time.time(),'automatic_retry':False})
    result={'condition':'v2-S2','gate':'A_PILOT_TOKEN_BUDGET','status':'FROZEN','horizon':30,'arm':'A','seeds':[1301,1302], 'feasibility_gate':False,'A_curve':'descriptive; B own reward supplies T5'}
    result.update(pilot_execution_sha256=lock['pilot_execution_lock']['sha256'],input_lock_sha256=plan['lock']['sha256'],
        LP_sha256=pilot['LP_sha256'],pilot_slots=len(lengths),pilot_generated_tokens=sum(lengths),
        token_budget=pilot_token_budget(lengths))
    write_new(root/'result.json',result);return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(run(json.loads(args.plan.read_text())),sort_keys=True))
