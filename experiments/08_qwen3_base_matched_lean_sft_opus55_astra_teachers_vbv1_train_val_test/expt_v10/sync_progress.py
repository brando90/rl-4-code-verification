"""Publish bounded, real host snapshots while the two remote verifier jobs continue independently."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
from relay_gx10 import SNAP,GX

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CANON=Path('/Users/lethan3/Documents/veribench-projects/rl-4-code-verification')
SNAP_FILES=['progress.json','row_results.csv','completion.json','unresolved_recovery/completion.json','gx10_relay.json']
GX_FILES=['lean-v4.22.0/setup_status.json','lean-v4.22.0/setup_completion.json','verification-v10/lean_corpus_v10/progress.json','verification-v10/lean_corpus_v10/row_results.csv','verification-v10/lean_corpus_v10/completion.json','verification-v10/lean_corpus_v10/controls.json']

def collect(command,root,names,prefix):
    code='import json,os,subprocess\nfrom pathlib import Path\np=Path('+repr(root)+').expanduser()\nnames='+repr(names)+'\ndata={n:(p/n).read_text() for n in names if (p/n).exists()}\nalive={}\nfor n,text in data.items():\n if n.endswith("progress.json"):\n  pid=json.loads(text).get("pid")\n  try:os.kill(pid,0);alive[n]=True\n  except (OSError,TypeError):alive[n]=False\ndata["liveness.json"]=json.dumps(dict(alive=alive,sessions=subprocess.run(["tmux","list-sessions","-F","#{session_name}"],capture_output=True,text=True).stdout.splitlines()))\nprint(json.dumps(data))'
    result=subprocess.run(command+['python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=60,check=True)
    data=json.loads(result.stdout);paths=[]
    for n,s in data.items():
        name=prefix+n.replace('/','_');path=HERE/'results'/name;path.write_text(s);paths.append(path)
    return data,paths

def update():
    data,paths=collect(SNAP,'/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v10',SNAP_FILES,'cluster_')
    gx,gpaths=collect(GX,'~/workspace/rl4cv-gx10',GX_FILES,'gx10_');paths+=gpaths
    main=json.loads(data['progress.json']);acc=json.loads(gx.get('verification-v10/lean_corpus_v10/progress.json','{}'))
    setup=json.loads(gx.get('lean-v4.22.0/setup_completion.json',gx.get('lean-v4.22.0/setup_status.json','{}')))
    stamp=datetime.now().astimezone().strftime('%m-%d-%Y %H:%M %Z')
    status='DONE' if main['state']=='DONE' and 'verification-v10/lean_corpus_v10/completion.json' in gx else 'RUNNING'
    sentence=f"{status}, {stamp}. Cluster: {main['completed']:,}/10,995 checked, {main['outcomes'].get('PASS',0):,} PASS with48slots. GX10: {acc.get('completed',0):,}/1,600 checked, {acc.get('outcomes',{}).get('PASS',0):,} PASS with16slots; setup {setup.get('state','UNKNOWN')}. The74-case earlier recovery finished with6recoveries pending comment/format reassembly. No new model calls or training."
    path=HERE/'results.md';text=path.read_text();text=re.sub(r'\*\*TLDR:\*\*[^\n]*','**TLDR:** '+sentence,text,count=1)
    marker='\n## Latest automatic snapshot\n'
    if marker in text:text=text[:text.index(marker)]
    text+=marker+'\n'+sentence+'\n\nTheGX10shard is a subset of the10,995original cells. Successful exact-source ARM receipts can be reused by unstarted cluster cells; host totals must not be added as distinct statements. Raw evidence remains on its execution host.\n';path.write_text(text);paths.append(path)
    ckpt=HERE/'CKPT_verification.md';s=ckpt.read_text();s=re.sub(r'Last updated:[^\n]*','Last updated: '+stamp+'.',s,count=1);s=re.sub(r'## Results\n.*?(?=## Stuck / blocked)', '## Results\n- '+sentence+'\n', s, count=1, flags=re.S);s+='- '+stamp+' -- '+sentence+'\n';ckpt.write_text(s);paths.append(ckpt)
    print(sentence,flush=True)
    key=(main['completed']//1000,main['state'],setup.get('state'),acc.get('completed',0)//500,acc.get('state'))
    return status,key,paths

def publish(paths):
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO,text=True).strip(),'Another writer owns staged changes.'
    subprocess.run(['git','pull','--ff-only','origin','main'],cwd=REPO,check=True,capture_output=True)
    names=[str(p.relative_to(REPO)) for p in paths]
    subprocess.run(['git','add','--']+names,cwd=REPO,check=True)
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO,text=True).splitlines()
    assert set(staged)<=set(names)
    diff=subprocess.check_output(['git','diff','--cached'],cwd=REPO,text=True)
    assert not re.search(r'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----',diff)
    subprocess.run(['git','diff','--cached','--check'],cwd=REPO,check=True,capture_output=True)
    if staged:
        subprocess.run(['git','commit','-m','Update live two-host Workbook verification receipts'],cwd=REPO,check=True,capture_output=True)
        subprocess.run(['git','push','origin','HEAD:main'],cwd=REPO,check=True,capture_output=True)
    for p in paths:
        target=CANON/p.relative_to(REPO);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');parser.add_argument('--publish',action='store_true');args=parser.parse_args()
    last=None
    while True:
        try:
            state,key,paths=update()
            if args.publish and (key!=last or state=='DONE'):publish(paths);last=key
            if not args.watch or state=='DONE':return
        except Exception as exc:
            print(type(exc).__name__,str(exc)[:500],flush=True)
            if not args.watch:raise
        time.sleep(60)

if __name__=='__main__':main()
