"""Finish the sole GX10 artifact handoff after existing SNAP authentication returns.

No fresh SNAP login, provider call, host choice or optimizer is performed here.
The initial deployment watcher remains the sole initial-weight writer.
"""
import base64
import fcntl
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
from arm_gx10_deploy import CONTROL,LOCAL,REMOTE,GX,SSH,write

HERE=Path(__file__).resolve().parent
GXSSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','cactushacks-gx10']
RUN='/lfs/skampere1/0/eth127/rl4cv_tiny_training'

def remote(command):return subprocess.run(SSH+[command],capture_output=True,text=True,timeout=120,check=True)
def read_remote(path):
    code='import pathlib,sys; p=pathlib.Path('+repr(path)+'); sys.stdout.write(p.read_text() if p.is_file() else "null")'
    return json.loads(remote('python3 -c '+shlex.quote(code)).stdout)
def put_small(files,receipt_name=None,receipt=None):
    """SHA-check each ordinary fixed destination before atomic publication."""
    payload={'root':GX,'files':[dict(path=name,data=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()) for name,raw in files.items()],
             'receipt_name':receipt_name,'receipt':receipt}
    code='''import base64,hashlib,json,pathlib,py_compile,sys
p=json.load(sys.stdin); root=pathlib.Path(p['root'])
for f in p['files']:
 r=pathlib.PurePosixPath(f['path']); assert not r.is_absolute() and '..' not in r.parts
 target=root/f['path']; target.parent.mkdir(parents=True,exist_ok=True); assert not target.is_symlink()
 data=base64.b64decode(f['data']); assert hashlib.sha256(data).hexdigest()==f['sha256']
 if target.exists():assert target.read_bytes()==data, 'Preserve existing different handoff: '+str(target)
 else:
  temp=target.with_name(target.name+'.handoff-partial');temp.write_bytes(data);temp.replace(target)
 assert hashlib.sha256(target.read_bytes()).hexdigest()==f['sha256']
 if target.suffix=='.py':py_compile.compile(str(target),doraise=True)
if p['receipt_name']:
 target=root/p['receipt_name']; raw=(json.dumps(p['receipt'],indent=2,sort_keys=True)+'\\n').encode()
 if target.exists():
  old=json.loads(target.read_bytes()); new=dict(p['receipt']); old.pop('observed_unix',None);new.pop('observed_unix',None);assert old==new
 else:
  temp=target.with_suffix('.tmp');temp.write_bytes(raw);temp.replace(target)
print(json.dumps({'state':'HASH_CHECKED','files':len(p['files'])}))
'''
    subprocess.run(GXSSH+['python3 -c '+shlex.quote(code)],input=json.dumps(payload),text=True,capture_output=True,timeout=120,check=True)

def port():
    done=read_remote(REMOTE+'/astra/completion.json')
    if done is None:return False
    assert done.get('model')=='gpt-6-astra' and done.get('effort')=='high',done
    assert done.get('returncode')==0 and done.get('state')=='EXITED',done
    code='import pathlib,json,base64; r=pathlib.Path('+repr(REMOTE+'/astra/work')+'); print(json.dumps({n:base64.b64encode((r/n).read_bytes()).decode() for n in ("train_gx10.py","PORT_NOTES.md")}))'
    data=json.loads(remote('python3 -c '+shlex.quote(code)).stdout)
    files={'code/'+name:base64.b64decode(value) for name,value in data.items()}
    # This is a transport/syntax receipt. The separate full-model smoke is mandatory.
    ready=dict(state='READY_FOR_SMOKE',train_wrapper_sha256=hashlib.sha256(files['code/train_gx10.py']).hexdigest(),
        port_notes_sha256=hashlib.sha256(files['code/PORT_NOTES.md']).hexdigest(),model='gpt-6-astra',effort='high',
        astra_completion_canonical_json_sha256=hashlib.sha256(json.dumps(done,sort_keys=True).encode()).hexdigest(),
        python='/home/lethan3/workspace/rl4cv-gx10/training-v14/.venv/bin/python',
        frozen_source_dir=GX+'/code/expt_v12_frozen',mandatory_disposable_full_model_smoke=True,
        optimizer_launched_by_transport=False,observed_unix=time.time())
    put_small(files,'code/port_ready.json',ready)
    for name,raw in files.items():
        path=LOCAL/'astra_outputs'/Path(name).name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    write(LOCAL/'port_ready.json',ready);return True

