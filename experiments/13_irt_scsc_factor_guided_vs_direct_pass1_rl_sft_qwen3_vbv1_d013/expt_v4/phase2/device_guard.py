"""TLDR: Admit only unoccupied authorized GPUs and fail closed on census or ownership errors."""
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import time

V3_WORK=Path('/lfs/skampere1/0/brando9/rl4cv_e13v3')
MINIMUM_IDLE_SECONDS=60


class Busy(RuntimeError):
    """The device is occupied, reserved, or cannot be safely inspected."""


def eligible(host,index):
    return (host=='skampere1' and index in (0,5,7)) or (host in ('skampere2','skampere3') and type(index) is int and index>=0)


def census(run=subprocess.run):
    def query(fields,kind):
        result=run(['/usr/bin/nvidia-smi',f'--query-{kind}={fields}','--format=csv,noheader,nounits'],
                   capture_output=True,text=True,timeout=15)
        if result.returncode!=0:raise Busy('GPU census failed')
        return [line.split(',') for line in result.stdout.splitlines() if line.strip()]
    try:
        devices={}
        for row in query('index,uuid','gpu'):
            if len(row)!=2:raise Busy('malformed GPU census')
            idx,uuid=(x.strip() for x in row); idx=int(idx)
            if idx in devices or not uuid.startswith('GPU-') or uuid in devices.values():raise Busy('ambiguous GPU mapping')
            devices[idx]=uuid
        if not devices:raise Busy('empty GPU census')
        apps=[]
        for row in query('gpu_uuid,pid','compute-apps'):
            if len(row)!=2:raise Busy('malformed process census')
            uuid,pid=(x.strip() for x in row)
            if uuid not in devices.values() or not pid.isdigit():raise Busy('unknown GPU or process')
            apps.append((uuid,int(pid)))
        return devices,apps
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        raise Busy('GPU probe unavailable') from exc


def ensure_idle(host,index,devices,apps,*,reservations=(),now=None):
    now=time.time() if now is None else now
    if not eligible(host,index) or index not in devices:raise Busy('device not authorized')
    uuid=devices[index]
    if any(u==uuid for u,pid in apps):raise Busy('compute process occupies device')
    for r in reservations:
        if r.get('status')=='ACTIVE' and r.get('expires_unix',float('inf'))>now and r.get('host',host)==host and (r.get('uuid')==uuid or r.get('index')==index):
            raise Busy('active reservation holds device')
    return uuid


def read_reservations(paths):
    result=[]
    for path in paths:
        try:
            value=json.loads(Path(path).read_text())
            if not isinstance(value,dict) or 'status' not in value:raise ValueError('invalid reservation')
            if value['status']=='ACTIVE':
                if not (type(value.get('index')) is int and value['index']>=0 or
                        isinstance(value.get('uuid'),str) and value['uuid'].startswith('GPU-')):
                    raise ValueError('reservation device missing')
                if 'expires_unix' in value and (type(value['expires_unix']) not in (int,float) or
                                               not math.isfinite(value['expires_unix'])):
                    raise ValueError('invalid reservation expiry')
            result.append(value)
        except (OSError,ValueError) as exc:raise Busy('reservation probe failed') from exc
    return result


def v3_reservations(work=None, *, exclude_lease=None):
    """Inspect all unfinished v3 leases without creating or changing v3 files."""
    work=Path(V3_WORK if work is None else work)
    excluded=Path(exclude_lease).resolve() if exclude_lease is not None else None
    try:
        if not work.is_dir():raise OSError('v3 reservation root unavailable')
        def unreadable(error):raise error
        paths=[]
        for root,dirs,files in os.walk(work/'phase2',onerror=unreadable):
            for name in files:
                if not name.endswith('_lease.json'):continue
                path=Path(root)/name
                if excluded is not None and path.resolve()==excluded:continue
                if not path.with_name(path.stem+'_end.json').exists():paths.append(path)
        reservations=read_reservations(paths)
        # An unfinished v3 job can outlive its advertised lease duration. Only
        # its end receipt releases that reservation; expiry alone is no proof.
        return [{k:v for k,v in row.items() if k!='expires_unix'} if row['status']=='ACTIVE' else row
                for row in reservations]
    except (OSError,ValueError) as exc:raise Busy('v3 reservation probe failed') from exc


