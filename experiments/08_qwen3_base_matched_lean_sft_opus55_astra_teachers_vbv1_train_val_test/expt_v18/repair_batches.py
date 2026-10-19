"""Finish original-pool proof cleanup using focused four-file Terra batches and exact frozen kernel checks."""
from __future__ import annotations
import argparse
import collections
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'expt_v15'),str(HERE.parent/'expt_v13')]
import campaign_budget as budget
import clean_existing as prior
from clean_existing import base,selection
RUN=budget.RUN
ROOT=RUN/'lean_corpus_v18'
OLD=RUN/'lean_corpus_v13'
prior.ROOT=ROOT
MODEL,EFFORT,LANES='gpt-5.6-terra','high',32
MAX_ATTEMPTS=2
INSPECTOR_SHA='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'

def read(path):return json.loads(Path(path).read_text())
def write(path,value):base.write(path,value)

def assert_inspector():
    assert base.sha(prior.FROZEN.read_bytes())==INSPECTOR_SHA,'Frozen inspector source changed.'
    if (ROOT/'dispatch.json').exists():assert read(ROOT/'dispatch.json')['inspector_sha256']==INSPECTOR_SHA

def funding_error(path):
    tokens=['insufficient_quota','billing_hard_limit','invalid_api_key','incorrect api key','error 401','usage_limit_reached']
    for line in path.read_text(errors='replace').splitlines():
        try:event=json.loads(line)
        except json.JSONDecodeError:continue
        if event.get('type') not in ['error','turn.failed']:continue
        message=json.dumps(event).lower()
        if any(token in message for token in tokens):return True
    return False

