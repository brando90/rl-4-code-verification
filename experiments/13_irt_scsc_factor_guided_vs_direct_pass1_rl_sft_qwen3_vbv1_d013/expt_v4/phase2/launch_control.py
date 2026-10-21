"""TLDR: Validate admission and timing before starting one v4-only tmux controller; never launch on import."""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
from admission import check_admission, launch_timing
from common import object_digest


def launch(plan, *, run=subprocess.run):
    admission=check_admission(plan['admission'],require_launch=True)
    if admission.get('launch_plan_sha256')!=object_digest(plan):raise ValueError('unbound launch plan')
    if not launch_timing(plan['v3_pilot_read_only'],veto_not_issued=__import__('os').environ.get('E13V4_A3_NO_VETO')=='1')['released']:raise ValueError('v3 release condition not met')
    session=plan['session']
    if not session.startswith('rl4cv-e13v4-'):raise ValueError('foreign session')
    probe=run(['tmux','has-session','-t',session],capture_output=True,text=True)
    if probe.returncode==0:return {'status':'ALREADY_RUNNING','session':session}
    if probe.returncode!=1 or (probe.stderr and not any(s in probe.stderr for s in ('no server running','can\'t find session','no sessions'))):
        raise RuntimeError('tmux state unresolved')
    command=plan['sequence_argv']
    if not isinstance(command,list) or any(not isinstance(x,str) for x in command):raise ValueError('argv required')
    run(['tmux','new-session','-d','-s',session,'-c',plan['checkout'],shlex.join(command)],check=True)
    run(['tmux','has-session','-t',session],check=True)
    return {'status':'STARTED','session':session}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True)
    a=p.parse_args();print(json.dumps(launch(json.loads(a.plan.read_text()))))
