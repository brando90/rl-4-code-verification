"""Keep the selected-proof annotation and Sol reconciliation pools live with bounded recovery and durable progress."""
from __future__ import annotations

import collections
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

import prefer_explicit as selection
from prefer_explicit import base
import review_flagged as review
import annotate_selected as annotations


def alive(pid):
    try:
        command=Path(f'/proc/{pid}/cmdline').read_bytes()
        return any(name in command for name in (b'annotate_selected.py',b'review_flagged.py',b'codex'))
    except (FileNotFoundError,TypeError):return False


def recover(folder,kind):
    state=json.loads((folder/'status.json').read_text())
    if kind=='review' and state['state']=='BLOCKED':
        for output in sorted(folder.glob('output_*.json'),reverse=True):
            try:
                decision=review.check_output(folder,output)
                base.write(folder/'native_blocked_status.json',state)
                base.write(folder/'status.json',dict(state='DONE',decision=decision['decision'],verified=decision['verified'],
                    model=decision.get('review_model'),attempts=int(output.stem.split('_')[-1])+1,recovered_by_watch=True))
                return
            except (FileNotFoundError,ValueError,KeyError,AssertionError):pass
        return
    if state['state'] not in ('RUNNING','CLAIMED') or alive(state.get('driver_pid')) or alive(state.get('pid')):return
    attempts=state.get('attempts',0)
    output=folder/f'output_{max(0,attempts-1)}.json'
    try:
        if kind=='review':
            decision=review.check_output(folder,output)
            outcome='ESCALATE_SOL' if decision['decision']=='needs_sol' and attempts<2 else 'DONE'
            base.write(folder/'status.json',dict(state=outcome,decision=decision['decision'],verified=decision['verified'],attempts=attempts,model=decision.get('review_model'),recovered_by_watch=True))
            return
        base.ROOT=annotations.ROOT
        receipts=base.validate(json.loads((folder/'inputs.json').read_text()),output)
        if all(r['comment_integrity']=='PASS' for r in receipts):
            base.write(folder/'receipts.json',receipts)
            base.write(folder/'status.json',dict(state='DONE',declared=len(receipts),assembled=len(receipts),annotation_issues=sum(bool(r['annotation_issue']) for r in receipts),attempts=attempts,recovered_by_watch=True))
            return
    except (FileNotFoundError,ValueError,KeyError,AssertionError):pass
    base.write(folder/f'dead_worker_{attempts}.json',dict(previous=state,observed_unix=time.time()))
    route='TERRA_PENDING' if state.get('model')=='gpt-5.6-terra' else 'PENDING'
    base.write(folder/'status.json',dict(state=route if attempts<2 else 'BLOCKED',attempts=attempts,declared=state.get('declared',1),error='worker and CLI exited without a completion receipt'))


