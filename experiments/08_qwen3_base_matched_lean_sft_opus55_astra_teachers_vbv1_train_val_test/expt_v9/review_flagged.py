"""Have Sol reconcile flagged Workbook proofs using only supplied alternatives and bounded kernel checks."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import prefer_explicit as selection
from prefer_explicit import base
from comment_integrity import insert_comments

HERE=Path(__file__).resolve().parent
ROOT=selection.ROOT/'review'
MODEL=os.environ.get('PROOF_REVIEW_MODEL','gpt-6.1-sol')
EFFORT='medium' if MODEL=='gpt-5.6-terra' else 'high'
LANES=64


def lane_name(lane):
    return ('terra_' if MODEL=='gpt-5.6-terra' else '')+f'lane_{lane:03d}'


def setup_terra():
    template=ROOT/'worker_template'
    config=(selection.RUN.parent/'rl4cv_tiny_curriculum/runtime/codex_profiles/natural_arithmetic/config.toml').read_text()
    for lane in range(LANES):
        name=f'terra_lane_{lane:03d}';work=ROOT/'workers'/name
        if not work.exists():subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/name;profile.mkdir(parents=True,exist_ok=True)
        (profile/'config.toml').write_text(config.replace('model_reasoning_effort = "high"','model_reasoning_effort = "medium"'))
    schema=json.loads((ROOT/'schema.json').read_text())
    schema['properties']['decision']['enum']=['keep_original','use_alternative','reject_statement','unresolved','needs_sol']
    base.write(ROOT/'schema.json',schema)


def prepare():
    if (ROOT/'dispatch.json').exists():raise RuntimeError('review already frozen')
    rows=base.read_rows(selection.ROOT/'selection.jsonl')
    workbook=json.loads(base.SOURCE.read_text())
    flagged=[r for r in rows if r['kind']=='workbook' and r['baseline_annotation_issue']]
    ROOT.mkdir(parents=True,exist_ok=True)
    for row in flagged:
        item=workbook[row['source_row']]
        data=dict(row,all_proof_alternatives=item['proof'])
        folder=ROOT/'cases'/row['task_id']
        base.write(folder/'input.json',data);base.write(folder/'status.json',dict(state='PENDING',attempts=0))
    schema=dict(type='object',additionalProperties=False,required=['task_id','decision','proof_index','rationale','comments'],properties=dict(
        task_id=dict(type='string'),decision=dict(type='string',enum=['keep_original','use_alternative','reject_statement','unresolved']),
        proof_index=dict(type='integer'),rationale=dict(type='string'),comments=dict(type='array',items=dict(type='object',additionalProperties=False,
            required=['before_line','text'],properties=dict(before_line=dict(type='integer'),text=dict(type='string'))))))
    base.write(ROOT/'schema.json',schema)
    template=ROOT/'worker_template';template.mkdir()
    subprocess.run(['git','init','-q',str(template)],check=True)
    (template/'AGENTS.md').write_text('Reconcile the supplied proof case, use the provided bounded verifier, and return the requested final JSON. The coordinator owns datasets, assembly and publication.\n')
    subprocess.run(['git','-C',str(template),'add','AGENTS.md'],check=True)
    subprocess.run(['git','-C',str(template),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize isolated Sol proof review workers'],check=True)
    config=(selection.RUN.parent/'rl4cv_tiny_curriculum/runtime/codex_profiles/natural_arithmetic/config.toml').read_text()
    for lane in range(LANES):
        work=ROOT/'workers'/f'lane_{lane:03d}'
        subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/f'lane_{lane:03d}';profile.mkdir(parents=True)
        (profile/'config.toml').write_text(config.replace('gpt-5.6-terra',MODEL))
    base.write(ROOT/'dispatch.json',dict(cases=len(flagged),model=MODEL,effort=EFFORT,lanes=LANES,max_cli_attempts_per_case=2,
        max_distinct_checked_proofs_per_case=4,global_compiler_slots=24,compiler_operation_timeout_seconds=15,
        per_cli_timeout_seconds=600,worker_deadline_seconds=2700,estimated_cost_usd_range=[75,200],
        credential='previously explicitly authorized LAB_OPENAI_API_KEY via Codex CLI',source_sha256=base.SOURCE_SHA,
        driver_sha256=base.sha(Path(__file__).read_bytes()),created_unix=time.time()))
    print((ROOT/'dispatch.json').read_text(),flush=True)


def verify(tid,index):
    folder=ROOT/'cases'/tid
    row=json.loads((folder/'input.json').read_text())
    alternatives=row['all_proof_alternatives']
    if not 0<=index<len(alternatives):raise ValueError('proof index outside supplied collection')
    target=folder/'checks'/f'proof_{index:02d}'
    target.mkdir(parents=True,exist_ok=True)
    receipt=target/'result.json'
    if receipt.exists():return json.loads(receipt.read_text())
    with (folder/'check.lock').open('a') as per_case:
        fcntl.flock(per_case,fcntl.LOCK_EX)
        if receipt.exists():return json.loads(receipt.read_text())
        ledger=folder/'checked_indices.json'
        checked=json.loads(ledger.read_text()) if ledger.exists() else []
        if index not in checked:
            if len(checked)>=4:raise RuntimeError('four-candidate verification budget exhausted')
            checked.append(index);base.write(ledger,checked)
        lean=selection.assemble(row,alternatives[index])
        path=target/'Solution.lean';path.write_text(lean)
        slots=ROOT/'compiler_slots';slots.mkdir(exist_ok=True)
        lock=None;deadline=time.monotonic()+120
        while lock is None and time.monotonic()<deadline:
            for slot in range(24):
                candidate=(slots/str(slot)).open('a')
                try:fcntl.flock(candidate,fcntl.LOCK_EX|fcntl.LOCK_NB);lock=candidate;break
                except BlockingIOError:candidate.close()
            if lock is None:time.sleep(.2)
        if lock is None:raise TimeoutError('bounded compiler slot acquisition timed out')
        try:
            os.environ['PATH']=str(selection.RUN/'bin')+':'+os.environ['PATH']
            os.environ.pop('TINY_OPENAI_API_KEY',None)
            frozen=selection.RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py'
            spec=importlib.util.spec_from_file_location('workbook_review_kernel',frozen)
            kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
            report=kernel.check_file(str(path),str(selection.RUN/'grading'),timeout=15,allow_native_decide=False,keep_dir=str(target/'kernel'))
            full=asdict(report)
            result=dict(task_id=tid,proof_index=index,source_sha256=base.sha(lean),compile_rc=report.compile_rc,
                kernel_honest=bool(report.probe_ok and report.n_theorems>=1 and report.n_honest==report.n_theorems),
                passed=bool(report.compile_rc==0 and report.probe_ok and report.n_theorems>=1 and report.n_honest==report.n_theorems),
                avoid_tactics=selection.automations(alternatives[index]),kernel_report=full)
            base.write(receipt,result)
            return result
        finally:lock.close()


def brief(row,errors=None):
    command=f'python3 {HERE}/review_flagged.py check --task {row["task_id"]} --index INDEX'
    text=f'''# Reconcile one flagged Lean proof

**TLDR:** Decide whether this public proof candidate or its statement is actually problematic. Select a verified supplied proof for the identical formal statement and annotate it clearly, or record why the statement should be excluded.

{base.PREAPPROVAL}

The first annotator's flag is a hypothesis, not a verdict. Review the formal statement, the informal intent, original proof index0 and ALL supplied alternatives below. `exact?` is a legitimate Lean proof-search tactic that can close a goal; it is not a placeholder. Distinguish a valid proof falsely flagged, an invalid script, a bad formalization of the informal statement, and a vacuous statement. For a mismatched/vacuous statement, return reject_statement with a precise explanation; another proof cannot fix the unchanged statement.

For a sound, meaningful statement, prefer an existing proof without these tactics: {json.dumps(selection.AUTOMATION)}. Plain exact, apply, rw, rfl, intro, have, calc, constructors, cases and induction are fine. If the original is valid but uses discouraged automation, still look for a valid explicit alternative. If no suitable explicit alternative can be verified, retain a verified automated proof and explain the fallback. Select only a supplied index; do not invent a theorem or proof. Tools may run the bounded checker below on at most4distinct supplied indices total across both CLI attempts. Test the strongest explicit candidate(s) first, and check original0 when needed to resolve the flag. Do not claim a selected proof is valid without a PASS from that checker. Compiler timeout is unresolved, not mathematical invalidity. All source files, logs and proof indices are coordinator-owned immutable artifacts.

Checker command (replace INDEX): `{command}`. It uses the pinned Lean4.22 and frozen kernel inspector, preserves the allowed-axiom gate and all original attempts, and caches checks. It returns diagnostics and the path to the exact checked source. You can inspect those task-specific files to understand errors. No protected benchmark tasks, validation outputs, new model calls or broad corpus compilation are assigned.

Return the requested final JSON with decision keep_original (index0), use_alternative (another existing index), reject_statement, or unresolved. Reject/unresolved uses proof_index=-1 and comments=[]. For keep/use, write a concise rationale distinguishing original status and chosen replacement, then line-indexed comments for THE CHECKED selected Solution.lean. Put at least two header lines before line1; first starts exactly "Proof sketch:". Explain the mathematical idea and why the selected script proves it, and comment meaningful proof steps every few lines with more detail at tricky transitions. Comment text is printable English, at most360characters, with no -- prefix or block-comment delimiters. Preserve every source byte; the coordinator inserts comments mechanically. Output only the requested final JSON.

Case:
{json.dumps(row,ensure_ascii=False)}
'''
    if errors:text+='\nMechanical/verification repair feedback:\n'+json.dumps(errors)
    if MODEL=='gpt-5.6-terra':
        text+='\nRouting: you are the routine Terra verifier/annotator. Compiler and kernel receipts decide formal proof validity. Resolve routine false flags and select supplied alternatives. If the mathematical or formal/informal interpretation remains genuinely ambiguous, return decision needs_sol, proof_index=-1, comments=[], and a precise uncertainty. A mere compiler timeout or exhausted check budget is unresolved, not an automatic stronger-model escalation. Preserve the total four-candidate/two-CLI budget.\n'
    else:
        text+='\nRouting: you are the requested Sol reviewer for original flagged cases, a bounded policy continuation, or a genuinely ambiguous Terra escalation. If it cannot be resolved within the preserved budget, return unresolved; do not escalate to yourself.\n'
    return text+'\nTL;DR: Verify and explain one supplied proof for the unchanged statement, preferring explicit steps; exclude bad statements and retain honest unresolved outcomes.\n'


def claim(lane):
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for folder in sorted((ROOT/'cases').iterdir()):
            state=json.loads((folder/'status.json').read_text())
            allowed=('TERRA_PENDING',) if MODEL=='gpt-5.6-terra' else ('PENDING','ESCALATE_SOL')
            if state['state'] in allowed:
                base.write(folder/'status.json',dict(state,state='CLAIMED',lane=lane,model=MODEL,effort=EFFORT,driver_pid=os.getpid(),claimed_unix=time.time()))
                return folder


def check_output(folder,path):
    decision=json.loads(path.read_text());row=json.loads((folder/'input.json').read_text())
    assert decision['task_id']==row['task_id']
    if decision['decision'] in ('keep_original','use_alternative'):
        index=decision['proof_index']
        assert type(index) is int and 0<=index<len(row['all_proof_alternatives']),'selected index is not a supplied proof'
        expected_label='keep_original' if index==0 else 'use_alternative'
        if decision['decision']!=expected_label:
            decision['model_decision_label']=decision['decision']
            decision['decision']=expected_label
            decision['coordinator_label_normalization']='Decision label is relative to original public proof index0; selected index, source, rationale and comments are unchanged.'
        result=json.loads((folder/'checks'/f'proof_{index:02d}'/'result.json').read_text())
        assert result['passed'],'selected proof did not pass the actual verifier'
        source=selection.assemble(row,row['all_proof_alternatives'][index])
        assert result['source_sha256']==base.sha(source),'verification receipt is for different source bytes'
        annotated=insert_comments(source,decision['comments'])
        (folder/'Selected.lean').write_text(source);(folder/'Commented.lean').write_text(annotated)
        decision.update(verified=True,source_sha256=base.sha(source),annotated_sha256=base.sha(annotated),automation=selection.automations(row['all_proof_alternatives'][index]))
    else:
        assert decision['proof_index']==-1 and decision['comments']==[],'reject/unresolved/escalation must use index=-1 and comments=[]'
        decision['verified']=False
    state=json.loads((folder/'status.json').read_text())
    match=re.fullmatch(r'output_(\d+)',path.stem)
    route=folder/f'route_{match.group(1)}.json' if match else None
    attribution=json.loads(route.read_text()) if route and route.exists() else state
    decision.update(review_model=attribution.get('model',MODEL),review_effort=attribution.get('effort',EFFORT))
    base.write(folder/'decision.json',decision)
    return decision


def worker(lane,once=False):
    work=ROOT/'workers'/lane_name(lane)
    env=dict(os.environ,CODEX_HOME=str(ROOT/'runtime'/lane_name(lane)),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY']=(Path.home()/'.config/rl4cv-tiny/lab-openai.key').read_text().strip()
    deadline=time.monotonic()+2700
    while time.monotonic()<deadline:
        folder=claim(lane)
        if folder is None:return
        row=json.loads((folder/'input.json').read_text());errors=None;success=False
        if (folder/'decision.json').exists():
            prior=json.loads((folder/'decision.json').read_text())
            if prior['decision']=='needs_sol':
                row['prior_terra_assessment']=prior
                base.write(folder/'terra_triage.json',prior)
        first_attempt=json.loads((folder/'status.json').read_text()).get('attempts',0)
        for attempt in range(first_attempt,2):
            output=folder/f'output_{attempt}.json';prompt=brief(row,errors)
            base.write(folder/f'route_{attempt}.json',dict(model=MODEL,effort=EFFORT,observed_unix=time.time()))
            (folder/f'prompt_{attempt}.md').write_text(prompt)
            command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check',
                '-m',MODEL,'-c',f'model_reasoning_effort="{EFFORT}"','--json','--output-schema',str(ROOT/'schema.json'),'-o',str(output),'-']
            with (folder/f'cli_{attempt}.jsonl').open('x') as stream:
                process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,cwd=work,env=env,text=True,start_new_session=True)
                process.stdin.write(prompt);process.stdin.close();started=time.monotonic()
                while process.poll() is None:
                    state=dict(state='RUNNING',lane=lane,task_id=row['task_id'],attempt=attempt,attempts=attempt+1,pid=process.pid,
                        driver_pid=os.getpid(),model=MODEL,effort=EFFORT,observed_unix=time.time())
                    base.write(folder/'status.json',state);base.write(ROOT/'status'/f'{lane_name(lane)}.json',state)
                    if time.monotonic()-started>600 or time.monotonic()>deadline:
                        os.killpg(process.pid,signal.SIGTERM)
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                        break
                    time.sleep(3)
            try:
                if process.returncode:raise RuntimeError(f'CLI exited {process.returncode}')
                result=check_output(folder,output)
                outcome='ESCALATE_SOL' if result['decision']=='needs_sol' and MODEL=='gpt-5.6-terra' and attempt<1 else 'DONE'
                base.write(folder/'status.json',dict(state=outcome,lane=lane,model=MODEL,effort=EFFORT,decision=result['decision'],verified=result['verified'],attempts=attempt+1,observed_unix=time.time()))
                success=True;break
            except Exception as exc:
                errors=dict(error=str(exc));base.write(folder/f'error_{attempt}.json',errors)
                if process.returncode:break
        if not success:base.write(folder/'status.json',dict(state='BLOCKED',lane=lane,error=errors,observed_unix=time.time()))
        if once:return


def launch(first=False):
    count=0
    for lane in ([0] if first else range(LANES)):
        tier='terra' if MODEL=='gpt-5.6-terra' else 'sol'
        name=f'codex-rl4cv-{tier}-proof-{lane:03d}'
        if subprocess.run(['tmux','has-session','-t',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:continue
        command=f'env PROOF_REVIEW_MODEL={MODEL} python3 -u {HERE}/review_flagged.py worker --lane {lane}'+(' --once' if first else '')+f' >> {ROOT}/workers/{lane_name(lane)}/driver.log 2>&1'
        subprocess.run(['tmux','new-session','-d','-s',name,command],check=True);count+=1
    print(json.dumps(dict(launched=count,model=MODEL,effort=EFFORT)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','launch','worker','check','setup-terra']);parser.add_argument('--lane',type=int)
    parser.add_argument('--first',action='store_true');parser.add_argument('--once',action='store_true');parser.add_argument('--task');parser.add_argument('--index',type=int)
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='setup-terra':setup_terra()
    elif args.action=='launch':launch(args.first)
    elif args.action=='worker':worker(args.lane,args.once)
    else:
        result=verify(args.task,args.index)
        print(json.dumps(dict(task_id=args.task,proof_index=args.index,passed=result['passed'],compile_rc=result['compile_rc'],
            kernel_honest=result['kernel_honest'],avoid_tactics=result['avoid_tactics'],source_file=str(ROOT/'cases'/args.task/'checks'/f'proof_{args.index:02d}'/'Solution.lean'),
            kernel_report=result['kernel_report']),ensure_ascii=False)[:18000])
