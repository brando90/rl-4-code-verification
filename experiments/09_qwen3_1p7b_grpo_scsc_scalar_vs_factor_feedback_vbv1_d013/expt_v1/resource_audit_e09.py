"""TLDR: Original run/deadline/disk/device-hour admission checks, without model calls."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e09')


def stamp():
    return datetime.now(timezone.utc)


def lease_usage(now=None):
    now = now or stamp()
    rows, seen = [], set()
    paths = [path for phase in ('technical_control', 'calibration', 'training', 'evaluation')
             for path in (ROOT / phase).glob('*/lease.json')]
    for path in paths:
        lease = json.loads(path.read_text())
        lease = lease.get('lease', lease)
        key = lease.get('lease_id')
        if not key or key in seen:
            continue
        seen.add(key)
        release = path.with_name('release.json')
        end = now
        active = not release.exists()
        if release.exists():
            data = json.loads(release.read_text())
            data = data.get('lease', data)
            ended = data.get('released_at') or data.get('released_utc')
            # Exit is durable after release; using its later timestamp is conservative.
            if ended is None:
                ended = json.loads(path.with_name('exit.json').read_text())['written_utc']
            end = datetime.fromisoformat(ended)
        start = datetime.fromisoformat(lease.get('since') or lease['granted_utc'])
        devices = len(lease.get('gpus', [lease['cuda_visible_devices']]))
        rows.append({'lease_id': key, 'start_utc': start.isoformat(), 'end_utc': end.isoformat(),
                     'active': active, 'devices': devices,
                     'device_hours': max(0., (end - start).total_seconds()) * devices / 3600})
    # The first inherited forward-only lease was 282 seconds on one device;
    # use the conservative recorded start/release interval, not CUDA-active time.
    rows.append({'lease_id': 'inherited_forward_preflight', 'active': False,
                 'devices': 1, 'device_hours': 282 / 3600})
    return rows


class ResourceGate:
    def __init__(self, reserve_seconds=3600):
        self.identity = json.loads((ROOT / 'run_identity.json').read_text())
        self.deadline = datetime.fromisoformat(self.identity['deadline_utc'])
        self.reserve = reserve_seconds
        self.last_disk = 0.

    def __call__(self):
        assert stamp() < self.deadline - timedelta(seconds=self.reserve), 'Original deadline finalization reserve reached'
        for path in (ROOT, Path('/tmp')):
            fs = os.statvfs(path)
            assert fs.f_bavail / fs.f_blocks >= self.identity['min_free_filesystem_fraction'], 'Filesystem headroom below fixed minimum'
        rows = lease_usage()
        assert sum(r['device_hours'] for r in rows) < self.identity['max_a100_device_hours'], 'Original device-hour cap reached'
        assert sum(r['devices'] for r in rows if r['active']) <= self.identity['max_devices'], 'Simultaneous device cap exceeded'
        if time.monotonic() - self.last_disk > 300:
            # Charge the whole shared uv cache conservatively because the exact
            # attempt-1 increment was not recorded; never assume it cost zero.
            paths = [str(ROOT), '/lfs/skampere1/0/brando9/.cache/uv']
            result = subprocess.run(['du', '-sx', '--block-size=1', *paths],
                                    capture_output=True, text=True, check=True, timeout=120)
            sizes = {line.split('\t', 1)[1]: int(line.split('\t', 1)[0]) for line in result.stdout.splitlines()}
            assert sum(sizes.values()) < self.identity['max_new_owned_gib'] * 1024**3, 'Original new-data cap reached'
            self.last_disk = time.monotonic()
            receipt = {'written_utc': stamp().isoformat(), 'run_id': self.identity['run_id'],
                       'deadline_utc': self.identity['deadline_utc'], 'finalization_reserve_seconds': self.reserve,
                       'owned_and_conservatively_charged_bytes': sizes,
                       'leases': rows, 'total_reserved_device_hours': sum(r['device_hours'] for r in rows),
                       'load_average': list(os.getloadavg()), 'native_cpu_count': os.cpu_count(),
                       'new_judge_calls_from_this_audit': 0}
            path = ROOT / 'receipts/resource_audit.json'
            tmp = path.with_suffix('.tmp')
            tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
            tmp.replace(path)


if __name__ == '__main__':
    ResourceGate()()
