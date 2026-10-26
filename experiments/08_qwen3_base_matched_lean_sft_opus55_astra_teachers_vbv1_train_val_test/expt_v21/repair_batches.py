"""Twenty-five Terra/high workers repair the fixed 500-example tiny training corpus."""
from __future__ import annotations
import argparse
import collections
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'expt_v18'),str(HERE.parent/'expt_v15'),str(HERE.parent/'expt_v13')]
spec=importlib.util.spec_from_file_location('tiny_v21_shared_core',HERE.parent/'expt_v18/repair_batches.py')
core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)
RUN=core.RUN;ROOT=RUN/'lean_corpus_v21';MODEL='gpt-5.6-terra';EFFORT='high';LANES=25
SOURCE=RUN/'curriculum/training.jsonl'
SOURCE_SHA='2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119'
ANNOTATED=RUN/'lean_corpus_v9/final/tiny_training.jsonl'
ANNOTATED_SHA='2f5dd34bd244508ed622a4d88d41abda3b9986ea62f5587b8ba41d849746252c'
core.ROOT=ROOT;core.HERE=HERE;core.LANES=LANES;core.prior.ROOT=ROOT
base,prior,budget=core.base,core.prior,core.budget
read,write=core.read,core.write
assert_inspector=core.assert_inspector
salvage=core.salvage

