"""Wake a budgeted Terra coordinator on completed validation or failed jobs and preserve unattended campaign evidence."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
ROOT=RUN/'adaptive_1p7b_campaign'
TRAIN=RUN/'corpus_training_v12'
MODEL='gpt-5.6-terra'
RESERVE=12.0
STOP=2.0

def read(path,default=None):
    try:return json.loads(Path(path).read_text())
    except (FileNotFoundError,json.JSONDecodeError):return default

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.{os.getpid()}.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def alive(pid):
    try:os.kill(int(pid),0);return True
    except (OSError,ValueError,TypeError):return False

def verify_summary(name,item,raw,scored):
    """Recompute complete-cell binary success using frozen V6 analysis before accepting the target."""
    summary=item.get('summary')
    if not summary or not Path(raw).exists() or not Path(scored).exists():return False
    try:
        key=hashlib.sha256((digest(raw)+digest(scored)+json.dumps(summary,sort_keys=True)).encode()).hexdigest()
        prior=ROOT/'independent_checks'/name/'receipt.json'
        old=read(prior,{})
        if old.get('input_hash')==key:return old.get('passed',False)
        sys.path[:0]=[str(RUN/'repo/src'),str(EXP/'expt_v6')]
        os.environ['TINY_RUN_ROOT']=str(TRAIN)
        import analyze
        analyze.RUN=prior.parent
        analyze.RUN.mkdir(parents=True,exist_ok=True)
        ids=(EXP/'expt_v1/results/split/vbv1_validation_task_ids.txt').read_text().splitlines()
        result,vector=analyze.evaluate(name,analyze.read(raw),analyze.read(scored),ids)
        passed=all(result[k]==summary[k] for k in ['declared_cells','scored_cells','successes','success_rate'])
        write(prior,dict(input_hash=key,passed=passed,recomputed=result,raw_path=str(raw),scored_path=str(scored),observed_unix=time.time()))
        return passed
    except (OSError,ValueError,AssertionError,KeyError) as exc:
        write(ROOT/'independent_checks'/name/'error.json',dict(error=repr(exc),observed_unix=time.time()))
        return False

def outcomes():
    found={}
    for label in ['current','cleaned']:
        terminal=read(TRAIN/label/'terminal.json')
        summary=read(TRAIN/'analysis'/f'v12_{label}_summary.json')
        if terminal or summary:
            name='v12_'+label
            found[name]=dict(terminal=terminal,summary=summary)
            found[name]['ordinary_receipt_verified']=verify_summary(name,found[name],TRAIN/'validation'/name/'raw.jsonl',TRAIN/'validation'/name/'scored.jsonl')
    for name in ['dispatcher.json','cleaned_dispatcher.json']:
        item=read(TRAIN/name,{})
        status=item.get('status','')
        if any(flag in status for flag in ['FAILED','DEAD','TIMEOUT']):found[name]=dict(terminal=item,summary=None)
    for manifest in sorted((ROOT/'trials').glob('*/manifest.json')):
        item=read(manifest,{})
        if item.get('summary_path') or item.get('terminal_path'):
            summary=read(item['summary_path']) if item.get('summary_path') else None
            terminal=read(item['terminal_path']) if item.get('terminal_path') else None
            if summary or terminal:
                name=item['trial_id'];found[name]=dict(terminal=terminal,summary=summary)
                found[name]['ordinary_receipt_verified']=bool(item.get('raw_path') and item.get('scored_path') and verify_summary(name,found[name],item['raw_path'],item['scored_path']))
    return found

def reached(items):
    return [name for name,item in items.items() if item.get('ordinary_receipt_verified') and item.get('summary') and
            item['summary'].get('declared_cells')==1080 and item['summary'].get('scored_cells')==1080 and
            float(item['summary'].get('success_rate',0))>=.25]

def pending_trials():
    waiting=[]
    for path in sorted((ROOT/'trials').glob('*/manifest.json')):
        m=read(path,{})
        terminal=read(m['terminal_path']) if m.get('terminal_path') else None
        summary=read(m['summary_path']) if m.get('summary_path') else None
        if not terminal and not summary:waiting.append(dict(trial_id=m.get('trial_id'),pid=m.get('pid'),alive=alive(m.get('pid')),manifest=str(path)))
    return waiting

def settle_coordinator(budget,identity,usage):
    """Settle one parent call idempotently, reconciling an earlier unknown charge from CLI receipts."""
    with budget.transaction() as data:
        reserved=data['reservations'].pop(identity,None)
        prior=data['charges'].get(identity)
        if reserved is None and prior is None:raise RuntimeError('Missing parent reservation and charge: '+identity)
        purpose=(reserved or prior)['purpose']
        if usage is None and prior is not None:return
        amount=budget.charge_estimate(usage) if usage is not None else reserved['usd']
        charge=dict(purpose=purpose,usd=amount,base_rate_estimate_usd=budget.estimate(usage) if usage is not None else None,usage=usage,unknown_usage=usage is None,time=time.time())
        data['charges'][identity]=charge
        data['events'].append(dict(event='parent_usage_reconciled' if prior else 'parent_settled',identity=identity,previous_usd=prior.get('usd') if prior else None,usd=amount,time=time.time()))
        return charge

def recover_finished_calls():
    sys.path.insert(0,str(EXP/'expt_v13'))
    import campaign_budget as budget
    decisions=read(ROOT/'decisions.json',{})
    for folder in sorted((ROOT/'coordination').glob('*')):
        run=read(folder/'running.json',{})
        if not run or (folder/'completion.json').exists() or alive(run.get('pid')):continue
        used,window=budget.session_usage(folder/'profile',run['started_unix'])
        settle_coordinator(budget,folder.name,used)
        packet=read(folder/'input.json',{})
        event=packet.get('event')
        result=dict(state='RECOVERED_COMPLETED_CALL',identity=folder.name,returncode=0 if (folder/'final.txt').exists() else -1,execution_verified=False,usage=used,reason='Recovered dead coordinator after parent reservation was prematurely settled; preserved output and actual CLI usage.',observed_unix=time.time())
        write(folder/'completion.json',result)
        if event and not any(x.get('identity')==folder.name for x in decisions.get(event,[])):decisions.setdefault(event,[]).append(result)
    write(ROOT/'decisions.json',decisions)
    return decisions

def coordinator(event,items,attempt):
    sys.path.insert(0,str(EXP/'expt_v13'))
    import campaign_budget as budget
    import clean_existing as cli
    identity=f'adaptation_{event[:16]}_{attempt}'
    if not budget.reserve(identity,'adaptation',RESERVE):
        snap=budget.snapshot()
        if not snap['tranche2activated']:
            budget.activate_second_tranche('First authorized tranche insufficient for validation-driven continuation; user approved an additional $300.')
        if not budget.reserve(identity,'adaptation',RESERVE):return dict(state='BUDGET_EXHAUSTED',identity=identity)
    folder=ROOT/'coordination'/identity;folder.mkdir(parents=True,exist_ok=True)
    profile=folder/'profile';profile.mkdir()
    template=RUN/'lean_corpus_v13/runtime/lane_00/config.toml'
    config=template.read_text()
    assert 'api.openai.com' in config and 'TINY_OPENAI_API_KEY' in config
    (profile/'config.toml').write_text(config)
    work=folder/'work';work.mkdir()
    subprocess.run(['git','init','-q',str(work)],check=True)
    (work/'AGENTS.md').write_text('Execute the campaign runbook and preserve scientific settings, explicit budget, source ownership and completed evidence. No external messages.\n')
    packet=dict(event=event,outcomes=items,pending_trials=pending_trials(),budget=budget.snapshot(),created_unix=time.time())
    write(folder/'input.json',packet)
    final=folder/'final.txt'
    brief=(HERE/'cc.md').read_text()+f'\n\nThis wake-up input is {folder}/input.json. Read it and execute the smallest useful next phase. Save a final plain-language summary to your normal final answer.\n'
    (folder/'prompt.md').write_text(brief)
    env=dict(os.environ,CODEX_HOME=str(profile),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY']=(RUN/'.private/lab-openai.key').read_text().strip()
    command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m',MODEL,'-c','model_reasoning_effort="high"','-c','model_context_window=128000','-c','model_auto_compact_token_limit=100000','--json','-o',str(final),'-']
    previous_manifests={str(p):digest(p) for p in (ROOT/'trials').glob('*/manifest.json')}
    started=time.time();reason=None;used=None;process=None
    # A sequential coordinator plus at most one in-flight request is covered by the reservation.
    # Maximum official full-context/cache-write +128k output exposure is <=$7.554.
    # Stop on observed conservative charge >=$2, leaving >$7.554 headroom within $12.
    try:
        with (folder/'cli.jsonl').open('x') as stream:
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,cwd=work,env=env,text=True,start_new_session=True)
            write(folder/'running.json',dict(pid=process.pid,model=MODEL,effort='high',started_unix=started,permission_mode='full access; no routine approvals',reservation_usd=RESERVE))
            process.stdin.write(brief);process.stdin.close()
            while process.poll() is None:
                used,window=cli.usage(profile,started)
                if used and budget.charge_estimate(used)>=STOP:reason='Observed conservative charge stop';cli.stop(process);break
                if time.time()-started>1800:reason='Thirty-minute coordinator time limit';cli.stop(process);break
                write(folder/'heartbeat.json',dict(pid=process.pid,elapsed_seconds=time.time()-started,observed_usage=used,observed_context_window=window,observed_unix=time.time()))
                time.sleep(2)
        used,window=cli.usage(profile,started)
    except BaseException as exc:
        reason=repr(exc)
        if process is not None:cli.stop(process)
    finally:
        settle_coordinator(budget,identity,used)
    result=dict(state='COORDINATOR_FINISHED',identity=identity,returncode=process.returncode if process else None,stop_reason=reason,usage=used,final_exists=final.exists(),finished_unix=time.time())
    changed=[]
    for p in (ROOT/'trials').glob('*/manifest.json'):
        if previous_manifests.get(str(p))!=digest(p):
            trial=read(p,{})
            trial_terminal=read(trial['terminal_path']) if trial.get('terminal_path') else None
            if alive(trial.get('pid')) or trial_terminal:changed.append(str(p))
    result.update(execution_verified=bool(changed),new_or_updated_live_trial_manifests=changed)
    write(folder/'completion.json',result)
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--selftest',action='store_true');args=parser.parse_args()
    if args.selftest:
        assert reached({'x':dict(ordinary_receipt_verified=True,summary=dict(declared_cells=1080,scored_cells=1080,success_rate=.25))})==['x']
        assert not reached({'x':dict(ordinary_receipt_verified=True,summary=dict(declared_cells=1080,scored_cells=1079,success_rate=1.0))})
        assert not reached({'x':dict(ordinary_receipt_verified=True,summary=dict(declared_cells=1080,scored_cells=1080,success_rate=.249))})
        assert alive(os.getpid()) and not alive(None)
        print('Target denominator, threshold and liveness controls PASS; no model calls.');return
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'coordinator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        initial=dict(source_sha256=digest(__file__),runbook_sha256=digest(HERE/'cc.md'),pid=os.getpid(),host=os.uname().nodename,started_unix=time.time(),model=MODEL,effort='high',state='ARMED_WAITING_FOR_OUTCOMES',reboot_recovery='No automatic reboot recovery configured; tmux survives SSH/laptop disconnect only.')
        write(ROOT/'coordinator_launch.json',initial)
        decisions=recover_finished_calls()
        protected=[EXP/'expt_v6/analyze.py',RUN/'repo/src/rl4cv/rewards.py',RUN/'repo/src/rl4cv/veribench/exp103.py',RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py']
        frozen={str(p):digest(p) for p in protected}
        write(ROOT/'frozen_evaluator_sources.json',frozen)
        while True:
            changed=[p for p,h in frozen.items() if digest(p)!=h]
            if changed:
                write(ROOT/'scientific_hold.json',dict(reason='Frozen evaluator source changed; no new adaptive calls.',paths=changed,observed_unix=time.time()));return
            if (ROOT/'STOP').exists():
                write(ROOT/'coordinator_stopped.json',dict(reason='Explicit campaign STOP file; healthy child jobs preserved pending user direction.',observed_unix=time.time()));return
            items=outcomes();goal=reached(items);pending=pending_trials()
            state='GOAL_REACHED' if goal else 'WAITING_FOR_VALIDATION'
            write(ROOT/'coordinator_heartbeat.json',dict(state=state,pid=os.getpid(),goal_reached_by=goal,outcomes=items,pending_trials=pending,decisions=len(decisions),observed_unix=time.time()))
            if goal:
                write(ROOT/'goal.json',dict(state='VALIDATION_TARGET_REACHED',systems=goal,metric='complete135-task,eight-sample validation binary success>=25%; adaptive validation, not held-out-test evidence',observed_unix=time.time()))
                if all(read(TRAIN/c/'terminal.json') for c in ['current','cleaned']):return
            elif items:
                # Wake on new finished outcomes, or a dead model-launched child; never spend to poll healthy jobs.
                dead=[p for p in pending if not p['alive']]
                packet=dict(outcomes=items,dead_trials=dead)
                event=hashlib.sha256(json.dumps(packet,sort_keys=True).encode()).hexdigest()
                attempts=len(decisions.get(event,[]))
                if event not in decisions or (attempts<2 and decisions[event][-1].get('state')!='BUDGET_EXHAUSTED' and (decisions[event][-1].get('returncode') not in [0,None] or not decisions[event][-1].get('execution_verified'))):
                    try:result=coordinator(event,items,attempts)
                    except Exception as exc:
                        result=dict(state='COORDINATOR_ERROR',identity=f'adaptation_{event[:16]}_{attempts}',returncode=-1,execution_verified=False,error=repr(exc),observed_unix=time.time())
                        write(ROOT/'last_coordinator_error.json',result)
                    decisions.setdefault(event,[]).append(result);write(ROOT/'decisions.json',decisions)
                    if result['state']=='BUDGET_EXHAUSTED':write(ROOT/'paid_work_hold.json',dict(reason='Authorized adaptation budget exhausted; preserve/finish healthy deterministic jobs.',observed_unix=time.time()))
            time.sleep(20)

if __name__=='__main__':main()
