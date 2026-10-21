"""TLDR: Hold a v4 device lock for a bounded stage after the idle-device guard admits it."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import socket
import time
from common import write_new
from device_guard import census, ensure_idle, eligible, Busy, check


@contextmanager
def allocation(work, admission_check, *, probe=census, host=None, duration_seconds=4*3600):
    admission_check()  # Always before census, lock, environment change, or lease.
    host=host or socket.gethostname().split('.')[0]
    work=Path(work);work.mkdir(parents=True,exist_ok=True)
    devices,apps=probe()
    for index in sorted(devices):
        if not eligible(host,index):continue
        stream=(work/f'gpu_{host}_{index}.lock').open('a')
        try:
            try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:continue
            devices,apps=probe()
            try:uuid=ensure_idle(host,index,devices,apps)
            except Busy:continue
            identity=f'e13v4-{os.getpid()}-{time.time_ns()}'
            path=work/(identity+'.lease.json');started=time.time()
            lease={'id':identity,'owner':'e13v4','status':'ACTIVE','host':host,'index':index,'uuid':uuid,
                   'started_unix':started,'expires_unix':started+duration_seconds}
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
        finally:
            fcntl.flock(stream,fcntl.LOCK_UN);stream.close()
    raise Busy('no authorized idle GPU; no allocation made')
