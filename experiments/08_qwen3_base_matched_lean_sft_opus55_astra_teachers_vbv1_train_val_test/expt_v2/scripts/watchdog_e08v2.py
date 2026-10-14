#!/usr/bin/env python3
"""Watch only version 2 jobs, resume a dead driver once per incident, and deduplicate failure emails."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

RUNTIME = Path('/lfs/skampere1/0/brando9/rl4cv_e08/v2')
TAG = '# e08v2-matched-test'


def alive(ident):
    if not ident:
        return False
    try:
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        start = Path(f"/proc/{ident['pid']}/stat").read_text().rsplit(')', 1)[1].split()[19]
        return boot == ident['boot_id'] and start == ident['pid_start']
    except FileNotFoundError:
        return False


def notify(root, key, message, mailer):
    marker = root / f'notified_{key}'
    if marker.exists():
        return
    subprocess.run(mailer + [message], check=True, timeout=60)
    marker.write_text(message+'\n')


def check(root=RUNTIME, mailer=None):
    wd = root / 'watchdog'
    wd.mkdir(parents=True, exist_ok=True)
    with (wd / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = (root / 'STATUS_e08v2').read_text().strip() if (root / 'STATUS_e08v2').exists() else 'RUNNING'
        if status in ('DONE', 'PARTIAL', 'FAILED'):
            cron = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if cron.returncode == 0 and TAG in cron.stdout:
                subprocess.run(['crontab', '-'], input=''.join(l+'\n' for l in cron.stdout.splitlines() if TAG not in l), text=True, check=True)
            return {'status': status}
        config = json.loads((wd / 'config.json').read_text())
        state_path = wd / 'state.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else {'jobs': {}}
        mailer = mailer or config['mailer']
        now = time.time()
        for job in config['jobs']:
            name = job['name']; record = state['jobs'].setdefault(name, {})
            if Path(job['done']).exists():
                record['status'] = 'done'; continue
            session = subprocess.run(['tmux', 'has-session', '-t', job['session']], capture_output=True).returncode == 0
            process = {}
            receipt = root / f'drivers/{name}.json'
            if receipt.exists(): process = json.loads(receipt.read_text())
            live_child = alive(process.get('child')) or alive(process.get('identity'))
            if not session and not live_child:
                if not record.get('recovered'):
                    subprocess.run(['tmux', 'new-session', '-d', '-s', job['session'], job['command']], check=True)
                    record.update(recovered=True, status='relaunched', incident_started=now)
                else:
                    record['status'] = 'dead_after_recovery'
                    notify(wd, name+'_dead', f'Version 2 driver {name} died after its one recovery; checkpoint needs continuation.', mailer)
            else:
                record['status'] = 'running' if session else 'orphan_alive_no_duplicate'
            paths = [p for glob in job.get('progress', []) for p in root.glob(glob) if p.is_file()]
            newest = max([p.stat().st_mtime for p in paths] or [config['started']])
            record['freshness_seconds'] = now-newest
            if now-newest > 7200:
                notify(wd, name+'_stale', f'Version 2 {name} has no progress for over two hours.', mailer)
        if not alive(config.get('owner')):
            notify(wd, 'owner_dead', 'Version 2 coordinator died; resume CKPT_codexv-rl4cv-e08v2-matched-test.md. Healthy jobs preserved.', mailer)
        if shutil.disk_usage(root).free < 20*1024**3:
            notify(wd, 'disk_low', 'Version 2 runtime has less than 20 GiB free.', mailer)
        state['checked_at'] = now
        temp = state_path.with_suffix('.tmp'); temp.write_text(json.dumps(state, indent=2)+'\n'); temp.replace(state_path)
        return state


def selftest():
    with tempfile.TemporaryDirectory(prefix='e08v2-watch-') as directory:
        root = Path(directory); (root/'watchdog').mkdir()
        session = f'e08v2-watch-selftest-{os.getpid()}'
        fake = root/'mailer.py'; fake.write_text("import sys\nfrom pathlib import Path\nwith Path(sys.argv[1]).open('a') as f: f.write(sys.argv[2]+'\\n')\n")
        cfg = dict(started=time.time(), owner=None, mailer=[sys.executable,str(fake),str(root/'mail.log')],jobs=[dict(name='simulated_failure',session=session,command='sleep 30',done=str(root/'done'),progress=[])])
        (root/'watchdog/config.json').write_text(json.dumps(cfg))
        try:
            assert check(root)['jobs']['simulated_failure']['status']=='relaunched'
            subprocess.run(['tmux','kill-session','-t',session],check=True)
            assert check(root)['jobs']['simulated_failure']['status']=='dead_after_recovery'
            check(root)
            assert len((root/'mail.log').read_text().splitlines())==2
        finally:
            subprocess.run(['tmux','kill-session','-t',session],capture_output=True)
        return {'selftest':'PASS','relaunches':1,'fake_emails':2,'duplicate_notifications':0}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--selftest',action='store_true'); args=parser.parse_args()
    print(json.dumps(selftest() if args.selftest else check()))
