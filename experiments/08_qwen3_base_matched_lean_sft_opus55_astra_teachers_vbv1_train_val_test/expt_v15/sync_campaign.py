"""Mirror compact remote campaign receipts and publish owned progress milestones without changing running sources."""
from __future__ import annotations
import argparse
import base64
import datetime
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import time

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
REPO=EXP.parent.parent
CANON=Path('/Users/lethan3/Documents/veribench-projects/rl-4-code-verification')
RUN='/lfs/skampere1/0/eth127/rl4cv_tiny_training'
SSH=['ssh','-S','/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control','-o','BatchMode=yes','-o','ConnectTimeout=10','eth127@skampere1.stanford.edu']

def mapping():
    out={}
    for condition in ['current','cleaned']:
        for source in ['data/prepare_receipt.json','data/row_results.csv','run/progress.json','run/result.json','run/first_update.json','run/identity.json','smoke/result.json','allocation.json','released.json','terminal.json']:
            out[f'corpus_training_v12/{condition}/{source}']=f'expt_v12/results/live_{condition}_{source.replace("/","_")}'
        for source in [f'analysis/v12_{condition}_summary.json',f'analysis/v12_{condition}_cells.csv',f'analysis/v12_{condition}_tasks.csv']:
            out['corpus_training_v12/'+source]='expt_v12/results/'+source.replace('/','_')
    for source in ['dispatcher.json','cleaned_dispatcher.json']:
        out['corpus_training_v12/'+source]='expt_v12/results/live_'+source
    for source in ['progress.json','dispatch.json','usage.json','completion.json','row_results.csv','row_progress.csv','watch_heartbeat.json','runtime_manifest.json','saved_alternative_summary.json','controls.json','guard_controls.json','calibration/summary.json','final/summary.json','final/row_results.csv']:
        out['lean_corpus_v13/'+source]='expt_v13/results/live_'+source.replace('/','_')
    for source in ['freeze.json','progress.json','completion.json','controls.json','row_results.csv','watcher.json','watch_status.json']:
        out['public_gap_sources_v14/bulk_validation/'+source]='expt_v14/results/live_bulk_'+source
    for source in ['coordinator_launch.json','coordinator_heartbeat.json','decisions.json','goal.json','paid_work_hold.json','scientific_hold.json','budget.json','frozen_evaluator_sources.json']:
        out['adaptive_1p7b_campaign/'+source]='expt_v15/results/'+source
    return out