def bundle(identity):
    builder={'evaluation':'prepare_eval_transfer.py','final':'prepare_final_transfer.py'}[identity]
    if identity=='final':
        completion=read_remote(RUN+'/lean_corpus_v18/completion.json')
        if completion is None:return False
        assert completion.get('state') in ('DONE','DONE_WITH_EXCLUSIONS'),completion
    subprocess.run(['scp','-q','-o','ControlPath='+str(CONTROL),'-o','ProxyCommand=/usr/bin/false','-o','BatchMode=yes',str(HERE/builder),'eth127@skampere1.stanford.edu:'+REMOTE+'/'],check=True,timeout=60)
    output=REMOTE+('/transfer_evaluation.json' if identity=='evaluation' else '/transfer_final.json')
    result=remote('python3 '+shlex.quote(REMOTE+'/'+builder)+' --output '+shlex.quote(output))
    (LOCAL/(identity+'_prepare.log')).write_text(result.stdout+result.stderr)
    subprocess.run([sys.executable,str(HERE/'relay_artifacts.py'),'--identity',identity],check=True)
    return True

def host_decision():
    path=RUN+'/corpus_training_v19/production_host.json';decision=read_remote(path)
    if decision is None:return False
    assert decision.get('state')=='FROZEN' and decision.get('host') in ('SNAP','GX10')
    # Copy exact source bytes; no new decision or pretty-printing of the artifact.
    encoded=remote('python3 -c '+shlex.quote('import base64,pathlib;print(base64.b64encode(pathlib.Path('+repr(path)+').read_bytes()).decode())')).stdout.strip()
    raw=base64.b64decode(encoded);assert json.loads(raw)==decision
    put_small({'production_host.json':raw})
    write(LOCAL/'production_host_transfer.json',dict(state='HASH_CHECKED',sha256=hashlib.sha256(raw).hexdigest(),host=decision['host'],observed_unix=time.time()))
    return True

def main():
    LOCAL.mkdir(parents=True,exist_ok=True)
    lock=(LOCAL/'finish.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    status=LOCAL/'finish_progress.json';state=json.loads(status.read_text()) if status.exists() else {}
    done=set(state.get('completed',[]))
    actions={'port':port,'evaluation':lambda:bundle('evaluation'),'final':lambda:bundle('final'),'host_decision':host_decision}
    while len(done)<len(actions):
        authenticated=False
        if CONTROL.exists() and (LOCAL/'deploy_launched.json').exists():
            authenticated=subprocess.run(['ssh','-S',str(CONTROL),'-O','check','eth127@skampere1.stanford.edu'],capture_output=True,timeout=5).returncode==0
        if authenticated:
            for name,action in actions.items():
                if name in done:continue
                try:
                    if action():
                        done.add(name)
                        write(status,dict(state='HANDOFF_PROGRESS',completed=sorted(done),observed_unix=time.time(),fresh_network_login_attempts=0))
                except subprocess.CalledProcessError as exc:
                    write(LOCAL/'finish_last_error.json',dict(stage=name,error=str(exc),observed_unix=time.time(),fresh_login_attempts=0))
                    # Preserve immutable receipts and never automatically repeat an Astra call.
                    raise
        write(status,dict(state='COMPLETE' if len(done)==len(actions) else 'WAITING_FOR_HANDOFF',completed=sorted(done),
            authenticated_existing_socket=authenticated,observed_unix=time.time(),fresh_network_login_attempts=0))
        if len(done)<len(actions):time.sleep(15)

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        write(LOCAL/'finish_failure.json',dict(error=repr(exc),observed_unix=time.time()));raise
