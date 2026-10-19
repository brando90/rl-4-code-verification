"""Rewrite only parsed proof terms in the 2,585 original training answers with bounded Terra workers."""
from __future__ import annotations
import argparse
import collections
from dataclasses import asdict
import fcntl
import functools
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
import budget_ledger as budget

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'expt_v9'),str(HERE.parent/'expt_v8')]
import prefer_explicit as selection
from prefer_explicit import base
RUN=budget.RUN
ROOT=RUN/'lean_corpus_v13'
SOURCE=RUN/'onep7/data/existing.jsonl'
SOURCE_SHA='7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b'
MODEL,EFFORT,LANES='gpt-5.6-terra','high',32
FROZEN=RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py'
TOKENIZER='/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
RESERVE=10.0
STOP_ESTIMATE=1.2

@functools.lru_cache(maxsize=1)
def kernel_module():
    spec=importlib.util.spec_from_file_location('cleanup_frozen_kernel',FROZEN)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module

def automation(code):
    return sorted(set(selection.PATTERN.findall(kernel_module().strip_comments(code))))

def saved_alternatives():
    """Look for saved proofs only when the entire non-proof file context agrees."""
    groups=collections.defaultdict(list);inputs={}
    for folder in sorted((ROOT/'cases').iterdir()):
        if not (folder/'input.json').exists():continue
        row=json.loads((folder/'input.json').read_text());source=(folder/'Original.lean').read_text()
        spans=sorted(row['ranges']+row['preserved_proofs'],key=lambda r:r['start'])
        skeleton=source
        for span in reversed(spans):skeleton=skeleton[:span['start']]+' PROOF '+skeleton[span['end']:]
        key=' '.join(kernel_module().strip_comments(skeleton,keep_literals=True).split())
        groups[base.sha(key)].append(folder.name);inputs[folder.name]=(row,spans)
    count=0
    for ids in groups.values():
        for tid in ids:
            row,spans=inputs[tid];matches={}
            for target in row['ranges']:
                position=next(i for i,s in enumerate(spans) if s['index']==target['index'])
                for other in ids:
                    if other==tid:continue
                    alt=inputs[other][1][position]
                    if not automation(alt['original']):
                        matches[str(target['index'])]=dict(source_case=other,proof=alt['original'],proof_sha256=base.sha(alt['original']));break
            count+=len(matches);base.write(ROOT/'cases'/tid/'saved_alternatives.json',matches)
    result=dict(scanned_original_answers=len(inputs),exact_nonproof_context_groups=len(groups),matching_explicit_proof_terms=count,observed_unix=time.time())
    base.write(ROOT/'saved_alternative_summary.json',result);return result

