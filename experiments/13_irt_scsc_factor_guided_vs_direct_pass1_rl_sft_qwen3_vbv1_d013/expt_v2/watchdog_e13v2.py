#!/usr/bin/env python3
"""Fence experiment-13 version-2 recovery and persist process identities and cell attempts."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys

WR = Path(os.environ.get('E13_WORK_ROOT', '/lfs/skampere1/0/brando9/rl4cv_e13v2'))


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(pid):
    """Read Linux identity without exposing arguments or environment contents."""
    try:
        raw = Path(f'/proc/{pid}/stat').read_text()
        fields = raw[raw.rfind(')') + 2:].split()
        if fields[0] == 'Z':
            return None
        return {'pid': int(pid), 'start_ticks': int(fields[19]), 'pgid': int(fields[2]),
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    except (OSError, ValueError, IndexError):
        return None


def live(row):
    current = identity(row['pid'])
    return current is not None and all(current[k] == row[k] for k in current)


@contextmanager
def locked(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'recovery.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def database(root):
    db = sqlite3.connect(root / 'ledger.sqlite3')
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=FULL')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS processes (
            run TEXT, role TEXT, pid INTEGER, start_ticks INTEGER, pgid INTEGER, boot_id TEXT,
            registered TEXT, PRIMARY KEY(run, role, pid, start_ticks, boot_id));
        CREATE TABLE IF NOT EXISTS attempts (
            run TEXT, cell TEXT, attempt INTEGER, source_hash TEXT, status TEXT,
            started TEXT, finished TEXT, PRIMARY KEY(run,cell,attempt));
        CREATE TABLE IF NOT EXISTS events (
            run TEXT, key TEXT, status TEXT, updated TEXT, PRIMARY KEY(run,key));
    ''')
    return db


def register(db, run, role, pid):
    item = identity(pid)
    if item is None:
        raise RuntimeError('cannot bind a dead process')
    db.execute('INSERT OR IGNORE INTO processes VALUES (?,?,?,?,?,?,?)',
               (run, role, item['pid'], item['start_ticks'], item['pgid'], item['boot_id'], now()))
    db.commit()
    return item


def begin(db, run, cell, source_hash):
    """Reserve before execution; only an explicitly transient prior attempt can retry."""
    rows = list(db.execute('SELECT * FROM attempts WHERE run=? AND cell=? ORDER BY attempt', (run, cell)))
    if any(r['source_hash'] != source_hash for r in rows):
        raise RuntimeError('integrity defect: changed source')
    if rows and (len(rows) >= 2 or rows[-1]['status'] != 'transient_infrastructure'):
        raise RuntimeError('cell not eligible for retry')
    attempt = len(rows) + 1
    db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,NULL)',
               (run, cell, attempt, source_hash, 'running', now()))
    db.commit()
    return attempt


def finish(db, run, cell, attempt, status):
    if status not in {'measured', 'transient_infrastructure', 'deterministic_resource_limit', 'integrity_defect'}:
        raise ValueError('unknown terminal class')
    cursor = db.execute('UPDATE attempts SET status=?,finished=? WHERE run=? AND cell=? AND attempt=? AND status=?',
                        (status, now(), run, cell, attempt, 'running'))
    if cursor.rowcount != 1:
        raise RuntimeError('attempt is absent or already terminal')
    db.commit()


def notify(db, run, key, message, mailer):
    """At-most-once send reservation survives crashes; uncertain sends require reconciliation."""
    if db.execute('SELECT 1 FROM events WHERE run=? AND key=?', (run, key)).fetchone():
        return False
    db.execute('INSERT INTO events VALUES (?,?,?,?)', (run, key, 'send_reserved', now()))
    db.commit()
    if not mailer:
        status = 'pending_mailer'
    else:
        result = subprocess.run(mailer, input=json.dumps({
            'to': ['brando.science@gmail.com'], 'cc': [], 'run': run,
            'subject': f'Experiment 13 version 2: {key}', 'body': message,
        }), text=True, capture_output=True, timeout=60)
        status = 'sent' if result.returncode == 0 else 'send_uncertain'
    db.execute('UPDATE events SET status=?,updated=? WHERE run=? AND key=?', (status, now(), run, key))
    db.commit()
    return status == 'sent'


def check(root, run, config):
    """Adopt live registered children before considering any replacement execution owner."""
    with locked(root):
        db = database(root)
        rows = [dict(r) for r in db.execute('SELECT * FROM processes WHERE run=?', (run,))]
        living = [r for r in rows if live(r)]
        owners = [r for r in living if r['role'] == 'owner']
        children = [r for r in living if r['role'] != 'owner']
        marker = root / 'terminal.json'
        if marker.exists():
            terminal = json.loads(marker.read_text())
            if terminal['run'] != run or terminal['status'] not in {'complete', 'stopped', 'needs_human'}:
                raise RuntimeError('unbound terminal marker')
            state = terminal['status']
            notify(db, run, state, terminal['message'], config.get('mailer'))
        elif len(owners) > 1:
            state = 'multiple_owners'
        elif owners:
            state = 'owner_alive'
        elif children:
            state = 'adopted_children'
        elif config.get('recover'):
            # Launch under the shared lock and register before allowing another recovery check.
            child = subprocess.Popen(config['recover'], start_new_session=True,
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            register(db, run, 'owner', child.pid)
            state = 'recovery_started_unverified'
        else:
            state = 'owner_absent'
        receipt = {'run': run, 'status': state, 'checked': now(),
                   'owners_alive': len(owners), 'children_adopted': len(children),
                   'identities': [{k: r[k] for k in ('pid', 'start_ticks', 'pgid', 'boot_id', 'role')} for r in living]}
        temporary = root / 'status.tmp'
        temporary.write_text(json.dumps(receipt, indent=2) + '\n')
        temporary.replace(root / 'status.json')
        db.close()
        return receipt


def kill_registered(db, run, pid):
    """Only a still-matching, registered process-group leader can authorize its group kill."""
    rows = list(db.execute('SELECT * FROM processes WHERE run=? AND pid=?', (run, pid)))
    matched = next((r for r in rows if live(r) and r['pid'] == r['pgid']), None)
    if matched is None:
        raise RuntimeError('refuse to kill unowned or reused process group')
    # pidfd prevents PID recycling between the identity check and the leader signal.
    fd = os.pidfd_open(pid)
    try:
        if not live(matched):
            raise RuntimeError('process identity changed')
        os.killpg(matched['pgid'], signal.SIGTERM)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=WR / 'watchdog')
    parser.add_argument('--run', default='e13v2')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('check')
    p = sub.add_parser('register')
    p.add_argument('--role', required=True)
    p.add_argument('--pid', required=True, type=int)
    args = parser.parse_args()
    if args.action == 'check':
        path = args.root / 'config.json'
        print(json.dumps(check(args.root, args.run, json.loads(path.read_text()) if path.exists() else {})))
    else:
        with locked(args.root):
            db = database(args.root)
            print(json.dumps(register(db, args.run, args.role, args.pid)))
            db.close()


if __name__ == '__main__':
    main()
