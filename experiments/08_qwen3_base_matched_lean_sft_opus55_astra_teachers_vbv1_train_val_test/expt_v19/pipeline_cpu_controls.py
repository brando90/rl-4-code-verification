"""Exercise only ordinary-code waiting/failure/death routing using disposable CPU subprocesses."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent

def child(mode):
    import chain_gx10 as c
    from common import ROOT,REPO,write
    REPO.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='')
    if mode=='missing':c.wait_ready(ROOT/'transfer_completion_never.json')
    elif mode=='failure':
        try:c.stage('controlled_failure',[sys.executable,'-c','raise SystemExit(7)'],env,5)
        except RuntimeError:
            assert json.loads((ROOT/'execution'/c.LABEL/'controlled_failure.json').read_text())['status']=='FAILED';print('PASS');return
        raise AssertionError('Expected nonzero stage failure')
    elif mode=='death':
        folder=ROOT/'execution'/c.LABEL;folder.mkdir(parents=True);write(folder/'training.json',dict(status='RUNNING',pid=999999999,start_ticks='0',boot_id='dead'))
        write(ROOT/'conditions/final/run/first_update.json',dict(status='PASS'))
        try:c.stage('training',[sys.executable,'-c','raise SystemExit(99)'],env,5)
        except RuntimeError as e:assert 'interrupted optimizer' in str(e);print('PASS');return
        raise AssertionError('Interrupted training must not reset optimizer')
    elif mode.startswith('phase_'):
        import coordinate_gpu_phase as phase
        from types import SimpleNamespace
        phase.LOCAL=ROOT/'phase';events=[];snap={};gx={};calls=0
        if mode=='phase_snap':snap['selection_ready.json']={'state':'READY'}
        else:gx.update({'transfer_completion_initial.json':{'state':'READY'},'code/port_ready.json':{'state':'READY'}})
        def get(host,names):
            nonlocal calls
            calls+=1;assert calls<100
            if host=='GX10' and 'gx10_smoke_grant.json' in gx:
                gx['gx10_gpu_phase_complete.json']={'state':'COMPLETE'}
                snap['selection_ready.json']={'state':'READY'}
            if 'snap_phase_grant.json' in snap:snap['production_host.json']={'state':'FROZEN','host':'SNAP'}
            return dict(snap if host=='SNAP' else gx)
        def put(host,name,value):
            if host=='SNAP' and mode=='phase_gx':assert 'gx10_gpu_phase_complete.json' in gx
            (snap if host=='SNAP' else gx)[name]=value;events.append((host,name))
        phase.get=get;phase.put=put;phase.ssh=lambda host:['mock'];phase.time=SimpleNamespace(time=time.time,sleep=lambda seconds:None);phase.main()
        assert json.loads((phase.LOCAL/'state.json').read_text())['state']=='COMPLETE'
        assert events==([('SNAP','snap_phase_grant.json')] if mode=='phase_snap' else [('GX10','gx10_smoke_grant.json'),('SNAP','snap_phase_grant.json')]);print('PASS')
    elif mode=='complete':
        folder=ROOT/'execution'/c.LABEL;folder.mkdir(parents=True);write(folder/'training.json',dict(status='RUNNING',pid=999999999,start_ticks='0',boot_id='dead'))
        write(ROOT/'conditions/final/run/result.json',dict(status='COMPLETE'));assert c.stage('training',[sys.executable,'-c','raise SystemExit(99)'],env,5)['status']=='DONE';print('PASS')

def main():
    if len(sys.argv)>1:child(sys.argv[1]);return
    records=[]
    with tempfile.TemporaryDirectory(prefix='v19-controls-') as temporary:
        for mode in ['missing','failure','death','complete','phase_snap','phase_gx']:
            root=Path(temporary)/mode;env=dict(os.environ,GX19_ROOT=str(root),GX19_REPO=str(root/'repo'),PYTHONPATH=str(HERE),CUDA_VISIBLE_DEVICES='')
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),mode],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            if mode=='missing':
                deadline=time.time()+5
                while time.time()<deadline and not (root/'chain_progress.json').exists():time.sleep(.05)
                assert process.poll() is None and json.loads((root/'chain_progress.json').read_text())['state']=='WAITING_FOR_TRANSFER_COMPLETION_NEVER'
                process.terminate();process.communicate(timeout=5)
            else:
                out,err=process.communicate(timeout=10);assert process.returncode==0,(mode,out,err)
            records.append(dict(name=mode,status='PASS'))
    files=['assemble_final_data.py','prepare_final_transfer.py','chain_gx10.py','watch_chain.py','train_snap.py','select_and_run.py','summarize_snap.py','arm_final_selector.py','inference_controls.py','coordinate_gpu_phase.py','watch_selector.py','pipeline_cpu_controls.py']
    for name in files:compile((HERE/name).read_bytes(),str(HERE/name),'exec')
    result=dict(status='PASS',controls=records,parsed_sources=files,source_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in files},hosted_model_calls=0,gpu_operations=0,ssh_operations=0,full_model_control_passed=False,observed_unix=time.time())
    output=HERE/'results/pipeline_cpu_controls.json';output.parent.mkdir(exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
