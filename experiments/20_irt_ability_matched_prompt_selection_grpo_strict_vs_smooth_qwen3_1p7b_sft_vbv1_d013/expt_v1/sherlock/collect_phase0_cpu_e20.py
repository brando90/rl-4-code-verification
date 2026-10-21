"""TLDR: Audit durable compiler/source streams and bundle scored Phase 0 tables without rerunning any model."""
from pathlib import Path
import csv,hashlib,json,os,tarfile,time,subprocess,collections
E=Path(os.environ.get('E20_ROOT','/scratch/users/brando9/rl4cv_sherlock/e20'));P=E/'phase0'; O=P/'collected_cpu';O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=[];calls=[];summ=collections.Counter();errors=[]
for stage in ['scores','partial']:
 for c in range(4):
  for k in range(8):
   name=f'e20_p0_c{c}_s{k}';d=P/stage/name
   for pattern in ['*_per_task.csv','*.json','completion_receipt.txt']:
    for p in d.glob(pattern):
     manifest.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,kind='score_output'))
   if not (d/'completion_receipt.txt').is_file():errors.append(f'{name}/{stage}: no completion receipt')
   for p in (d/'compiler_diagnostics').glob('call_*/execution.json'):
    x=json.loads(p.read_text());folder=p.parent;ident=x.get('context',{})
    item=dict(stage=stage,job=name,path=str(p),sha256=sha(p),state=x['state'],exit_code=x.get('exit_code'),timed_out=x.get('timed_out'),compiler_sha256=x['compiler']['sha256'],stdout_sha256='',stderr_sha256='',stdout_bytes=0,stderr_bytes=0,source_count=len(x.get('sources',[])))
    for stream in ['stdout','stderr']:
     q=folder/f'{stream}.log'
     if not q.is_file():errors.append(f'{q}: missing');continue
     h=sha(q);item[stream+'_sha256']=h;item[stream+'_bytes']=q.stat().st_size
     if x.get(stream+'_sha256') and x[stream+'_sha256']!=h:errors.append(f'{q}: hash mismatch')
    for source in x.get('sources',[]):
     q=folder/source['snapshot']
     if not q.is_file() or sha(q)!=source['sha256']:errors.append(f'{q}: source missing/hash mismatch')
    summ[stage+':'+x['state']]+=1;calls.append(item)
   launcher=d/'compiler_diagnostics/launcher.json'
   if stage=='scores':
    if not launcher.is_file():errors.append(f'{launcher}:missing')
    else:
     x=json.loads(launcher.read_text());manifest.append(dict(path=str(launcher),sha256=sha(launcher),bytes=launcher.stat().st_size,kind='D109_launcher'))
     if x['state']!='COMPLETE':errors.append(f'{launcher}: {x["state"]}')
for name,rows in [('score_output_manifest.csv',manifest),('compiler_call_manifest.csv',calls)]:
 if not rows:errors.append(name+':empty');continue
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary=dict(created_unix=time.time(),cpu_only=True,outputs=len(manifest),compiler_calls=len(calls),call_states=dict(summ),errors=errors)
(O/'diagnostic_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
# A compact retrieval bundle keeps original scorer rows and partial records plus checksummed raw-diagnostic pointers.
archive=P/'phase0_cpu_tables.tgz'
with tarfile.open(archive,'w:gz') as tf:
 for p in [P/'phase0_gen_receipts.csv',P/'phase0_cells_e20.csv',P/'phase0_summary_e20.json',*O.iterdir()]:
  if p.is_file():tf.add(p,arcname=str(p.relative_to(P)))
 for row in manifest:
  p=Path(row['path']);tf.add(p,arcname=str(p.relative_to(P)))
print(json.dumps(summary));print(sha(archive),str(archive))
raise SystemExit(bool(errors))