def prepare():
    assert not (ROOT/'dispatch.json').exists(),'Tiny V21 dispatch already frozen.'
    assert_inspector();assert base.sha(SOURCE.read_bytes())==SOURCE_SHA
    assert base.sha(ANNOTATED.read_bytes())==ANNOTATED_SHA
    rows=base.read_rows(SOURCE);annotated={r['task_id']:r for r in base.read_rows(ANNOTATED)}
    assert len(rows)==len(annotated)==500
    topics=list(dict.fromkeys(r['topic'] for r in rows));assert len(topics)==25
    paths=[]
    for i,row in enumerate(rows):
        folder=ROOT/'cases'/row['task_id'];write(folder/'original.json',row)
        answer=row['messages'][-1]['content'];match=re.fullmatch(r'FILE: ([^\n]+)\n```lean\n(.*)```\n',answer,re.S);assert match
        source=match[2];assert base.sha(source)==row['lean_sha256']
        (folder/'Original.lean').write_text(source)
        write(folder/'envelope.json',dict(path=match[1],prefix=answer[:match.start(2)],suffix=answer[match.end(2):]))
        prior_receipt=RUN/'curriculum/examples'/row['task_id']/'receipts/verification.json'
        receipt=read(prior_receipt);assert receipt['accepted'] and receipt['lean_sha256']==base.sha(source)
        (folder/'prior_verification.json').write_bytes(prior_receipt.read_bytes())
        (folder/'annotated_seed_response.txt').write_text(annotated[row['task_id']]['messages'][-1]['content'])
        paths.append(str(folder/'Original.lean'))
    (ROOT/'source_paths.txt').write_text('\n'.join(paths)+'\n')
    leanbin='/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin'
    env=dict(os.environ,PATH=str(RUN/'bin')+':'+leanbin+':'+os.environ['PATH'],CUDA_VISIBLE_DEVICES='')
    with (ROOT/'parse_results.jsonl').open('w') as stream:
        subprocess.run(['lake','env','lean','--run',str(HERE.parent/'expt_v13/proof_ranges.lean'),str(ROOT/'source_paths.txt')],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=300)
    parsed={}
    for line in (ROOT/'parse_results.jsonl').read_text().splitlines():
        try:item=json.loads(line)
        except ValueError:continue
        if 'path' in item:parsed[item['path']]=item
    manifest=[]
    for i,row in enumerate(rows):
        tid=row['task_id'];folder=ROOT/'cases'/tid;source=(folder/'Original.lean').read_text();raw=source.encode();record=parsed[str(folder/'Original.lean')]
        assert not record.get('error') and record.get('ranges'),(tid,record)
        targets=[];preserved=[]
        for n,item in enumerate(record['ranges']):
            a=len(raw[:item['start_byte']].decode());b=len(raw[:item['end_byte']].decode())
            proof=source[a:b];hits=prior.automation(proof);anonymous=item['kind'].endswith('.example')
            command=raw[item['command_start_byte']:item['command_end_byte']].decode()
            item.update(index=n,start=a,end=b,original=proof,statement=command[:len(raw[item['command_start_byte']:item['start_byte']].decode())],automation=hits,anonymous=anonymous)
            (preserved if not hits or (anonymous and hits==['native_decide']) else targets).append(item)
        assert targets,'Prior inventory found no wholly strict tiny source; investigate any unexpected no-target file before paid work.'
        inp=dict(task_id=tid,index=i,source_task_id=tid,source=row['source'],topic=row['topic'],ranges=targets,preserved_proofs=preserved,original_sha256=base.sha(source),parser_error=None)
        write(folder/'input.json',inp);write(folder/'seed_proofs.json',{str(r['index']):r['original'] for r in targets})
        write(folder/'status.json',dict(state='PENDING',verified=False,attempts=0))
        manifest.append(dict(task_id=tid,example_index=i,topic=row['topic'],targets=len(targets),original_input_sha256=base.sha((folder/'input.json').read_bytes()),assistant_tokens=row['n_assistant_tokens']))
    batches=[]
    for lane,topic in enumerate(topics):
        ids=[r['task_id'] for r in rows if r['topic']==topic];assert len(ids)==20
        for n in range(5):
            name=f'batch_{lane*5+n:04d}';folder=ROOT/'batches'/name
            write(folder/'input.json',dict(batch_id=name,lane=lane,topic=topic,tasks=ids[n*4:n*4+4]))
            write(folder/'status.json',dict(state='PENDING',attempts=0));batches.append(name)
    template=ROOT/'worker_template';template.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','init','-q',str(template)],check=True)
    (template/'AGENTS.md').write_text('Repair only your assigned tiny training examples. Preserve every implementation, API, theorem/specification statement and test. Use the bounded frozen checker. The coordinator owns shared inputs, budget, credentials and publication. No additional model calls.\n')
    subprocess.run(['git','-C',str(template),'add','AGENTS.md'],check=True)
    subprocess.run(['git','-C',str(template),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize fixed twenty-case tiny proof repair workers'],check=True)
    config=(RUN/'lean_corpus_v18/runtime/lane_00/config.toml').read_text();assert 'TINY_OPENAI_API_KEY' in config
    for lane in range(LANES):
        work=ROOT/'workers'/f'lane_{lane:02d}';subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/f'lane_{lane:02d}';profile.mkdir(parents=True);(profile/'config.toml').write_text(config)
    (ROOT/'schema.json').write_bytes((RUN/'lean_corpus_v18/schema.json').read_bytes())
    write(ROOT/'manifest.json',manifest)
    write(ROOT/'dispatch.json',dict(declared=500,model=MODEL,effort=EFFORT,lanes=25,cases_per_lane=20,batches=125,batch_size=4,compiler_slots=16,max_cli_attempts_per_batch=2,max_candidate_hashes_per_case=4,cli_seconds=900,compiler_seconds=120,assistant_token_cap_exclusive=1000,total_token_cap=16384,source_sha256=SOURCE_SHA,annotated_source_sha256=ANNOTATED_SHA,strict_reusable_prior_files=0,shared_total_authorized=900,cleanup_authorized_cap=780,estimated_additional_conservative_usd=[25,150],cost_forecast_uncertain=True,inspector_sha256=core.INSPECTOR_SHA,created_unix=time.time()))
    print(json.dumps(summarize()),flush=True)

def claim(lane,first=False,batch_name=None):
    if (ROOT/'provider_hold.json').exists() or (ROOT/'user_stop_paid_generation.json').exists():return None
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for folder in sorted((ROOT/'batches').iterdir()):
            if read(folder/'input.json')['lane']!=lane:continue
            if batch_name and folder.name!=batch_name:continue
            state=read(folder/'status.json')
            if state['state']=='PENDING':
                write(folder/'status.json',dict(state,state='CLAIMED',lane=lane,driver_pid=os.getpid(),claimed_unix=time.time()));return folder

_prompt=core.prompt
def prompt(batch,work,tasks,feedback):
    return _prompt(batch,work,tasks,feedback)+'\nTINY V21 REQUIREMENTS: Your static lane owns exactly20 original training tasks in five four-case batches. This turn repairs only the four cases shown above. Each final assistant FILE answer must be STRICTLY BELOW1000Qwen tokens, including concise proof sketch and meaningful inline comments; full conversation<=16384. Keep all named numeric-test theorems and their original statements. Replace their decide/norm_num/etc with explicit readable proofs; never delete or rename tests. Existing original anonymous concrete native_decide tests alone may remain. The other generation-stop flags apply to other corpora; the user expressly authorized this500tiny repair phase. No validation or evaluation material is provided.\n'
core.claim=claim;core.prompt=prompt

def summarize():
    result=core.summarize();result['declared']=500;write(ROOT/'progress.json',result);return result

def worker(lane):
    lane_root=ROOT/'workers'/f'lane_{lane:02d}';profile=ROOT/'runtime'/f'lane_{lane:02d}'
    env=dict(os.environ,CODEX_HOME=str(profile),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY']=(RUN/'.private/lab-openai.key').read_text().strip()
    while True:
        batch=claim(lane)
        if batch is None:return
        state=read(batch/'status.json');work=lane_root/batch.name;work.mkdir(exist_ok=True)
        oldwork=Path(state.get('work',str(work)));ids=read(batch/'input.json')['tasks']
        for tid in ids:
            case=work/tid;case.mkdir(exist_ok=True)
            for name in ['proofs.json','sketch.txt']:
                if oldwork!=work and (oldwork/tid/name).exists() and not (case/name).exists():(case/name).write_bytes((oldwork/tid/name).read_bytes())
            if not (case/'proofs.json').exists():(case/'proofs.json').write_bytes((ROOT/'cases'/tid/'seed_proofs.json').read_bytes())
            if not (case/'sketch.txt').exists():(case/'sketch.txt').write_text('')
            core.mechanical_rfl(tid,case)
        feedback=None
        for attempt in range(state.get('attempts',0),2):
            if (ROOT/'user_stop_paid_generation.json').exists():return
            tasks=[tid for tid in ids if not read(ROOT/'cases'/tid/'status.json')['state'].startswith('ACCEPTED')]
            if not tasks:break
            output=batch/f'output_{attempt}.json';brief=prompt(batch,work,tasks,feedback);(batch/f'prompt_{attempt}.md').write_text(brief)
            identity=f'v21/{batch.name}/{attempt}'
            command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m',MODEL,'-c','model_reasoning_effort="high"','-c','model_context_window=128000','-c','model_auto_compact_token_limit=100000','--json','--output-schema',str(ROOT/'schema.json'),'-o',str(output),'-']
            def started(pid,stamp):
                nonlocal state
                state=dict(state='RUNNING',lane=lane,work=str(work),pid=pid,driver_pid=os.getpid(),attempts=attempt+1,attempt=attempt,budget_identity=identity,started_unix=stamp,tasks=tasks,model=MODEL,effort=EFFORT)
                write(batch/'status.json',state)
                for tid in tasks:write(ROOT/'cases'/tid/'status.json',dict(state='REPAIR_RUNNING',batch=batch.name,lane=lane,work=str(work/tid),attempts=attempt+1))
            run=budget.run_cli(command,env,brief,'cleanup',identity,profile,lane_root,batch/f'cli_{attempt}.jsonl',reservation=10,stop_at=1.2,timeout=900,on_start=started,model=MODEL)
            if run['state']=='BUDGET_HOLD':write(batch/'status.json',dict(state,state='BUDGET_HOLD',attempts=attempt));return
            write(batch/f'usage_{attempt}.json',run)
            try:
                result=read(output);assert result['batch_id']==batch.name
                decisions={r['task_id']:r for r in result['results']};assert set(decisions)==set(tasks)
            except Exception as exc:decisions={};feedback=dict(error=repr(exc),cli=run)
            outcome=[]
            for tid in tasks:
                try:
                    decision=decisions[tid];assert decision['decision']=='cleaned'
                    core.admit(tid,work/tid,decision['rationale']);outcome.append(dict(task_id=tid,verified=True))
                except Exception:
                    try:salvage(tid,work/tid);outcome.append(dict(task_id=tid,verified=True))
                    except Exception as exc:outcome.append(dict(task_id=tid,verified=False,error=repr(exc),decision=decisions.get(tid)))
            write(batch/f'outcomes_{attempt}.json',outcome);feedback=outcome
            if core.funding_error(batch/f'cli_{attempt}.jsonl'):
                write(ROOT/'provider_hold.json',dict(batch=batch.name,reason='Provider funding/authentication failure; no alternate route.',observed_unix=time.time()));break
        for tid in ids:
            status=read(ROOT/'cases'/tid/'status.json')
            if not status['state'].startswith('ACCEPTED'):write(ROOT/'cases'/tid/'status.json',dict(status,state='EXCLUDED_BOUNDED_REPAIR',verified=False,reason='V21 bounded repair ended without an explicit verified proof; not a mathematical impossibility claim.',finished_unix=time.time()))
        write(batch/'status.json',dict(state,state='DONE',finished_unix=time.time()))

def launch():
    for lane in range(25):
        name=f'codex-rl4cv-terra-tiny-v21-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        subprocess.run(['tmux','new-session','-d','-s',name,f'python3 -u {HERE}/repair_batches.py worker --lane {lane} >> {ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'],check=True)
    print(json.dumps(dict(state='LAUNCHED',sessions=25,observed_unix=time.time())),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','launch','worker','check','check-batch','status']);p.add_argument('--lane',type=int);p.add_argument('--task');p.add_argument('--batch');p.add_argument('--work',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='launch':launch()
    elif a.action=='worker':worker(a.lane)
    elif a.action=='check':print(json.dumps(core.compact_diagnostic(core.check(a.task,a.work)),ensure_ascii=False))
    elif a.action=='check-batch':print(json.dumps([core.compact_diagnostic(r) for r in core.check_batch(a.batch,a.work)],ensure_ascii=False))
    else:print(json.dumps(summarize()))
