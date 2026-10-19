"""Confirm admission version 2 preserves all IDs, input messages and original proofs while correcting four comments."""
import hashlib
import json
from pathlib import Path
import time

ROOT=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14')


def rows(path):return {r['task_id']:r for r in (json.loads(line) for line in path.read_text().splitlines())}


def main():
    old=rows(ROOT/'admission_v1/training.jsonl');new=rows(ROOT/'admission_v2/training.jsonl')
    assert set(old)==set(new) and len(new)==678
    changed=[]
    for tid,row in new.items():
        assert row['messages'][:2]==old[tid]['messages'][:2]
        assert row['original_source_sha256']==old[tid]['original_source_sha256']
        if row['messages'][-1]!=old[tid]['messages'][-1]:changed.append(tid)
    assert len(changed)==4
    result=dict(same_task_ids=678,same_input_messages=678,same_original_source_hashes=678,
        changed_comment_answers=4,changed_task_ids=changed,original_proof_changes=0,observed_unix=time.time(),
        old_training_sha256=hashlib.sha256((ROOT/'admission_v1/training.jsonl').read_bytes()).hexdigest(),
        new_training_sha256=hashlib.sha256((ROOT/'admission_v2/training.jsonl').read_bytes()).hexdigest())
    (ROOT/'admission_v2/comment_fix_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
