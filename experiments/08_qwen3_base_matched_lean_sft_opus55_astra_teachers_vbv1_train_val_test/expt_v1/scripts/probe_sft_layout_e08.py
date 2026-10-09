"""Run bounded disposable offload checks under a task lease and retain every outcome."""
import os,sys,json,time,pathlib,subprocess,fcntl,datetime,signal,hashlib
W=pathlib.Path('/lfs/skampere1/0/brando9/rl4cv_e08');D=W/'layout_probe_10-09-2026';E=W/'rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1';sys.path.insert(0,str(E/'scripts'));import gpu_lease_e08 as GL
if (D/'execution.json').exists():
 raise SystemExit('Probe already recorded; preserve its spent accounting and freeze a new authorized plan before another attempt')
key='e08-layout-probe-8339e1ac'; now=time.time(); expiry=now+1780  # reserve 20 seconds for owned-process cleanup within the 1800-second lease window
report={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'started_epoch':now,'deadline_epoch':expiry,'identity':GL.identity(os.getpid()),'steps':[],'devices':[0,1],'status':'STARTING','budget_seconds':1800}
def save():
 (D/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
def owned_pids():
 out=[]
 for p in pathlib.Path('/proc').iterdir():
  if not p.name.isdigit() or int(p.name)==os.getpid():continue
  try:
   if p.stat().st_uid!=os.getuid():continue
   env=(p/'environ').read_bytes().split(b'\0')
   if b'RAY_TMPDIR=/tmp/user/11295/e08layout_8339' in env or any(v.startswith(b'RAY_TMPDIR=') and b'e08layout_8339' in v for v in env):out.append(int(p.name))
  except (OSError,PermissionError): pass
 return out
with (W/'pipeline/lock').open('a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX);table=GL.gpu_table();leases=GL.load();busy={g for l in GL.live_leases(leases).values() for g in l['gpus']}
 if any(table[g] or g in busy for g in [0,1]):report['status']='RESOURCE_WAIT';save();sys.exit(3)
 leases[key]={'owner':'e08-layout-probe','stage':'disposable-tp2-offload','kind':'infrastructure-probe','gpus':[0,1],'cuda_visible_devices':'0,1','since':GL.ts(),'expires_utc':datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc).isoformat(),'identity':GL.identity(os.getpid()),'boundary':'Cumulative 1800 seconds, maximum two devices; every output disposable','released':False};GL.save(leases)
env=dict(os.environ);env.update(CUDA_VISIBLE_DEVICES='0,1',HF_HOME=str(W/'cache/huggingface'),HF_HUB_OFFLINE='1',UV_CACHE_DIR=str(W/'cache/uv'),UV_PYTHON_INSTALL_DIR=str(W/'cache/uv_python'),RAY_TMPDIR=f'/tmp/user/{os.getuid()}/e08layout_8339',E08_MODEL_PATH=str(W/'cache/huggingface/hub/models--Qwen--Qwen3-14B-Base/snapshots/0b0bd3732e2c374d483664439ea334928b65f304'),E08_CHECKPOINT_DIR=str(D/'checkpoints'),E08_LOG_DIR=str(D/'logs'),E08_TENSORBOARD_DIR=str(D/'tb'),E08_RUN_NAME='e08-disposable-tp2-offload',E08_TRAIN_JSONL=str(D/'train6.jsonl'),E08_VAL_JSONL=str(W/'sft/s_v1_val_dummy.jsonl'),OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',RAY_ADDRESS='local')
env.pop('PYTHONPATH',None);report['status']='RUNNING';save()
try:
 for k in [2,3]:
  f=D/f'to_step_{k}.log';beg=time.time()
  with f.open('w') as log:
   p=subprocess.Popen(['uv','run','examples/run_sft.py','--config',str(D/'probe.yaml'),f'sft.max_num_steps={k}'],cwd=W/'nemo_rl',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   report['driver']={'pid':p.pid,'identity':GL.identity(p.pid),'target_step':k};save();next_sample=0
   while p.poll() is None and time.time()<expiry:
    if time.time()>next_sample:
     q=subprocess.run(['nvidia-smi','-i','0,1','--query-gpu=index,memory.used,memory.free,utilization.gpu,utilization.memory','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=15)
     with (D/'resources.jsonl').open('a') as rr:rr.write(json.dumps({'time':time.time(),'gpus':q.stdout,'load':pathlib.Path('/proc/loadavg').read_text().strip(),'owned_pids':owned_pids()})+'\n')
     next_sample=time.time()+10
    time.sleep(1)
   if p.poll() is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    report['status']='TIMEOUT'
   report['steps'].append({'target':k,'exit':p.returncode,'seconds':time.time()-beg,'log':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()});save()
   if p.returncode!=0:report['status']='FAILED' if report['status']!='TIMEOUT' else report['status'];break
 else:report['status']='EXECUTION_COMPLETE_PENDING_ADMISSION'
finally:
 cleanup=owned_pids();report['cleanup_pids']=cleanup
 for pid in cleanup:
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
 time.sleep(3)
 for pid in owned_pids():
  try:os.kill(pid,signal.SIGKILL)
  except ProcessLookupError:pass
 report['remaining_owned_pids']=owned_pids();report['elapsed_seconds']=time.time()-now;report['device_seconds']=2*report['elapsed_seconds'];report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
 with (W/'pipeline/lock').open('a') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);leases=GL.load();leases[key].update(released=True,released_at=GL.ts(),elapsed_seconds=report['elapsed_seconds']);GL.save(leases)
