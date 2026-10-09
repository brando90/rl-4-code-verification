"""TLDR: Run-bound child registration before exec, with identity-checked cleanup."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e09')


def identity(pid):
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return {'pid': int(pid), 'start_ticks': fields[19],
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def alive(record):
    try:
        return identity(record['pid']) == {k: record[k] for k in ('pid', 'start_ticks', 'boot_id')}
    except (FileNotFoundError, ProcessLookupError):
        return False


@contextmanager
def registry(root=ROOT):
    with (root / 'children.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = root / 'child_receipts.json'
        data = json.loads(path.read_text())
        yield data
        data['written_utc'] = datetime.now(timezone.utc).isoformat()
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
        temp.replace(path)


def spawn(args, *, kind, root=ROOT, **kwargs):
    """The child waits in the owned runtime until its process receipt is durable."""
    read_fd, write_fd = os.pipe()
    cwd = str(kwargs.pop('cwd', root))
    bootstrap = ('import os,sys; fd=int(sys.argv[1]); go=os.read(fd,1); os.close(fd); '
                 'assert go==b"1", "unregistered child"; os.chdir(sys.argv[2]); '
                 'os.execvpe(sys.argv[3],sys.argv[3:],os.environ)')
    proc = None
    try:
        proc = subprocess.Popen(['/usr/bin/python3', '-c', bootstrap, str(read_fd), cwd, *map(str, args)],
                                cwd=root, pass_fds=(read_fd,), **kwargs)
        record = {**identity(proc.pid), 'kind': kind,
                  'run_id': json.loads((root / 'run_identity.json').read_text())['run_id'],
                  'command_sha256': hashlib.sha256(json.dumps(list(map(str, args))).encode()).hexdigest()}
        with registry(root) as data:
            data.setdefault('processes', []).append(record)
        os.write(write_fd, b'1')
        return proc
    finally:
        os.close(read_fd)
        os.close(write_fd)


def stop(record, root=ROOT):
    """Stop only the exact owned process group; foreign/reused PIDs are untouched."""
    if alive(record):
        assert os.getpgid(record['pid']) == record['pid'], 'Child must own its process group'
        os.killpg(record['pid'], signal.SIGTERM)
        for _ in range(30):
            if not alive(record):
                break
            time.sleep(.1)
        if alive(record):
            os.killpg(record['pid'], signal.SIGKILL)
    with registry(root) as data:
        data['processes'] = [r for r in data.get('processes', [])
                             if (r.get('pid'), r.get('start_ticks')) != (record['pid'], record['start_ticks'])]
