"""TLDR: Score v4 train outputs with the unchanged strict oracle and retain compiler streams durably."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from common import write_new,digest


@contextmanager
def retain_commands(root):
    """Stream subprocess output before completion, including timeout/abrupt-stop evidence."""
    root=Path(root);root.mkdir(parents=True,exist_ok=True);original=subprocess.run;counter=0
    def logged(args,**kwargs):
        nonlocal counter
        if not kwargs.get('capture_output') and kwargs.get('stdout')!=subprocess.PIPE:
            return original(args,**kwargs)
        target=root/f'{counter:04d}';counter+=1;target.mkdir()
        timeout=kwargs.pop('timeout',None);check=kwargs.pop('check',False)
        kwargs.pop('capture_output',None);kwargs.pop('stdout',None);kwargs.pop('stderr',None)
        text=kwargs.pop('text',False) or kwargs.pop('universal_newlines',False)
        encoding=kwargs.pop('encoding',None) or 'utf-8';errors=kwargs.pop('errors',None) or 'strict'
        source_bindings=[]
        for i,arg in enumerate(args):
            p=Path(str(arg))
            if p.suffix=='.lean' and p.is_file():
                dest=target/f'source_{i}.lean';dest.write_bytes(p.read_bytes())
                source_bindings.append({'original':str(p),'retained':str(dest),'sha256':digest(dest)})
        write_new(target/'intent.json',{'argv':args,'cwd':str(kwargs.get('cwd','')),'sources':source_bindings,
            'started_unix':time.time(),'exit_status':'unknown until exit.json'})
        with (target/'stdout').open('wb') as out,(target/'stderr').open('wb') as err:
            kwargs.pop('start_new_session',None)
            child=subprocess.Popen(args,stdout=out,stderr=err,start_new_session=True,**kwargs)
            try:code=child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);code=child.wait()
                write_new(target/'exit.json',{'returncode':code,'timeout':True})
                raise subprocess.TimeoutExpired(args,timeout,output=(target/'stdout').read_bytes(),stderr=(target/'stderr').read_bytes())
            write_new(target/'exit.json',{'returncode':code,'timeout':False})
        stdout=(target/'stdout').read_bytes();stderr=(target/'stderr').read_bytes()
        if text:stdout=stdout.decode(encoding,errors);stderr=stderr.decode(encoding,errors)
        if check and code:raise subprocess.CalledProcessError(code,args,stdout,stderr)
        return subprocess.CompletedProcess(args,code,stdout,stderr)
    subprocess.run=logged
    try:yield
    finally:subprocess.run=original


def score_one(job):
    import legacy
    from score_training import score_one as official
    row,root,config=job;root=Path(root);root.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    try:
        with retain_commands(root/'raw_compiler'):
            value=official(row,root,config)
        result={**row,**value,'sample_idx':row['sample'],'wall_seconds':time.monotonic()-start}
    except (subprocess.TimeoutExpired,MemoryError) as exc:
        result={**row,'sample_idx':row['sample'],'strict':None,'factored_reward':None,
                'status':'deterministic_resource_limit','error_type':type(exc).__name__,'wall_seconds':time.monotonic()-start}
    except Exception as exc:
        result={**row,'sample_idx':row['sample'],'strict':None,'factored_reward':None,
                'status':'unresolved_measurement','error_type':type(exc).__name__,'error':str(exc),'wall_seconds':time.monotonic()-start}
    result['score_root']=str(root);write_new(root/'result.json',result);return result


def score(config,rows,root):
    from concurrent.futures import ProcessPoolExecutor
    from multiprocessing import get_context
    if not rows or len(rows)>1024 or len({r['cell_id'] for r in rows})!=len(rows):raise ValueError('invalid scoring inventory')
    with ProcessPoolExecutor(max_workers=8,mp_context=get_context('spawn')) as pool:
        values=list(pool.map(score_one,[(r,str(Path(root)/f'{i:05d}'),config['scoring']) for i,r in enumerate(rows)]))
    return {'rows':values,'declared':len(rows),'measured':sum(r['strict'] is not None for r in values)}
