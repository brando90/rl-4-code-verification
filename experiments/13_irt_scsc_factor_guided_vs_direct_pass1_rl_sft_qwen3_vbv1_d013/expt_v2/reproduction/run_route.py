#!/usr/bin/env python3
"""Run one isolated R2 route with shared memory admission, persistent attempts and sanitized opaque receipts."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import argparse
import hashlib
import fcntl
import traceback
import json
import os
import subprocess
import sys
import time
import psutil

HERE=Path(__file__).resolve().parent;V2=HERE.parent
sys.path.insert(0,str(V2))
import watchdog_e13v2 as watchdog
RUN='e13v2_a1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def alive_group(identity):
    if watchdog.live(identity):return True
    if identity['boot_id']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():return False
    for proc in psutil.process_iter(['pid','status']):
        try:
            if proc.info['status']!='zombie' and os.getpgid(proc.pid)==identity['pgid']:return True
        except (psutil.Error,ProcessLookupError,PermissionError):pass
    return False


def route_receipt(root,route,rows,results):
    measured=[r for r in results if r['status']=='measured']
    limits=[r for r in results if r['status']=='deterministic_resource_limit']
    failures=[r for r in results if r['status'] not in {'measured','deterministic_resource_limit'}]
    complete=len(results)==len(rows) and not failures
    equal=all(r.get('oracle_equal',False) for r in measured)
    consistent=all(not r.get('consistency','untyped_missing').startswith('untyped') for r in measured)
    status='PASS' if complete and equal and consistent else ('FAIL' if complete else 'INCOMPLETE')
    result={'route':route,'declared':len(rows),'accounted':len(results),'measured':len(measured),
            'typed_deterministic_limits':len(limits),'complete_required':complete,
            'equality':'PASS' if equal and consistent and complete else 'FAIL' if not equal or not consistent else 'INCOMPLETE',
            'status':status,'manifest_sha256':sha(root/(route+'_manifest.jsonl')),
            'results_sha256':sha(root/route/'results.jsonl'),'test_outcomes_disclosed':False}
    # No cell identifiers, scores, components, examples, or discrepancy details leave opaque storage.
    (root/(route+'_public_receipt.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return status


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--route',choices=['ordinary','opaque'],required=True);ap.add_argument('--resume',action='store_true');a=ap.parse_args()
    root=Path(os.environ['WR'])/'R2';wd=root.parent/'watchdog'
    execution=json.loads((root/'execution_lock.json').read_text());l1_path=V2/'locks/L1v2.json'
    if sha(l1_path)!=execution['L1v2_sha256']:raise ValueError('L1v2 binding changed')
    l1=json.loads(l1_path.read_text())
    for path,expected in l1['hashes'].items():
        if sha(path)!=expected:raise ValueError('frozen implementation/input binding changed')
    route_fence=(root/(a.route+'_execution.lock')).open('a')
    fcntl.flock(route_fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
    rows=[json.loads(line) for line in (root/(a.route+'_manifest.jsonl')).read_text().splitlines()]
    if any((r['split']=='test')!=(a.route=='opaque') for r in rows):raise ValueError('route binding changed')
    folder=root/a.route;folder.mkdir(exist_ok=a.resume)
    with watchdog.locked(wd):
        db=watchdog.database(wd);watchdog.register(db,RUN,'r2_'+a.route,os.getpid())
        db.execute('CREATE TABLE IF NOT EXISTS r2_slots (run TEXT,pid INTEGER,identity_json TEXT,cell TEXT,PRIMARY KEY(run,pid))');db.commit();db.close()
    result_path=folder/'results.jsonl';done={}
    if result_path.exists():
        if not a.resume:raise ValueError('existing route cannot be rerun')
        for line in result_path.read_text().splitlines():
            value=json.loads(line)
            if value['ordinal'] in done:raise ValueError('duplicate result')
            done[value['ordinal']]=value
    if any(i<0 or i>=len(rows) or v['cell_id']!=rows[i]['cell_id'] for i,v in done.items()):raise ValueError('replaced route result')

    def run(ordinal,row):
        cell='R2/'+row['cell_id']
        while True:
            with watchdog.locked(wd):
                db=watchdog.database(wd)
                slots=list(db.execute('SELECT * FROM r2_slots WHERE run=?',(RUN,)))
                active=0;cell_alive=False
                for slot in slots:
                    if alive_group(json.loads(slot['identity_json'])):
                        active+=1
                        if slot['cell']==cell:cell_alive=True
                    else:db.execute('DELETE FROM r2_slots WHERE run=? AND pid=?',(RUN,slot['pid']))
                mem=psutil.virtual_memory();admitted=min(execution['max_workers'],int(.5*mem.available/execution['p99_peak_bytes']))
                if not cell_alive and active<admitted and mem.available>=.25*mem.total:
                    prior=list(db.execute('SELECT * FROM attempts WHERE run=? AND cell=? ORDER BY attempt',(RUN,cell)))
                    if prior and prior[-1]['status'] not in {'running','transient_infrastructure'}:
                        existing=folder/'cells'/f'{ordinal:05d}'/f"attempt_{prior[-1]['attempt']}"/'receipt.json'
                        if not existing.is_file():
                            db.close();return {'ordinal':ordinal,'cell_id':row['cell_id'],'status':'integrity_defect','attempt':prior[-1]['attempt']}
                        result=json.loads(existing.read_text())
                        if result.get('source_sha256')!=row['source_sha256']:raise ValueError('recovery receipt binding changed')
                        db.close();return result
                    if prior and prior[-1]['status']=='running':
                        # Resume only after registered children were adopted and have finished.
                        existing=folder/'cells'/f'{ordinal:05d}'/f"attempt_{prior[-1]['attempt']}"/'receipt.json'
                        if existing.is_file():
                            result=json.loads(existing.read_text())
                            if result.get('source_sha256')!=row['source_sha256']:raise ValueError('recovery receipt binding changed')
                            db.execute('UPDATE attempts SET status=?,finished=? WHERE run=? AND cell=? AND attempt=?',(result['status'],watchdog.now(),RUN,cell,prior[-1]['attempt']));db.commit();db.close();return result
                        db.execute('UPDATE attempts SET status=?,finished=? WHERE run=? AND cell=? AND attempt=?',('transient_infrastructure',watchdog.now(),RUN,cell,prior[-1]['attempt']));db.commit()
                    if len(prior)>=2:
                        db.close();return {'ordinal':ordinal,'cell_id':row['cell_id'],'status':'transient_infrastructure','attempt':2}
                    attempt=watchdog.begin(db,RUN,cell,row['source_sha256'])
                    log=folder/f'{ordinal:05d}_attempt_{attempt}.log';handle=log.open('x')
                    command=['prlimit',f"--as={execution['address_space_bytes']}",'--',sys.executable,str(HERE/'cell_worker.py'),'--route',a.route,'--ordinal',str(ordinal),'--attempt',str(attempt)]
                    child=subprocess.Popen(command,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
                    identity=watchdog.register(db,RUN,'r2_cell',child.pid)
                    db.execute('INSERT INTO r2_slots VALUES (?,?,?,?)',(RUN,child.pid,json.dumps(identity),cell));db.commit();db.close();break
                db.commit();db.close()
            time.sleep(1)
        returncode=child.wait();handle.close()
        while alive_group(identity):time.sleep(1)
        receipt=folder/'cells'/f'{ordinal:05d}'/f'attempt_{attempt}'/'receipt.json'
        result=json.loads(receipt.read_text()) if receipt.exists() else {'ordinal':ordinal,'cell_id':row['cell_id'],'status':'unresolved_measurement','returncode':returncode,'attempt':attempt}
        with watchdog.locked(wd):
            db=watchdog.database(wd)
            db.execute('UPDATE attempts SET status=?,finished=? WHERE run=? AND cell=? AND attempt=?',(result['status'],watchdog.now(),RUN,cell,attempt))
            db.execute('DELETE FROM r2_slots WHERE run=? AND pid=?',(RUN,child.pid));db.commit();db.close()
        return result

    with result_path.open('a' if a.resume else 'x') as out,ThreadPoolExecutor(max_workers=execution['max_workers']) as pool:
        pending=[pool.submit(run,i,row) for i,row in enumerate(rows) if i not in done]
        for future in as_completed(pending):
            result=future.result();done[result['ordinal']]=result
            out.write(json.dumps(result)+'\n');out.flush();os.fsync(out.fileno())
            if len(done)%100==0:print(json.dumps({'route':a.route,'processed':len(done),'declared':len(rows)}),flush=True)
    status=route_receipt(root,a.route,rows,list(done.values()))
    return 0 if status=='PASS' else 1


if __name__=='__main__':
    try:code=main()
    except Exception as exc:
        root=Path(os.environ['WR'])/'R2'
        route=sys.argv[sys.argv.index('--route')+1]
        folder=root/route;folder.mkdir(exist_ok=True)
        (folder/'private_coordinator_error.txt').write_text(traceback.format_exc())
        print(json.dumps({'route':route,'status':'INCOMPLETE','error_type':type(exc).__name__,'test_outcomes_disclosed':False}),flush=True)
        code=1
    raise SystemExit(code)