def prepare():
    assert base.sha(SOURCE.read_bytes())==SOURCE_SHA
    ROOT.mkdir(parents=True,exist_ok=True)
    assert not list((ROOT/'cases').glob('*/cli_*.jsonl')),'Paid dispatch already started; inputs frozen.'
    parse_file=ROOT/'parse_results.jsonl'
    complete_cache=False
    if parse_file.exists():
        parsed_rows=[]
        for line in parse_file.read_text().splitlines():
            try:record=json.loads(line)
            except json.JSONDecodeError:continue
            if 'path' in record:parsed_rows.append(record)
        complete_cache=len(parsed_rows)==2585 and not any(r.get('error') for r in parsed_rows)
        if not complete_cache:parse_file.rename(ROOT/f'parse_results_preflight_{int(time.time())}.jsonl')
    rows=base.read_rows(SOURCE);assert len(rows)==2585
    paths=[]
    for i,row in enumerate(rows):
        folder=ROOT/'cases'/f'existing_{i:04d}';folder.mkdir(parents=True,exist_ok=True)
        base.write(folder/'original.json',row)
        answer=row['messages'][-1]['content']
        matches=list(re.finditer(r'(?m)^FILE: ([^\n]+)\n```lean\n(.*?)^```\s*$',answer,re.S|re.M))
        if len(matches)!=1:
            base.write(folder/'status.json',dict(state='FALLBACK',reason='Unsupported original FILE envelope; original retained.'));continue
        source=matches[0].group(2)
        assert base.sha(source)==row['lean_sha256'],folder.name
        (folder/'Original.lean').write_text(source)
        (folder/'status.json').unlink(missing_ok=True)
        base.write(folder/'envelope.json',dict(path=matches[0].group(1),prefix=answer[:matches[0].start(2)],suffix=answer[matches[0].end(2):]))
        paths.append(str(folder/'Original.lean'))
    (ROOT/'source_paths.txt').write_text('\n'.join(paths)+'\n')
    leanbin='/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin'
    env=dict(os.environ,PATH=str(RUN/'bin')+':'+leanbin+':'+os.environ['PATH'],CUDA_VISIBLE_DEVICES='')
    if not complete_cache:
        with (ROOT/'parse_results.jsonl').open('w') as stream:
            subprocess.run(['lake','env','lean','--run',str(HERE/'proof_ranges.lean'),str(ROOT/'source_paths.txt')],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=900)
    parsed={}
    for line in (ROOT/'parse_results.jsonl').read_text().splitlines():
        try:r=json.loads(line)
        except json.JSONDecodeError:continue
        if 'path' in r:parsed[r['path']]=r
    manifest=[]
    for i,row in enumerate(rows):
        folder=ROOT/'cases'/f'existing_{i:04d}'
        if (folder/'status.json').exists():
            manifest.append(dict(task_id=folder.name,index=i,targets=0));continue
        source=(folder/'Original.lean').read_text();raw=source.encode();ranges=parsed.get(str(folder/'Original.lean'),{})
        targets=[];preserved=[]
        for n,item in enumerate(ranges.get('ranges',[])):
            a=len(raw[:item['start_byte']].decode());b=len(raw[:item['end_byte']].decode())
            proof=source[a:b];found=automation(proof)
            command=raw[item['command_start_byte']:item['command_end_byte']].decode()
            anonymous=item['kind'].endswith('.example')
            native_test=anonymous and 'native_decide' in found
            item.update(index=n,start=a,end=b,original=proof,statement=command[:len(raw[item['command_start_byte']:item['start_byte']].decode())],automation=found,anonymous=anonymous)
            if found and not native_test:targets.append(item)
            else:preserved.append(item)
        inp=dict(task_id=folder.name,index=i,source_task_id=row['task_id'],source=row['source'],ranges=targets,preserved_proofs=preserved,original_sha256=base.sha(source),parser_error=ranges.get('error'))
        base.write(folder/'input.json',inp)
        state='PENDING' if targets else 'FALLBACK' if ranges.get('error') or not ranges.get('ranges') else 'UNCHANGED'
        base.write(folder/'status.json',dict(state=state,attempts=0,reason=ranges.get('error','No targeted automation in parsed proof bodies.')))
        manifest.append(dict(task_id=folder.name,index=i,targets=len(targets),assistant_tokens=row['n_assistant_tokens'],input_sha256=base.sha((folder/'input.json').read_bytes())))
    base.write(ROOT/'manifest.json',manifest)
    template=ROOT/'worker_template';template.mkdir(exist_ok=True);subprocess.run(['git','init','-q',str(template)],check=True)
    (template/'AGENTS.md').write_text('Perform the assigned teacher proof rewrite in its case folder using the coordinator checker. Preserve the fixed training task. The coordinator owns inputs, budgets and publication.\n')
    subprocess.run(['git','-C',str(template),'add','AGENTS.md'],check=True)
    if subprocess.run(['git','-C',str(template),'rev-parse','HEAD'],capture_output=True).returncode:
        subprocess.run(['git','-C',str(template),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize isolated original-pool proof workers'],check=True)
    config=(RUN/'lean_corpus_v11/runtime/lane_00/config.toml').read_text()
    assert 'TINY_OPENAI_API_KEY' in config and 'api.openai.com' in config
    for lane in range(LANES):
        work=ROOT/'workers'/f'lane_{lane:02d}'
        if not work.exists():subprocess.run(['git','-C',str(template),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile=ROOT/'runtime'/f'lane_{lane:02d}';profile.mkdir(parents=True,exist_ok=True);(profile/'config.toml').write_text(config)
    schema=dict(type='object',additionalProperties=False,required=['task_id','decision','rationale'],properties=dict(task_id=dict(type='string'),decision=dict(type='string',enum=['cleaned','unresolved']),rationale=dict(type='string')))
    base.write(ROOT/'schema.json',schema)
    base.write(ROOT/'dispatch.json',dict(cases=2585,model=MODEL,effort=EFFORT,lanes=32,compiler_slots=16,max_cli_attempts=2,max_candidate_hashes=4,compiler_timeout_seconds=120,cli_timeout_seconds=900,initial_cleanup_cap_usd=240,authorized_cleanup_cap_usd=480,per_attempt_reserved_usd=RESERVE,per_attempt_observed_stop_usd=STOP_ESTIMATE,rate_source='local api_budget_guard/config.toml; configured estimate, not invoice',rates_per_million=budget.RATES,credential='explicitly authorized lab key through Codex CLI; private LFS file',source_sha256=SOURCE_SHA,inspector_sha256=base.sha(FROZEN.read_bytes()),created_unix=time.time()))
    print(json.dumps(summarize()),flush=True)

def claim(lane):
    if (ROOT/'provider_hold.json').exists():return None
    with (ROOT/'queue.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        manifest=json.loads((ROOT/'manifest.json').read_text())
        # Short complete files first provide actual progress and a measured cost estimate.
        for item in sorted(manifest,key=lambda r:(r.get('assistant_tokens',999999),r['index'])):
            folder=ROOT/'cases'/item['task_id'];status=json.loads((folder/'status.json').read_text())
            if status['state']=='PENDING':
                base.write(folder/'status.json',dict(status,state='CLAIMED',lane=lane,driver_pid=os.getpid(),claimed_unix=time.time()));return folder

def assemble(folder,work):
    row=json.loads((folder/'input.json').read_text());source=(folder/'Original.lean').read_text()
    assert base.sha(source)==row['original_sha256']
    proposals=json.loads((work/'proofs.json').read_text())
    assert set(proposals)=={str(r['index']) for r in row['ranges']},'Supply every and only targeted proof.'
    sketch=(work/'sketch.txt').read_text().strip().splitlines();assert 2<=len(sketch)<=10
    assert all(0<len(line)<=400 and '-/' not in line for line in sketch)
    for item in reversed(row['ranges']):
        proof=proposals[str(item['index'])].strip()
        assert proof.startswith('by\n') or proof.startswith('by '),'Each replacement is a by proof.'
        assert not automation(proof),f'Discouraged automation: {automation(proof)}'
        masked=kernel_module().strip_comments(proof)
        assert not re.search(r'\b(sorry|admit|axiom|run_tac|run_cmd|unsafe|elab|macro)\b',masked)
        # Indent the entire proof term relative to the unchanged statement.
        indent=' '*(len(source[:item['start']].rsplit('\n',1)[-1])-len(source[:item['start']].rsplit('\n',1)[-1].lstrip()))
        lines=proof.splitlines();proof=lines[0]+'\n'+'\n'.join(indent+line for line in lines[1:])
        source=source[:item['start']]+proof+source[item['end']:]
    # Imports retain their original leading position, as the benchmark requires.
    imports=list(re.finditer(r'(?m)^import [^\n]+\n',source));assert imports
    at=imports[-1].end();comment='\n/- Proof sketch:\n'+'\n'.join(sketch)+'\n-/\n'
    return source[:at]+comment+source[at:]

def verify(task,work):
    folder=ROOT/'cases'/task
    with (folder/'check.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        source=assemble(folder,work);digest=base.sha(source);target=folder/'checks'/digest;receipt=target/'result.json'
        if receipt.exists():return json.loads(receipt.read_text())
        assert len(list((folder/'checks').glob('*')))<4,'At most four distinct candidate hashes.'
        target.mkdir(parents=True);path=target/'Solution.lean';path.write_text(source)
        slot=None;deadline=time.time()+600
        while slot is None and time.time()<deadline:
            for n in range(16):
                handle=(ROOT/f'compiler_{n:02d}.lock').open('a')
                try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);slot=handle;break
                except BlockingIOError:handle.close()
            if slot is None:time.sleep(.25)
        assert slot is not None,'Compiler queue wait exceeded ten minutes.'
        kernel=kernel_module();result=dict(task_id=task,source_sha256=digest,passed=False,scope_gate='construction_only_original_proof_terms',checked_unix=time.time())
        try:
            os.environ.pop('TINY_OPENAI_API_KEY',None);os.environ['PATH']=str(RUN/'bin')+':'+os.environ['PATH']
            report=kernel.check_file(str(path),str(RUN/'grading'),timeout=120,allow_native_decide=False,keep_dir=str(target/'kernel'))
            data=asdict(report);base.write(target/'kernel_report.json',data)
            result.update(passed=bool(kernel.valid_report(data) and report.n_theorems>=1 and report.n_honest==report.n_theorems and report.source_sha256==digest),kernel_report=data)
        finally:slot.close()
        base.write(receipt,result);return result

def prompt(folder,work,feedback):
    return f'''# Rewrite one complete Python-to-Lean training answer

**TLDR:** Replace broad automation in the supplied parsed proof bodies with concise explicit proofs. Keep the actual implementation, specifications and tests unchanged. Include a short proof sketch and explanations every few meaningful proof lines, with more around tricky steps.

{base.PREAPPROVAL}

You are {MODEL}, high effort, on the explicitly authorized lab-key Codex CLI route. Your case is {folder.name}. Work in {work}, reading Original.lean, input.json and training_prompt.txt. These are training-split materials. The coordinator reconstructs the entire file by replacing only the listed proof terms; it preserves every statement, namespace, definition, API and original concrete native_decide test. All targeted named AND anonymous mathematical proofs must avoid: {json.dumps(selection.AUTOMATION)}. Plain exact, apply, rw, rfl, change, calc, constructors, induction, cases, explicit linear_combination and named mathematical lemmas are allowed. Do not conceal automation in wrappers, rename statements, weaken hypotheses, or remove proof obligations. Helpers can be local have/let proofs inside the original proof term. No sorry, admit, new axioms, unsafe/elaborator escape hatches or native_decide in replacements.

Write proofs.json: an object mapping each target proof's numeric index (as a string) to its replacement complete Lean term beginning `by`. Supply every listed target. Keep their existing local binder names available from the unchanged statement. Write sketch.txt with2–10short English lines explaining the main mathematical methods in the file. Do not reproduce private reasoning; explain the finished construction. Keep it concise without obfuscation. Original answers can be long; the final full prompt+answer must fit16384Qwen tokens.

Read saved_alternatives.json when present and prefer its exact-context explicit proof for the listed target. Otherwise write the replacement. You may inspect current Mathlib source at /lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src/.lake/packages/mathlib for lemma names. Use the coordinator command `python3 {HERE}/clean_existing.py check --task {folder.name} --work {work}`. It snapshots exact final bytes, enforces proof policy, and invokes pinned Lean4.22/kernel checking of every named theorem. Original anonymous native_decide tests remain valid executable tests. At most4distinct candidate hashes and120seconds/compiler operation across both CLI attempts,900seconds this turn. Read returned diagnostics and repair within this budget. Full compiler logs are under the result's evidence directory. Do not run extra direct Lean probes or new model calls; the coordinator owns these fixed budgets.

Return JSON task_id={folder.name}, decision=cleaned or unresolved, rationale. cleaned requires the exact final files to have checker passed=true; any subsequent edit needs a new checker pass. An unresolved answer is retained honestly with the original as separately flagged fallback. Previous feedback: {json.dumps(feedback)}
'''

def usage(profile,started):
    total={};found=False;window=0
    for path in profile.glob('sessions/**/*.jsonl'):
        if path.stat().st_mtime<started:continue
        last=None
        for line in path.read_text(errors='replace').splitlines():
            try:r=json.loads(line)
            except json.JSONDecodeError:continue
            p=r.get('payload',{})
            if r.get('type')=='event_msg' and p.get('type')=='token_count' and p.get('info'):
                last=p['info']['total_token_usage'];window=max(window,p['info'].get('model_context_window',0) or 0)
        if last:
            found=True
            for k,v in last.items():total[k]=total.get(k,0)+v
    return total if found else None,window

def stop(process):
    if process.poll() is not None:return
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()

def worker(lane,once=False):
    lane_root=ROOT/'workers'/f'lane_{lane:02d}';profile=ROOT/'runtime'/f'lane_{lane:02d}'
    env=dict(os.environ,CODEX_HOME=str(profile),CUDA_VISIBLE_DEVICES='',TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY']=(RUN/'.private/lab-openai.key').read_text().strip()
    while True:
        folder=claim(lane)
        if folder is None:return
        work=lane_root/folder.name;work.mkdir(exist_ok=True)
        previous_status=json.loads((folder/'status.json').read_text())
        previous=Path(previous_status.get('work',str(work)))
        if previous!=work:
            for name in ['proofs.json','sketch.txt']:
                if (previous/name).exists() and not (work/name).exists():(work/name).write_bytes((previous/name).read_bytes())
        for name in ['input.json','Original.lean','saved_alternatives.json']:
            if (folder/name).exists():(work/name).write_bytes((folder/name).read_bytes())
        row=json.loads((folder/'original.json').read_text());(work/'training_prompt.txt').write_text(row['messages'][1]['content'])
        inp=json.loads((folder/'input.json').read_text())
        if not (work/'proofs.json').exists():base.write(work/'proofs.json',{str(r['index']):r['original'] for r in inp['ranges']})
        if not (work/'sketch.txt').exists():(work/'sketch.txt').write_text('')
        feedback=None;success=False;status={}
        for attempt in range(int(previous_status.get('attempts',0)),2):
            identity=f'v13/{folder.name}/{attempt}'
            output=folder/f'output_{attempt}.json';brief=prompt(folder,work,feedback);(folder/f'prompt_{attempt}.md').write_text(brief)
            command=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m',MODEL,'-c',f'model_reasoning_effort="{EFFORT}"','-c','model_context_window=128000','-c','model_auto_compact_token_limit=100000','--json','--output-schema',str(ROOT/'schema.json'),'-o',str(output),'-']
            def on_start(pid,started):
                nonlocal status
                status=dict(state='RUNNING',lane=lane,work=str(work),pid=pid,driver_pid=os.getpid(),attempts=attempt+1,attempt=attempt,model=MODEL,effort=EFFORT,started_unix=started,budget_identity=identity)
                base.write(folder/'status.json',status)
            run=budget.run_cli(command,env,brief,'cleanup',identity,profile,lane_root,folder/f'cli_{attempt}.jsonl',reservation=RESERVE,stop_at=STOP_ESTIMATE,on_start=on_start)
            if run['state']=='BUDGET_HOLD':
                base.write(folder/'status.json',dict(state='BUDGET_HOLD',attempts=attempt,reason='Configured-price cleanup cap including in-flight reservations.'));return
            cap_reason=run.get('stop_reason');base.write(folder/f'usage_{attempt}.json',run)
            try:
                assert run['returncode']==0,f'CLI returned {run["returncode"]};{cap_reason}'
                result=json.loads(output.read_text());assert result['task_id']==folder.name
                if result['decision']=='cleaned':
                    source=assemble(folder,work);digest=base.sha(source);receipt=json.loads((folder/'checks'/digest/'result.json').read_text());assert receipt['passed']
                    (folder/'Solution.lean').write_text(source);result.update(verified=True,source_sha256=digest)
                else:result['verified']=False
                base.write(folder/'decision.json',result);base.write(folder/'status.json',dict(status,state='DONE',decision=result['decision'],verified=result['verified'],finished_unix=time.time()));success=True;break
            except Exception as exc:
                feedback=dict(error=repr(exc));base.write(folder/f'error_{attempt}.json',feedback)
                text=(folder/f'cli_{attempt}.jsonl').read_text(errors='replace').lower()
                if any(t in text for t in ['insufficient_quota','billing_hard_limit','invalid_api_key','incorrect api key','error401','error 401']):
                    base.write(ROOT/'provider_hold.json',dict(case=folder.name,error='Provider funding/authentication hold; original fallback retained.',observed_unix=time.time()));break
                if cap_reason:break
        if not success:base.write(folder/'status.json',dict(status,state='FALLBACK',error=feedback,finished_unix=time.time()))
        if once:return

def launch(first=False):
    for lane in (range(4) if first else range(LANES)):
        name=f'codex-rl4cv-terra-clean-v13-{lane:02d}'
        if subprocess.run(['tmux','has-session','-t',name],capture_output=True).returncode==0:continue
        command=f'python3 -u {shlex.quote(str(HERE/"clean_existing.py"))} worker --lane {lane}'+(' --once' if first else '')+f' >> {ROOT}/workers/lane_{lane:02d}/driver.log 2>&1'
        subprocess.run(['tmux','new-session','-d','-s',name,command],check=True)

def summarize():
    states=collections.Counter();verified=0
    for p in (ROOT/'cases').glob('*/status.json'):
        r=json.loads(p.read_text());states[r['state']]+=1;verified+=bool(r.get('verified'))
    result=dict(declared=2585,states=dict(states),verified=verified,observed_unix=time.time())
    base.write(ROOT/'progress.json',result);return result

def selftest():
    global ROOT
    ROOT=ROOT/'checker_controls'
    folder=ROOT/'cases/control';work=ROOT/'workers/lane_00/control';work.mkdir(parents=True,exist_ok=True)
    source='import Mathlib\n\ndef unchangedImplementation (n : Nat) := n + 1\ntheorem immutableStatement : True := by exact True.intro\nexample : unchangedImplementation 1 = 2 := by native_decide\n'
    start=source.index('by exact');end=start+len('by exact True.intro')
    base.write(folder/'input.json',dict(original_sha256=base.sha(source),ranges=[dict(index=0,start=start,end=end)]))
    (folder/'Original.lean').write_text(source)
    (work/'sketch.txt').write_text('Use the constructor of True for the named theorem.\nKeep the implementation and concrete native test unchanged.\n')
    base.write(work/'proofs.json',{'0':'by\n  exact True.intro'})
    assert verify('control',work)['passed']
    result=assemble(folder,work);assert 'def unchangedImplementation (n : Nat) := n + 1' in result
    assert 'example : unchangedImplementation 1 = 2 := by native_decide' in result
    base.write(work/'proofs.json',{'0':'by\n  skip'})
    assert not verify('control',work)['passed']
    base.write(work/'proofs.json',{'0':'by\n  exact?'})
    try:assemble(folder,work)
    except AssertionError:pass
    else:raise AssertionError('Automation policy negative must fail.')
    # Test session token consumption and the same configured-price stop without any model call.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'sessions/one.jsonl';path.parent.mkdir()
        path.write_text(json.dumps(dict(type='event_msg',payload=dict(type='token_count',info=dict(total_token_usage=dict(input_tokens=300000,cached_input_tokens=0,output_tokens=1),model_context_window=128000))))+'\n')
        observed,window=budget.session_usage(Path(td),0)
        assert window==128000 and budget.charge_estimate(observed)>STOP_ESTIMATE
    base.write(ROOT/'completion.json',dict(state='PASS',positive_kernel=True,unsolved_negative=True,automation_negative=True,implementation_and_native_test_preserved=True,synthetic_usage_stop=True,observed_unix=time.time()))
    print('Pinned kernel positive/negative, proof-only scope and synthetic usage-stop controls PASS.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','launch','worker','check','status','selftest','alternatives']);p.add_argument('--lane',type=int);p.add_argument('--first',action='store_true');p.add_argument('--once',action='store_true');p.add_argument('--task');p.add_argument('--work',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='launch':launch(a.first)
    elif a.action=='worker':worker(a.lane,a.once)
    elif a.action=='selftest':selftest()
    elif a.action=='alternatives':print(json.dumps(saved_alternatives()))
    elif a.action=='check':print(json.dumps(verify(a.task,a.work),ensure_ascii=False)[:24000])
    else:print(json.dumps(summarize()))
