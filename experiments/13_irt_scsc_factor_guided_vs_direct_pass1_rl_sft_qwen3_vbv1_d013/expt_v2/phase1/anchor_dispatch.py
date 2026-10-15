"""Dispatch a published S2 anchor panel in bounded leases, preserving every completed cell."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from anchor_lease import claim,release,remaining_seconds,MAX_DEVICE_HOURS,MAX_SEGMENT_SECONDS
from device_watch import observe
from dispatch import command,retire_remote_lease
from anchor_storage import atomic_json,write_new,mkdir
from panel import digest


def published_blob(repository,path,revision):
    repository=Path(repository);path=Path(path)
    subprocess.run(['git','merge-base','--is-ancestor',revision,'origin/main'],cwd=repository,check=True)
    blob=subprocess.check_output(['git','show',revision+':'+str(path.relative_to(repository))],cwd=repository)
    if blob!=path.read_bytes():raise ValueError('anchor prerequisite differs from its published revision')


def published(plan):
    published_blob(plan['repository'],plan['lock'],plan['published_revision'])
    lock=json.loads(Path(plan['lock']).read_text())
    if lock.get('gate')!='ANCHOR_GENERATION_S2' or lock.get('status')!='FROZEN':
        raise ValueError('anchor generation lock is not final')
    for binding in lock['bindings']:
        if digest(binding['path'])!=binding['sha256']:
            raise ValueError('anchor source/input binding changed: '+binding['path'])
    bound={b['path'] for b in lock['bindings']}
    if not {lock['LP1_result'],lock['S2_lock'],plan['configuration']}<=bound:
        raise ValueError('anchor lock omits its admission or configuration')
    published_blob(plan['repository'],lock['LP1_result'],lock['LP1_publication'])
    published_blob(plan['repository'],lock['S2_lock'],lock['S2_publication'])
    lp1=json.loads(Path(lock['LP1_result']).read_text())
    if (lp1.get('status')!='PASS' or lp1.get('condition')!='v2-S2'
            or not lp1.get('admission_statistics_computed') or lp1.get('a5_stage')!='confirmation'
            or lp1.get('numerical_dtype')!='float16' or lp1.get('gate_lock_sha256')!=digest(lock['S2_lock'])):
        raise ValueError('anchor generation lacks final S2 LP-1 admission')
    config=json.loads(Path(plan['configuration']).read_text())
    if (config['batch']!=lock['batch'] or config['maximum_seconds']!=MAX_SEGMENT_SECONDS
            or config['device_hour_cap']!=MAX_DEVICE_HOURS or config['maximum_cells']!=256):
        raise ValueError('anchor allocation differs from the frozen envelope')
    for route in config['routes']:
        if route['runtime']['numerical_dtype']!='float16' or route['runtime']['batch_size']!=32:
            raise ValueError('anchor route changed the admitted numerical/sampler settings')
        if route['runtime']['batch']!=config['batch']:
            raise ValueError('anchor route batch mismatch')
    if config['batch']=='full2':
        path=lock.get('calibration')
        if path not in bound:raise ValueError('independent batch 2 calibration is not bound')
        published_blob(plan['repository'],path,lock['calibration_publication'])
        calibration=json.loads(Path(path).read_text())
        if calibration.get('status')!='FROZEN' or calibration.get('F2')!=.75:
            raise ValueError('batch 2 requires frozen calibration, items and F2')
    return config


def remote_inventory(route):
    """Read the full ledger after checking the small inventory implementation/input hashes."""
    runtime=route['runtime'];directory=str(Path(route['supervisor_script']).parent)
    required={str(Path(directory)/name) for name in ('anchor_panel.py','panel.py','anchor_storage.py','lease.py')}
    required|={runtime['manifest'],runtime['train_ids']}
    bindings=[b for b in runtime['bindings'] if b['path'] in required]
    if {b['path'] for b in bindings}!=required:raise ValueError('unbound remote ledger reader')
    script='''import hashlib,json,pathlib,sys
c=json.load(sys.stdin)
for b in c['bindings']:
 assert hashlib.sha256(pathlib.Path(b['path']).read_bytes()).hexdigest()==b['sha256'],'ledger input changed'
sys.path.insert(0,c['directory'])
from anchor_panel import inventory
m=json.loads(pathlib.Path(c['manifest']).read_text())
s=inventory(m,pathlib.Path(c['train_ids']).read_text().splitlines(),c['root'])
print(json.dumps({'declared':s['declared'],'completed':len(s['completed']),'pending':len(s['pending']),'exhausted':len(s['exhausted']),'started_cells':len(s['completed'])+len(s['exhausted'])+sum(a==2 for _,_,a in s['pending'])}))
'''
    payload={'bindings':bindings,'directory':directory,'manifest':runtime['manifest'],
             'train_ids':runtime['train_ids'],'root':runtime['generation_root']}
    result=command(route['host'],[runtime['python'],'-c',script],input=json.dumps(payload),
                   capture_output=True,text=True,check=True,timeout=180)
    return json.loads(result.stdout)


def install_segment(route,lease,runtime,config_path,lease_path):
    script='''import json,pathlib,sys
p=json.load(sys.stdin)
sys.path.insert(0,p['directory'])
from anchor_storage import write_new
for name,value in [('lease',p['lease']),('config',p['config'])]:
 write_new(p[name+'_path'],value)
'''
    payload={'lease':lease,'config':runtime,'lease_path':lease_path,'config_path':config_path,
             'directory':str(Path(route['supervisor_script']).parent)}
    command(route['host'],['python3','-c',script],input=json.dumps(payload),capture_output=True,
            text=True,check=True,timeout=30)


def dispatch(plan_path):
    plan=json.loads(Path(plan_path).read_text());root=Path(plan['state_root']);mkdir(root)
    with (root/'dispatch.lock').open('a') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'ALREADY_SUPERVISED'}
        config=published(plan)
        state=json.loads((root/'state.json').read_text()) if (root/'state.json').exists() else {
            'status':'READY','batch':config['batch'],'next_segment':0,'host':None,'condition':'v2-S2'}
        if state['status'] in ('COMPLETE','INCOMPLETE','HALTED_INFRA','CLEANUP_REQUIRED','RESOURCE_EXHAUSTED'):
            return state
        if state['status']=='RUNNING' or (root/f"segment_{state['next_segment']:05d}").exists():
            return {**state,'status':'RECOVERY_REQUIRED','reason':'adopt prior work and reconcile its lease before resuming'}
        subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'watchdog_e13v2.py'),
            '--root',plan['watchdog_root'],'--run',plan['watchdog_run'],
            'register','--role','anchor-'+config['batch'],'--pid',str(os.getpid())],check=True)
        while True:
            routes=[r for r in config['routes'] if state['host'] in (None,r['host'])]
            if not routes:raise ValueError('selected anchor host disappeared from the frozen routes')
            unspent,unreserved=remaining_seconds(plan['lease_root'])
            if unspent<1200:
                state.update(status='RESOURCE_EXHAUSTED',unspent_seconds=unspent)
                atomic_json(root/'state.json',state);return state
            if unreserved<1200:
                state.update(status='WAIT_FOR_BUDGET_SLOT',unspent_seconds=unspent,unreserved_seconds=unreserved)
                atomic_json(root/'state.json',state);return state
            allocation_seconds=min(config['maximum_seconds'],unreserved)
            reasons=[];selected=None
            # A lost coordinator-state file must not permit generation on a fresh
            # host while completed/attempted cells survive on another route.
            ledgers=[]
            for route in routes:
                try:
                    ledgers.append((route,remote_inventory(route)))
                except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as exc:
                    if isinstance(exc,subprocess.CalledProcessError) and exc.returncode!=255:
                        raise
                    reasons.append({'host':route['host'],'reason':'ledger host temporarily unavailable'})
            if state['host'] is None:
                surviving=[(r,s) for r,s in ledgers if s.get('started_cells',s['completed']+s['exhausted'])>0]
                if len(surviving)>1:
                    raise RuntimeError('multiple surviving anchor ledgers require reconciliation')
                if surviving:
                    ledgers=surviving;state['host']=surviving[0][0]['host']
                    atomic_json(root/'state.json',state)
                elif len(ledgers)!=len(routes):
                    state.update(status='WAIT_FOR_HOST',candidate_rejections=reasons)
                    atomic_json(root/'state.json',state);return state
            for route,prior in ledgers:
                if prior['completed']==prior['declared'] or prior['pending']==0:
                    state.update(status='COMPLETE' if prior['completed']==prior['declared'] else 'INCOMPLETE',
                                 host=route['host'],progress=prior)
                    atomic_json(root/'state.json',state);return state
                inventory=observe(route['host'])
                if not inventory['inventory_complete']:continue
                for index in inventory['idle_device_indices']:
                    try:
                        lease=claim(plan['lease_root'],inventory,index,sources=config['foreign_registries'],
                            reservation_bindings=config['reservation_bindings'],batch=config['batch'],
                            seconds=allocation_seconds,reservation_inventory=config.get('reservation_inventory'))
                    except RuntimeError as exc:
                        reasons.append({'host':route['host'],'index':index,'reason':str(exc)});continue
                    fresh=observe(route['host'])
                    if (not fresh['inventory_complete'] or index not in fresh['idle_device_indices']
                            or not any(d['index']==index and d['uuid']==lease['uuid'] for d in fresh['devices'])):
                        release(plan['lease_root'],lease['id'],cleanup_verified=True);continue
                    selected=(route,lease,prior);break
                if selected:break
            if not selected:
                state.update(status='WAIT_FOR_IDLE_DEVICE',
                             candidate_rejections=reasons)
                atomic_json(root/'state.json',state);return state
            route,lease,prior=selected;segment=state['next_segment']
            launched=False
            try:
                local=root/f'segment_{segment:05d}'
                if local.exists():raise FileExistsError('anchor segment already has receipts')
                mkdir(local)
                runtime=dict(route['runtime']);segment_root=Path(runtime['panel_root'])/'segments'/f'{segment:05d}'
                config_path=str(segment_root/'runtime.json');lease_path=str(segment_root/'lease.json')
                runtime.update(attempt_root=str(segment_root),lease_path=lease_path,segment_id=segment,
                               maximum_seconds=allocation_seconds,maximum_cells=config['maximum_cells'])
                state.update(status='RUNNING',host=route['host'],lease_id=lease['id'],segment_id=segment)
                atomic_json(root/'state.json',state)
                install_segment(route,lease,runtime,config_path,lease_path)
                write_new(local/'launch.json',{'lease_id':lease['id'],'host':route['host'],'uuid':lease['uuid'],
                    'segment_id':segment,'published_revision':plan['published_revision'],'progress_before':prior,
                    'config_path':config_path,'lease_path':lease_path})
                argv=['env','E13_EXECUTION_ID='+lease['id'],*[k+'='+val for k,val in route['environment'].items()],
                    runtime['python'],str(Path(route['supervisor_script']).with_name('device_binding.py')),
                    '--lease',lease_path,'--purpose','anchors','--',runtime['python'],route['supervisor_script'],
                    '--config',config_path]
                with (local/'execution.log').open('x') as log:
                    launched=True
                    child=command(route['host'],argv,stdout=log,stderr=subprocess.STDOUT,
                                  timeout=allocation_seconds+180,check=False)
                fetched=command(route['host'],['python3','-c',
                    'import pathlib,sys;print(pathlib.Path(sys.argv[1]).read_text())',str(segment_root/'result.json')],
                    capture_output=True,text=True,check=True,timeout=30)
                result=json.loads(fetched.stdout);result['supervisor_exit_code']=child.returncode
                if child.returncode and result['status'] not in ('INCOMPLETE_INFRA','CLEANUP_REQUIRED'):
                    result['status']='INCOMPLETE_INFRA'
                clean=bool(result.get('cleanup_verified'))
                if clean:retire_remote_lease(route['host'],lease_path,lease['id'])
                release(plan['lease_root'],lease['id'],cleanup_verified=clean)
                write_new(local/'result.json',result)
                state.update(next_segment=segment+1,last_result=result,lease_id=None)
                if not clean:state['status']='CLEANUP_REQUIRED'
                elif result['status']=='INCOMPLETE_INFRA':state['status']='HALTED_INFRA'
                elif result['status'] in ('COMPLETE','INCOMPLETE'):state['status']=result['status']
                elif result.get('completed',0)<=prior['completed']:
                    state.update(status='HALTED_INFRA',reason='segment made no completed-cell progress')
                else:state['status']='READY'
                atomic_json(root/'state.json',state)
                if state['status']!='READY':return state
            except BaseException:
                release(plan['lease_root'],lease['id'],cleanup_verified=not launched)
                state.update(status='CLEANUP_REQUIRED' if launched else 'HALTED_INFRA',reason='unknown execution exit; reconcile before any new lease')
                atomic_json(root/'state.json',state);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,required=True)
    print(json.dumps(dispatch(parser.parse_args().plan),sort_keys=True))
