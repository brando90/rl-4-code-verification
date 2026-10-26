"""Mirror and publish actual Sol repair outcomes while the remote queue owns execution and recovery."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import shlex
import subprocess
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
CANON=Path('/Users/lethan3/Documents/veribench-projects/rl-4-code-verification')
SSH=['ssh','-S','/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control','-o','BatchMode=yes','-o','ConnectTimeout=10','eth127@skampere1.stanford.edu']
COLLECT=r'''import json,csv,io,collections
from pathlib import Path
p=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v11')
names=['progress.json','usage.json','dispatch.json','manifest.json','completion.json','checker_controls/completion.json','final/summary.json','final/row_results.csv','provider_hold.json']
data={n.replace('/','_'):(p/n).read_text() for n in names if (p/n).exists()}
rows=[]
for item in json.loads((p/'manifest.json').read_text()):
 tid=item['task_id'];f=p/'cases'/tid;status=json.loads((f/'status.json').read_text());decision=json.loads((f/'decision.json').read_text()) if (f/'decision.json').exists() else {}
 rows.append(dict(task_id=tid,state=status['state'],attempts=status.get('attempts',0),verified=decision.get('verified',False),decision=decision.get('decision',''),source_sha256=decision.get('source_sha256',''),rationale=decision.get('rationale',''),error=str(status.get('error',''))))
s=io.StringIO();w=csv.DictWriter(s,fieldnames=['task_id','state','attempts','verified','decision','source_sha256','rationale','error'],lineterminator='\n');w.writeheader();w.writerows(rows);data['repair_rows.csv']=s.getvalue()
if (p/'final/protected_screen.json').exists():
 screen=json.loads((p/'final/protected_screen.json').read_text());screen.pop('clean_ids',None);data['protected_screen_summary.json']=json.dumps(screen,indent=2)+'\n'
print(json.dumps(data))
'''

def update():
    response=subprocess.run(SSH+['python3 -c '+shlex.quote(COLLECT)],capture_output=True,text=True,timeout=60,check=True)
    data=json.loads(response.stdout);paths=[]
    for name,text in data.items():
        p=HERE/'results'/name;p.write_text(text);paths.append(p)
    progress=json.loads(data['progress.json']);complete=json.loads(data.get('completion.json','{}'));summary=json.loads(data.get('final_summary.json','{}'))
    verified=progress['verified'];done=progress['states'].get('DONE',0);state=complete.get('state','RUNNING')
    stamp=datetime.now().astimezone().strftime('%m-%d-%Y %H:%M %Z')
    sentence=f"{state}, {stamp}. Sol/high: {done}/68 cases complete, {verified} exact-source kernel-verified explicit repairs; {progress['states'].get('RUNNING',0)} running and {progress['states'].get('PENDING',0)} pending."
    if summary:sentence+=f" Final formatting/screens admit {summary['training_rows']} repaired examples; no new training."
    p=HERE/'results.md';text=p.read_text();text=re.sub(r'\*\*TLDR:\*\*[^\n]*','**TLDR:** '+sentence,text,count=1);marker='\n## Latest execution snapshot\n'
    if marker in text:text=text[:text.index(marker)]
    text+=marker+'\n'+sentence+'\n\n[All68case rows](results/repair_rows.csv) · [Usage estimate](results/usage.json) · [Frozen dispatch](results/dispatch.json). Raw candidates, logs, final Lean files and training artifacts remain under `/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v11/`.\n';p.write_text(text);paths.append(p)
    p=HERE/'CKPT_repairs.md';s=p.read_text();s=re.sub(r'Last updated:[^\n]*','Last updated: '+stamp+'.',s,count=1);s=re.sub(r'## Results\n.*?(?=## Stuck / blocked)','## Results\n- '+sentence+'\n',s,count=1,flags=re.S);s+='- '+stamp+' -- '+sentence+'\n';p.write_text(s);paths.append(p)
    print(sentence,flush=True)
    return state,(done//10,verified//10,state),paths

def publish(paths):
    assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO,text=True).strip()
    subprocess.run(['git','pull','--ff-only','origin','main'],cwd=REPO,capture_output=True,check=True)
    names=[str(p.relative_to(REPO)) for p in paths];subprocess.run(['git','add','--']+names,cwd=REPO,check=True)
    staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=REPO,text=True).splitlines();assert set(staged)<=set(names)
    diff=subprocess.check_output(['git','diff','--cached'],cwd=REPO,text=True)
    assert not re.search(r'sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----',diff)
    subprocess.run(['git','diff','--cached','--check'],cwd=REPO,capture_output=True,check=True)
    if staged:
        subprocess.run(['git','commit','-m','Update live Sol explicit-proof repair outcomes'],cwd=REPO,capture_output=True,check=True)
        pushed=subprocess.run(['git','push','origin','HEAD:main'],cwd=REPO,capture_output=True,text=True)
        if pushed.returncode:
            subprocess.run(['git','fetch','origin','main'],cwd=REPO,check=True,capture_output=True)
            subprocess.run(['git','merge','--no-edit','origin/main'],cwd=REPO,check=True,capture_output=True)
            subprocess.run(['git','push','origin','HEAD:main'],cwd=REPO,check=True,capture_output=True)
    for p in paths:
        target=CANON/p.relative_to(REPO);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');parser.add_argument('--publish',action='store_true');args=parser.parse_args();last=None
    while True:
        try:
            state,key,paths=update()
            if args.publish and (key!=last or state!='RUNNING'):publish(paths);last=key
            if not args.watch or state!='RUNNING':return
        except Exception as exc:
            print(type(exc).__name__,str(exc)[:500],flush=True)
            if not args.watch:raise
        time.sleep(45)

if __name__=='__main__':main()
