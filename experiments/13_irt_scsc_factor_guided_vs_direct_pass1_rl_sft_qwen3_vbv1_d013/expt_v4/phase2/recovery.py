"""TLDR: Classify stage recovery from durable effects without resampling or repeating statistics."""
import argparse
import json
from pathlib import Path
from stage_ledger import read


def inspect(work):
    work=Path(work)
    for reserved in sorted(work.glob('*/statistics_reserved.json')):
        if not (reserved.parent/'statistic.json').exists():
            return {'action':'STOP_STATISTIC','path':str(reserved),'reason':'statistic reserved; never recompute'}
    empty=[];account=[]
    for intent in sorted(work.rglob('intent.json')):
        attempts=sorted(intent.parent.glob('attempt_*'))
        if not attempts:continue
        latest=attempts[-1]
        if (latest/'complete.json').exists():account.append(str(latest));continue
        failure=latest/'infrastructure_failure.json'
        expected={'generated_responses':0,'optimizer_started':False,'statistics_started':False}
        if not failure.exists() or read(failure)!=expected:
            return {'action':'STOP_PARTIAL','path':str(latest),'reason':'partial or unknown effects; no retry'}
        if len(attempts)>=3:return {'action':'STOP_A4_CAP','path':str(latest),'attempts':len(attempts)}
        empty.append(str(latest))
    return {'action':'RETRY_EMPTY' if empty else 'ACCOUNT_OR_CONTINUE','empty_attempts':empty,
            'completed_operations':len(account),'resample':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True,type=Path)
    print(json.dumps(inspect(p.parse_args().work),sort_keys=True))
