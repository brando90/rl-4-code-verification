"""Poll for an idle device and execute the published A6 diagnostic once with retained cleanup and costs."""
import argparse,fcntl,json,os,socket,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from g1_driver import verify_publication
from panel import digest
from anchor_storage import write_new,atomic_json
from device_watch import observe
from device_binding import launch_environment
from lp1 import cleanup
from a6_lease import claim,release,verify_allocation,accounting


def authorize(plan):
    locked=verify_publication(plan['lock'],plan['repository'],plan['published_revision'])
    if locked.get('gate')!='A6_DIAGNOSTIC' or locked.get('status')!='FROZEN':raise ValueError('published diagnostic lock required')
    for b in locked['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('diagnostic binding changed: '+b['path'])
    required=[Path(__file__).resolve(),HERE/'a6_runtime.py',HERE/'a6_generation.py',HERE/'a6_lease.py']
    bound={b['path']:b['sha256']for b in locked['bindings']}
    if any(bound.get(str(p))!=digest(p)for p in required):raise ValueError('diagnostic executor not bound')
    cfg=locked['configuration'];allocation,sha=verify_allocation({'allocation':cfg['allocation'],'repository':plan['repository'],'published_revision':plan['published_revision']})
    if bound.get(cfg['allocation'])!=sha or allocation['cumulative_device_hours']!=2. or allocation['maximum_lease_seconds']!=7200:raise ValueError('diagnostic allocation changed')
    if set(allocation['routes'])!={socket.gethostname().split('.')[0]}:raise ValueError('diagnostic route is local only')
    return locked,cfg,allocation,sha


def run(plan):
    locked,cfg,allocation,allocation_sha=authorize(plan);root=Path(cfg['root']);root.mkdir(parents=True,exist_ok=True)
    with (root/'controller.lock').open('a')as fence:
        fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (root/'result.json').exists():return json.loads((root/'result.json').read_text())
        if (root/'attempt.json').exists():return {'status':'RECOVERY_REQUIRED','automatic_retry':False}
        host=next(iter(allocation['routes']));inventory=observe(host);record={'status':'WAIT_FOR_IDLE_DEVICE','inventory':inventory,'rejections':[],'device_claims':0}
        lease=None
        registry=json.loads((Path(cfg['lease_root'])/'registry.json').read_text())
        spent,reserved=accounting(registry,allocation['phase'],allocation_sha)
        seconds=min(7200,int((allocation['cumulative_device_hours']-spent-reserved)*3600))
        if seconds<=90:return {'status':'RESOURCE_EXHAUSTED','device_claims':0,'automatic_retry':False}
        if inventory['inventory_complete']:
            for index in inventory['idle_device_indices']:
                try:lease=claim(cfg['lease_root'],inventory,index,allocation=allocation,allocation_sha=allocation_sha,seconds=seconds,run_key='A6/once')
                except RuntimeError as exc:record['rejections'].append({'index':index,'reason':str(exc)});continue
                break
        if lease is None:
            atomic_json(root/'latest_poll.json',record);return {'status':'WAIT_FOR_IDLE_DEVICE','device_claims':0}
        result={'condition':'v2-S2','purpose':'A6_pipeline_diagnostic','status':'INCOMPLETE','lease_id':lease['id'],'automatic_retry':False,'lock_sha256':digest(plan['lock'])}
        try:
            fresh=observe(host)
            if not fresh['inventory_complete']or lease['index']not in fresh['idle_device_indices']or not any(d['uuid']==lease['uuid']and d['index']==lease['index']for d in fresh['devices']):
                release(cfg['lease_root'],lease['id'],cleanup_verified=True)
                atomic_json(root/'latest_poll.json',{'status':'DEVICE_CHANGED_BEFORE_LAUNCH','device_claims':1,'lease_id':lease['id']})
                return {'status':'WAIT_FOR_IDLE_DEVICE','device_claims':1}
            write_new(root/'attempt.json',{**result,'started_unix':time.time(),'published_revision':plan['published_revision'],'inventory':fresh})
            runtime={**cfg['runtime'],'lease_id':lease['id'],'lease_path':str(Path(cfg['lease_root'])/(lease['id']+'.json')),
                'generation_root':str(root/'generation')}
            configpath=root/'runtime.json';write_new(configpath,runtime)
            env=launch_environment(lease,'anchors',{**os.environ,**cfg['environment']})
            with(root/'generation.log').open('x')as log:
                child=subprocess.Popen([runtime['python'],str(HERE/'a6_runtime.py'),'--config',str(configpath)],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                write_new(root/'process.json',{'pid':child.pid,'start_ticks':Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],
                    'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'lease_id':lease['id'],'visible_index':env['CUDA_VISIBLE_DEVICES']})
                subprocess.run([sys.executable,str(HERE.parent/'watchdog_e13v2.py'),'--root',cfg['watchdog_root'],'--run',cfg['watchdog_run'],'register','--role','A6-diagnostic','--pid',str(child.pid)],check=True)
                result['worker_exit_code']=child.wait(timeout=max(1,lease['expires_unix']-time.time()-90))
            if result['worker_exit_code']==0:result['status']='GENERATION_COMPLETE'
        except BaseException as exc:result.update(error_type=type(exc).__name__,error=str(exc))
        finally:
            if (root/'attempt.json').exists():
                cleaned=cleanup(lease['id']);write_new(root/'cleanup.json',cleaned)
                retired=release(cfg['lease_root'],lease['id'],cleanup_verified=cleaned['verified'])
                result.update(cleanup_verified=cleaned['verified'],released=retired,ended_unix=time.time())
                if not cleaned['verified']:result['status']='CLEANUP_REQUIRED'
                write_new(root/'result.json',result)
            else:
                # No experiment child exists before the exclusive attempt marker.
                current=json.loads((Path(cfg['lease_root'])/(lease['id']+'.json')).read_text())
                if current['status']=='ACTIVE':release(cfg['lease_root'],lease['id'],cleanup_verified=True)
        return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(json.loads(a.plan.read_text())),sort_keys=True))
