"""Verify a useful first worker action, fan out remaining topic workers, and keep run-bound liveness counts."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).parent
topics=list(dict.fromkeys(json.loads(l)['topic'] for l in (ROOT/'manifest.jsonl').read_text().splitlines()))

def snapshot(state,**kw):
    statuses=[]
    for p in (ROOT/'runtime/status').glob('*.json'):
        try:statuses.append(json.loads(p.read_text()))
        except json.JSONDecodeError:pass
    data={'run_id':'rl4cv-tiny-500-terra-high-20261019','observed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'supervisor_pid':os.getpid(),'state':state,'launched':len(statuses),'locally_verified':sum(s['accepted'] for s in statuses),'declared':500,'workers':statuses,**kw}
    p=ROOT/'runtime/supervisor.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(p)
    return data

end=time.monotonic()+300
while not (ROOT/'runtime/READY').exists() and time.monotonic()<end:
    snapshot('WAITING_FOR_PROTOTYPES');time.sleep(3)
if not (ROOT/'runtime/READY').exists():
    snapshot('PROTOTYPE_GATE_BLOCKED');raise SystemExit('prototype verification did not finish')
snapshot('VERIFYING_FIRST_WORKER')
subprocess.run([sys.executable,str(ROOT/'prepare_workers.py'),'--launch','first'],check=True)
first=ROOT/'workers'/topics[0]/'codex_attempt_0.jsonl'
end=time.monotonic()+180
while time.monotonic()<end:
    snap=snapshot('VERIFYING_FIRST_WORKER')
    if snap['workers'] and snap['workers'][0].get('state')=='BLOCKED':raise SystemExit('first worker blocked; inspect supervisor receipt')
    text=first.read_text(errors='replace') if first.exists() else ''
    if any(word in text for word in ['"type":"item.started"','"type":"item.completed"','"type": "item.started"','"type": "item.completed"']):break
    time.sleep(3)
else:
    snapshot('FIRST_WORKER_UNVERIFIED');raise SystemExit('no useful first model response before preflight timeout')
subprocess.run([sys.executable,str(ROOT/'prepare_workers.py'),'--launch','rest'],check=True)
end=time.monotonic()+4000
while time.monotonic()<end:
    data=snapshot('RUNNING')
    if len(data['workers'])==25 and all(s.get('state') in ['DONE','INCOMPLETE','BLOCKED','TIMEOUT','DEAD'] for s in data['workers']):
        snapshot('GENERATION_DONE' if data['locally_verified']==500 else 'GENERATION_INCOMPLETE');break
    for s in data['workers']:
        if s.get('state')=='RUNNING':
            try:os.kill(s['driver_pid'],0)
            except ProcessLookupError:
                p=ROOT/'runtime/status'/f"{s['topic']}.json";s['state']='DEAD';p.write_text(json.dumps(s,indent=2))
    time.sleep(15)
else:snapshot('SUPERVISION_TIMEOUT')
