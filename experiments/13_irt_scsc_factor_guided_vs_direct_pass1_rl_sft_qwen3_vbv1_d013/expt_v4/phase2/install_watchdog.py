"""TLDR: Preview or install only the v4 cron entry after launch admission; never edit v3 hooks."""
import argparse
from pathlib import Path
import shlex
import subprocess
from admission import check_admission

TAG='# e13v4-autoresume'


def cron_text(existing,python,script,plan,log):
    command='env E13V4_A3_NO_VETO=1 '+ ' '.join(shlex.quote(str(p)) for p in (python,script,'--plan',plan,'--execute'))
    # crond treats percent specially even inside shell quotes.
    if any(c in command+str(log) for c in ('\n','\r','%')):raise ValueError('unsafe cron path')
    lines=[l for l in existing.splitlines() if not l.rstrip().endswith(TAG)]
    lines.append(f'*/10 * * * * {command} >> {shlex.quote(str(log))} 2>&1 {TAG}')
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('python','plan','log','admission'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--install',action='store_true');a=p.parse_args()
    result=subprocess.run(['crontab','-l'],capture_output=True,text=True,check=False)
    if result.returncode and 'no crontab' not in result.stderr:raise RuntimeError('crontab probe failed')
    proposed=cron_text(result.stdout,a.python,Path(__file__).with_name('autoresume_watchdog.py'),a.plan,a.log)
    if a.install:
        check_admission(a.admission,require_launch=True)
        from pause_v3 import VETO_END
        import os,time
        if time.time()<VETO_END or os.environ.get('E13V4_A3_NO_VETO')!='1':raise ValueError('A3 veto window/no-veto condition required')
        subprocess.run(['crontab','-'],input=proposed,text=True,check=True)
        actual=subprocess.check_output(['crontab','-l'],text=True)
        if actual!=proposed:raise RuntimeError('cron readback mismatch')
    else:print(proposed,end='')
