#!/usr/bin/env python3
"""Execute the frozen train diagnostic once with owned process groups and headroom admission."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import math
import threading
import numpy as np

import psutil

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE.parent/'R0_attempt_2'))
sys.path.insert(0,str(HERE))
from historical_oracle_v2 import digest
import watchdog_e13v2 as watchdog


def main():
    wr=Path(os.environ['WR']);root=wr/'R1_attempt_1'
    lock=json.loads((root/'execution_lock.json').read_text())
    for path,expected in lock['hashes'].items():
        if digest(path)!=expected:raise ValueError('R1 binding changed')
    rows=json.loads((root/'sample.json').read_text())
    (root/'started.json').open('x').write(json.dumps({'created':datetime.now(timezone.utc).isoformat()})+'\n')
    with watchdog.locked(wr/'watchdog'):
        db=watchdog.database(wr/'watchdog');watchdog.register(db,'e13v2_a1','r1_gate',os.getpid());db.close()
    completed_peaks=[]
    memory_lock=threading.Lock()
    admission=threading.Condition()
    active=[0]
    def run(ordinal,row):
        with admission:
            while True:
                mem=psutil.virtual_memory()
                with memory_lock:
                    p99=float(np.percentile(completed_peaks,99)) if completed_peaks else lock['address_space_bytes']
                allowed=min(48,max(1,math.floor(.5*mem.available/max(p99,1))))
                if mem.available >= .25*mem.total and active[0]<allowed:
                    active[0]+=1
                    break
                admission.wait(timeout=1)
        with watchdog.locked(wr/'watchdog'):
            db=watchdog.database(wr/'watchdog');attempt=watchdog.begin(db,'e13v2_a1','R1_attempt_1/'+row['cell_id'],row['source_sha256']);db.close()
        log=root/f'{ordinal:04d}.log'
        with log.open('x') as handle:
            command=['prlimit',f"--as={lock['address_space_bytes']}",'--',sys.executable,str(HERE/'r1_worker_v2.py'),'--ordinal',str(ordinal)]
            child=subprocess.Popen(command,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
            with watchdog.locked(wr/'watchdog'):
                db=watchdog.database(wr/'watchdog');watchdog.register(db,'e13v2_a1','r1_cell_launcher',child.pid);db.close()
            exit_code=child.wait()
        receipt_path=root/'cells'/f'{ordinal:04d}'/'receipt.json'
        result=json.loads(receipt_path.read_text()) if receipt_path.is_file() else {'cell_id':row['cell_id'],'status':'unresolved_measurement','original_category':row['original_category']}
        result.update(ordinal=ordinal,exit_code=exit_code)
        with watchdog.locked(wr/'watchdog'):
            db=watchdog.database(wr/'watchdog')
            db.execute('UPDATE attempts SET status=?,finished=? WHERE run=? AND cell=? AND attempt=?',
                       (result['status'],watchdog.now(),'e13v2_a1','R1_attempt_1/'+row['cell_id'],attempt));db.commit();db.close()
        if result.get('peak_tree_rss_bytes',0)>0:
            with memory_lock:completed_peaks.append(result['peak_tree_rss_bytes'])
        with admission:
            active[0]-=1;admission.notify_all()
        return result
    with (root/'results.jsonl').open('x') as out:
        first=run(0,rows[0]);out.write(json.dumps(first)+'\n');out.flush();os.fsync(out.fileno())
        if not completed_peaks:raise RuntimeError('bootstrap cell lacks memory evidence; stop before concurrent admission')
        mem=psutil.virtual_memory();p99=float(np.percentile(completed_peaks,99))
        workers=min(48,max(1,math.floor(.5*mem.available/p99)))
        (root/'memory_admission.json').write_text(json.dumps({'bootstrap_cells':1,'bootstrap_peak_bytes':completed_peaks[0],'available_bytes':mem.available,'workers':workers,'address_space_bytes':lock['address_space_bytes'],'aggregate_policy':'admit only above 25 percent available; lower active limit using observed p99 and current headroom'},indent=2)+'\n')
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending=[pool.submit(run,i,row) for i,row in enumerate(rows[1:],1)]
            for future in as_completed(pending):
                result=future.result();out.write(json.dumps(result)+'\n');out.flush();os.fsync(out.fileno())
                print(json.dumps({'ordinal':result['ordinal'],'status':result['status']}),flush=True)
    from summarize_r1 import summarize
    receipt=summarize(root)
    print(json.dumps({k:receipt[k] for k in ('stage','status','declared','measured','oracle_matches')}),flush=True)
    return 0 if receipt['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
