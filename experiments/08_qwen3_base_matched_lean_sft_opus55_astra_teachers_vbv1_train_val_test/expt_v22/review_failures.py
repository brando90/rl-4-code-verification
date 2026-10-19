"""Separate, bounded Sol/high review of terminal V21 tiny proof failures."""
from __future__ import annotations
import argparse
import collections
from dataclasses import asdict
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'expt_v18'),str(HERE.parent/'expt_v15'),str(HERE.parent/'expt_v13')]
spec=importlib.util.spec_from_file_location('sol_v22_checked_core',HERE.parent/'expt_v18/repair_batches.py')
core=importlib.util.module_from_spec(spec);sys.modules[spec.name]=core;spec.loader.exec_module(core)
RUN=core.RUN;ROOT=RUN/'lean_corpus_v22';OLD=RUN/'lean_corpus_v21'
MODEL,EFFORT,LANES='gpt-6.1-sol','high',6
SOURCE=RUN/'curriculum/training.jsonl'
SOURCE_SHA='2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119'
core.ROOT=ROOT;core.HERE=HERE;core.MODEL=MODEL;core.prior.ROOT=ROOT
base,prior,budget=core.base,core.prior,core.budget
read,write=core.read,core.write
assert_inspector=core.assert_inspector
salvage=core.salvage

def sync_failures():
    added=[]
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if (ROOT/'cohort_closed.json').exists():
            assert read(ROOT/'cohort_closed.json')['manifest_sha256']==base.sha((ROOT/'manifest.json').read_bytes())
            return []
        manifest=read(ROOT/'manifest.json') if (ROOT/'manifest.json').exists() else []
        known={r['task_id'] for r in manifest};indices={r['task_id']:r for r in read(OLD/'manifest.json')}
        for batch in sorted((OLD/'batches').iterdir()):
            if read(batch/'status.json')['state']!='DONE':continue
            for tid in read(batch/'input.json')['tasks']:
                if tid in known:continue
                source=OLD/'cases'/tid;state=read(source/'status.json')
                if state['state']!='EXCLUDED_BOUNDED_REPAIR':continue
                folder=ROOT/'cases'/tid;folder.mkdir(parents=True)
                for name in ['input.json','original.json','Original.lean','envelope.json','prior_verification.json']:(folder/name).write_bytes((source/name).read_bytes())
                inp=read(folder/'input.json');seeds={str(r['index']):r['original'] for r in inp['ranges']}
                oldwork=Path(state['work']) if state.get('work') else None
                if oldwork and (oldwork/'proofs.json').exists():
                    try:
                        proposed=read(oldwork/'proofs.json')
                        if isinstance(proposed,dict):
                            for key in seeds:
                                if isinstance(proposed.get(key),str):seeds[key]=proposed[key]
                    except (OSError,ValueError):pass
                write(folder/'seed_proofs.json',seeds)
                sketch=(oldwork/'sketch.txt').read_text() if oldwork and (oldwork/'sketch.txt').exists() else ''
                (folder/'seed_sketch.txt').write_text(sketch)
                diagnostics=[]
                for path in sorted((source/'checks').glob('*/result.json'),key=lambda p:p.stat().st_mtime)[-3:]:
                    result=read(path);report=result.get('kernel_report',{});evidence=Path(report['evidence_dir']) if report.get('evidence_dir') else None
                    stdout=(evidence/'compile_stdout.log').read_text(errors='replace') if evidence and (evidence/'compile_stdout.log').exists() else ''
                    diagnostics.append(dict(receipt=str(path),source_sha256=result.get('source_sha256'),errors=report.get('probe_errors',[]),compiler_stdout=stdout[-6000:],non_kernel_error=result.get('error')))
                write(folder/'prior_failures.json',dict(first_pass_status=state,batch=str(batch),diagnostics=diagnostics,old_work=str(oldwork) if oldwork else None))
                write(folder/'status.json',dict(state='PENDING',verified=False,attempts=0))
                manifest.append(dict(task_id=tid,example_index=indices[tid]['example_index'],topic=indices[tid]['topic'],original_input_sha256=base.sha((folder/'input.json').read_bytes()),prior_failure_status_sha256=base.sha((source/'status.json').read_bytes())))
                known.add(tid);added.append(tid)
        write(ROOT/'manifest.json',manifest)
        if (OLD/'completion.json').exists():write(ROOT/'cohort_closed.json',dict(state='CLOSED',declared=len(manifest),v21_completion_sha256=base.sha((OLD/'completion.json').read_bytes()),manifest_sha256=base.sha((ROOT/'manifest.json').read_bytes()),observed_unix=time.time()))
    return added

