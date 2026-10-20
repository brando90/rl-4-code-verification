"""TLDR: Admit only unoccupied authorized GPUs and fail closed on census or ownership errors."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time


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
            result.append(value)
        except (OSError,ValueError) as exc:raise Busy('reservation probe failed') from exc
    return result


def check(config, *, run=subprocess.run, read_environment=None, host=None, now=None):
    try:lease=json.loads(Path(config['lease_path']).read_text())
    except (OSError,ValueError) as exc:raise Busy('lease unavailable') from exc
    host=socket.gethostname().split('.')[0] if host is None else host
    now=time.time() if now is None else now
    if (lease.get('owner')!='e13v4' or lease.get('host')!=host or lease.get('status')!='ACTIVE'
            or not eligible(host,lease.get('index')) or now>=lease.get('expires_unix',0)
            or os.environ.get('CUDA_VISIBLE_DEVICES')!=str(lease['index'])
            or os.environ.get('E13V4_EXECUTION_ID')!=lease.get('id') or os.environ.get('HF_HUB_OFFLINE')!='1'):
        raise Busy('invalid v4 lease or runtime environment')
    devices,apps=census(run)
    if devices.get(lease['index'])!=lease.get('uuid'):raise Busy('physical device changed')
    read_environment=read_environment or (lambda pid:Path('/proc',str(pid),'environ').read_bytes())
    marker=('E13V4_EXECUTION_ID='+lease['id']).encode()
    for uuid,pid in apps:
        if uuid!=lease['uuid']:continue
        try:environment=read_environment(pid).split(b'\0')
        except OSError as exc:raise Busy('compute ownership unreadable') from exc
        if marker not in environment:raise Busy('foreign process occupies device')
    return lease
