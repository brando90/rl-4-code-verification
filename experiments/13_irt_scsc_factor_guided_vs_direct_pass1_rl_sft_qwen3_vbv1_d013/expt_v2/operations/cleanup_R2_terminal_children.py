"""Operational cleanup of registered descendants after their cell worker and receipt are terminal.
No measurement is run, changed, retried or disclosed. Signals use verified per-process pidfds.
"""
from pathlib import Path
import argparse,json,os,sys,signal,hashlib,time,psutil
root=Path('/lfs/skampere1/0/brando9/rl4cv_e13v2');v=root/'rl-4-code-verification/experiments/13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/expt_v2';sys.path.insert(0,str(v));import watchdog_e13v2 as w
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');a=ap.parse_args();RUN='e13v2_a1';wd=root/'watchdog'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def members(pgid):
 out=[]
 for p in psutil.process_iter(['pid','status']):
  try:
   if p.info['status']!='zombie' and os.getpgid(p.pid)==pgid:out.append(p.pid)
  except (psutil.Error,ProcessLookupError,PermissionError):pass
 return out
# Only routing metadata and terminal process receipt identity/status are consulted.
index={}
for route in ['ordinary','opaque']:
 for ordinal,line in enumerate((root/'R2'/f'{route}_manifest.jsonl').open()):
  row=json.loads(line);index['R2/'+row['cell_id']]=(route,ordinal,row['source_sha256'])
db=w.database(wd);eligible=[];blocked=0
for slot in db.execute('SELECT * FROM r2_slots WHERE run=?',(RUN,)):
 ident=json.loads(slot['identity_json'])
 if w.live(ident):continue
 pids=members(ident['pgid'])
 if not pids:continue
 route,ordinal,source_hash=index[slot['cell']]
 prior=db.execute('SELECT * FROM attempts WHERE run=? AND cell=? ORDER BY attempt DESC LIMIT 1',(RUN,slot['cell'])).fetchone()
 receipt=root/'R2'/route/'cells'/f'{ordinal:05d}'/f"attempt_{prior['attempt']}"/'receipt.json'
 if not receipt.is_file():blocked+=1;continue
 value=json.loads(receipt.read_text())
 if value['cell_id']!=slot['cell'][3:] or value['source_sha256']!=source_hash or value['status'] not in {'measured','deterministic_resource_limit','integrity_defect','unresolved_measurement'}:blocked+=1;continue
 verified=[]
 for pid in pids:
  registered=[dict(r) for r in db.execute('SELECT * FROM processes WHERE run=? AND pid=?',(RUN,pid))]
  match=next((r for r in registered if w.live(r) and r['pgid']==ident['pgid']),None)
  if match is None:break
  verified.append(match)
 if len(verified)!=len(pids):blocked+=1;continue
 eligible.append({'leader':ident,'receipt':str(receipt),'receipt_sha256':sha(receipt),'descendants':verified})
db.close()
audit={'at':w.now(),'apply':a.apply,'eligible_completed_workers':len(eligible),'registered_terminal_descendants':sum(len(x['descendants']) for x in eligible),'blocked_groups':blocked,'scientific_outcomes_disclosed':False,'measurement_retries':0}
# Full operational identities remain private; public output contains only process/completeness counts.
private=root/'state'/f"R2_terminal_child_cleanup_{time.time_ns()}.json"
private.write_text(json.dumps({'summary':audit,'process_receipts':eligible},indent=2)+'\n')
if a.apply:
 signalled=[]
 with w.locked(wd):
  for item in eligible:
   leader=item['leader']
   if w.live(leader) or sha(item['receipt'])!=item['receipt_sha256']:raise RuntimeError('terminal receipt/worker identity changed')
   current=members(leader['pgid']);known={r['pid'] for r in item['descendants']}
   if not set(current)<=known:raise RuntimeError('unregistered process joined group')
   for row in item['descendants']:
    if not w.live(row):continue
    fd=os.pidfd_open(row['pid'])
    try:
     if not w.live(row):continue
     signal.pidfd_send_signal(fd,signal.SIGTERM,None,0);signalled.append(row)
    finally:os.close(fd)
 deadline=time.monotonic()+5
 while time.monotonic()<deadline and any(w.live(r) for r in signalled):time.sleep(.1)
 forced=0
 for row in signalled:
  if not w.live(row):continue
  fd=os.pidfd_open(row['pid'])
  try:
   if w.live(row):signal.pidfd_send_signal(fd,signal.SIGKILL,None,0);forced+=1
  finally:os.close(fd)
 audit.update(signalled_processes=len(signalled),forced_kills=forced)
 private.write_text(json.dumps({'summary':audit,'process_receipts':eligible},indent=2)+'\n')
print(json.dumps(audit))
