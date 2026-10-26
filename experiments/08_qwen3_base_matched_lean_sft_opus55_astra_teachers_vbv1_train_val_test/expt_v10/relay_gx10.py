"""Relay checked GX10 successes to unstarted cluster cells, retaining independent host evidence and ownership."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

SNAP=['ssh','-S','/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control','-o','BatchMode=yes','-o','ConnectTimeout=10','eth127@skampere1.stanford.edu']
GX=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','cactushacks-gx10']
FETCH='''import json,subprocess
from pathlib import Path
p=Path.home()/"workspace/rl4cv-gx10/verification-v10/lean_corpus_v10"
rows=[]
for f in (p/"checks").glob("workbook_*/result.json"):
 r=json.loads(f.read_text())
 if r["passed"]:
  rows.append(dict(result=r,report=json.loads((f.parent/"kernel_report.json").read_text())))
print(json.dumps(dict(rows=rows,complete=(p/"completion.json").exists(),alive=subprocess.run(["tmux","has-session","-t","rl4cv-gx10-verify-v10"],capture_output=True).returncode==0)))
'''
IMPORT=r'''import json,sys,hashlib,importlib.util,os,time
from pathlib import Path
p=Path("/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v10")
spec=importlib.util.spec_from_file_location("relay_kernel",p.parent/"repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py")
k=importlib.util.module_from_spec(spec);sys.modules[spec.name]=k;spec.loader.exec_module(k)
manifest={r["task_id"]:r for r in map(json.loads,(p/"manifest.jsonl").read_text().splitlines())}
payload=json.load(sys.stdin);imported=existing=0
for row in payload["rows"]:
 r=row["result"];report=row["report"];tid=r["task_id"]
 assert r["source_sha256"]==manifest[tid]["source_sha256"]==report["source_sha256"]
 assert k.valid_report(report) and report["n_theorems"]>=1 and report["n_honest"]==report["n_theorems"]
 saved=p/"gx10_received"/tid;saved.mkdir(parents=True,exist_ok=True)
 (saved/"result.json").write_text(json.dumps(r,indent=2)+"\n");(saved/"kernel_report.json").write_text(json.dumps(report,indent=2)+"\n")
 target=p/"checks"/tid
 if target.exists():existing+=1;continue
 staging=p/"gx10_received"/(tid+"_staging");staging.mkdir(exist_ok=True)
 r=dict(r,evidence_host="cactushacks-gx10",imported_unix=time.time(),import_policy="native same-version kernel PASS, exact frozen source hash, no existing cluster owner")
 (staging/"result.json").write_text(json.dumps(r,indent=2)+"\n");(staging/"kernel_report.json").write_text(json.dumps(report,indent=2)+"\n")
 try:os.rename(staging,target);imported+=1
 except OSError:
  if not target.exists():raise
  existing+=1
summary=dict(gx10_successes=len(payload["rows"]),new_imports=imported,existing_cells=existing,gx10_complete=payload["complete"],observed_unix=time.time())
(p/"gx10_relay.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary))
'''

def remote(command,code,stdin=None):
    return subprocess.run(command+['python3 -c '+shlex.quote(code)],input=stdin,capture_output=True,text=True,timeout=60,check=True).stdout

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--once',action='store_true');args=parser.parse_args()
    while True:
        try:
            data=remote(GX,FETCH)
            report=remote(SNAP,IMPORT,data)
            print(report.strip(),flush=True)
            if json.loads(data)['complete'] or args.once:return
            if not json.loads(data)['alive']:raise SystemExit('GX10 worker exited without completion; raw logs retained; cluster continues full cohort.')
        except (subprocess.SubprocessError,ValueError) as exc:print(type(exc).__name__,str(exc)[:300],flush=True)
        time.sleep(30)

if __name__=='__main__':main()
