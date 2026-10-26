from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import sys,json,time,fcntl
sys.path.insert(0,"/lfs/skampere1/0/eth127/rl4cv_tiny_training/repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v18")
import repair_batches as r
with (r.ROOT/"mechanical_prescreen.lock").open("a") as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 r.assert_inspector();r.prior.kernel_module()
 ids=[p.parent.name for p in (r.ROOT/"cases").glob("*/status.json") if r.read(p)["state"]=="PENDING"]
 def one(tid):
  work=r.ROOT/"mechanical_prescreen"/tid;work.mkdir(parents=True,exist_ok=True)
  r.mechanical_rfl(tid,work)
  return dict(task_id=tid,status=r.read(r.ROOT/"cases"/tid/"status.json")["state"])
 done=[]
 r.write(r.ROOT/"mechanical_prescreen_progress.json",dict(state="RUNNING",declared=len(ids),completed=0,paid_calls=0,observed_unix=time.time()))
 with ThreadPoolExecutor(max_workers=16) as pool:
  jobs={pool.submit(one,tid):tid for tid in ids}
  for f in as_completed(jobs):
   try:done.append(f.result())
   except Exception as exc:done.append(dict(task_id=jobs[f],error=repr(exc)))
   r.write(r.ROOT/"mechanical_prescreen_progress.json",dict(state="RUNNING",declared=len(ids),completed=len(done),accepted=sum(x.get("status","")=="ACCEPTED_MECHANICAL_RFL" for x in done),paid_calls=0,observed_unix=time.time()))
 r.write(r.ROOT/"mechanical_prescreen_completion.json",dict(state="DONE",declared=len(ids),completed=len(done),accepted=sum(x.get("status","")=="ACCEPTED_MECHANICAL_RFL" for x in done),paid_calls=0,results=done,observed_unix=time.time()))
