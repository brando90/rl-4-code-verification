"""Annotate pinned Workbook proof candidates with bounded parallel Codex CLI workers on SNAP."""
from __future__ import annotations

import argparse
import collections
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

from comment_integrity import insert_comments

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path(os.environ.get('TINY_RUN_ROOT', '/lfs/skampere1/0/eth127/rl4cv_tiny_training'))
ROOT = RUN / 'lean_corpus_v8/workbook_annotations'
SOURCE = RUN / 'lean_corpus_v8/sources/lean_workbook/lean_workbook.json'
SOURCE_SHA = '577430f83caf094f1d9b99c9a3d18d92130fa21e74939d1b528b39c1927a7b0c'
MODEL, EFFORT, BATCH_SIZE, LANES = 'gpt-5.6-terra', 'medium', 64, 100
PREAPPROVAL = 'SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).'


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    tmp.replace(path)


def read_rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def prepare():
    sys.path.insert(0, str(REPO / 'src'))
    from rl4cv.screens import screen
    assert sha(SOURCE.read_bytes()) == SOURCE_SHA
    if (ROOT / 'dispatch.json').exists():
        raise RuntimeError('dispatch already frozen; use launch or status')
    ROOT.mkdir(parents=True, exist_ok=True)
    protected = {}
    vb = RUN / 'repo/external/veribench'
    split = HERE.parent / 'expt_v1/results/split/vbv1_split_manifest.csv'
    for row in csv.DictReader(split.open()):
        if row['split'] in ('validation', 'test'):
            protected[row['task_id'] + '/python'] = (vb / 'veribench_dataset/py_src' / row['py_relpath']).read_text()
            protected[row['task_id'] + '/lean'] = (vb / 'veribench_dataset/lean_src/veribench' / row['gold_relpath']).read_text()
    assert len(protected) == 714
    for row in read_rows(RUN / 'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if row['cohort'] == 'fresh':
            protected[row['task_id'] + '/python'] = row['python']
    assert len(protected) == 764
    candidates, all_rows = [], json.loads(SOURCE.read_text())
    for index, row in enumerate(all_rows):
        if not row.get('proof'):
            continue
        statement, proof = row['formal_statement'], row['proof'][0]
        match = re.search(r'sorry\s*$', statement)
        assert match and re.search(r':=\s*by\s+sorry\s*$', statement)
        source = 'import Mathlib\nopen BigOperators Nat Real Rat\n\n' + statement[:match.start()].rstrip() + '\n'
        source += ''.join('  ' + line + '\n' for line in proof.splitlines())
        candidates.append(dict(task_id=f'workbook_{index:06d}', source_row=index, source_split=row['split'],
            natural_language_statement=row['natural_language_statement'], tags=row['tags'],
            formal_statement=statement, proof_index=0, proof=proof, lean=source,
            source_sha256=sha(source), original_statement_sha256=sha(statement), original_proof_sha256=sha(proof),
            verification='public_candidate_not_checked_on_current_toolchain'))
    assert len(candidates) == 12823
    pool = {r['task_id']: r['natural_language_statement'] + '\n' + r['lean'] for r in candidates}
    report = screen(pool, protected)
    # Screen individual formal statements too; a long assembled file cannot dilute a match.
    statements = screen({r['task_id']: r['formal_statement'] for r in candidates}, protected)
    write(ROOT / 'screening.json', dict(full=report, statements=statements, protected=764))
    clean = set(report['clean_ids']) & set(statements['clean_ids'])
    for row in candidates:
        row['screen_clean'] = row['task_id'] in clean
    manifest = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in candidates)
    (ROOT / 'manifest.jsonl').write_text(manifest)
    eligible = [r for r in candidates if r['screen_clean']]
    batches = [eligible[i:i+BATCH_SIZE] for i in range(0, len(eligible), BATCH_SIZE)]
    schema = dict(type='object', additionalProperties=False, required=['annotations'], properties=dict(annotations=dict(
        type='array', items=dict(type='object', additionalProperties=False, required=['task_id', 'comments', 'annotation_issue'], properties=dict(
            task_id=dict(type='string'), annotation_issue=dict(type='string'), comments=dict(type='array', items=dict(
                type='object', additionalProperties=False, required=['before_line','text'], properties=dict(
                    before_line=dict(type='integer'), text=dict(type='string')))))))))
    write(ROOT / 'schema.json', schema)
    base = ROOT / 'worker_template'
    base.mkdir(exist_ok=True)
    subprocess.run(['git', 'init', '-q', str(base)], check=True)
    (base / 'AGENTS.md').write_text('Annotate the supplied proof candidates. All required inputs are inline in each prompt. Return the requested JSON. The coordinator owns sources, assembly, validation, publication and progress.\n')
    subprocess.run(['git','-C',str(base),'add','AGENTS.md'],check=True)
    subprocess.run(['git','-C',str(base),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize isolated Workbook comment workers'],check=True)
    config = (RUN.parent / 'rl4cv_tiny_curriculum/runtime/codex_profiles/natural_arithmetic/config.toml').read_text()
    for lane in range(LANES):
        work = ROOT / 'workers' / f'lane_{lane:03d}'
        subprocess.run(['git','-C',str(base),'worktree','add','--detach','-q',str(work),'HEAD'],check=True)
        profile = ROOT / 'runtime' / f'lane_{lane:03d}'
        profile.mkdir(parents=True)
        (profile / 'config.toml').write_text(config.replace('model_reasoning_effort = "high"','model_reasoning_effort = "medium"'))
    for index, batch in enumerate(batches):
        folder = ROOT / 'batches' / f'batch_{index:03d}'
        write(folder / 'inputs.json', batch)
        write(folder / 'status.json', dict(state='PENDING', declared=len(batch), attempts=0))
    write(ROOT / 'dispatch.json', dict(source_revision='2e066e310b2c6d2c27616927ae131f82901c8f1c', source_sha256=SOURCE_SHA,
        declared_candidates=12823, annotation_eligible=len(eligible), excluded_by_protected_screen=12823-len(eligible),
        batches=len(batches), batch_size=BATCH_SIZE, concurrent_lanes=LANES, model=MODEL, effort=EFFORT,
        max_cli_attempts_per_batch=2, timeout_seconds_per_attempt=600, worker_deadline_seconds=2700,
        manifest_sha256=sha(manifest), credential='previously explicitly authorized LAB_OPENAI_API_KEY through Codex CLI',
        estimated_cost_usd=140, compilation='not_run_for_comment_insertion', current_toolchain_verification='pending',
        driver_sha256=sha(Path(__file__).read_bytes()), integrity_sha256=sha((HERE/'comment_integrity.py').read_bytes()), created_unix=time.time()))
    print((ROOT / 'dispatch.json').read_text(), flush=True)


def prompt(batch, repair=None):
    items = []
    for row in batch:
        items.append(dict(task_id=row['task_id'], statement_english=row['natural_language_statement'], tags=row['tags'],
            numbered_lean='\n'.join(f'{i}: {line}' for i,line in enumerate(row['lean'].splitlines(),1))))
    text = f'''# Explain existing Lean Workbook proof scripts

**TLDR:** Add a concise mathematical proof sketch and helpful comments to each supplied Lean file. Return line-indexed insertions; the coordinator preserves the original source exactly.

{PREAPPROVAL}

All inputs are below; return the requested final JSON directly. You are explaining existing public proof candidates, not repairing or generating proofs. Do not change any theorem, hypothesis, tactic, expression, import or original comment. Do not run Lean compilation. No additional model calls are assigned. Protected benchmark material and model validation outputs are outside this assignment.

For EVERY task return task_id, comments, annotation_issue. Each comment object has before_line (original 1-based line) and text (one plain English line without a -- prefix). Insert before line1 at least two short header comments: first starts exactly "Proof sketch:" and states the actual mathematical idea; following header lines connect that idea to the supplied Lean proof. Put additional comments before meaningful proof steps every few lines, with more explanation at tricky transitions. For one-line proofs, a brief sketch and one precise tactic explanation suffice. Explain why a lemma, hypothesis, simplification or computation establishes the goal; avoid merely reading syntax aloud, generic boilerplate and unsupported mathematical claims. Keep comments concise without obfuscation. If the proof is flawed or you cannot explain a step confidently, describe the specific problem in annotation_issue instead of inventing a justification. Otherwise annotation_issue is the empty string. Do not insert inside an existing multiline string or block comment. Each text line must be printable, at most360 characters, and contain neither block-comment delimiter. Preserve source comments as part of the original file. Aim below1000 Qwen assistant tokens for the whole commented file where feasible, but do not delete or shorten any original code to meet that aim. A genuinely longer proof may remain longer with its token count recorded.

Inputs:
{json.dumps(items, ensure_ascii=False)}
'''
    if repair:
        text += '\nThe prior output failed these mechanical checks; correct those annotations only:\n' + json.dumps(repair)
    return text + '\nTL;DR: Return one JSON annotation record for every supplied task, with a mathematical sketch at the top and accurate explanations of the unchanged proof.\n'


def validate(batch, output):
    data = json.loads(output.read_text())
    returned = data['annotations']
    byid = {r['task_id']:r for r in returned}
    if len(byid) != len(returned) or set(byid) != {r['task_id'] for r in batch}:
        raise ValueError('task coverage or duplicate IDs')
    receipts = []
    for row in batch:
        record = byid[row['task_id']]
        try:
            annotated = insert_comments(row['lean'], record['comments'])
            issue = record['annotation_issue']
            assert isinstance(issue, str)
            target = ROOT / 'examples' / row['task_id']
            write(target / 'comments.json', record)
            (target / 'Solution.lean').write_text(annotated)
            receipt = dict(task_id=row['task_id'], comment_integrity='PASS',
                source_sha256=row['source_sha256'], annotated_sha256=sha(annotated), comments=len(record['comments']),
                annotation_issue=issue, current_toolchain_verification='pending', compilation_rerun=False)
            write(target / 'receipt.json', receipt)
            receipts.append(receipt)
        except Exception as exc:
            receipts.append(dict(task_id=row['task_id'], comment_integrity='FAIL', error=str(exc)))
    return receipts


def claim(lane):
    with (ROOT / 'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for folder in sorted((ROOT / 'batches').glob('batch_*')):
            status = json.loads((folder / 'status.json').read_text())
            if status['state'] == 'PENDING':
                write(folder / 'status.json', dict(status, state='CLAIMED', lane=lane, driver_pid=os.getpid(), claimed_unix=time.time()))
                return folder
    return None


def worker(lane, once=False):
    work = ROOT / 'workers' / f'lane_{lane:03d}'
    env = dict(os.environ, CODEX_HOME=str(ROOT/'runtime'/f'lane_{lane:03d}'), CUDA_VISIBLE_DEVICES='', TOKENIZERS_PARALLELISM='false')
    env['TINY_OPENAI_API_KEY'] = (Path.home()/'.config/rl4cv-tiny/lab-openai.key').read_text().strip()
    worker_status = ROOT / 'status' / f'lane_{lane:03d}.json'
    deadline = time.monotonic() + 2700
    while time.monotonic() < deadline:
        folder = claim(lane)
        if folder is None:
            write(worker_status, dict(state='DONE', lane=lane, driver_pid=os.getpid(), observed_unix=time.time()))
            return
        batch = json.loads((folder/'inputs.json').read_text())
        prior_errors, success = None, False
        first_attempt=json.loads((folder/'status.json').read_text()).get('attempts',0)
        for attempt in range(first_attempt,2):
            output = folder / f'output_{attempt}.json'
            if output.exists():
                raise RuntimeError('attempt already exists; refusing duplicate generation')
            brief = prompt(batch, prior_errors)
            (folder/f'prompt_{attempt}.md').write_text(brief)
            cmd = ['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check',
                '-m',MODEL,'-c',f'model_reasoning_effort="{EFFORT}"','--json','--output-schema',str(ROOT/'schema.json'),'-o',str(output),'-']
            with (folder/f'cli_{attempt}.jsonl').open('x') as log:
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
                    cwd=work, env=env, text=True, start_new_session=True)
                process.stdin.write(brief)
                process.stdin.close()
                started = time.monotonic()
                while process.poll() is None:
                    state = dict(state='RUNNING',lane=lane,batch=folder.name,attempt=attempt,pid=process.pid,
                        driver_pid=os.getpid(),observed_unix=time.time(),model=MODEL,effort=EFFORT)
                    write(worker_status,state)
                    write(folder/'status.json',dict(state,declared=len(batch),attempts=attempt+1))
                    if time.monotonic()-started > 600 or time.monotonic() > deadline:
                        os.killpg(process.pid,signal.SIGTERM)
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                        break
                    time.sleep(3)
            try:
                if process.returncode:
                    raise RuntimeError(f'CLI exited {process.returncode}; see cli_{attempt}.jsonl')
                receipts = validate(batch,output)
                prior_errors = [r for r in receipts if r['comment_integrity'] != 'PASS']
                if prior_errors:
                    raise ValueError(json.dumps(prior_errors))
                write(folder/'receipts.json',receipts)
                write(folder/'status.json',dict(state='DONE',lane=lane,declared=len(batch),assembled=len(receipts),
                    annotation_issues=sum(bool(r['annotation_issue']) for r in receipts),attempts=attempt+1,completed_unix=time.time()))
                success = True
                break
            except Exception as exc:
                prior_errors = prior_errors or [dict(error=str(exc))]
                write(folder/f'error_{attempt}.json',dict(error=str(exc),observed_unix=time.time()))
                # Authentication and payment errors do not benefit from an identical retry.
                if process.returncode:
                    break
        if not success:
            write(folder/'status.json',dict(state='BLOCKED',lane=lane,declared=len(batch),error=prior_errors,observed_unix=time.time()))
        if once:
            write(worker_status,dict(state='PILOT_FINISHED',lane=lane,batch=folder.name,success=success,observed_unix=time.time()))
            return
    write(worker_status,dict(state='DEADLINE',lane=lane,observed_unix=time.time()))


def launch(first=False):
    lanes = [0] if first else range(LANES)
    launched=0
    for lane in lanes:
        name = f'codex-rl4cv-workbook-{lane:03d}'
        if subprocess.run(['tmux','has-session','-t',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
            continue
        log = ROOT / 'workers' / f'lane_{lane:03d}' / 'driver.log'
        command = f'python3 -u {HERE}/annotate_workbook.py worker --lane {lane}' + (' --once' if first else '') + f' >> {log} 2>&1'
        subprocess.run(['tmux','new-session','-d','-s',name,command],check=True)
        launched+=1
    print(json.dumps(dict(launched=launched,first=first)),flush=True)


def status():
    states, rows, issues = collections.Counter(), 0, 0
    for file in (ROOT/'batches').glob('*/status.json'):
        data=json.loads(file.read_text());states[data['state']]+=1
        if data['state']=='DONE':
            rows+=data['assembled'];issues+=data['annotation_issues']
    result=dict(batch_states=dict(states),assembled=rows,annotation_issues=issues,observed_unix=time.time())
    write(ROOT/'progress.json',result)
    print(json.dumps(result,indent=2),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','launch','worker','status'])
    parser.add_argument('--first',action='store_true');parser.add_argument('--once',action='store_true');parser.add_argument('--lane',type=int)
    args=parser.parse_args()
    if args.action=='prepare':prepare()
    elif args.action=='launch':launch(args.first)
    elif args.action=='worker':worker(args.lane,args.once)
    else:status()
