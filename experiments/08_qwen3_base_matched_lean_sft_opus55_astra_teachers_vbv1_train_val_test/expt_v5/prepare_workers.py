"""Prepare disjoint topic worktrees, explicit worker runbooks, and named tmux launches."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).parent
PYTHON=ROOT/'runtime/venv/bin/python'
TASKS=[json.loads(l) for l in (ROOT/'manifest.jsonl').read_text().splitlines()]
PREAPPROVAL='SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).'

def prepare():
    base=ROOT/'worker_source';base.mkdir(exist_ok=True)
    if not (base/'.git').exists():
        subprocess.run(['git','init','-q',str(base)],check=True)
        (base/'AGENTS.md').write_text('Create the 20 fixed examples in RUNBOOK.md. You own this worker worktree only. The coordinator owns shared scripts, immutable task semantics, and consolidated results. Preserve other workers and credentials; never print or read credential values. Use the provided compiler/checker. Do not change shared checker acceptance. No training or model substitutions are part of this assignment.\n')
        subprocess.run(['git','-C',str(base),'add','AGENTS.md'],check=True)
        subprocess.run(['git','-C',str(base),'-c','user.name=Ethan Han','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize isolated curriculum worker template'],check=True)
    for topic in dict.fromkeys(t['topic'] for t in TASKS):
        w=ROOT/'workers'/topic
        if not w.exists():subprocess.run(['git','-C',str(base),'worktree','add','--detach','-q',str(w),'HEAD'],check=True)
        tasks=[t for t in TASKS if t['topic']==topic]
        (w/'tasks.json').write_text(json.dumps([{k:v for k,v in t.items() if k!='tests'} for t in tasks],indent=2))
        snippets='\n\n'.join('### '+p.stem+'\n```lean\n'+p.read_text()+'```' for p in (ROOT/'prototypes').glob('*.lean'))
        runbook=f'''# Twenty concise {topic} Python-to-Lean training examples

{PREAPPROVAL}

Generate all 20 concrete tasks in tasks.json. Their Python functions, intent, parameter order and natural-number restrictions are fixed. The shared manifest has 32 fixed expected test cases for each task. Write examples/<task_id>/Solution.lean for each task. Each complete assistant training response must have fewer than 1000 Qwen tokens, including the file envelope and template loss span. Prefer the shortest clear, idiomatic, complete solution; meaningful names and standard tactics; only necessary helpers; no redundant explanations, unnecessary abstractions, or obfuscation. Preserve all semantics and required obligations. Use the fixed Python source, with Int for general integers and Nat for explicitly nonnegative inputs and length/count results, List for lists, Bool for predicates, Prod for pairs, Option Int for optional results. Namespace Tiny; def solution arguments follow the task's args order. Import Mathlib. At least one universally meaningful spec_ theorem (not just True or a self-equality), plus at least two test_ executable-example theorems, proved without sorry/admit/native_decide/axioms/unsafe/partial/opaque. Specifications must constrain intended behavior, not merely repeat an implementation with identical sides.

Choose short appropriate techniques among rfl, simp, simpa, rw, calc, intro, apply, constructor, rcases, cases, by_cases, induction, omega, norm_num, ring, linarith, aesop. Diversity is a secondary goal: never force an artificial tactic or lengthen a solution merely to demonstrate a technique. For lists, cover length/membership/order/pointwise behavior as appropriate. Python zip truncates; empty lists and negative integers are legal unless explicitly constrained. Python // and % have floor semantics for positive divisors. Avoid accidental Nat subtraction for signed Python results. Empty outputs need explicit result types.

Run this actual checker for each task, or for the whole topic:
```
{PYTHON} {ROOT}/check_example.py --topic {topic}
```
It compiles with the pinned Lean 4.22.0/Mathlib cache, checks kernel axioms, compares 32 Python cases, counts Qwen tokens, and verifies the exact pinned warm-start extractor/template. For one example use --task <task_id>. Compilation has an four-slot shared queue; you may run multiple checks but do not bypass the queue or alter shared dependencies. Read receipts/compile.json or receipts/differential.json for diagnostics. Preserve every accepted example. Repair failing or too-long files until all 20 pass. You may inspect installed Mathlib sources for correct lemma names. Do not modify the shared checker, fixed tasks, other worker directories or existing experiments. No direct model API calls, additional worker launches, training, git pushes, or secret access are needed for this bounded worker task. Model generation is already provided through this Codex session with Terra/high.

Supplementary coordinator-authored style prototypes (preserve this attribution if reused):
{snippets}

Keep a short progress.json and final summary naming accepted/missing examples and actual blockers. A short answer alone is not completion: all evaluated files and verification receipts must exist. The coordinator mirrors meaningful progress into the canonical repository results.md; your own progress is local to this worktree. Do not claim final global admission before the coordinator's protected-reference screen.
'''
        (w/'RUNBOOK.md').write_text(runbook)
    return list(dict.fromkeys(t['topic'] for t in TASKS))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--launch',choices=['first','rest','all']);a=ap.parse_args()
    topics=prepare()
    if a.launch:
        if not (ROOT/'runtime/READY').exists():raise SystemExit('Runtime/prototype gate not ready')
        chosen=topics[:1] if a.launch=='first' else topics[1:] if a.launch=='rest' else topics
        for topic in chosen:
            name='codex-rl4cv-tiny-'+topic.replace('_','-')
            if subprocess.run(['tmux','has-session','-t','='+name],capture_output=True).returncode==0:continue
            subprocess.run(['tmux','new-session','-d','-s',name,f'python3 -u {ROOT}/worker_driver.py {topic} > {ROOT}/workers/{topic}/driver.log 2>&1'],check=True)
            print(json.dumps({'topic':topic,'session':name,'launched':True}),flush=True)
