"""Dispatch Terra comment insertions on fixed training-only inputs and preserve code byte for byte."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
RUN=Path(os.environ.get('TINY_RUN_ROOT','/lfs/skampere1/0/eth127/rl4cv_tiny_training'))
ROOT=RUN/'lean_corpus_v8'
OLD=RUN.parent/'rl4cv_tiny_curriculum'
SOURCE=RUN/'curriculum'
EXPECTED='2f50cd04757904b2ac703693c4520df813dd98e0f18881de92c515c7f87bb119'
MODEL='gpt-5.6-terra'
PREAPPROVAL='SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).'

def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2)+'\n');tmp.replace(p)
def read(p):return [json.loads(s) for s in p.read_text().splitlines()]
def extract(row):
 s=row['messages'][-1]['content'];m=re.fullmatch(r'FILE: ([^\n]+)\n```lean\n(.*)```\n',s,re.S);assert m
 return m.group(1),m.group(2)
def apply_comments(source,comments):
 lines=source.splitlines(keepends=True);indexed={}
 assert isinstance(comments,list) and comments
 for c in comments:
  assert set(c)=={'before_line','text'},c
  n=c['before_line'];text=c['text']
  assert isinstance(n,int) and 1<=n<=len(lines)
  assert isinstance(text,str) and text.strip() and '\n' not in text and '\r' not in text
  assert len(text)<=360,'split long explanations into focused comments'
  assert not any(x in text for x in ['/-','-/','\x00'])
  indexed.setdefault(n,[]).append(text.strip())
 out=[]
 for n,line in enumerate(lines,1):
  indent=re.match(r'\s*',line).group().replace('\n','')
  out.extend(indent+'-- '+t+'\n' for t in indexed.get(n,[]));out.append(line)
 annotated=''.join(out)
 retained=''.join(line for line in annotated.splitlines(keepends=True) if not line.lstrip().startswith('--'))
 assert retained==source, 'original code lines changed'
 return annotated

def tasks():
 assert hashlib.sha256((SOURCE/'training.jsonl').read_bytes()).hexdigest()==EXPECTED
 return read(SOURCE/'training.jsonl')

def check(topic):
 rows=[r for r in tasks() if r['topic']==topic];w=ROOT/'annotations/workers'/topic
 if not w.exists():w=ROOT/'annotations/worker_records'/topic
 results=[]
 for row in rows:
  tid=row['task_id'];p=w/'annotations'/f'{tid}.json'
  try:
   comments=json.loads(p.read_text());_,source=extract(row)
   annotated=apply_comments(source,comments)
   target=ROOT/'annotations/examples'/tid/'Solution.lean';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(annotated)
   results.append(dict(task_id=tid,assembled=True,comments=len(comments),source_sha256=hashlib.sha256(source.encode()).hexdigest(),annotated_sha256=hashlib.sha256(annotated.encode()).hexdigest()))
  except Exception as exc:results.append(dict(task_id=tid,assembled=False,error=str(exc)))
 write(w/'progress.json',dict(topic=topic,declared=len(rows),assembled=sum(r['assembled'] for r in results),rows=results))
 return results

def prepare():
 source_tasks={r['task_id']:r for r in read(HERE.parent/'expt_v5/manifest.jsonl')}
 bytopic={}
 for r in tasks():bytopic.setdefault(r['topic'],[]).append(r)
 base=ROOT/'annotations/worker_template';base.mkdir(parents=True,exist_ok=True)
 if not (base/'.git').exists():
  subprocess.run(['git','init','-q',str(base)],check=True)
  (base/'AGENTS.md').write_text('Annotate exactly the fixed training examples in RUNBOOK.md. Your files are inputs.json and annotations/. The coordinator owns assembly and all shared sources. Use only the supplied task material, preserve existing code, and never read credentials. Follow the runbook to completion.\n')
  subprocess.run(['git','-C',str(base),'add','AGENTS.md'],check=True)
  subprocess.run(['git','-C',str(base),'-c','user.name=Ethan Lee','-c','user.email=eth127@stanford.edu','commit','-qm','Initialize isolated annotation workspace'],check=True)
 for topic,rows in bytopic.items():
  w=ROOT/'annotations/workers'/topic
  if not w.exists():subprocess.run(['git','-C',str(base),'worktree','add','--detach','-q',str(w),'HEAD'],check=True)
  inputs=[]
  for r in rows:
   t=source_tasks[r['task_id']];_,lean=extract(r)
   inputs.append(dict(task_id=r['task_id'],python=t['python'],intent=t['intent'],lean=lean,numbered_lean='\n'.join(f'{i}: {line}' for i,line in enumerate(lean.splitlines(),1))))
  write(w/'inputs.json',inputs)
  (w/'annotations').mkdir(exist_ok=True)
  (w/'RUNBOOK.md').write_text(f'''# Explain twenty verified {topic} training examples

{PREAPPROVAL}

You are the requested {MODEL} worker with high reasoning. Read inputs.json; it contains20existing training Python/Lean pairs with English intent. For EACH task write annotations/<task_id>.json, a JSON list of objects exactly {{"before_line": integer, "text": "one short English comment"}}. The coordinator inserts each comment immediately before that original 1-based Lean line. Begin every file with a short top-of-file solution/proof sketch, inserted before line1 as several comment lines. State the overall semantic and proof approach in a few clear sentences. Then explain every few meaningful code lines, with more detail around tricky sections; no fixed comment count. Explain the Python behavior, type/domain choices (especially Int vs Nat and truncating Nat subtraction), matching library operations, the specification's meaning, and why a tactic/lemma proves the goal. Give test or boundary-case rationale where helpful. Explain rather than paraphrase syntax or emit boilerplate. These examples are short; keep explanations focused. Comments plus unchanged code should fit below1000 Qwen tokens.

The source code is already verified. Preserve every implementation, theorem statement, proof, test and anonymous example exactly; you are inserting comments only. Use only inputs.json and your annotation files, without validation tasks, model evaluation outputs, new examples, external models or credentials. You may use Python/scripts to write and inspect your twenty JSON files efficiently. The coordinator performs compilation, kernel and behavior validation centrally, so your task is explanations and complete correct JSON outputs. No training or new proof generation is assigned.

Run this deterministic checker after writing files:
`python3 {HERE/'annotate_tiny.py'} check --topic {topic}`
Read your progress.json, fix every missing/malformed annotation and finish all20. A short final response alone is not completion. End with the count completed and any concrete blocker.
''')
 write(ROOT/'annotations/dispatch.json',dict(tasks=500,topics=list(bytopic),model=MODEL,effort='high',source_sha256=EXPECTED,credential_alias='previously authorized LAB_OPENAI_API_KEY',max_cli_attempts_per_topic=2,deadline_seconds_per_topic=1800))
 return list(bytopic)

def worker(topic):
 w=ROOT/'annotations/workers'/topic;deadline=time.monotonic()+1800
 profile=OLD/'runtime/codex_profiles'/topic
 assert (profile/'config.toml').is_file()
 env=dict(os.environ,CODEX_HOME=str(profile),TOKENIZERS_PARALLELISM='false',CUDA_VISIBLE_DEVICES='')
 env['TINY_OPENAI_API_KEY']=(Path.home()/'.config/rl4cv-tiny/lab-openai.key').read_text().strip()
 path=ROOT/'annotations/status'/f'{topic}.json'
 for attempt in range(2):
  results=check(topic)
  if all(r['assembled'] for r in results):break
  prompt=(w/'RUNBOOK.md').read_text()
  if attempt:prompt+='\nRepair continuation: inspect progress.json and finish only malformed/missing comments. Preserve completed files.\n'
  log=w/f'attempt_{attempt}.jsonl'
  cmd=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m',MODEL,'-c','model_reasoning_effort="high"','--json','-o',str(w/f'final_{attempt}.txt'),prompt]
  with log.open('x') as stream:
   p=subprocess.Popen(cmd,cwd=w,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   while p.poll() is None:
    write(path,dict(topic=topic,state='RUNNING',pid=p.pid,driver_pid=os.getpid(),attempt=attempt,model=MODEL,effort='high',observed_unix=time.time(),assembled=sum(r['assembled'] for r in results)))
    if time.monotonic()>deadline:
     os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=15);write(path,dict(topic=topic,state='TIMEOUT'));return
    time.sleep(3)
  if p.returncode:
   write(path,dict(topic=topic,state='BLOCKED',exit_code=p.returncode,log=str(log)));return
 results=check(topic);write(path,dict(topic=topic,state='DONE' if all(r['assembled'] for r in results) else 'INCOMPLETE',assembled=sum(r['assembled'] for r in results),declared=len(results),observed_unix=time.time()))

def launch(which):
 topics=prepare(); chosen=topics[:1] if which=='first' else topics[1:] if which=='rest' else topics
 for topic in chosen:
  name='codex-rl4cv-comment-'+topic.replace('_','-')
  command=f'python3 -u {HERE}/annotate_tiny.py worker --topic {topic} > {ROOT}/annotations/workers/{topic}/driver.log 2>&1'
  subprocess.run(['tmux','new-session','-d','-s',name,command],check=True)
  print(json.dumps(dict(topic=topic,session=name)),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','launch','worker','check']);ap.add_argument('--topic');ap.add_argument('--which',choices=['first','rest','all'],default='first');a=ap.parse_args()
 if a.action=='prepare':prepare()
 elif a.action=='launch':launch(a.which)
 elif a.action=='worker':worker(a.topic)
 else:
  result=check(a.topic);print(json.dumps(result,indent=2));sys.exit(not all(r['assembled'] for r in result))
