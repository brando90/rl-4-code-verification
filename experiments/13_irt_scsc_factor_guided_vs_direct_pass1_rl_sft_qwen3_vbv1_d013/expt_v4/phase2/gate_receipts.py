"""TLDR: Reserve each v4 gate once before statistics and keep infrastructure retries separate."""
import json
from pathlib import Path
from common import digest, object_digest, write_new

GATES=('V4-T1','V4-G0','V4-T2','V4-T3','V4-T4','V4-T5-30','V4-T5-60')


def evaluate_once(root,gate,inputs,statistic):
    """An exclusive reservation survives failed statistics; no outcome-based rerun is allowed."""
    if gate not in GATES:raise ValueError('unregistered gate')
    root=Path(root)/gate
    root.mkdir(parents=True,exist_ok=False)
    bindings={str(Path(p).resolve()):digest(p) for p in inputs}
    write_new(root/'reservation.json',{'gate':gate,'input_hashes':bindings,'statistics_reserved':True})
    result=statistic()
    write_new(root/'result.json',{'gate':gate,'input_hashes':bindings,'result':result,
                                 'result_sha256':object_digest(result)})
    return result


def allow_infrastructure_retry(attempts):
    """A4 permits at most three attempts only while none generated any response or statistic."""
    return (len(attempts)<3 and all(a['generated_responses']==0 and not a['statistics_computed'] for a in attempts))