def verify_shared_locks(lease, *, v3_work=None):
    """Verify the allocator still holds the recorded locks, using only its own proc files."""
    try:
        pid=lease['lock_owner_pid']
        if type(pid) is not int or pid<=0:raise ValueError('invalid allocator pid')
        ticks=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]
        if ticks!=lease['lock_owner_start_ticks']:raise ValueError('allocator identity changed')
        locks=lease['shared_locks']
        expected={str(Path(lease['lease_work'])/f"gpu_{lease['host']}_{lease['index']}.lock")}
        if lease['host']=='skampere1':
            expected.add(str(Path(V3_WORK if v3_work is None else v3_work).resolve()/f"gpu_{lease['index']}.lock"))
        if {lock['path'] for lock in locks}!=expected or len(locks)!=len(expected):
            raise ValueError('shared lock set changed')
        for lock in locks:
            path=Path(lock['path']);info=path.stat()
            if (info.st_dev,info.st_ino)!=(lock['device'],lock['inode']):
                raise ValueError('shared lock file changed')
            held=Path(f"/proc/{pid}/fd/{lock['fd']}").stat()
            if (held.st_dev,held.st_ino)!=(info.st_dev,info.st_ino):
                raise ValueError('shared lock descriptor changed')
            lock_id=f'{os.major(info.st_dev):02x}:{os.minor(info.st_dev):02x}:{info.st_ino}'
            lines=Path(f"/proc/{pid}/fdinfo/{lock['fd']}").read_text().splitlines()
            if not any(line.split()[2:]==['FLOCK','ADVISORY','WRITE',str(pid),lock_id,'0','EOF']
                       for line in lines if line.startswith('lock:')):
                raise ValueError('allocator no longer holds shared lock')
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        raise Busy('shared lock ownership unavailable') from exc


def check(config, *, run=subprocess.run, read_environment=None, host=None, now=None,
          pre_engine=False, probe=None, v3_work=None):
    try:lease=json.loads(Path(config['lease_path']).read_text())
    except (OSError,ValueError) as exc:raise Busy('lease unavailable') from exc
    if Path(config['lease_path']).with_suffix('.end.json').exists():raise Busy('lease already released')
    if lease.get('kind')=='cpu':
        if (lease.get('owner')!='e13v4' or lease.get('status')!='ACTIVE' or
            time.time()>=lease.get('expires_unix',0) or os.environ.get('CUDA_VISIBLE_DEVICES')!='' or
            os.environ.get('E13V4_EXECUTION_ID')!=lease.get('id') or
            config.get('synthetic',False)!=lease.get('synthetic',False)):
            raise Busy('invalid CPU lease')
        if not config.get('synthetic') and config.get('stage') not in ('score','audit_score','export'):raise Busy('CPU lease cannot authorize a model stage')
        return lease
    host=socket.gethostname().split('.')[0] if host is None else host
    now=time.time() if now is None else now
    if (lease.get('owner')!='e13v4' or lease.get('host')!=host or lease.get('status')!='ACTIVE'
            or not eligible(host,lease.get('index')) or now>=lease.get('expires_unix',0)
            or os.environ.get('CUDA_VISIBLE_DEVICES')!=str(lease['index'])
            or os.environ.get('E13V4_EXECUTION_ID')!=lease.get('id') or os.environ.get('HF_HUB_OFFLINE')!='1'):
        raise Busy('invalid v4 lease or runtime environment')
    devices,apps=census(run) if probe is None else probe()
    if devices.get(lease['index'])!=lease.get('uuid'):raise Busy('physical device changed')
    if pre_engine:
        # Any process is disqualifying before engine creation, even our own UID.
        # Never inspect another user's /proc environment on this refusal path.
        ensure_idle(host,lease['index'],devices,apps,now=now)
        observations=lease.get('idle_observations',[])
        try:
            if (len(observations)!=2 or
                observations[1]['monotonic']-observations[0]['monotonic']<MINIMUM_IDLE_SECONDS or
                any(row['uuid']!=lease['uuid'] or row['compute_processes']!=0 or row['active_reservations']!=0
                    for row in observations)):
                raise ValueError('missing sustained-idle proof')
        except (KeyError,TypeError,ValueError) as exc:raise Busy('invalid sustained-idle observations') from exc
        verify_shared_locks(lease,v3_work=v3_work)
        reservations=v3_reservations(v3_work,exclude_lease=config['lease_path']) if host=='skampere1' else []
        ensure_idle(host,lease['index'],devices,apps,reservations=reservations,now=now)
        return lease
    read_environment=read_environment or (lambda pid:Path('/proc',str(pid),'environ').read_bytes())
    marker=('E13V4_EXECUTION_ID='+lease['id']).encode()
    for uuid,pid in apps:
        if uuid!=lease['uuid']:continue
        try:environment=read_environment(pid).split(b'\0')
        except OSError as exc:raise Busy('compute ownership unreadable') from exc
        if marker not in environment:raise Busy('foreign process occupies device')
    return lease
