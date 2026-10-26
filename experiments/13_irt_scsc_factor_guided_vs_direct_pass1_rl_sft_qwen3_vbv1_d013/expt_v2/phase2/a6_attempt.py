"""Authorize a published A6 infrastructure successor only before any diagnostic response exists."""
import argparse,json
from pathlib import Path
from a6_driver import authorize,run
from panel import digest


def check_predecessors(lock):
    admission=lock['infrastructure_attempt']
    number=admission['number'];previous=admission['previous']
    if type(number)is not int or not 2<=number<=3 or len(previous)!=number-1:
        raise ValueError('A6 infrastructure attempt limit or chronology violated')
    if admission['maximum_attempts']!=3 or admission['cumulative_device_hours']!=2.:
        raise ValueError('A6 attempt or cumulative resource cap changed')
    roots=[]
    for index,item in enumerate(previous,1):
        root=Path(item['root']);roots.append(root)
        if item['number']!=index:raise ValueError('A6 predecessor order changed')
        for name,sha in item['evidence'].items():
            if digest(root/name)!=sha:raise ValueError('A6 predecessor evidence changed')
        result=json.loads((root/'result.json').read_text())
        if result['status']!='INCOMPLETE' or not result['cleanup_verified'] or result['released']['status']!='RELEASED':
            raise ValueError('A6 predecessor is not a clean infrastructure failure')
        # A durable response, a completed cohort, or any scoring makes this
        # infrastructure route ineligible; no automatic measurement retry.
        if any(root.rglob('*.generation.json')) or (root/'generation/result.json').exists():
            raise ValueError('A6 predecessor generated diagnostic responses')
    if len(set(roots))!=len(roots) or Path(lock['configuration']['root'])in roots:
        raise ValueError('A6 attempts must retain separate immutable evidence')
    if Path(lock['configuration']['scoring']['root']).exists():
        raise ValueError('A6 scoring has already started')


def execute(plan):
    lock,_,_,_=authorize(plan)
    bound={b['path']:b['sha256']for b in lock['bindings']}
    if bound.get(str(Path(__file__).resolve()))!=digest(__file__):
        raise ValueError('A6 successor admission executable not bound')
    check_predecessors(lock)
    return run(plan)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    print(json.dumps(execute(json.loads(a.plan.read_text())),sort_keys=True))
