"""Wait for exact owned worker exits and removal from the device census without changing any ownership guard."""
from pathlib import Path
import subprocess
import time


def process_identity(pid):
    """Read Linux birth identity without accessing an exiting process's environment."""
    try:fields=Path('/proc',str(pid),'stat').read_text().rpartition(')')[2].split()
    except (FileNotFoundError,ProcessLookupError):return None
    return {'pid':int(pid),'start_ticks':int(fields[19]),'state':fields[0]}


def compute_pids():
    result=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],
        capture_output=True,text=True,check=True,timeout=15)
    return {int(line.strip()) for line in result.stdout.splitlines() if line.strip()}


def wait_for_workers(identities,*,query=compute_pids,identity=process_identity,
                     clock=time.monotonic,sleep=time.sleep,timeout=60):
    """Observe only; never kill a process, accept an unreadable owner, or bypass the next device guard."""
    if (not identities or len({x['pid']for x in identities})!=len(identities)
            or any(type(x['pid']) is not int or x['pid']<=0 or type(x['start_ticks']) is not int
                   or x['start_ticks']<=0 for x in identities)):
        raise ValueError('exact nonempty owned worker identities required')
    started=clock();polls=0
    while True:
        current=[identity(x['pid']) for x in identities]
        exited=all(now is None or now['start_ticks']!=old['start_ticks'] or now['state']in ('Z','X')
                   for old,now in zip(identities,current))
        visible=query();polls+=1
        if exited and not ({x['pid']for x in identities}&visible):
            return {'status':'PASS','owned_workers_exited':True,'no_owned_gpu_processes':True,
                    'workers':identities,'polls':polls,'elapsed_seconds':clock()-started}
        if clock()-started>=timeout:
            raise TimeoutError('owned worker shutdown did not clear before generator handoff')
        sleep(.25)
