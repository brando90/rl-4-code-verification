#!/usr/bin/env python3
"""Observe device availability; this poller never claims a device or starts a model.

A candidate still needs current foreign-lease/reservation checks and an E13 lease
at launch. Keeping polling separate prevents an unfinished LP-1 lock from running.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import fcntl
import io
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import tempfile

HOSTS = ('skampere1', 'skampere2', 'skampere3', 'mercury1', 'mercury2')

# Only hardware/process metadata is returned. No process arguments or environment.
REMOTE = r'''
import datetime,json,os,pathlib,pwd,socket,subprocess
out={'host':socket.gethostname().split('.')[0],'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
for key,args in [('devices',['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits']),('processes',['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits'])]:
 r=subprocess.run(args,capture_output=True,text=True,timeout=30)
 if r.returncode: raise RuntimeError(key+' query failed: '+str(r.returncode))
 out[key]=r.stdout
owners={}
for row in out['processes'].splitlines():
 pid=int(row.split(',')[1]); owners[str(pid)]=pwd.getpwuid(pathlib.Path('/proc/'+str(pid)).stat().st_uid).pw_name
out['process_owners']=owners
p='/lfs/'+out['host']+'/0'; v=os.statvfs(p)
out['local_storage']={'path':p,'available_bytes':v.f_bavail*v.f_frsize,'total_bytes':v.f_blocks*v.f_frsize}
print(json.dumps(out))
'''


def classify(raw: dict) -> dict:
    """Reject incomplete inventory, then identify idle hardware (not a lease)."""
    devices = {}
    indices = set()
    for row in csv.reader(io.StringIO(raw['devices'])):
        if not row:
            continue
        if len(row) != 6:
            raise ValueError('malformed device row')
        index, uuid, name, total, used, utilization = [x.strip() for x in row]
        index = int(index)
        if index in indices or uuid in devices or not uuid.startswith('GPU-'):
            raise ValueError('duplicate or invalid device identity')
        memory, used_memory, util = float(total), float(used), float(utilization)
        if not (memory > 0 and 0 <= used_memory <= memory and 0 <= util <= 100):
            raise ValueError('invalid device counters')
        indices.add(index)
        devices[uuid] = {'index': index, 'uuid': uuid, 'name': name,
                         'memory_mib': memory, 'used_memory_mib': used_memory,
                         'utilization': util, 'processes': []}
    if not devices:
        raise ValueError('empty device inventory')
    for row in csv.reader(io.StringIO(raw['processes'])):
        if not row:
            continue
        if len(row) != 3:
            raise ValueError('malformed process row')
        uuid, pid, _ = [x.strip() for x in row]
        if uuid not in devices or not pid.isdigit() or int(pid) <= 0:
            raise ValueError('unknown process device or identifier')
        owner = raw['process_owners'].get(pid)
        if not owner or len(owner.split()) != 1:
            raise ValueError('unresolved process owner')
        devices[uuid]['processes'].append({'pid': int(pid), 'owner': owner})
    storage = raw['local_storage']
    total, available = storage['total_bytes'], storage['available_bytes']
    if not (0 <= available <= total and total > 0):
        raise ValueError('invalid storage counters')
    # PLAN's default route: local storage with normal host headroom. A different
    # bounded storage route needs its own declared, checked execution manifest.
    headroom = available / total >= .05
    idle = [v['index'] for v in devices.values()
            if not v['processes'] and v['utilization'] == 0 and v['used_memory_mib'] < 1024]
    return {'host': raw['host'], 'checked_utc': raw['checked_utc'],
            'inventory_complete': True, 'devices': list(devices.values()),
            'local_storage': storage, 'default_storage_headroom': headroom,
            'idle_device_indices': sorted(idle),
            'candidate_indices_pending_lease_checks': sorted(idle) if headroom else [],
            'device_claims': 0}


def observe(host: str) -> dict:
    if host not in HOSTS:
        raise ValueError('unregistered host')
    local = socket.gethostname().split('.')[0] == host
    args = (['python3', '-c', REMOTE] if local else
            ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', host,
             'python3 -c ' + shlex.quote(REMOTE)])
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=85)
        if result.returncode:
            raise RuntimeError('inventory command exit ' + str(result.returncode))
        raw = json.loads(result.stdout)
        if raw['host'] != host:
            raise ValueError('host identity mismatch')
        return classify(raw)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return {'host': host, 'inventory_complete': False,
                'error': str(exc), 'candidate_indices_pending_lease_checks': [], 'device_claims': 0}


def poll(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'poll.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(HOSTS)) as pool:
            nodes = dict(zip(HOSTS, pool.map(observe, HOSTS)))
        receipt = {'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                   'status': 'OBSERVATION_ONLY', 'nodes': nodes, 'device_claims': 0,
                   'model_calls': 0, 'automatic_launch_enabled': False}
        encoded = json.dumps(receipt, indent=2) + '\n'
        # Keep every observation; a reboot or next cron invocation cannot erase it.
        with tempfile.NamedTemporaryFile(mode='w', prefix='poll_', suffix='.json',
                                         dir=root, delete=False) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        temporary = root / 'latest.tmp'
        temporary.write_text(encoded)
        temporary.replace(root / 'latest.json')
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    receipt = poll(args.root)
    print(json.dumps({'checked_utc': receipt['checked_utc'],
                      'candidates': {h: r['candidate_indices_pending_lease_checks']
                                     for h, r in receipt['nodes'].items()},
                      'device_claims': 0, 'automatic_launch_enabled': False}))


if __name__ == '__main__':
    main()
