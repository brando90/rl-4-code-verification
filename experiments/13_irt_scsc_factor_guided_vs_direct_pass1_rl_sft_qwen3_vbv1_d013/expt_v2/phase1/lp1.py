"""Supervise one bounded LP-1 attempt and clean only its marked subprocesses."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from panel import write_new
from probability import assess_probability
from runtime import check_bindings, check_lease


def marked_processes(marker):
    found = []
    key = ('E13_EXECUTION_ID='+marker).encode()
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid(): continue
        try:
            if entry.stat().st_uid != os.getuid(): continue
            if key in (entry/'environ').read_bytes().split(b'\0'):
                found.append(int(entry.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return found


def cleanup(marker):
    """PID file descriptors fence signals against process-identifier reuse."""
    signalled = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in marked_processes(marker):
            try:
                fd = os.pidfd_open(pid)
                try:
                    if pid in marked_processes(marker):
                        signal.pidfd_send_signal(fd, sig); signalled.append({'pid': pid, 'signal': int(sig)})
                finally: os.close(fd)
            except ProcessLookupError:
                pass
        deadline = time.monotonic()+10
        while marked_processes(marker) and time.monotonic() < deadline:
            time.sleep(.1)
    return {'verified': not marked_processes(marker), 'signals': signalled}


def run(config_path):
    config = json.loads(Path(config_path).read_text())
    check_bindings(config); check_lease(config)
    marker = os.environ['E13_EXECUTION_ID']
    lease = json.loads(Path(config['lease_path']).read_text())
    if marker != lease['id']: raise ValueError('execution marker/lease mismatch')
    root = Path(config['attempt_root']); root.mkdir(parents=True, exist_ok=True)
    launch = {'started_unix': time.time(), 'lease_id': marker,
                                  'declared_responses': 8, 'optimizer_updates': 0, 'retries': 0,
                                  'pid': os.getpid(), 'pgid': os.getpgid(os.getpid()),
                                  'start_ticks': Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
                                  'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                                  'attempt_number':config.get('attempt_number',1)}
    write_new(root/'launch.json', launch)
    deadline = time.monotonic()+config['maximum_seconds']
    result = {'status': 'INCOMPLETE', 'optimizer_updates': 0, 'retries': 0,
              'attempt_number':config.get('attempt_number',1), 'attempt_counted':False,
              'admission_statistics_computed':False}
    cleanup_receipts = []
    def interrupted(signum, frame):
        raise TimeoutError('supervisor interrupted by signal '+str(signum))
    prior_handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGHUP)}
    try:
        for stage in ('preflight', 'generate', 'trainer'):
            if stage == 'generate':
                preflight = json.loads((root/'preflight.json').read_text())
                if preflight['status'] != 'PASS': raise RuntimeError('engine preflight did not pass')
                write_new(root/'attempt.json', {**launch, 'started_unix':time.time(),
                                               'preflight':'PASS'})
                result['attempt_counted'] = True
            check_lease(config)
            # Cleanup and lease retirement consume the same frozen allocation.
            remaining = min(deadline-time.monotonic(), lease['expires_unix']-time.time())-45
            if remaining <= 0: raise TimeoutError('bounded allocation exhausted')
            with (root/(stage+'.log')).open('x') as stream:
                completed = subprocess.run([config['python'], str(Path(__file__).with_name('runtime.py')),
                    '--config', str(config_path), '--stage', stage], stdout=stream, stderr=subprocess.STDOUT,
                    timeout=remaining, check=False, start_new_session=True)
            cleaned = cleanup(marker); cleanup_receipts.append(cleaned)
            if completed.returncode != 0 or not cleaned['verified']:
                raise RuntimeError(stage+' failed or left an owned process')
        generation_root = Path(config['generation_root'])
        rows = [json.loads((generation_root/f'{i:05d}.probability.json').read_text()) for i in range(8)]
        manifest = json.loads(Path(config['manifest']).read_text())
        # Set before assessment so a crash during statistic computation can never
        # be mistaken for an infrastructure attempt eligible for A4.
        result['admission_statistics_computed'] = True
        write_new(root/'statistics_started.json', {'attempt_number':config.get('attempt_number',1)})
        result.update(assess_probability(rows, eos_token_ids=manifest['terminal_token_ids']))
        if 'a5_stage' in config:
            from a5_admission import qualifies
            result.update(condition='v2-S2', a5_stage=config['a5_stage'],
                          candidate=config['candidate'], numerical_dtype=config['numerical_dtype'])
            if config['a5_stage'] == 'development':
                result['development_qualifies'] = qualifies(result)
        result.update(optimizer_updates=0, retries=0, lease_id=marker,
                      resource_seconds=config['maximum_seconds']-(deadline-time.monotonic()),
                      sampler={'temperature': 1., 'top_p': 1., 'top_k': -1, 'max_new_tokens': 8192},
                      route=config['route'], terminal_token_ids=manifest['terminal_token_ids'])
    except BaseException as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        cleanup_receipts.append(cleanup(marker))
        result['cleanup_verified'] = all(r['verified'] for r in cleanup_receipts)
        if not result['cleanup_verified']:
            result['probability_status'] = result['status']
            result['status'] = 'INCOMPLETE'
        write_new(root/'cleanup.json', cleanup_receipts)
        write_new(root/'result.json', result)
        for sig, handler in prior_handlers.items(): signal.signal(sig, handler)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    print(json.dumps(run(parser.parse_args().config), sort_keys=True))


if __name__ == '__main__':
    main()
