"""Run one Lab-funded Terra/high Codex CLI worker with bounded repair and durable progress receipts."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).parent
TOPIC=sys.argv[1]
WORKER=ROOT/'workers'/TOPIC
STATUS=ROOT/'runtime/status'/f'{TOPIC}.json'
STATUS.parent.mkdir(parents=True,exist_ok=True)
tasks=[json.loads(l) for l in (ROOT/'manifest.jsonl').read_text().splitlines() if json.loads(l)['topic']==TOPIC]

def counts():
    rs=[]
    for t in tasks:
        p=WORKER/'examples'/t['task_id']/'receipts/verification.json'
        if p.exists():
            try:rs.append(json.loads(p.read_text()))
            except json.JSONDecodeError:pass
    return {'accepted':sum(bool(r.get('accepted')) for r in rs),'checked':len(rs),'declared':20}

def status(**kw):
    d={'topic':TOPIC,'observed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'model':'gpt-5.6-terra','reasoning_effort':'high','credential_alias':'LAB_OPENAI_API_KEY','session':os.environ.get('TINY_SESSION_NAME','codex-rl4cv-tiny-'+TOPIC.replace('_','-')),'driver_pid':os.getpid(),**counts(),**kw}
    tmp=STATUS.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2));tmp.replace(STATUS)

home=ROOT/'runtime/codex_profiles'/TOPIC;home.mkdir(parents=True,exist_ok=True);home.chmod(0o700)
(home/'config.toml').write_text('''model = "gpt-5.6-terra"
model_reasoning_effort = "high"
model_provider = "authorized_openai"
approval_policy = "never"
sandbox_mode = "danger-full-access"
[model_providers.authorized_openai]
name = "Lab OpenAI key; explicitly authorized by user"
base_url = "https://api.openai.com/v1"
env_key = "TINY_OPENAI_API_KEY"
wire_api = "responses"
requires_openai_auth = false
''')
env=os.environ.copy();env['CODEX_HOME']=str(home);env['TINY_ROOT']=str(ROOT)
env['TINY_OPENAI_API_KEY']=(Path.home()/'.config/rl4cv-tiny/lab-openai.key').read_text().strip()
env['TOKENIZERS_PARALLELISM']='false'
prompt=(WORKER/'RUNBOOK.md').read_text()
deadline=time.monotonic()+3600
for attempt in range(int(os.environ.get('TINY_START_ATTEMPT','0')),3):
    if counts()['accepted']==20:break
    if attempt:
        prompt+='\nREPAIR CONTINUATION: inspect current receipts and repair only missing or failing examples. Preserve all accepted example bytes. Return only when all 20 pass or record the concrete blocker.\n'
    log=WORKER/f'codex_attempt_{attempt}.jsonl'
    cmd=['/usr/local/bin/codex','exec','--dangerously-bypass-approvals-and-sandbox','--skip-git-repo-check','-m','gpt-5.6-terra','-c','model_reasoning_effort="high"','--json','-o',str(WORKER/f'final_{attempt}.txt'),prompt]
    with log.open('w') as fh:
        p=subprocess.Popen(cmd,cwd=WORKER,env=env,stdout=fh,stderr=subprocess.STDOUT,start_new_session=True)
        while p.poll() is None:
            status(state='RUNNING',attempt=attempt,child_pid=p.pid,log=str(log))
            if time.monotonic()>deadline:
                os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=15);status(state='TIMEOUT',attempt=attempt);raise SystemExit(124)
            time.sleep(5)
    text=log.read_text(errors='replace')
    if p.returncode!=0:
        status(state='BLOCKED',attempt=attempt,exit_code=p.returncode,error_tail=text[-1500:]);raise SystemExit(p.returncode)
    if counts()['accepted']==20:break
status(state='DONE' if counts()['accepted']==20 else 'INCOMPLETE',attempt=attempt)

