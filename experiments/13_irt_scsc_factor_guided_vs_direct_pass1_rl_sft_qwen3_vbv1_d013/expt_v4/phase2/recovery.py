"""TLDR: Classify stage recovery from durable effects without resampling or repeating statistics."""
import argparse
import json
from pathlib import Path
from stage_ledger import read
from effect_receipts import verified_failure, retryable_empty


def refusal_count(root):
    # Count worker refusals plus the single legacy pre-engine refusal.
    leaves=list(Path(root).glob('attempt_*/**/lease_trials/*/lease_refused.json'))
    legacy=sum((p/'zero_effect_evidence.json').exists() and
               bool(read(p/'zero_effect_evidence.json').get('legacy_traceback_proof',False))
               for p in Path(root).glob('attempt_*'))
    return len(leaves)+legacy


def inspect(work):
    work=Path(work)
    for reserved in sorted(work.glob('*/statistics_reserved.json')):
        if not (reserved.parent/'statistic.json').exists():
            return {'action':'STOP_STATISTIC','path':str(reserved),'reason':'statistic reserved; never recompute'}
    empty=[];account=[];refused=[]
    for intent in sorted(work.rglob('intent.json')):
        attempts=sorted(intent.parent.glob('attempt_*'))
        if not attempts:continue
        latest=attempts[-1]
        if (latest/'complete.json').exists():account.append(str(latest));continue
        if verified_failure(latest,refused=True):
            if refusal_count(intent.parent)>=120:
                return {'action':'STOP_LEASE_CAP','path':str(latest),'lease_refusals':refusal_count(intent.parent)}
            refused.append(str(latest));continue
        if not retryable_empty(latest):
            return {'action':'STOP_PARTIAL','path':str(latest),'reason':'partial or unknown effects; no retry'}
        consumed=sum(not verified_failure(p,refused=True) for p in attempts)
        if consumed>=3:return {'action':'STOP_A4_CAP','path':str(latest),'attempts':consumed}
        empty.append(str(latest))
    return {'action':'RETRY_EMPTY' if empty else 'ACCOUNT_OR_CONTINUE','empty_attempts':empty,
            'completed_operations':len(account),'lease_refusals':refused,'resample':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True,type=Path)
    print(json.dumps(inspect(p.parse_args().work),sort_keys=True))
