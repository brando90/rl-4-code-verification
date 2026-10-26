"""Watch the Workbook CLI pool on SNAP, recover dead bounded attempts, and finalize completed artifacts."""
from __future__ import annotations

import collections
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import annotate_workbook as job


def alive(pid):
    if not pid:
        return False
    try:
        command=Path(f'/proc/{pid}/cmdline').read_bytes()
        return b'annotate_workbook.py' in command or b'codex' in command
    except FileNotFoundError:
        return False


def recover(folder):
    state=json.loads((folder/'status.json').read_text())
    if state['state'] not in ('CLAIMED','RUNNING') or alive(state.get('driver_pid')) or alive(state.get('pid')):
        return
    attempts=state.get('attempts',0)
    output=folder/f'output_{max(0,attempts-1)}.json'
    if output.exists():
        try:
            receipts=job.validate(json.loads((folder/'inputs.json').read_text()),output)
            if all(r['comment_integrity']=='PASS' for r in receipts):
                job.write(folder/'receipts.json',receipts)
                job.write(folder/'status.json',dict(state='DONE',declared=len(receipts),assembled=len(receipts),
                    annotation_issues=sum(bool(r['annotation_issue']) for r in receipts),attempts=attempts,recovered_by_watch=True))
                return
        except Exception:
            pass
    job.write(folder/f'dead_attempt_{attempts}.json',dict(previous_state=state,observed_unix=time.time()))
    job.write(folder/'status.json',dict(state='PENDING' if attempts<2 else 'BLOCKED',declared=state['declared'],
        attempts=attempts,error='worker and CLI processes exited without a completion receipt',recovered_by_watch=True))


def aggregate():
    usage=collections.Counter()
    for path in (job.ROOT/'batches').glob('*/cli_*.jsonl'):
        for line in path.read_text().splitlines():
            try:event=json.loads(line)
            except json.JSONDecodeError:continue
            if event.get('type')=='turn.completed':usage.update(event.get('usage',{}))
    estimate=((usage['input_tokens']-usage['cached_input_tokens'])*2+usage['cached_input_tokens']*.2+usage['output_tokens']*12)/1e6
    job.write(job.ROOT/'usage.json',dict(tokens=dict(usage),configured_rate_estimate_usd=estimate,
        estimate_not_provider_invoice=True,cache_write_surcharges_unknown=True,observed_unix=time.time()))


def main():
    with (job.ROOT/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        started=time.monotonic()
        while time.monotonic()-started<3600:
            for folder in sorted((job.ROOT/'batches').glob('batch_*')):
                recover(folder)
            result=job.status();aggregate()
            states=result['batch_states']
            if not any(states.get(s,0) for s in ('PENDING','CLAIMED','RUNNING')):
                python='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false')
                with (job.ROOT/'finalization.log').open('a') as log:
                    check=subprocess.run([python,str(job.HERE/'finalize_annotations.py'),'workbook'],
                        env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
                job.write(job.ROOT/'completion.json',dict(state='DONE' if not states.get('BLOCKED') and check.returncode==0 else 'INCOMPLETE',
                    finalizer_exit=check.returncode,progress=result,observed_unix=time.time()))
                return
            if states.get('PENDING'):
                # The launcher preserves live lane sessions and only fills vacant slots.
                job.launch()
            time.sleep(15)
        job.write(job.ROOT/'completion.json',dict(state='WATCH_DEADLINE',observed_unix=time.time()))


if __name__=='__main__':main()
