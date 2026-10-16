"""Retire exact orphaned primary Lean children after the frozen scorer's timeout."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import time

from recovery_watch import write

HERE = Path(__file__).resolve().parent
ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e08/sft_v3')
LEAN = Path('/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin/lean')
MIN_AGE = 620  # Frozen 600-second scorer timeout plus scheduling margin.
MAX_PER_SCAN = 16


def window_open(root, now):
    """Unreadable deadline/phase evidence fails closed; polling does not extend it."""
    config = json.loads((root / 'recovery_config.json').read_text())
    deadline = float(config['recovery_deadline_unix'])
    if not math.isfinite(deadline) or not math.isfinite(now) or now >= deadline:
        return False
    states = [json.loads((root / f'phase_{phase}_state.json').read_text()) for phase in 'ab']
    if not all(isinstance(s, dict) and s.get('status') for s in states):
        raise ValueError('missing phase state')
    return not all(s['status'] in ('DONE', 'COMPLETE') for s in states)


class Fence:
    """Bind an orphan to a declared raw validation cell and the pinned executable."""
    def __init__(self, root, manifest, lean=LEAN, proc=Path('/proc')):
        self.root, self.proc, self.lean = root.resolve(), proc, lean.resolve(strict=True)
        self.jobs = self.root / 'ladder/validation/jobs'
        self.cells = {(r['system'], r['task_id'], int(r['sample_idx'])) for r in manifest['cells']}
        self.labels = {r['label'] for r in manifest['systems']}
        self.tasks = set(manifest['task_ids'])
        self.boot = (proc / 'sys/kernel/random/boot_id').read_text().strip()
        st = self.lean.stat()
        self.executable = (st.st_dev, st.st_ino)
        self.raw = {}

    def source_cell(self, source):
        path = Path(source)
        if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_file():
            raise ValueError('noncanonical source')
        parts = path.relative_to(self.jobs).parts
        if len(parts) != 4 or parts[-2:] != ('verifier', 'solution.lean'):
            raise ValueError('not a primary scoring source')
        match = re.fullmatch(r'(.+)_g8_s([0-7])', parts[0])
        if match is None:
            raise ValueError('bad sample directory')
        label, sample, task = match[1], int(match[2]), parts[1]
        cell = (label, task, sample)
        if label not in self.labels or task not in self.tasks or cell not in self.cells:
            raise ValueError('undeclared cell')
        if label not in self.raw:
            raw_path = self.root / f'ladder/validation/raw/gen_{label}_g8.jsonl'
            rows = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
            keys = [(r['task_id'], int(r['sample_idx'])) for r in rows]
            expected = {(t, s) for lab, t, s in self.cells if lab == label}
            if len(keys) != len(expected) or set(keys) != expected:
                raise ValueError('incomplete or duplicate raw manifest')
            self.raw[label] = {key: hashlib.sha256(r['lean'].encode()).hexdigest()
                               for key, r in zip(keys, rows) if isinstance(r.get('lean'), str)}
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != self.raw[label].get((task, sample)):
            raise ValueError('source differs from raw generation')
        return {'label': label, 'task_id': task, 'sample_idx': sample, 'source': str(path),
                'source_sha256': digest}

    def inspect(self, pid):
        """Return immutable candidate evidence; reject every live parent tree."""
        folder = self.proc / str(pid)
        fields = (folder / 'stat').read_text().rsplit(')', 1)[1].split()
        if fields[0] == 'Z' or int(fields[1]) != 1:
            return None
        uid = next(line for line in (folder / 'status').read_text().splitlines() if line.startswith('Uid:'))
        if any(int(value) != os.getuid() for value in uid.split()[1:]):
            return None
        start = int(fields[19])
        uptime = float((self.proc / 'uptime').read_text().split()[0])
        age = uptime - start / os.sysconf('SC_CLK_TCK')
        if age < MIN_AGE:
            return None
        exe = folder / 'exe'
        if os.readlink(exe) != str(self.lean):
            return None
        st = exe.stat()
        if (st.st_dev, st.st_ino) != self.executable:
            return None
        argv = (folder / 'cmdline').read_bytes().rstrip(b'\0').split(b'\0')
        if len(argv) != 2 or argv[0].decode() not in ('lean', str(self.lean)):
            return None
        cell = self.source_cell(argv[1].decode())
        return {'pid': pid, 'boot_id': self.boot, 'start_ticks': str(start), 'ppid': 1,
                'uid': os.getuid(), 'executable': str(self.lean), 'exe_dev': st.st_dev,
                'exe_ino': st.st_ino, 'argv_sha256': hashlib.sha256(b'\0'.join(argv)).hexdigest(),
                **cell}


def inspect_or_none(fence, pid):
    try:
        return fence.inspect(pid)
    except (OSError, ValueError, KeyError, TypeError, StopIteration, IndexError, UnicodeError):
        return None


def retire(fence, candidate, permitted, grace=1):
    """Pidfds prevent PID reuse; revalidate the entire fence before each signal."""
    result = {**candidate, 'signals': [], 'observed_unix': time.time()}
    fd = os.pidfd_open(candidate['pid'])
    try:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            if not permitted() or inspect_or_none(fence, candidate['pid']) != candidate:
                break
            signal.pidfd_send_signal(fd, sig)
            result['signals'].append(sig.name)
            time.sleep(grace)
        result['still_eligible'] = inspect_or_none(fence, candidate['pid']) == candidate
        return result
    finally:
        os.close(fd)


def scan(root=ROOT, apply=False):
    receipt = {'observed_unix': time.time(), 'apply': apply, 'minimum_age_seconds': MIN_AGE,
               'frozen_timeout_seconds': 600, 'max_per_scan': MAX_PER_SCAN, 'candidates': [], 'actions': []}
    with (root / 'lean_orphan_cleanup.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {**receipt, 'status': 'LOCKED'}
        permitted = lambda: window_open(root, time.time())
        if not permitted():
            return {**receipt, 'status': 'STOPPED'}
        manifest = json.loads((HERE / 'results/ladder_manifest_v3.json').read_text())
        fence = Fence(root, manifest)
        for folder in fence.proc.iterdir():
            if not folder.name.isdigit():
                continue
            candidate = inspect_or_none(fence, int(folder.name))
            if candidate:
                receipt['candidates'].append(candidate)
        receipt['candidates'].sort(key=lambda r: int(r['start_ticks']))
        if apply:
            for candidate in receipt['candidates'][:MAX_PER_SCAN]:
                try:
                    receipt['actions'].append(retire(fence, candidate, permitted))
                except (OSError, ValueError, KeyError, TypeError) as exc:
                    receipt['actions'].append({**candidate, 'error': str(exc)})
        receipt['status'] = 'SCANNED'
        # Cleanup evidence never writes to the scorer, raw data, or phase state.
        if receipt['candidates']:
            with (root / 'lean_orphan_cleanup_events.jsonl').open('a') as stream:
                stream.write(json.dumps(receipt, sort_keys=True) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
        write(root / 'lean_orphan_cleanup_latest.json', receipt)
        return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    result = scan(args.root, args.apply)
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in result.items()}))
