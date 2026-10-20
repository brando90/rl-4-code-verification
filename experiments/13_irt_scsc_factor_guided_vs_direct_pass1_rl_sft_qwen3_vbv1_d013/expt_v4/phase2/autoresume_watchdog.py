"""TLDR: Supervise v4-only trajectories with durable attempts, liveness fences and no resampling."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
from common import canonical

PREFIX='rl4cv-e13v4-'


class ProbeError(RuntimeError):
    """Unknown liveness prohibits restart."""


def decide(*,live,complete,partials,restarts,next_update):
    if live or complete:return ('skip',None)
    if len(partials)>1:return ('diagnose',None)
    if not partials:action,update='launch',next_update
    else:
        p=partials[0]; update=p['update']
        if p['optimizer_result']:action='account_then_launch'
        elif p['generations']==0:action='archive_then_launch'
        elif p['generations']==256 and p['scored'] and p['pre_state_bound']:action='replay_saved_then_launch'
        else:return ('diagnose',update)
    if restarts.get(str(update),0)>=3:return ('diagnose',update)
    return action,update


def live(root, session, run=subprocess.run):
    if not session.startswith(PREFIX):raise ProbeError('foreign session prefix')
    result=run(['tmux','list-sessions','-F','#{session_name}\t#{pane_dead}'],capture_output=True,text=True,timeout=15)
    if result.returncode:
        # Permission errors / generic connection errors are NOT evidence of no server.
        if 'no server running' not in result.stderr:raise ProbeError('tmux census failed')
    else:
        for line in result.stdout.splitlines():
            parts=line.split('\t')
            if len(parts)!=2 or parts[1] not in ('0','1'):raise ProbeError('bad tmux row')
            if (parts[0]==session or parts[0].startswith(session+'-retry-')) and parts[1]=='0':return True
    result=run(['pgrep','-af',str(Path(root).resolve())],capture_output=True,text=True,timeout=15)
    if result.returncode not in (0,1):raise ProbeError('process census failed')
    if result.returncode==0:
        if not result.stdout.strip():raise ProbeError('empty successful process census')
        return True
    return False


def trajectory_state(root,horizon):
    root=Path(root)
    dirs=sorted(p for p in root.glob('update_*') if p.is_dir() and len(p.name)==12 and p.name[7:].isdigit())
    completed=[];partials=[]
    for p in dirs:
        update=int(p.name[7:])
        if (p/'summary.json').exists():completed.append(update);continue
        partials.append({'update':update,'generations':len(list((p/'generate/output').glob('*.generation.json'))),
                         'scored':(p/'score/groups.json').exists(),
                         'optimizer_result':(p/'update/output/result.json').exists(),
                         'pre_state_bound':(p/'update/output/replay_binding.json').exists()})
    if completed!=list(range(1,len(completed)+1)):raise ProbeError('noncontiguous completed updates')
    return {'complete':len(completed)>=horizon,'partials':partials,'next_update':len(completed)+1}


def atomic(path,value):
    path=Path(path);tmp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    with tmp.open('wb') as stream:
        stream.write(canonical(value)+b'\n');stream.flush();os.fsync(stream.fileno())
    os.replace(tmp,path)


def tick(plan,*,dry_run=True,run=subprocess.run,admission_check=None):
    """Commands are bound by admission; repair commands must consume saved state, never resample."""
    from admission import check_admission
    check=admission_check or check_admission
    admission=check(Path(plan['admission']),require_launch=not dry_run)
    if not dry_run and admission.get('watchdog_plan_sha256')!=__import__('common').object_digest(plan):
        raise ValueError('watchdog commands are not bound by admission')
    work=Path(plan['work']);work.mkdir(parents=True,exist_ok=True)
    with (work/'autoresume.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'SKIPPED_OVERLAP'}
        state_path=work/'autoresume_state.json'
        state=json.loads(state_path.read_text()) if state_path.exists() else {}
        report={}
        for t in plan['trajectories']:
            key=f"{t['arm']}_{t['seed']}";root=work/'pilot'/key
            session=f"{PREFIX}pilot-{t['arm']}-{t['seed']}"
            try:
                if t['arm'] not in ('A','B','P') or t['seed'] not in (1301,1302) or t['horizon'] not in (30,60):
                    raise ProbeError('invalid trajectory')
                info=trajectory_state(root,t['horizon'])
                action,update=decide(live=live(root,session,run),restarts=state.get(key,{}),**info)
                report[key]={'action':action,'update':update}
                if dry_run or action in ('skip','diagnose'):continue
                root.mkdir(parents=True,exist_ok=True)
                with (root/'controller.lock').open('a') as fence:
                    fcntl.flock(fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    if live(root,session,run):continue
                    check(Path(plan['admission']),require_launch=True)
                    count=state.setdefault(key,{}); count[str(update)]=count.get(str(update),0)+1
                    atomic(state_path,state)  # reserve before any action
                    command=t['commands'][action]
                    if not isinstance(command,list) or not command or any(not isinstance(s,str) for s in command):
                        raise ValueError('bound argument-vector command required')
                    # The external owner helper launches its own v4 tmux session. No session killing here.
                    result=run(command,capture_output=True,text=True,timeout=45)
                    report[key]['returncode']=result.returncode
                    report[key]['first_output']=result.stdout[-500:]
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
                report[key]={'action':'diagnose','error':str(error)}
        if not dry_run:atomic(work/'autoresume_status.json',report)
        return {'status':'DRY_RUN' if dry_run else 'CHECKED','trajectories':report}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--execute',action='store_true');a=p.parse_args()
    print(json.dumps(tick(json.loads(a.plan.read_text()),dry_run=not a.execute),sort_keys=True))
