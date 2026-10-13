#!/usr/bin/env python3
"""Launch ordinary and opaque R2 processes; combine only their public admission receipts."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


def combine(receipts):
    by_route={r['route']:r for r in receipts}
    if set(by_route)!={'ordinary','opaque'}:raise ValueError('missing route')
    if by_route['ordinary']['declared']!=33456 or by_route['opaque']['declared']!=5328:
        raise ValueError('route denominator changed')
    complete=all(r['complete_required'] for r in receipts)
    equal=all(r['equality']=='PASS' for r in receipts)
    return {'gate':'R2','status':'PASS' if complete and equal else 'FAIL' if complete else 'INCOMPLETE',
            'declared':38784,'accounted':sum(r['accounted'] for r in receipts),
            'measured':sum(r['measured'] for r in receipts),
            'typed_deterministic_limits':sum(r['typed_deterministic_limits'] for r in receipts),
            'complete_required':complete,'equality':'PASS' if equal else 'FAIL' if complete else 'INCOMPLETE',
            'routes':receipts,'test_outcomes_disclosed':False}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');a=ap.parse_args()
    root=Path(os.environ['WR'])/'R2';children=[]
    for route in ('ordinary','opaque'):
        log=(root/(route+'_coordinator.log')).open('a' if a.resume else 'x')
        cmd=[sys.executable,str(HERE/'run_route.py'),'--route',route]+(['--resume'] if a.resume else [])
        children.append((route,subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT),log))
    receipts=[]
    for route,child,log in children:
        child.wait();log.close();path=root/(route+'_public_receipt.json')
        if not path.exists():
            print(json.dumps({'gate':'R2','status':'INCOMPLETE','route':route,'public_receipt_missing':True}),flush=True)
            return 1
        receipts.append(json.loads(path.read_text()))
    result=combine(receipts)
    (root/'public_result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
