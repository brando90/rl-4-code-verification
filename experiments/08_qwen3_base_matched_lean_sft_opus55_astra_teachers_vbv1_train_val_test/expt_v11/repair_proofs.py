"""Generate and verify explicit repaired proofs for the frozen 68 unresolved Workbook statements with Sol/high."""
from __future__ import annotations
import argparse
import collections
from dataclasses import asdict
import fcntl
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
sys.path[:0]=[str(HERE.parent/'expt_v9'),str(HERE.parent/'expt_v8')]
import prefer_explicit as selection
from prefer_explicit import base
RUN=selection.RUN
ROOT=RUN/'lean_corpus_v11'
MODEL,EFFORT,LANES='gpt-6.1-sol','high',16
FROZEN=RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py'
LEGACY='''macro "∑ " i:ident " in " s:term ", " f:term : term =>
  `(Finset.sum $s (fun $i => $f))
macro "∏ " i:ident " in " s:term ", " f:term : term =>
  `(Finset.prod $s (fun $i => $f))
'''

def kernel_module():
    spec=importlib.util.spec_from_file_location('repair_frozen_kernel',FROZEN)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module

def prepare():
    assert not (ROOT/'dispatch.json').exists(),'Repair dispatch already frozen.'
    prior=RUN/'lean_corpus_v10/unresolved_recovery'
    rows=[r for r in json.loads((prior/'progress.json').read_text())['rows'] if not r['passed']]
    assert len(rows)==68
    ROOT.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for old in sorted(rows,key=lambda r:r['task_id']):
        tid=old['task_id'];source=RUN/'lean_corpus_v9/review/cases'/tid
        row=json.loads((source/'input.json').read_text())
        types=next(r['failure_types'] for r in json.loads((RUN/'lean_corpus_v10/unresolved_audit.json').read_text())['rows'] if r['task_id']==tid)
        row.update(recovery=old,diagnostic_types=types,prior_review=json.loads((source/'decision.json').read_text()),prior_case_folder=str(source))
        folder=ROOT/'cases'/tid;base.write(folder/'input.json',row);base.write(folder/'status.json',dict(state='PENDING',attempts=0))
        manifest.append(dict(task_id=tid,statement_sha256=base.sha(row['formal_statement']),input_sha256=base.sha((folder/'input.json').read_bytes())))
    base.write(ROOT/'manifest.json',manifest)
    schema=dict(type='object',additionalProperties=False,required=['task_id','decision','rationale'],properties=dict(task_id=dict(type='string'),decision=dict(type='string',enum=['repaired','cannot_repair']),rationale=dict(type='string')))
    base.write(ROOT/'schema.json',schema)
    template=ROOT/'worker_template';template.mkdir()
    subprocess.run(['git','init','-q',str(template)],check=True)
    (template/'AGENTS.md').write_text('Repair the assigned unchanged theorem using explicit proof steps. Work only in the named case subfolder; use the coordinator checker and return the requested final JSON. The coordinator owns shared inputs, receipts and publication.\n')
    subprocess.run(['git','-C',str(template),'add','AGENTS.md'],check=True)
    subprocess.run(['git','-C',str(template),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize isolated explicit-proof repair workers'],check=True)
    config=(RUN/'lean_corpus_v9/review/runtime/lane_000/config.toml').read_text()
    assert 'TINY_OPENAI_API_KEY' in config and 'api.openai.com' in config
    for lane in range(LANES):
        work=ROOT/'workers'/f'lane_{lane:02d}';subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/f'lane_{lane:02d}';profile.mkdir(parents=True);(profile/'config.toml').write_text(config)
    base.write(ROOT/'dispatch.json',dict(cases=68,model=MODEL,effort=EFFORT,lanes=LANES,compiler_slots=4,max_cli_attempts=2,max_candidate_hashes=8,compiler_timeout_seconds=60,cli_timeout_seconds=900,estimated_cost_usd=[10,50],credential='previously authorized LAB_OPENAI_API_KEY through Codex CLI',inspector_sha256=base.sha(FROZEN.read_bytes()),manifest_sha256=base.sha((ROOT/'manifest.json').read_bytes()),created_unix=time.time()))
    print((ROOT/'dispatch.json').read_text(),flush=True)

def claim(lane):
    if (ROOT/'provider_hold.json').exists():return None
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for folder in sorted((ROOT/'cases').iterdir()):
            status=json.loads((folder/'status.json').read_text())
            if status['state']=='PENDING':
                base.write(folder/'status.json',dict(status,state='CLAIMED',lane=lane,driver_pid=os.getpid(),claimed_unix=time.time()));return folder

def assemble(row,work):
    body=(work/'proof.lean').read_text().strip()
    support=(work/'support.lean').read_text().strip()
    sketch=(work/'sketch.txt').read_text().strip().splitlines()
    assert 2<=len(sketch)<=8,'Write a focused proof sketch in2–8short English lines.'
    assert all(0<len(s)<=360 and s.isprintable() for s in sketch)
    assert body and not body.startswith('by\n'),'proof.lean contains the tactic body without an outer by.'
    statement=re.sub(r'\s*:=\s*by\s+sorry\s*$','',row['formal_statement']);assert statement!=row['formal_statement']
    header='\n'.join('-- '+('Proof sketch: ' if i==0 else '')+s for i,s in enumerate(sketch))+'\n'
    source=header+'import Mathlib\nopen BigOperators Nat Real Rat\n\n'+support+'\n\n'+statement+' := by\n'+''.join('  '+s+'\n' for s in body.splitlines())
    assert statement+' := by\n' in source
    return source

def verify(tid,work):
    folder=ROOT/'cases'/tid;row=json.loads((folder/'input.json').read_text());work=work.resolve()
    assert work.parent.parent==ROOT/'workers' and work.name==tid,'Checker workspace is outside the assigned worker/case folder.'
    source=assemble(row,work);digest=base.sha(source);target=folder/'checks'/digest;receipt=target/'result.json'
    if receipt.exists():return json.loads(receipt.read_text())
    with (folder/'check.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if receipt.exists():return json.loads(receipt.read_text())
        ledger=folder/'checked_hashes.json';hashes=json.loads(ledger.read_text()) if ledger.exists() else []
        if digest not in hashes:
            assert len(hashes)<8,'Eight-candidate repair check budget exhausted.'
            hashes.append(digest);base.write(ledger,hashes)
        target.mkdir(parents=True,exist_ok=True);path=target/'Solution.lean';path.write_text(source)
        kernel=kernel_module();dispatch=ROOT/'dispatch.json'
        if dispatch.exists():assert base.sha(FROZEN.read_bytes())==json.loads(dispatch.read_text())['inspector_sha256']
        masked=kernel.strip_comments(source)
        avoid=selection.automations(masked)
        result=dict(task_id=tid,source_sha256=digest,passed=False,remaining_automation=avoid,source_file=str(path))
        if avoid or re.search(r'\b(sorry|admit|axiom|native_decide)\b',masked):
            result['error']='Replace discouraged automation or forbidden proof escapes; use explicit steps.';base.write(receipt,result);return result
        slots=ROOT/'compiler_slots';slots.mkdir(exist_ok=True);slot=None;deadline=time.monotonic()+300
        while slot is None and time.monotonic()<deadline:
            for i in range(4):
                candidate=(slots/str(i)).open('a')
                try:fcntl.flock(candidate,fcntl.LOCK_EX|fcntl.LOCK_NB);slot=candidate;break
                except BlockingIOError:candidate.close()
            if slot is None:time.sleep(.25)
        assert slot is not None,'Compiler slot wait exceeded five minutes.'
        try:
            os.environ.pop('TINY_OPENAI_API_KEY',None)
            os.environ['PATH']=str(RUN/'bin')+':'+os.environ['PATH']
            report=kernel.check_file(str(path),str(RUN/'grading'),timeout=60,allow_native_decide=False,keep_dir=str(target/'kernel'))
            data=asdict(report);base.write(target/'kernel_report.json',data)
            result.update(passed=bool(kernel.valid_report(data) and report.n_theorems>=1 and report.n_honest==report.n_theorems and report.source_sha256==digest),compile_rc=report.compile_rc,n_theorems=report.n_theorems,n_honest=report.n_honest,kernel_report=data)
        finally:slot.close()
        base.write(receipt,result);return result

def validate(folder,work,output):
    result=json.loads(output.read_text());assert result['task_id']==folder.name
    if result['decision']=='repaired':
        row=json.loads((folder/'input.json').read_text());source=assemble(row,work);digest=base.sha(source)
        receipt=json.loads((folder/'checks'/digest/'result.json').read_text())
        assert receipt['passed'] and not receipt['remaining_automation'],'Final bytes need an actual clean kernel PASS.'
        assert (folder/'checks'/digest/'Solution.lean').read_text()==source
        (folder/'Solution.lean').write_text(source)
        result.update(verified=True,source_sha256=digest,proof_bytes=str(folder/'Solution.lean'))
    else:
        assert result['decision']=='cannot_repair';result['verified']=False
    result.update(model=MODEL,effort=EFFORT);base.write(folder/'decision.json',result);return result

def prompt(row,work,feedback):
    checker=f'python3 {HERE}/repair_proofs.py check --task {row["task_id"]} --work {work}'
    return f'''# Repair one Lean proof with explicit steps

**TLDR:** Write a genuinely repaired proof of the identical target statement, verify it with the provided checker, and explain it concisely. You may now write new proof bodies and helper lemmas; the previous existing-alternative-only restriction is lifted for this assignment.

{base.PREAPPROVAL}

You are {MODEL}, high reasoning, on the explicitly authorized lab-key Codex CLI route. Your case folder is {work}. Read its input.json and the saved diagnostics. All task inputs are public Workbook material. Cached Mathlib source is /lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src/.lake/packages/mathlib. You may search that source for exact lemma names and signatures. No additional model calls are assigned.

Write proof.lean (ONLY the tactic body, without an outer by), support.lean (optional helper lemmas, notation compatibility and reasonable Lean resource options), and sketch.txt (2–8short English lines describing the mathematical proof). The coordinator inserts the unchanged target statement and imports. Preserve the mathematical statement, name, domains and every hypothesis. Keep compatibility notation semantically faithful; do not redefine mathematics or add assumptions. If the statement is actually false or mismatched, report cannot_repair with a precise explanation instead of changing it.

Replace search/broad automation with named lemmas and explicit reasoning. Avoid all these tokens: {json.dumps(selection.AUTOMATION)}. Plain exact, apply, rw, rfl, change, intro, have, calc, constructors, cases, induction and explicit linear_combination with supplied coefficients are fine. Do not hide discouraged tactics inside wrappers. No sorry, admit, declared axioms or native_decide. Keep proofs as concise as possible without obfuscation; aim below1000assistant tokens where practical, with a hard16384conversation-token cap at final assembly. Add short English comments every few meaningful proof lines and more at tricky steps; top sketch explains the actual method, not private reasoning.

The initial support file provides legacy finite-sum/product notation when needed. You may fix actual proof errors, use current Mathlib lemma names, add proved helper lemmas, and adjust resource options if needed. Prefer mathematical lemmas over enormous closed-term computation. All named target/helper theorems must pass the same kernel/axiom gate.

Run `{checker}` after writing candidate files. It snapshots exact source bytes, checks the unchanged statement and automation policy, then runs pinned Lean4.22/kernel checks. You have at most8distinct candidate hashes across both CLI attempts,60seconds per compiler operation, and a900-second CLI turn. Use only this bounded compilation helper. Full compiler artifacts live under the returned kernel evidence directory; inspect compile logs for multiline type-inference diagnostics. A failure or timeout is not a proof of falsehood. You must get passed=true for the final exact bytes; call the checker again if you edit them afterward. A shorter successful explicit proof is preferred to an automated fallback; unresolved is acceptable when the fixed budget cannot establish a proof.

Return JSON only with task_id, decision=repaired or cannot_repair, and a concise rationale. For repaired, your three task files must be final and have a checker PASS. Preserve all coordinator inputs and old evidence. Work only in this case folder. Complete this assigned case within its bounds, retaining an honest failed outcome if necessary.

Prior feedback for this attempt: {json.dumps(feedback)}
'''

def worker(lane,once=False):
    lane_root=ROOT/'workers'/f'lane_{lane:02d}'
    env=dict(os.environ,CODEX_HOME=str(ROOT/'runtime'/f'lane_{lane:02d}'),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY']=(Path.home()/'.config/rl4cv-tiny/lab-openai.key').read_text().strip()
    while True:
        folder=claim(lane)
        if folder is None:return
        row=json.loads((folder/'input.json').read_text());work=lane_root/folder.name;work.mkdir(exist_ok=True)
        prior_status=json.loads((folder/'status.json').read_text())
        previous=Path(prior_status.get('work',str(work)))
        for name in ['proof.lean','support.lean','sketch.txt']:
            if previous!=work and (previous/name).exists() and not (work/name).exists():(work/name).write_bytes((previous/name).read_bytes())
        (work/'input.json').write_bytes((folder/'input.json').read_bytes())
        for name,text in [('support.lean',LEGACY if 'syntax_compatibility' in row['diagnostic_types'] else ''),('proof.lean',''),('sketch.txt','')]:
            if not (work/name).exists():(work/name).write_text(text)
        state=json.loads((folder/'status.json').read_text());feedback=None;success=False
        for attempt in range(state.get('attempts',0),2):
            output=folder/f'output_{attempt}.json';brief=prompt(row,work,feedback);(folder/f'prompt_{attempt}.md').write_text(brief)
            command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m',MODEL,'-c',f'model_reasoning_effort="{EFFORT}"','--json','--output-schema',str(ROOT/'schema.json'),'-o',str(output),'-']
            with (folder/f'cli_{attempt}.jsonl').open('x') as stream:
                process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,cwd=lane_root,env=env,text=True,start_new_session=True)
                status=dict(state='RUNNING',lane=lane,work=str(work),pid=process.pid,driver_pid=os.getpid(),attempts=attempt+1,attempt=attempt,model=MODEL,effort=EFFORT,started_unix=time.time())
                base.write(folder/'status.json',status);process.stdin.write(brief);process.stdin.close()
                try:process.wait(timeout=900)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGTERM)
                    try:process.wait(timeout=10)
                    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
            try:
                assert process.returncode==0,f'CLI returned {process.returncode}'
                result=validate(folder,work,output)
                base.write(folder/'status.json',dict(status,state='DONE',decision=result['decision'],verified=result['verified'],finished_unix=time.time()));success=True;break
            except Exception as exc:
                feedback=dict(error=repr(exc));base.write(folder/f'error_{attempt}.json',feedback)
                if process.returncode:
                    text=(folder/f'cli_{attempt}.jsonl').read_text(errors='replace').lower()
                    if any(t in text for t in ['insufficient_quota','billing_hard_limit','invalid_api_key','incorrect api key','error 401']):base.write(ROOT/'provider_hold.json',dict(case=folder.name,attempt=attempt,error='Provider funding/authentication hold; no alternate key or model used.',observed_unix=time.time()))
                    break
        if not success:base.write(folder/'status.json',dict(status,state='BLOCKED',error=feedback,finished_unix=time.time()))
        if once:return

def launch(first=False):
    for lane in ([0] if first else range(LANES)):
        name=f'codex-rl4cv-sol-repair-v11-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        command=f'python3 -u {HERE}/repair_proofs.py worker --lane {lane}'+(' --once' if first else '')+f' >> {ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'
        subprocess.run(['tmux','new-session','-d','-s',name,command],check=True)

def summarize():
    states=collections.Counter();decisions=collections.Counter();verified=0
    for p in (ROOT/'cases').glob('*/status.json'):
        r=json.loads(p.read_text());states[r['state']]+=1;verified+=bool(r.get('verified'));decisions.update([r['decision']] if r.get('decision') else [])
    result=dict(declared=68,states=dict(states),decisions=dict(decisions),verified=verified,observed_unix=time.time());base.write(ROOT/'progress.json',result);return result

def selftest():
    global ROOT
    ROOT=ROOT/'checker_controls'
    tid='control';folder=ROOT/'cases'/tid;work=ROOT/'workers/lane_00'/tid;work.mkdir(parents=True,exist_ok=True)
    row=dict(formal_statement='theorem repairV11Control : True := by sorry')
    base.write(folder/'input.json',row)
    (work/'support.lean').write_text('')
    (work/'sketch.txt').write_text('Use the constructor proving True.\nThe named constructor directly inhabits the unchanged proposition.\n')
    (work/'proof.lean').write_text('exact True.intro\n')
    assert verify(tid,work)['passed']
    (work/'proof.lean').write_text('skip\n')
    assert not verify(tid,work)['passed']
    (work/'proof.lean').write_text('exact?\n')
    result=verify(tid,work);assert not result['passed'] and result['remaining_automation']==['exact?']
    base.write(ROOT/'completion.json',dict(state='PASS',positive_kernel=True,unsolved_negative=True,automation_negative=True,observed_unix=time.time()))
    print('Actual positive/unsolved-negative and automation-policy controls PASS.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','launch','worker','check','status','selftest']);parser.add_argument('--lane',type=int);parser.add_argument('--first',action='store_true');parser.add_argument('--once',action='store_true');parser.add_argument('--task');parser.add_argument('--work',type=Path);args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='launch':launch(args.first)
    elif args.action=='worker':worker(args.lane,args.once)
    elif args.action=='selftest':selftest()
    elif args.action=='check':print(json.dumps(verify(args.task,args.work),ensure_ascii=False)[:22000])
    else:print(json.dumps(summarize()))
