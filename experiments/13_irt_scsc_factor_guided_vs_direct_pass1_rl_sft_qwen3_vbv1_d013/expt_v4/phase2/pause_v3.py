"""TLDR: Master-invoked V4-A3 clean-boundary pause; no action occurs on import or before the veto window."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from common import write_new

WORK=Path('/lfs/skampere1/0/brando9/rl4cv_e13v3')
ALLOWED=('A_1301','A_1302','B_1302','P_1301','P_1302')
from datetime import datetime
VETO_END=datetime.fromisoformat('2026-10-21T12:00:00-07:00').timestamp()


def boundary(pane,processes,leases):
    """Pure refusal test; a waiting line never overrides an active stage or lease."""
    if any(p['kind']=='stage' for p in processes):return 'WAIT_STAGE_RUNNING'
    if leases:return 'WAIT_LEASE_HELD'
    if 'waiting for an idle GPU' not in pane:return 'WAIT_BOUNDARY'
    if sum(p['kind']=='runner' for p in processes)!=1:return 'WAIT_RUNNER_IDENTITY'
    return 'READY'


def proc(pid):
    path=Path('/proc')/str(pid)
    fields=(path/'stat').read_text().rsplit(')',1)[1].split()
    boot=int(next(line.split()[1] for line in Path('/proc/stat').read_text().splitlines() if line.startswith('btime ')))
    arguments=[x.decode() for x in (path/'cmdline').read_bytes().split(b'\0') if x]
    return {'arguments':arguments,'start_unix':boot+int(fields[19])/os.sysconf('SC_CLK_TCK'),'pid':int(pid),'pgid':int(fields[2]),'ppid':int(fields[1]),'start_ticks':fields[19],
            'uid':path.stat().st_uid,'command':(path/'cmdline').read_bytes().replace(b'\0',b' ').decode()}


def is_runner(arguments,arm,seed):
    # A shell's command string is not a second runner identity.
    if len(arguments)<2 or not Path(arguments[0]).name.startswith('python'):return False
    script=Path(arguments[1]).name;rest=arguments[2:]
    if script=='resume_pilot_after_foreign_gpu.py':return rest[:3]==['retry',arm,seed]
    if script!='pilot_run.py':return False
    try:return rest[rest.index('--arm')+1]==arm and rest[rest.index('--seed')+1]==seed
    except (ValueError,IndexError):return False


def isolated_group(runner,pane_pid,members):
    if len(members)==1:return members[0]['pid']==runner['pid']
    if len(members)!=2:return False
    shell=next((m for m in members if m['pid']==pane_pid),None)
    return bool(shell and runner['ppid']==pane_pid and runner['pgid']==pane_pid and
        shell['uid']==runner['uid'] and shell['arguments'] and
        Path(shell['arguments'][0]).name in ('sh','bash','dash','zsh') and
        {m['pid'] for m in members}=={pane_pid,runner['pid']})


def snapshot(key,work=WORK):
    arm,seed=key.split('_')
    panes=subprocess.check_output(['tmux','list-panes','-a','-F','#{session_name}\t#{pane_id}\t#{pane_pid}'],text=True)
    matching=[line.split('\t') for line in panes.splitlines() if line.split('\t')[0]==f'rl4cv-e13v3-pilot-{arm}-{seed}' or line.split('\t')[0].startswith(f'rl4cv-e13v3-retry-{arm}-{seed}-u')]
    if len(matching)!=1:raise ValueError('exactly one owned trajectory pane required')
    session,pane,pane_pid=matching[0]
    text=subprocess.check_output(['tmux','capture-pane','-p','-S','-30','-t',pane],text=True)
    rows=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:
            p=proc(path.name)
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue
        if p['uid']!=os.getuid():continue
        cmd=p['command']
        if is_runner(p['arguments'],arm,seed):
            p['kind']='runner';rows.append(p)
        elif str(work/'phase2/pilot'/key)+'/' in cmd and 'pause_v3.py' not in cmd:
            p['kind']='stage';rows.append(p)
    leases=[]
    for path in (work/'phase2/pilot'/key).glob('**/*_lease.json'):
        if not path.with_name(path.stem+'_end.json').exists():leases.append(str(path))
    # Verify ancestry to the pane and entire process-group membership, not a name match alone.
    for row in rows:
        if row['kind']!='runner':continue
        ancestor=row['pid'];seen=set()
        while ancestor not in seen and ancestor>1 and ancestor!=int(pane_pid):
            seen.add(ancestor);ancestor=proc(ancestor)['ppid']
        if ancestor!=int(pane_pid):raise ValueError('runner is not in recorded pane')
        members=[]
        for path in Path('/proc').iterdir():
            if not path.name.isdigit():continue
            try:q=proc(path.name)
            except (FileNotFoundError,ProcessLookupError,PermissionError):continue
            if q['pgid']==row['pgid']:members.append(q)
        # The runner's own verified pane shell shares its process group on SNAP.
        # Every other member remains a refusal, including stage subprocesses.
        row['process_group_members']=members
        if not isolated_group(row,int(pane_pid),members):rows.append({'kind':'stage'})
    return {'completed_updates':len(list((work/'phase2/pilot'/key).glob('update_*/summary.json'))),'planned_updates':30,'trajectory':key,'pane':pane,'session':session,'pane_text':text,'processes':rows,'leases':leases}


def pause(admission,*,work=WORK,veto_not_issued=False,probe=snapshot,kill=os.killpg,now=None):
    from admission import check_admission
    now=time.time() if now is None else now
    if now<VETO_END or not veto_not_issued:raise ValueError('V4-A3 veto window/absence of veto not satisfied')
    check_admission(admission,require_launch=True)
    work=Path(work);path=work/'phase2/autoresume_paused.json'
    # Same lock as watchdog prevents a relaunch between stop and durable pause state.
    with (work/'phase2/autoresume.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads(path.read_text()) if path.exists() else {'amendment':'V4-A3','trajectories':{}}
        report={}
        for key in ALLOWED:
            if key in state['trajectories']:report[key]='ALREADY_PAUSED';continue
            snap=probe(key,work);status=boundary(snap['pane_text'],snap['processes'],snap['leases'])
            if status!='READY':report[key]=status;continue
            runner=next(p for p in snap['processes'] if p['kind']=='runner')
            if proc(runner['pid'])['start_ticks']!=runner['start_ticks']:raise ValueError('PID reused')
            # Freeze the runner to close its lease-acquisition race, then recheck.
            kill(runner['pgid'],signal.SIGSTOP)
            try:
                fresh=probe(key,work)
                if boundary(fresh['pane_text'],fresh['processes'],fresh['leases'])!='READY':
                    report[key]='WAIT_RACE';continue
                if proc(runner['pid'])['start_ticks']!=runner['start_ticks']:raise ValueError('PID reused')
                receipt={**snap,'paused_unix':time.time(),'pid':runner['pid'],
                         'start_ticks':runner['start_ticks'],'start_unix':runner['start_unix'],'pgid':runner['pgid']}
                state['trajectories'][key]=receipt
                tmp=path.with_name('.autoresume_paused.tmp')
                with tmp.open('w') as f:
                    json.dump(state,f,sort_keys=True);f.flush();os.fsync(f.fileno())
                os.replace(tmp,path)
                kill(runner['pgid'],signal.SIGTERM)
                report[key]='PAUSED'
            finally:
                try:kill(runner['pgid'],signal.SIGCONT)
                except ProcessLookupError:pass
        return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--admission',required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--veto-not-issued',action='store_true')
    a=p.parse_args()
    if not a.execute:raise SystemExit('No action; master must invoke --execute after the veto window.')
    print(json.dumps(pause(a.admission,veto_not_issued=a.veto_not_issued)))
