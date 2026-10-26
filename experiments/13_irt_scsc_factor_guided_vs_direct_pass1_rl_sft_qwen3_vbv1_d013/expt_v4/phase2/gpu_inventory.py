"""TLDR: Record read-only GPU devices, owners and process ancestry without accessing credentials."""
import argparse
import datetime
import json
import os
from pathlib import Path
import pwd
import shlex
import socket
import subprocess
from common import write_new


def local_snapshot():
    def query(fields,kind):
        return subprocess.check_output(['/usr/bin/nvidia-smi',f'--query-{kind}={fields}','--format=csv,noheader,nounits'],
                                       text=True,timeout=15)
    mapping={uuid.strip():int(idx) for idx,uuid in (line.split(',') for line in query('index,uuid','gpu').splitlines())}
    processes=[]
    for line in query('gpu_uuid,pid,process_name','compute-apps').splitlines():
        uuid,pid,name=(x.strip() for x in line.split(',',2));pid=int(pid)
        row={'device':mapping[uuid],'uuid':uuid,'pid':pid,'process':name}
        try:
            owner=pwd.getpwuid(Path('/proc',str(pid)).stat().st_uid).pw_name;row['owner']=owner
            # Only paths and script names, never environment variables or arbitrary arguments.
            if owner==pwd.getpwuid(os.getuid()).pw_name:
                ancestry=[];parent=pid
                for _ in range(12):
                    proc=Path('/proc',str(parent))
                    args=proc.joinpath('cmdline').read_bytes().decode(errors='replace').split('\0')
                    scripts=[s for s in args if s.endswith('.py') and not s.startswith('-')]
                    ancestry.append({'pid':parent,'cwd':str(proc.joinpath('cwd').resolve()),'scripts':scripts})
                    status=proc.joinpath('status').read_text();parent=int(next(s.split(':',1)[1] for s in status.splitlines() if s.startswith('PPid:')))
                    if parent<=1:break
                row['owned_ancestry']=ancestry
        except OSError as e:row['identity_error']=type(e).__name__
        processes.append(row)
    return {'host':socket.gethostname().split('.')[0],'processes':processes,
            'idle_devices':sorted(set(mapping.values())-{p['device'] for p in processes})}


def collect(hosts,output):
    rows=[]
    here=socket.gethostname().split('.')[0]
    for host in hosts:
        try:
            if host==here:value=local_snapshot()
            else:
                # Send this self-contained read-only function; remote hosts need no checkout or install.
                import inspect
                source='import subprocess, pathlib, socket, os, pwd, json\nfrom pathlib import Path\n'+inspect.getsource(local_snapshot)+'\nprint(json.dumps(local_snapshot()))\n'
                command='python3 -c '+shlex.quote(source)
                result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',host,command],capture_output=True,text=True,timeout=30)
                if result.returncode:raise RuntimeError('remote census failed: '+result.stderr[:150])
                value=json.loads(result.stdout)
            rows.append(value)
        except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as e:rows.append({'host':host,'status':'UNRESOLVED','error':str(e)})
    result={'tldr':'Read-only GPU census; no device was allocated or signalled.',
            'observed_at':datetime.datetime.now().astimezone().isoformat(),'hosts':rows}
    write_new(output,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--hosts',nargs='+',default=['skampere1','skampere2','skampere3']);a=p.parse_args()
    print(json.dumps(collect(a.hosts,a.output),sort_keys=True))