def prepare():
    assert not (ROOT/'dispatch.json').exists(),'Sol review already frozen.'
    assert_inspector();assert base.sha(SOURCE.read_bytes())==SOURCE_SHA
    ROOT.mkdir(parents=True,exist_ok=True);write(ROOT/'manifest.json',[])
    template=ROOT/'worker_template';template.mkdir()
    subprocess.run(['git','init','-q',str(template)],check=True)
    (template/'AGENTS.md').write_text('Review only the assigned failed training proof. Preserve fixed source statements, implementations and tests. Use the bounded frozen checker and no additional model calls. Shared queue, budget, receipts and publication belong to the coordinator.\n')
    subprocess.run(['git','-C',str(template),'add','AGENTS.md'],check=True)
    subprocess.run(['git','-C',str(template),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize separate Sol tiny-proof review workers'],check=True)
    config=(OLD/'runtime/lane_00/config.toml').read_text();assert 'TINY_OPENAI_API_KEY' in config and 'api.openai.com' in config
    for lane in range(LANES):
        work=ROOT/'workers'/f'lane_{lane:02d}';subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/f'lane_{lane:02d}';profile.mkdir(parents=True);(profile/'config.toml').write_text(config)
    schema=dict(type='object',additionalProperties=False,required=['task_id','decision','rationale'],properties=dict(task_id=dict(type='string'),decision=dict(type='string',enum=['cleaned','unresolved']),rationale=dict(type='string')))
    write(ROOT/'schema.json',schema)
    write(ROOT/'dispatch.json',dict(model=MODEL,effort=EFFORT,lanes=6,cohort='Terminal V21 bounded-repair failures only; original500source indices preserved.',max_cli_attempts_per_case=2,max_new_candidate_hashes_per_case=4,compiler_slots_shared_with='lean_corpus_v21/compiler_00.lock…compiler_15.lock',compiler_seconds=120,cli_seconds=900,reservation_usd=10,observed_conservative_stop_usd=1.2,shared_total_authorized=900,cleanup_cap=780,source_sha256=SOURCE_SHA,inspector_sha256=core.INSPECTOR_SHA,official_model_doc='https://developers.openai.com/api/docs/models/gpt-6.1-sol',official_pricing='https://developers.openai.com/api/docs/pricing',estimated_additional_conservative_usd=[10,70],forecast_uncertain=True,created_unix=time.time()))
    print(json.dumps(dict(added=sync_failures(),progress=summarize())),flush=True)

def claim(lane):
    if (ROOT/'provider_hold.json').exists() or (ROOT/'user_stop_paid_generation.json').exists():return None
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for item in read(ROOT/'manifest.json'):
            folder=ROOT/'cases'/item['task_id'];state=read(folder/'status.json')
            if state['state']=='PENDING':
                write(folder/'status.json',dict(state,state='CLAIMED',lane=lane,driver_pid=os.getpid(),claimed_unix=time.time()));return folder

def check(tid,work):
    assert_inspector();folder=ROOT/'cases'/tid
    with (folder/'check.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        source=prior.assemble(folder,work);digest=base.sha(source);target=folder/'checks'/digest;receipt=target/'result.json'
        if receipt.exists():return read(receipt)
        assert len(list((folder/'checks').glob('*')))<4,'Four NEW Sol candidate hashes exhausted; V21 evidence is immutable and separate.'
        target.mkdir(parents=True);path=target/'Solution.lean';path.write_text(source)
        slot=None;deadline=time.time()+600
        while slot is None and time.time()<deadline:
            for n in range(16):
                handle=(OLD/f'compiler_{n:02d}.lock').open('a')
                try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);slot=handle;break
                except BlockingIOError:handle.close()
            if slot is None:time.sleep(.25)
        assert slot is not None,'Shared compiler queue wait exceeded ten minutes.'
        result=dict(task_id=tid,source_sha256=digest,passed=False,scope_gate='construction_only_original_proof_terms',checked_unix=time.time())
        try:
            os.environ.pop('TINY_OPENAI_API_KEY',None);os.environ['PATH']=str(RUN/'bin')+':'+os.environ['PATH'];kernel=prior.kernel_module()
            report=kernel.check_file(str(path),str(RUN/'grading'),timeout=120,allow_native_decide=False,keep_dir=str(target/'kernel'));data=asdict(report)
            write(target/'kernel_report.json',data)
            result.update(passed=bool(kernel.valid_report(data) and report.n_theorems>=1 and report.n_honest==report.n_theorems and report.source_sha256==digest),kernel_report=data)
        finally:slot.close()
        write(receipt,result);return result

def prompt(folder,work,feedback):
    row=read(folder/'input.json');seeds=read(work/'proofs.json');source=core.render_context(row,(folder/'Original.lean').read_text(),seeds)
    return f'''# Sol review of one failed tiny training proof
{base.PREAPPROVAL}

You are the explicitly requested {MODEL}, high reasoning. The prior Terra phase failed to establish this complete file within its bounds. Review its ACTUAL training compiler failures, repair the proof, and preserve an honest outcome. This is a separate bounded follow-up; do not modify V21 or any validation/evaluation data. No additional model calls are assigned.

Case: {folder.name}; work: {work}. Write proofs.json mapping every target numeric index to a complete by proof, and sketch.txt with2–10short English lines explaining the finished proof. Keep implementations, all theorem/specification statements, hypotheses, domains, APIs, namespaces and tests fixed. Do not delete or rename named numeric-test theorems. The coordinator reconstructs only original parsed proof terms. Existing anonymous concrete native_decide tests alone remain unchanged.

Avoid ALL {json.dumps(core.selection.AUTOMATION)} in replacement proofs; no wrappers hiding these operations, sorry/admit/new axioms, unsafe/elaborator or command escapes. Plain exact, apply, rw, rfl, change, cases, induction, constructors and explicit linear_combination are allowed. Prefer named lemmas or explicit structural mathematics. Include meaningful English comments every few proof lines and at tricky steps. Be concise without obfuscation: assistant FILE answer STRICTLY BELOW1000Qwen tokens, whole conversation<=16384.

Use only this bounded checker: python3 {HERE}/review_failures.py check --task {folder.name} --work {work}. At most4NEW distinct candidate hashes in this Sol phase,120seconds per compilation,900seconds this CLI turn and2CLI turns per case. It uses the exact frozen inspector and shared16compiler slots. Inspect actual diagnostics; final exact bytes must have passed=true. No extra direct Lean probes. Mathlib source is cached at /lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src/.lake/packages/mathlib. Shared queue, budget, credentials and parent processes belong to the coordinator.

Prior training compiler evidence: {json.dumps(read(folder/'prior_failures.json'))}
Current turn feedback: {json.dumps(feedback)}

Fixed Lean context with target labels:
```lean
{source}
```

Return only JSON task_id={folder.name},decision=cleaned or unresolved,rationale. A failed bounded attempt is not a claim that the statement is false.
'''

def provider_error(path):
    if core.funding_error(path):return 'Provider funding/authentication error'
    for line in path.read_text(errors='replace').splitlines():
        try:event=json.loads(line)
        except ValueError:continue
        if event.get('type') not in ['error','turn.failed']:continue
        text=json.dumps(event).lower()
        if any(word in text for word in ['model_not_found','model not found','does not exist','not authorized','unsupported model']):return 'Requested Sol model is unavailable or unauthorized on the existing route'

def worker(lane):
    assert MODEL in budget.RATES and budget.UPPER[MODEL]==dict(input=5.,cached_input=.2,output=15.),'Verified Sol pricing must be installed before provider work.'
    lane_root=ROOT/'workers'/f'lane_{lane:02d}';profile=ROOT/'runtime'/f'lane_{lane:02d}'
    env=dict(os.environ,CODEX_HOME=str(profile),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false');env['TINY_OPENAI_API_KEY']=(RUN/'.private/lab-openai.key').read_text().strip()
    while True:
        folder=claim(lane)
        if folder is None:return
        work=lane_root/folder.name;work.mkdir(exist_ok=True);state=read(folder/'status.json');oldwork=Path(state.get('work',str(work)))
        for name,seed in [('proofs.json','seed_proofs.json'),('sketch.txt','seed_sketch.txt')]:
            if not (work/name).exists():(work/name).write_bytes((oldwork/name).read_bytes() if oldwork!=work and (oldwork/name).exists() else (folder/seed).read_bytes())
        feedback=None
        for attempt in range(state.get('attempts',0),2):
            if (ROOT/'user_stop_paid_generation.json').exists() or (ROOT/'provider_hold.json').exists():return
            output=folder/f'output_{attempt}.json';brief=prompt(folder,work,feedback);(folder/f'prompt_{attempt}.md').write_text(brief);identity=f'v22/{folder.name}/{attempt}'
            command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m',MODEL,'-c','model_reasoning_effort="high"','-c','model_context_window=128000','-c','model_auto_compact_token_limit=100000','--json','--output-schema',str(ROOT/'schema.json'),'-o',str(output),'-']
            def started(pid,stamp):
                nonlocal state
                state=dict(state='RUNNING',lane=lane,work=str(work),pid=pid,driver_pid=os.getpid(),attempts=attempt+1,attempt=attempt,budget_identity=identity,started_unix=stamp,model=MODEL,effort=EFFORT);write(folder/'status.json',state)
            run=budget.run_cli(command,env,brief,'cleanup',identity,profile,lane_root,folder/f'cli_{attempt}.jsonl',reservation=10,stop_at=1.2,timeout=900,on_start=started,model=MODEL)
            if run['state']=='BUDGET_HOLD':write(folder/'status.json',dict(state,state='BUDGET_HOLD',attempts=attempt));return
            write(folder/f'usage_{attempt}.json',run)
            try:
                result=read(output);assert result['task_id']==folder.name and result['decision']=='cleaned'
                core.admit(folder.name,work,result['rationale']);break
            except Exception as exc:
                try:salvage(folder.name,work);break
                except Exception as inner:feedback=dict(error=repr(exc),salvage_error=repr(inner));write(folder/f'error_{attempt}.json',feedback)
            issue=provider_error(folder/f'cli_{attempt}.jsonl')
            if issue:
                write(ROOT/'provider_hold.json',dict(case=folder.name,reason=issue+'; no model/key substitution.',observed_unix=time.time()));break
        status=read(folder/'status.json')
        if not status['state'].startswith('ACCEPTED'):write(folder/'status.json',dict(status,state='EXCLUDED_BOUNDED_REPAIR',verified=False,reason='Separate Sol bounded review did not establish an explicit checked proof.',finished_unix=time.time()))

def summarize():
    states=collections.Counter(read(p)['state'] for p in (ROOT/'cases').glob('*/status.json'))
    result=dict(declared=len(read(ROOT/'manifest.json')),states=dict(states),verified=sum(v for k,v in states.items() if k.startswith('ACCEPTED')),cohort_closed=(ROOT/'cohort_closed.json').exists(),observed_unix=time.time());write(ROOT/'progress.json',result);return result

def launch():
    assert MODEL in budget.RATES,'Sol pricing not yet installed.'
    for lane in range(LANES):
        name=f'codex-rl4cv-sol-tiny-review-v22-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        subprocess.run(['tmux','new-session','-d','-s',name,f'python3 -u {HERE}/review_failures.py worker --lane {lane} >> {ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'],check=True)
    print(json.dumps(dict(state='LAUNCHED',lanes=LANES,model=MODEL,effort=EFFORT,observed_unix=time.time())),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','sync','launch','worker','check','status']);p.add_argument('--lane',type=int);p.add_argument('--task');p.add_argument('--work',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='sync':print(json.dumps(sync_failures()))
    elif a.action=='launch':launch()
    elif a.action=='worker':worker(a.lane)
    elif a.action=='check':
        try:print(json.dumps(core.compact_diagnostic(check(a.task,a.work)),ensure_ascii=False))
        except Exception as exc:print(json.dumps(dict(task_id=a.task,passed=False,error=repr(exc))))
    else:print(json.dumps(summarize()))