def collect():
    paths=mapping()
    code='''import pathlib,json,base64,hashlib
root=pathlib.Path(%r)
paths=json.loads(%r)
out={}
for rel in paths:
 p=root/rel
 if p.is_file():
  raw=p.read_bytes();out[rel]=dict(sha256=hashlib.sha256(raw).hexdigest(),data=base64.b64encode(raw).decode())
trial_root=root/'adaptive_1p7b_campaign/trials'
allowed={'PROTOCOL.md','CKPT.md','results.md','manifest.json','config.json','summary.json','cells.csv','tasks.csv','input_manifest.json','source_manifest.json','admission.json'}
for p in sorted(trial_root.glob('*/*')):
 if p.is_file() and (p.name in allowed or p.suffix in ['.py','.sh']):
  rel=str(p.relative_to(root));raw=p.read_bytes()
  if len(raw)<10_000_000:out[rel]=dict(sha256=hashlib.sha256(raw).hexdigest(),data=base64.b64encode(raw).decode())
print(json.dumps(out))
'''%(RUN,json.dumps(list(paths)))
    payload=json.loads(subprocess.check_output(SSH+['python3 -c '+shlex.quote(code)],timeout=60))
    touched=[]
    for rel,item in payload.items():
        raw=base64.b64decode(item['data']);assert hashlib.sha256(raw).hexdigest()==item['sha256']
        relative=paths.get(rel)
        if relative is None:
            assert rel.startswith('adaptive_1p7b_campaign/trials/')
            relative='expt_v15/results/'+rel.removeprefix('adaptive_1p7b_campaign/')
        target=EXP/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or target.read_bytes()!=raw:target.write_bytes(raw);touched.append(target)
    def obj(rel):
        item=payload.get(rel)
        return json.loads(base64.b64decode(item['data'])) if item else {}
    current=obj('corpus_training_v12/current/run/progress.json');cleaned=obj('corpus_training_v12/cleaned/run/progress.json')
    cleanup=obj('lean_corpus_v13/progress.json');bulk=obj('public_gap_sources_v14/bulk_validation/progress.json');budget=obj('adaptive_1p7b_campaign/budget.json')
    charged=sum(x['usd'] for x in budget.get('charges',{}).values());base=sum(x.get('base_rate_estimate_usd') or 0 for x in budget.get('charges',{}).values());held=sum(x['usd'] for x in budget.get('reservations',{}).values())
    now=datetime.datetime.now().astimezone().strftime('%m-%d-%Y %H:%M %Z')
    status=dict(observed=now,current=current,cleaned=cleaned,cleanup=cleanup,public_source_checks=bulk,budget_conservative_charge=charged,budget_base_rate_estimate=base,budget_reserved=held,second_tranche_active=budget.get('tranche2activated',False),goal=obj('adaptive_1p7b_campaign/goal.json'))
    path=HERE/'results/campaign_status.json';path.write_text(json.dumps(status,indent=2)+'\n');touched.append(path)
    results=HERE/'results.md';text=results.read_text().split('\n## Latest automatic snapshot\n')[0]
    text+='\n## Latest automatic snapshot\n\n'+now+'.\n\n'
    for condition in ['current','cleaned']:
        summary=obj(f'corpus_training_v12/analysis/v12_{condition}_summary.json')
        terminal=obj(f'corpus_training_v12/{condition}/terminal.json')
        if summary:text+=f'- {condition} validation: {summary.get("successes")}/1,080 binary successes; {summary.get("success_rate",0):.2%}, complete manifest.\n'
        elif terminal:text+=f'- {condition} terminal state: {terminal.get("status")}; details retained in the receipt.\n'
    text+=f'- Current training: {current.get("step",0):,}/5,470 updates; {current.get("loss_tokens",0):,} assistant loss tokens.\n'
    text+=f'- Cleaned training: {cleaned.get("step",0):,} updates; waits for verified cleanup when zero.\n'
    text+=f'- Cleanup: {cleanup.get("states",{})}; declared {cleanup.get("declared",2585):,}.\n'
    text+=f'- Additional public sources: {bulk.get("completed",0):,}/{bulk.get("declared",729):,} checked; {bulk.get("outcomes",{})}.\n'
    text+=f'- Paid work: ${base:.2f} base-rate usage estimate; ${charged:.2f} conservatively charged; ${held:.2f} reserved for in-flight work. Estimates are not invoices.\n'
    text+=f'- Second authorized $300 tranche activated: {status["second_tranche_active"]}. Goal receipt: {bool(status["goal"])}.\n'
    results.write_text(text);touched.append(results)
    states=cleanup.get('states',{});done=sum(v for k,v in states.items() if k in ['DONE','CLEANED','FALLBACK','UNCHANGED'])
    milestone=(current.get('step',0)//250,cleaned.get('step',0)//250,done//50,bulk.get('completed',0)//100,bool(status['goal']),status['second_tranche_active'],bool(obj('corpus_training_v12/current/terminal.json')),bool(obj('corpus_training_v12/cleaned/terminal.json')))
    return touched,milestone,status

def mirror(paths):
    for source in paths:
        target=CANON/source.relative_to(REPO);target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes());assert hashlib.sha256(target.read_bytes()).digest()==hashlib.sha256(source.read_bytes()).digest()

def publish(paths):
    relative=sorted({str(p.relative_to(REPO)) for p in paths})
    assert all('/results/' in p or p==str((HERE/'results.md').relative_to(REPO)) for p in relative)
    def git(*args,check=True):return subprocess.run(['git',*args],cwd=REPO,text=True,capture_output=True,check=check)
    git('add','--',*relative);git('diff','--cached','--check')
    staged=git('diff','--cached','--name-only').stdout.splitlines();assert set(staged)<=set(relative),'Unrelated staged paths; preserve and stop publisher'
    diff=git('diff','--cached').stdout
    assert not re.search(r'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}',diff),'Potential secret; stop publisher'
    assert not re.search(r'''(?i)(?:api[_-]?key|password|secret|bearer)\s*[:=]\s*["'][A-Za-z0-9_\-/+]{24,}''',diff),'Potential literal credential; stop publisher'
    if not staged:return
    # Experiment source and src/tests gates are frozen; only measured progress tables/docs are published.
    git('commit','-m','Update 1.7B training, teacher cleanup and source verification progress')
    for attempt in range(3):
        git('fetch','origin','main');git('merge','--no-edit','origin/main')
        result=git('push','origin','HEAD:main',check=False)
        if result.returncode==0:return
        if 'fetch first' not in result.stderr and 'non-fast-forward' not in result.stderr:raise RuntimeError(result.stderr)
    raise RuntimeError('Concurrent main updates prevented bounded publish; local commit preserved')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');parser.add_argument('--publish',action='store_true');args=parser.parse_args();last=None
    while True:
        try:
            paths,mark,status=collect();mirror(paths)
            if args.publish and mark!=last:publish(paths);last=mark
            print(json.dumps(dict(current_step=status['current'].get('step'),cleanup=status['cleanup'].get('states'),conservative_charge=status['budget_conservative_charge'],observed=status['observed'])),flush=True)
        except Exception as exc:
            print(json.dumps(dict(error=repr(exc),observed=time.time())),flush=True)
            if not args.watch:raise
        if not args.watch:return
        time.sleep(120)

if __name__=='__main__':main()
