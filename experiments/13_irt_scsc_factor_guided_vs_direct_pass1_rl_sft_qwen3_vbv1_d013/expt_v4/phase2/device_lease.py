"""TLDR: Hold a v4 device lock for a bounded stage after the idle-device guard admits it."""
from contextlib import contextmanager, ExitStack
import fcntl
import os
from pathlib import Path
import socket
import time
from common import write_new
from device_guard import census, ensure_idle, eligible, Busy, v3_reservations, V3_WORK, MINIMUM_IDLE_SECONDS


def shared_locks(held,work,host,index,v3_work):
    """Take mutual locks while opening existing v3 files strictly read-only."""
    paths=[(work/f'gpu_{host}_{index}.lock','a')]
    if host=='skampere1':paths.append((v3_work/f'gpu_{index}.lock','r'))
    records=[]
    for path,mode in paths:
        stream=held.enter_context(path.open(mode))
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        info=os.fstat(stream.fileno())
        records.append({'path':str(path),'fd':stream.fileno(),'device':info.st_dev,'inode':info.st_ino})
    return records


def observation(host,index,probe,v3_work,clock,*,uuid=None):
    """A complete observation includes fresh device mapping, compute census and v3 leases."""
    devices,apps=probe()
    reservations=v3_reservations(v3_work) if host=='skampere1' else []
    found=ensure_idle(host,index,devices,apps,reservations=reservations)
    if uuid is not None and found!=uuid:raise Busy('physical device changed during idle observation')
    return {'monotonic':clock(),'observed_unix':time.time(),'uuid':found,
            'compute_processes':0,'active_reservations':0}


def pilot_capacity(work,*,probe=census,host=None,v3_work=None):
    """Require three idle devices under shared locks, releasing every probe lock on return."""
    host=host or socket.gethostname().split('.')[0]
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    v3_work=Path(V3_WORK if v3_work is None else v3_work).resolve()
    with ExitStack() as held:
        devices,apps=probe();selected=[]
        for index in sorted(devices):
            if not eligible(host,index):continue
            with ExitStack() as candidate:
                try:
                    shared_locks(candidate,work,host,index,v3_work)
                    ensure_idle(host,index,devices,apps)
                except (OSError,Busy):continue
                held.enter_context(candidate.pop_all());selected.append(index)
            if len(selected)==3:break
        if len(selected)<3:raise Busy('pilot requires 3 idle authorized GPUs with all shared locks free')
        devices,apps=probe()
        reservations=v3_reservations(v3_work) if host=='skampere1' else []
        for index in selected:ensure_idle(host,index,devices,apps,reservations=reservations)
        return {'required':3,'host':host,'idle_authorized_devices':selected,'standing_reservation':False}


@contextmanager
def allocation(work, admission_check, *, probe=census, host=None, duration_seconds=4*3600,
               v3_work=None, clock=time.monotonic, sleep=time.sleep):
    admission_check()  # Always before census, lock, environment change, or lease.
    host=host or socket.gethostname().split('.')[0]
    work=Path(work).resolve();work.mkdir(parents=True,exist_ok=True)
    v3_work=Path(V3_WORK if v3_work is None else v3_work).resolve()
    devices,apps=probe()
    for index in sorted(devices):
        if not eligible(host,index):continue
        with ExitStack() as held:
            try:
                locks=shared_locks(held,work,host,index,v3_work)
                first=observation(host,index,probe,v3_work,clock)
                sleep(MINIMUM_IDLE_SECONDS)
                second=observation(host,index,probe,v3_work,clock,uuid=first['uuid'])
                if second['monotonic']-first['monotonic']<MINIMUM_IDLE_SECONDS:
                    raise Busy('idle observation interval shorter than 60 seconds')
            except (OSError,Busy):continue
            admission_check()  # Admission must still hold after the idle wait.
            identity=f'e13v4-{os.getpid()}-{time.time_ns()}'
            path=work/(identity+'.lease.json');started=time.time()
            lease={'id':identity,'owner':'e13v4','status':'ACTIVE','host':host,'index':index,'uuid':second['uuid'],
                   'started_unix':started,'expires_unix':started+duration_seconds,
                   'idle_observations':[first,second],'lease_work':str(work),'shared_locks':locks,
                   'lock_owner_pid':os.getpid(),
                   'lock_owner_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
            write_new(path,lease)
            updates={'CUDA_VISIBLE_DEVICES':str(index),'CUDA_DEVICE_ORDER':'PCI_BUS_ID',
                     'E13V4_EXECUTION_ID':identity,'HF_HUB_OFFLINE':'1'}
            original={k:os.environ.get(k) for k in updates};os.environ.update(updates)
            try:yield path
            finally:
                write_new(path.with_suffix('.end.json'),{'id':identity,'status':'RELEASED','ended_unix':time.time(),
                          'device_hours':(time.time()-started)/3600})
                for k,v in original.items():
                    if v is None:os.environ.pop(k,None)
                    else:os.environ[k]=v
            return
    raise Busy('no authorized GPU passed two idle observations at least 60 seconds apart; no allocation made')