def prepare():
    assert_inspector()
    assert not (ROOT/'dispatch.json').exists(),'V18 input already frozen.'
    assert base.sha(prior.SOURCE.read_bytes())==prior.SOURCE_SHA
    complete=read(OLD/'completion.json');assert complete['state']=='DONE_PARTIAL' and complete['replacements']==818
    assert read(OLD/'dispatch.json')['inspector_sha256']==INSPECTOR_SHA
    replacement_path=OLD/'final/replacements.jsonl';assert base.sha(replacement_path.read_bytes())==complete['replacements_sha256']
    accepted={r['example_index']:r for r in base.read_rows(replacement_path)}
    manifest=[];pending=[];unchanged=[]
    for item in read(OLD/'manifest.json'):
        tid=item['task_id'];source=OLD/'cases'/tid;folder=ROOT/'cases'/tid;folder.mkdir(parents=True,exist_ok=True)
        for name in ['original.json','input.json','Original.lean','envelope.json','saved_alternatives.json']:
            if (source/name).exists():(folder/name).write_bytes((source/name).read_bytes())
        inp=read(folder/'input.json');oldstatus=read(source/'status.json');index=inp['index']
        record=dict(task_id=tid,example_index=index,original_input_sha256=base.sha((folder/'input.json').read_bytes()),prior_state=oldstatus['state'],targets=len(inp['ranges']),assistant_tokens=item.get('assistant_tokens',99999))
        if index in accepted:
            rep=accepted[index];oldreceipt=Path(rep['verification_receipt']);receipt=read(oldreceipt)
            assert base.sha(oldreceipt.read_bytes())==rep['verification_receipt_sha256']
            assert receipt['passed'] and prior.kernel_module().valid_report(receipt['kernel_report'])
            lean=(source/'Solution.lean').read_text();digest=base.sha(lean);assert digest==rep['lean_sha256']==receipt['kernel_report']['source_sha256']
            target=folder/'checks'/digest;target.mkdir(parents=True,exist_ok=True)
            (target/'Solution.lean').write_text(lean);(folder/'Solution.lean').write_text(lean)
            (target/'result.json').write_bytes(oldreceipt.read_bytes())
            write(target/'inheritance.json',dict(v18_inherited_from=str(oldreceipt),v18_inherited_receipt_sha256=base.sha(oldreceipt.read_bytes())))
            write(folder/'status.json',dict(state='ACCEPTED_INHERITED',verified=True,source_sha256=digest,receipt=str(target/'result.json'),original_receipt_sha256=base.sha(oldreceipt.read_bytes())))
        elif not inp['ranges']:
            write(folder/'status.json',dict(state='UNCHANGED_CHECK_PENDING',verified=False));unchanged.append(tid)
        else:
            seeds={str(r['index']):r['original'] for r in inp['ranges']};seed_source=None
            work=Path(oldstatus['work']) if oldstatus.get('work') else None
            if work and (work/'proofs.json').exists():
                try:
                    oldseed=read(work/'proofs.json')
                    if not isinstance(oldseed,dict):raise ValueError('Prior partial proof map is not an object.')
                    for key in seeds:
                        if isinstance(oldseed.get(key),str):seeds[key]=oldseed[key]
                    seed_source=str(work/'proofs.json')
                except (OSError,ValueError,TypeError,AttributeError):pass
            write(folder/'seed_proofs.json',seeds);write(folder/'seed_receipt.json',dict(source=seed_source,sha256=base.sha(json.dumps(seeds,sort_keys=True))))
            write(folder/'status.json',dict(state='PENDING',verified=False));pending.append(record)
        manifest.append(record)
    assert len(manifest)==2585 and len(accepted)==818 and len(unchanged)==227 and len(pending)==1540
    ordered=sorted(pending,key=lambda r:(r['assistant_tokens'],r['example_index']))
    failures=[r for r in ordered if r['prior_state']=='DONE']
    fresh=[r for r in ordered if r['prior_state']=='FALLBACK']
    first=[failures[0] if failures else ordered[0]]
    for ratio in [.25,.5,.75]:
        choice=fresh[min(len(fresh)-1,int(ratio*len(fresh)))]
        if choice not in first:first.append(choice)
    while len(first)<4:
        first.append(next(r for r in ordered if r not in first))
    rest=[r for r in ordered if r not in first];groups=[first]+[rest[i:i+4] for i in range(0,len(rest),4)]
    for n,group in enumerate(groups):
        folder=ROOT/'batches'/f'batch_{n:04d}'
        write(folder/'input.json',dict(batch_id=folder.name,tasks=[r['task_id'] for r in group]))
        write(folder/'status.json',dict(state='PENDING',attempts=0))
    template=ROOT/'worker_template';template.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','init','-q',str(template)],check=True)
    (template/'AGENTS.md').write_text('Finish assigned proof-only training-data repairs. The coordinator owns shared queue, budget, receipts, credentials and publication; write only the assigned proof/sketch artifacts and use its bounded checker. Preserve the unchanged source specifications.\n')
    subprocess.run(['git','-C',str(template),'add','AGENTS.md'],check=True)
    if subprocess.run(['git','-C',str(template),'rev-parse','--verify','HEAD'],capture_output=True).returncode:
        subprocess.run(['git','-C',str(template),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize focused full-cleanup workers'],check=True)
    config=(OLD/'runtime/lane_00/config.toml').read_text();assert 'TINY_OPENAI_API_KEY' in config
    for lane in range(LANES):
        work=ROOT/'workers'/f'lane_{lane:02d}'
        if not (work/'.git').exists():subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/f'lane_{lane:02d}';profile.mkdir(parents=True,exist_ok=True);(profile/'config.toml').write_text(config)
    schema=dict(type='object',additionalProperties=False,required=['batch_id','results'],properties=dict(batch_id=dict(type='string'),results=dict(type='array',items=dict(type='object',additionalProperties=False,required=['task_id','decision','rationale'],properties=dict(task_id=dict(type='string'),decision=dict(type='string',enum=['cleaned','unresolved']),rationale=dict(type='string'))))))
    write(ROOT/'schema.json',schema);write(ROOT/'manifest.json',manifest)
    write(ROOT/'unchanged_manifest.json',unchanged)
    write(ROOT/'dispatch.json',dict(declared=2585,inherited=818,unchanged_recheck=227,remaining=1540,batches=len(groups),batch_size=4,model=MODEL,effort=EFFORT,lanes=32,compiler_slots=16,max_cli_attempts_per_batch=2,max_candidate_hashes_per_case=4,cli_seconds=900,compiler_seconds=120,shared_total_authorized=900,cleanup_authorized_cap=780,estimated_additional_conservative_usd=[154,308],projection_uncertain=True,prior_completion_sha256=base.sha((OLD/'completion.json').read_bytes()),original_pool_sha256=prior.SOURCE_SHA,inspector_sha256=base.sha(prior.FROZEN.read_bytes()),created_unix=time.time()))
    print(json.dumps(summarize()),flush=True)

def claim(lane,first=False):
    if (ROOT/'provider_hold.json').exists():return None
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for folder in sorted((ROOT/'batches').iterdir()):
            if first and folder.name!='batch_0000':continue
            status=read(folder/'status.json')
            if status['state']=='PENDING':
                write(folder/'status.json',dict(status,state='CLAIMED',lane=lane,driver_pid=os.getpid(),claimed_unix=time.time()));return folder

def render_context(row,source,seeds):
    for item in reversed(row['ranges']):
        key=str(item['index']);body=seeds[key]
        source=source[:item['start']]+f'/- V18 TARGET {key}: replace this proof term only. -/ '+body+source[item['end']:]
    return source

def prompt(batch,work,tasks,feedback):
    text=f'''# Finish four fixed Python-to-Lean proof repairs
{base.PREAPPROVAL}

You are {MODEL} with high reasoning, using the user-authorized lab-key Codex CLI route. Write concise explicit proofs with a short mathematical sketch and meaningful comments every few proof lines. The full unchanged file contexts below are TRAINING material. The coordinator reconstructs only the original parsed proof terms: every implementation, specification, domain, hypothesis, namespace, API and test input stays fixed. Original anonymous concrete native_decide tests stay unchanged.

Final proof replacements must avoid ALL of {json.dumps(selection.AUTOMATION)}. Plain exact/apply/rw/rfl/change/calc/constructor/cases/induction and explicit linear_combination are fine. Local have/let helper proofs are allowed. No sorry/admit/new axioms, native_decide in replacements, unsafe/elaborator escapes or hidden automation wrappers. Existing saved explicit partial proofs are seeded below. Final artifacts must contain no excluded tactic and must be concise, readable explicit mathematics. Do not change the statements, rename theorems, or train a huge obfuscated expanded term. No new model calls are assigned.

Your assigned folder is {work}. For EACH case, write {work}/CASE/proofs.json mapping every target numeric index (string) to a complete proof term beginning by, and sketch.txt with2–10short English lines explaining the finished construction. Files are preseeded. The inline context labels identify exact target indices; those labels are not part of the original source. No need to read the full training prompt or large coordinator input metadata. You may inspect cached Mathlib at /lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src/.lake/packages/mathlib for exact lemma names. All shared queue, budget, provider, receipt and parent process state belong to the ordinary coordinator: leave them unchanged.

Write initial replacements for the assigned cases, then run ONE command to check all candidates: python3 {HERE}/repair_batches.py check-batch --batch {batch.name} --work {work}. Individual check: same script check --task CASE --work {work}/CASE. The checker uses unchanged pinned Lean4.22 and kernel axiom rules. It snapshots exact bytes and gives compiler diagnostics; inspect the returned per-case evidence. At most4distinct candidate hashes per case in V18,120seconds/compiler operation,900seconds this CLI attempt. No extra direct Lean calls. A completed explicit file must have passed=true on its FINAL exact bytes. If you edit after checking, check again. The final answer must still fit the original16384-token training conversation, so be concise without obfuscation.

Return only JSON batch_id={batch.name}, results=[{{task_id,decision=cleaned or unresolved,rationale}}] for every assigned case. Unresolved is an honest bounded-attempt outcome and will be explicitly EXCLUDED from the fully cleaned pool, never silently replaced with automated proof training data. Coordinator feedback: {json.dumps(feedback)}
'''
    for tid in tasks:
        folder=ROOT/'cases'/tid;row=read(folder/'input.json');seeds=read(work/tid/'proofs.json')
        text+=f'\n## {tid}; target keys {list(seeds)}\n```lean\n'+render_context(row,(folder/'Original.lean').read_text(),seeds)+'\n```\n'
    return text

def check(task,work):
    assert_inspector()
    return prior.verify(task,work)

def check_batch(batch,work):
    ids=read(ROOT/'batches'/batch/'input.json')['tasks'];results=[]
    for tid in ids:
        if read(ROOT/'cases'/tid/'status.json')['state'].startswith('ACCEPTED'):continue
        try:results.append(check(tid,work/tid))
        except Exception as exc:results.append(dict(task_id=tid,passed=False,error=repr(exc)))
    return results

def admit(tid,work,rationale):
    assert_inspector()
    folder=ROOT/'cases'/tid;source=prior.assemble(folder,work);digest=base.sha(source)
    target=folder/'checks'/digest;receipt=read(target/'result.json')
    assert receipt['passed'] and prior.kernel_module().valid_report(receipt['kernel_report'])
    assert receipt['kernel_report']['source_sha256']==digest
    (folder/'Solution.lean').write_text(source)
    write(folder/'status.json',dict(state='ACCEPTED_REPAIRED',verified=True,source_sha256=digest,receipt=str(target/'result.json'),rationale=rationale,model=MODEL,effort=EFFORT,finished_unix=time.time()))

def salvage(tid,work):
    """Keep actual checked proof bytes even if the worker later changed an unfinished draft."""
    try:
        admit(tid,work,'Recovered exact final-byte checker success from bounded CLI artifacts.');return
    except Exception:pass
    assert_inspector();folder=ROOT/'cases'/tid;options=[]
    for path in (folder/'checks').glob('*/result.json'):
        try:
            receipt=read(path);source=(path.parent/'Solution.lean').read_text();digest=base.sha(source)
            assert receipt['task_id']==tid and receipt['passed'] and receipt['scope_gate']=='construction_only_original_proof_terms'
            assert prior.kernel_module().valid_report(receipt['kernel_report']) and receipt['kernel_report']['source_sha256']==digest==path.parent.name
            options.append((len(source.encode()),digest,path,source))
        except (OSError,ValueError,KeyError,AssertionError):continue
    assert options,'No exact checked explicit source survived the bounded attempt.'
    _,digest,path,source=min(options,key=lambda item:(item[0],item[1]))
    (folder/'Solution.lean').write_text(source)
    mechanical=read(folder/'mechanical_rfl.json') if (folder/'mechanical_rfl.json').exists() else {}
    is_mechanical=mechanical.get('passed') and mechanical.get('source_sha256')==digest
    write(folder/'status.json',dict(state='ACCEPTED_MECHANICAL_RFL' if is_mechanical else 'ACCEPTED_SAVED_CANDIDATE',verified=True,source_sha256=digest,receipt=str(path),rationale='Shortest exact checked explicit source retained after later unfinished draft edits; no new model call.',model=None if is_mechanical else MODEL,effort=None if is_mechanical else EFFORT,finished_unix=time.time()))

def mechanical_rfl(tid,work):
    folder=ROOT/'cases'/tid
    if read(folder/'status.json')['state'].startswith('ACCEPTED'):return
    candidate=work/'mechanical_rfl';candidate.mkdir(exist_ok=True)
    row=read(folder/'input.json')
    write(candidate/'proofs.json',{str(r['index']):'by\n  -- Both sides reduce to the same expression.\n  rfl' for r in row['ranges']})
    (candidate/'sketch.txt').write_text('Unfold the definitions and reduce the computations in each obligation.\nEvery targeted equality or equivalence is then reflexive.\n')
    try:
        receipt=check(tid,candidate)
        write(folder/'mechanical_rfl.json',dict(passed=receipt['passed'],source_sha256=receipt['source_sha256'],observed_unix=time.time()))
        if receipt['passed']:
            admit(tid,candidate,'All targeted obligations proved by explicit definitional reflexivity; no model call.')
            status=read(folder/'status.json');write(folder/'status.json',dict(status,state='ACCEPTED_MECHANICAL_RFL',method='definitional_reflexivity',model=None,effort=None))
    except Exception as exc:write(folder/'mechanical_rfl.json',dict(passed=False,error=repr(exc),observed_unix=time.time()))

def worker(lane,once=False):
    lane_root=ROOT/'workers'/f'lane_{lane:02d}';profile=ROOT/'runtime'/f'lane_{lane:02d}'
    env=dict(os.environ,CODEX_HOME=str(profile),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY']=(RUN/'.private/lab-openai.key').read_text().strip()
    while True:
        batch=claim(lane,first=once)
        if batch is None:return
        state=read(batch/'status.json');work=lane_root/batch.name;work.mkdir(exist_ok=True)
        oldwork=Path(state.get('work',str(work)));ids=read(batch/'input.json')['tasks']
        for tid in ids:
            case=work/tid;case.mkdir(exist_ok=True)
            for name in ['proofs.json','sketch.txt']:
                if oldwork!=work and (oldwork/tid/name).exists() and not(case/name).exists():(case/name).write_bytes((oldwork/tid/name).read_bytes())
            if not(case/'proofs.json').exists():(case/'proofs.json').write_bytes((ROOT/'cases'/tid/'seed_proofs.json').read_bytes())
            if not(case/'sketch.txt').exists():(case/'sketch.txt').write_text('')
            mechanical_rfl(tid,case)
        feedback=None
        for attempt in range(state.get('attempts',0),MAX_ATTEMPTS):
            tasks=[tid for tid in ids if not read(ROOT/'cases'/tid/'status.json')['state'].startswith('ACCEPTED')]
            if not tasks:break
            output=batch/f'output_{attempt}.json';brief=prompt(batch,work,tasks,feedback);(batch/f'prompt_{attempt}.md').write_text(brief)
            identity=f'v18/{batch.name}/{attempt}'
            command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m',MODEL,'-c','model_reasoning_effort="high"','-c','model_context_window=128000','-c','model_auto_compact_token_limit=100000','--json','--output-schema',str(ROOT/'schema.json'),'-o',str(output),'-']
            def started(pid,stamp):
                nonlocal state
                state=dict(state='RUNNING',lane=lane,work=str(work),pid=pid,driver_pid=os.getpid(),attempts=attempt+1,attempt=attempt,budget_identity=identity,started_unix=stamp,tasks=tasks)
                write(batch/'status.json',state)
                for tid in tasks:write(ROOT/'cases'/tid/'status.json',dict(state='REPAIR_RUNNING',batch=batch.name,lane=lane,work=str(work/tid),attempts=attempt+1))
            run=budget.run_cli(command,env,brief,'cleanup',identity,profile,lane_root,batch/f'cli_{attempt}.jsonl',reservation=10,stop_at=1.2,timeout=900,on_start=started,model=MODEL)
            if run['state']=='BUDGET_HOLD':
                write(batch/'status.json',dict(state,state='BUDGET_HOLD',attempts=attempt));return
            write(batch/f'usage_{attempt}.json',run)
            try:
                result=read(output);assert result['batch_id']==batch.name
                decisions={r['task_id']:r for r in result['results']};assert set(decisions)==set(tasks)
            except Exception as exc:decisions={};feedback=dict(error=repr(exc),cli=run)
            outcome=[]
            for tid in tasks:
                try:
                    decision=decisions[tid];assert decision['decision']=='cleaned'
                    admit(tid,work/tid,decision['rationale']);outcome.append(dict(task_id=tid,verified=True))
                except Exception as exc:
                    # A genuine final-byte checker pass is sufficient even if the CLI's final JSON was interrupted.
                    try:salvage(tid,work/tid);outcome.append(dict(task_id=tid,verified=True))
                    except Exception as inner:outcome.append(dict(task_id=tid,verified=False,error=repr(inner),decision=decisions.get(tid)))
            write(batch/f'outcomes_{attempt}.json',outcome);feedback=outcome
            if funding_error(batch/f'cli_{attempt}.jsonl'):
                write(ROOT/'provider_hold.json',dict(batch=batch.name,reason='Provider funding/authentication failure; no alternate route.',observed_unix=time.time()));break
        for tid in ids:
            status=read(ROOT/'cases'/tid/'status.json')
            if not status['state'].startswith('ACCEPTED'):write(ROOT/'cases'/tid/'status.json',dict(status,state='EXCLUDED_BOUNDED_REPAIR',verified=False,reason='Explicit proof not established within the new V18 bounded repair attempts; not a mathematical impossibility claim.',finished_unix=time.time()))
        write(batch/'status.json',dict(state,state='DONE',finished_unix=time.time()))
        if once:return

def audit_unchanged(tid):
    assert_inspector()
    folder=ROOT/'cases'/tid;source=(folder/'Original.lean').read_text();digest=base.sha(source);target=folder/'checks'/digest;target.mkdir(parents=True,exist_ok=True)
    path=target/'Solution.lean';path.write_text(source)
    slot=None
    while slot is None:
        for n in range(16):
            handle=(ROOT/f'compiler_{n:02d}.lock').open('a')
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);slot=handle;break
            except BlockingIOError:handle.close()
        if slot is None:time.sleep(.25)
    try:
        os.environ['PATH']=str(RUN/'bin')+':'+os.environ['PATH'];kernel=prior.kernel_module()
        report=kernel.check_file(str(path),str(RUN/'grading'),timeout=120,allow_native_decide=False,keep_dir=str(target/'kernel'));data=asdict(report)
        passed=bool(kernel.valid_report(data) and report.n_theorems>=1 and report.n_honest==report.n_theorems and report.source_sha256==digest)
        receipt=dict(task_id=tid,source_sha256=digest,passed=passed,scope_gate='byte_identical_original_no_targeted_automation',kernel_report=data)
        write(target/'result.json',receipt)
        if passed:(folder/'Solution.lean').write_text(source)
        write(folder/'status.json',dict(state='ACCEPTED_UNCHANGED' if passed else 'EXCLUDED_ORIGINAL_KERNEL',verified=passed,source_sha256=digest,receipt=str(target/'result.json')))
    finally:slot.close()

def audit():
    assert_inspector()
    prior.kernel_module()
    ids=[tid for tid in read(ROOT/'unchanged_manifest.json') if read(ROOT/'cases'/tid/'status.json')['state']=='UNCHANGED_CHECK_PENDING']
    with ThreadPoolExecutor(max_workers=16) as pool:list(pool.map(audit_unchanged,ids))
    write(ROOT/'unchanged_audit_completion.json',dict(state='DONE',declared=227,observed_unix=time.time()))

def summarize():
    cases=collections.Counter(read(p)['state'] for p in (ROOT/'cases').glob('*/status.json'))
    batches=collections.Counter(read(p)['state'] for p in (ROOT/'batches').glob('*/status.json'))
    result=dict(declared=2585,states=dict(cases),batches=dict(batches),verified=sum(v for k,v in cases.items() if k.startswith('ACCEPTED')),observed_unix=time.time())
    write(ROOT/'progress.json',result);return result

def launch(first=False):
    for lane in ([0] if first else range(32)):
        name=f'codex-rl4cv-terra-full-v18-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        command=f'python3 -u {HERE}/repair_batches.py worker --lane {lane}'+(' --once' if first else '')+f' >> {ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'
        subprocess.run(['tmux','new-session','-d','-s',name,command],check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','launch','worker','check','check-batch','audit','status']);p.add_argument('--lane',type=int);p.add_argument('--first',action='store_true');p.add_argument('--once',action='store_true');p.add_argument('--task');p.add_argument('--batch');p.add_argument('--work',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='launch':launch(a.first)
    elif a.action=='worker':worker(a.lane,a.once)
    elif a.action=='audit':audit()
    elif a.action=='check':print(json.dumps(check(a.task,a.work),ensure_ascii=False)[:16000])
    elif a.action=='check-batch':print(json.dumps(check_batch(a.batch,a.work),ensure_ascii=False)[:48000])
    else:print(json.dumps(summarize()))
