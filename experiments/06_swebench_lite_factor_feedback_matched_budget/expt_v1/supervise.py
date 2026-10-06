"""Run one bounded remote coordinator with process receipts and one safe restart, preserving healthy child jobs."""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def process_identity(pid):
    try:
        stat = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return {'pid': pid, 'start_ticks': stat[19], 'state': stat[0]}
    except (OSError, IndexError):
        return None


def owned_children(root, ignored):
    """Detect surviving processes by owned cwd, without reading potentially secret command arguments."""
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit() or int(path.name) in ignored:
            continue
        try:
            if path.stat().st_uid != os.getuid():
                continue
            cwd = (path / 'cwd').resolve(strict=True)
            if cwd == root or root in cwd.parents:
                ident = process_identity(int(path.name))
                if ident and ident['state'] != 'Z':
                    found.append(ident)
        except OSError:
            continue
    return found


def supervise(root, prompt, runtime, command, interval=120, max_attempts=2):
    root, runtime = root.resolve(), runtime.resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    lock = (runtime / 'supervisor.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_path = runtime / 'supervisor.json'
    previous = json.loads(state_path.read_text()) if state_path.exists() else {}
    run_id = previous.get('run_id', 'rl4cv-e06-swebench-validation-v1-10-05-2026')
    attempts = previous.get('attempts', 0)
    boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    state = {'run_id': run_id, 'boot_id': boot_id, 'supervisor': process_identity(os.getpid()),
             'attempts': attempts, 'max_attempts': max_attempts, 'reboot_auto_resume': False,
             'root': str(root), 'notification': 'Codex same-thread heartbeat; no email configured'}
    # Don't restart after an unexpected supervisor loss while the old coordinator/children survive.
    ignored = {os.getpid(), os.getppid()}
    while attempts < max_attempts:
        receipt_path = runtime / 'worker_completion.json'
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if receipt.get('run_id') == run_id and receipt.get('status') in {'complete', 'needs_attention', 'failed'}:
                state.update(phase='receipt_available_requires_master_verification', observed_at=now(), receipt=receipt)
                save(state_path, state)
                return 0 if receipt['status'] == 'complete' else 3
        children = owned_children(root, ignored)
        if children:
            state.update(phase='adopting_live_owned_processes', observed_at=now(), owned_processes=children)
            save(state_path, state)
            time.sleep(interval)
            continue
        attempts += 1
        state.update(attempts=attempts, phase='starting_coordinator', observed_at=now())
        save(state_path, state)
        env = os.environ.copy()
        for key in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'GEMINI_API_KEY'):
            env.pop(key, None)
        with prompt.open('rb') as inp, (runtime / f'coordinator_{attempts}.jsonl').open('ab') as log:
            process = subprocess.Popen(command, cwd=root, stdin=inp, stdout=log,
                                       stderr=subprocess.STDOUT, env=env, start_new_session=True)
            state['coordinator'] = process_identity(process.pid)
            while process.poll() is None:
                state.update(phase='coordinator_running', observed_at=now(), owned_processes=owned_children(root, ignored))
                save(state_path, state)
                try:
                    process.wait(timeout=interval)
                except subprocess.TimeoutExpired:
                    pass
        state.update(phase='coordinator_exited', observed_at=now(), coordinator_exit_code=process.returncode)
        save(state_path, state)
        if attempts == max_attempts and not receipt_path.exists():
            state.update(phase='needs_attention_attempt_limit', observed_at=now(), owned_processes=owned_children(root, ignored))
            save(state_path, state)
            return 4
        # Validate the final receipt at the top of the loop even on the last attempt.
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if receipt.get('run_id') == run_id and receipt.get('status') in {'complete', 'needs_attention', 'failed'}:
                state.update(phase='receipt_available_requires_master_verification', observed_at=now(), receipt=receipt)
                save(state_path, state)
                return 0 if receipt['status'] == 'complete' else 3
    return 4


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', required=True, type=Path)
    ap.add_argument('--prompt', required=True, type=Path)
    ap.add_argument('--runtime', required=True, type=Path)
    ap.add_argument('--interval', type=float, default=120)
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        # Real disposable subprocess, simulated first failure, then terminal receipt; no model call.
        runtime = args.runtime.resolve()
        code = ('import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); n=p/"fake_count"; '
                'v=int(n.read_text())+1 if n.exists() else 1; n.write_text(str(v)); '
                '(p/"worker_completion.json").write_text(json.dumps({"run_id":"rl4cv-e06-swebench-validation-v1-10-05-2026",'
                '"status":"complete","simulation":True})) if v==2 else None; sys.exit(0 if v==2 else 7)')
        result = supervise(args.root, args.prompt, runtime, [sys.executable, '-c', code, str(runtime)],
                           interval=.05)
        assert result == 0 and (runtime / 'fake_count').read_text() == '2'
        print('PASS: first failure retained, one restart, terminal simulation receipt; no model calls')
        return
    command = ['codex', 'exec', '--dangerously-bypass-approvals-and-sandbox', '-m', 'gpt-5.6-terra',
               '-c', 'model_reasoning_effort="high"', '--json', '-']
    raise SystemExit(supervise(args.root, args.prompt, args.runtime, command, args.interval))


if __name__ == '__main__':
    main()
