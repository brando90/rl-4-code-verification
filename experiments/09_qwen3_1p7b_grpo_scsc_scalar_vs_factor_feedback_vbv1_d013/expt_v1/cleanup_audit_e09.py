"""TLDR: Audit only run-tagged children of exited technical controls; never stop shared Ray."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import time

ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e09')


def inspect():
    rows = []
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():
            continue
        try:
            if directory.stat().st_uid != os.getuid():
                continue
            # Read only this allowlisted non-secret tag; never emit process environments.
            tag = next((v.split(b'=', 1)[1].decode() for v in (directory / 'environ').read_bytes().split(b'\0')
                        if v.startswith(b'E09_CONTROL_DIR=')), None)
            if tag is None or Path(tag).parent != ROOT / 'technical_control':
                continue
            fields = (directory / 'stat').read_text().rsplit(')', 1)[1].split()
            rows.append({'pid': int(directory.name), 'start_ticks': fields[19], 'state': fields[0],
                         'boot_id': boot, 'control_dir': tag, 'comm': (directory / 'comm').read_text().strip(),
                         'control_has_exit_receipt': (Path(tag) / 'exit.json').is_file()})
        except (OSError, StopIteration, UnicodeError):
            continue
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stop-exited-remnants', action='store_true')
    args = parser.parse_args()
    before = inspect()
    signaled = []
    if args.stop_exited_remnants:
        for row in before:
            if row['control_has_exit_receipt'] and row['state'] != 'Z':
                fresh = next((r for r in inspect() if r['pid'] == row['pid']), None)
                if fresh and fresh['start_ticks'] == row['start_ticks'] and fresh['boot_id'] == row['boot_id']:
                    os.kill(row['pid'], signal.SIGTERM)
                    signaled.append(row)
        if signaled:
            time.sleep(3)
    result = {'written_utc': datetime.now(timezone.utc).isoformat(), 'before': before,
              'signaled_exited_control_remnants': signaled, 'after': inspect(),
              'shared_ray_stop_used': False, 'foreign_processes_modified': False}
    (ROOT / 'receipts/cleanup_audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