def add_new_flags():
    """Append newly flagged selected-script cases without changing frozen initial cases."""
    rows={r['task_id']:r for r in base.read_rows(selection.ROOT/'selection.jsonl')}
    new=[];workbook=None
    for receipt in (annotations.ROOT/'examples').glob('*/receipt.json'):
        data=json.loads(receipt.read_text())
        tid=data['task_id'];folder=review.ROOT/'cases'/tid
        if not data.get('annotation_issue') or folder.exists():continue
        if workbook is None:workbook=json.loads(base.SOURCE.read_text())
        row=dict(rows[tid],baseline_annotation_issue='New selected-proof annotation: '+data['annotation_issue'],all_proof_alternatives=workbook[rows[tid]['source_row']]['proof'])
        with (review.ROOT/'queue.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if folder.exists():continue
            folder.mkdir(parents=True)
            base.write(folder/'input.json',row)
            route='TERRA_PENDING' if (review.ROOT/'routing_amendment.json').exists() else 'PENDING'
            base.write(folder/'status.json',dict(state=route,attempts=0))
        new.append(tid)
    if new:base.write(review.ROOT/'amendments'/f'new_flags_{int(time.time())}.json',dict(cases=new,reason='user requested Sol review of all questionable cases, including new selected-script flags',observed_unix=time.time()))


def summarize(root,pattern):
    states=collections.Counter();decisions=collections.Counter();verified=0
    for file in root.glob(pattern):
        data=json.loads(file.read_text());states[data['state']]+=1
        if data['state']=='DONE':
            if data.get('decision'):decisions[data['decision']]+=1
            verified+=bool(data.get('verified'))
    return dict(states=dict(states),decisions=dict(decisions),verified=verified)


def usage(root,input_rate,cached_rate,output_rate):
    count=collections.Counter()
    for path in root.glob('*/cli_*.jsonl'):
        for line in path.read_text(errors='replace').splitlines():
            try:event=json.loads(line)
            except json.JSONDecodeError:continue
            if event.get('type')=='turn.completed':count.update(event.get('usage',{}))
    cost=((count['input_tokens']-count['cached_input_tokens'])*input_rate+count['cached_input_tokens']*cached_rate+count['output_tokens']*output_rate)/1e6
    return dict(tokens=dict(count),configured_rate_estimate_usd=cost,estimate_not_invoice=True,cache_write_surcharges_unknown=True)


def review_usage():
    grouped={}
    for path in (review.ROOT/'cases').glob('*/cli_*.jsonl'):
        route=path.with_name(path.stem.replace('cli_','route_')+'.json')
        model=json.loads(route.read_text())['model'] if route.exists() else 'gpt-6.1-sol'
        count=grouped.setdefault(model,collections.Counter())
        for line in path.read_text(errors='replace').splitlines():
            try:event=json.loads(line)
            except json.JSONDecodeError:continue
            if event.get('type')=='turn.completed':count.update(event.get('usage',{}))
    output={}
    for model,count in grouped.items():
        cached,generated=(.2,12) if model=='gpt-5.6-terra' else (.1,10)
        cost=((count['input_tokens']-count['cached_input_tokens'])*2+count['cached_input_tokens']*cached+count['output_tokens']*generated)/1e6
        output[model]=dict(tokens=dict(count),configured_rate_estimate_usd=cost,estimate_not_invoice=True,cache_write_surcharges_unknown=True)
    return output


def launch_terra():
    env=dict(os.environ,PROOF_REVIEW_MODEL='gpt-5.6-terra')
    subprocess.run(['python3',str(selection.HERE/'review_flagged.py'),'launch'],env=env,check=True)


def main():
    root=selection.ROOT
    with (root/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        start=time.monotonic()
        while time.monotonic()-start<3600:
            for folder in (review.ROOT/'cases').iterdir():recover(folder,'review')
            for folder in (annotations.ROOT/'batches').iterdir():recover(folder,'annotations')
            add_new_flags()
            result=dict(review=summarize(review.ROOT,'cases/*/status.json'),annotations=summarize(annotations.ROOT,'batches/*/status.json'),observed_unix=time.time())
            base.write(root/'live_progress.json',result)
            base.write(root/'usage.json',dict(review_by_model=review_usage(),terra_annotations=usage(annotations.ROOT/'batches',2,.2,12),observed_unix=time.time()))
            print(json.dumps(result),flush=True)
            pending=lambda group:any(group['states'].get(state,0) for state in ('PENDING','TERRA_PENDING','ESCALATE_SOL','CLAIMED','RUNNING'))
            if not pending(result['review']) and not pending(result['annotations']):
                # Reconcile any additional inventory-policy cases after their original worker finishes.
                subprocess.run(['python3',str(selection.HERE/'audit_automation.py')],check=True,timeout=120)
                result['review']=summarize(review.ROOT,'cases/*/status.json')
                if pending(result['review']):
                    if result['review']['states'].get('TERRA_PENDING'):launch_terra()
                    if result['review']['states'].get('PENDING') or result['review']['states'].get('ESCALATE_SOL'):review.launch()
                    continue
            if not pending(result['review']) and not pending(result['annotations']) and result['review']['states'].get('POLICY_PENDING'):
                # Finish healthy initial workers before reusing the remaining native attempt.
                time.sleep(4)
                for folder in (review.ROOT/'cases').iterdir():
                    state=json.loads((folder/'status.json').read_text())
                    if state['state']=='POLICY_PENDING':
                        if (folder/'decision.json').exists():(folder/'decision.json').rename(folder/'decision_initial_policy.json')
                        base.write(folder/'status.json',dict(state,state='TERRA_PENDING'))
                launch_terra()
                continue
            if not pending(result['review']) and not pending(result['annotations']):
                python='/lfs/skampere1/0/brando9/rl4cv_e08/nemo_rl/.venv/bin/python'
                with (root/'finalization.log').open('a') as log:
                    process=subprocess.run([python,str(selection.HERE/'finalize_explicit.py')],stdout=log,stderr=subprocess.STDOUT,timeout=900)
                add_new_flags()
                followup=summarize(review.ROOT,'cases/*/status.json')
                if followup['states'].get('TERRA_PENDING') or followup['states'].get('PENDING') or followup['states'].get('ESCALATE_SOL'):
                    if followup['states'].get('TERRA_PENDING'):launch_terra()
                    if followup['states'].get('PENDING') or followup['states'].get('ESCALATE_SOL'):review.launch()
                    continue
                summary=json.loads((root/'finalization.json').read_text()) if (root/'finalization.json').exists() else {}
                outcome='FINALIZATION_FAILED' if process.returncode else 'NEEDS_RECOVERY' if summary.get('unexpected_failures') else 'DONE_WITH_RECORDED_EXCLUSIONS'
                base.write(root/'completion.json',dict(state=outcome,finalizer_exit=process.returncode,progress=result,unexpected_failures=summary.get('unexpected_failures'),observed_unix=time.time()))
                return
            if result['review']['states'].get('PENDING') or result['review']['states'].get('ESCALATE_SOL'):review.launch()
            if result['review']['states'].get('TERRA_PENDING'):launch_terra()
            if result['annotations']['states'].get('PENDING'):annotations.launch()
            time.sleep(15)
        base.write(root/'completion.json',dict(state='WATCH_DEADLINE',observed_unix=time.time()))


if __name__=='__main__':main()
