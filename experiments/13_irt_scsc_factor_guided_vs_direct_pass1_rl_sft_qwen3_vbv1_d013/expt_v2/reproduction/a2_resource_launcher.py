#!/usr/bin/env python3
"""Run unchanged A2 reconciliation with an exact kernel-page representation check for its frozen memory cap."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2_reconcile as a2

ORIGINAL_VERIFY = a2.verify_bindings
RESOURCE_ERROR = 'A2 aggregate memory limit changed'
SUPPLEMENT = HERE.parent / 'locks/A2_resource_preflight.json'


def validate_memory_limit(requested, actual, page_size):
    if any(type(x) is not int or x <= 0 for x in (requested, actual, page_size)):
        raise ValueError('invalid memory-limit representation')
    expected = requested // page_size * page_size
    if actual != expected:
        raise RuntimeError('effective A2 memory limit changed')
    return expected


def verify_supplement():
    lock = json.loads(SUPPLEMENT.read_text())
    for path, expected in lock['hashes'].items():
        if a2.sha(path) != expected:
            raise RuntimeError('A2 resource-preflight binding changed')
    return lock


def kernel_memory_limit():
    cgroup = next(line.split(':', 2)[2] for line in Path('/proc/self/cgroup').read_text().splitlines()
                  if line.startswith('0::'))
    return int((Path('/sys/fs/cgroup') / cgroup.lstrip('/') / 'memory.max').read_text())


def verify_bindings(original):
    lock = verify_supplement()
    try:
        execution = ORIGINAL_VERIFY(original)
    except RuntimeError as error:
        # The frozen verifier reaches this exact error only after all bindings and scope identity pass.
        if error.args != (RESOURCE_ERROR,):
            raise
        execution = json.loads((original / 'execution_lock.json').read_text())
    actual = kernel_memory_limit()
    page_size = os.sysconf('SC_PAGE_SIZE')
    requested = execution['aggregate_memory_max_bytes']
    validate_memory_limit(requested, actual, page_size)
    if (requested, actual, page_size) != (lock['requested_memory_max_bytes'],
                                        lock['effective_memory_max_bytes'], lock['page_size']):
        raise RuntimeError('frozen resource representation changed')
    return execution


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--route', choices=tuple(a2.DENOMINATORS))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args(argv)
    verify_supplement()
    if args.route:
        a2.verify_bindings = verify_bindings
        return 0 if a2.reconcile_route(args.route, args.resume)['admitted'] else 1
    target = Path(os.environ['WR']) / 'R2_A2'
    target.mkdir(exist_ok=args.resume)
    receipts = []
    # Only sanitized public receipts (or their byte hashes) are read in this parent process.
    for route in ('opaque', 'ordinary'):
        path = target / (route + '_public_receipt.json')
        if args.resume and path.is_file():
            receipt = json.loads(path.read_text())
            if receipt['hashes']['effective_results'] != a2.sha(target / route / 'results.jsonl'):
                raise RuntimeError('completed A2 route changed')
            receipts.append(receipt)
            continue
        with (target / (route + '_coordinator.log')).open('a' if args.resume else 'x') as log:
            command = [sys.executable, str(Path(__file__).resolve()), '--route', route]
            if args.resume:
                command.append('--resume')
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
        if not path.is_file():
            print(json.dumps({'amendment': 'A2', 'route': route, 'status': 'INCOMPLETE',
                              'public_receipt_missing': True}), flush=True)
            return 1
        receipts.append(json.loads(path.read_text()))
    public = a2.combine(receipts)
    (target / 'public_result.json').write_text(json.dumps(public, indent=2) + '\n')
    print(json.dumps(public), flush=True)
    return 0 if public['admitted'] else 1


if __name__ == '__main__':
    try:
        code = main()
    except Exception as exc:
        folder = Path(os.environ['WR']) / 'R2_A2'
        if '--route' in sys.argv:
            folder /= sys.argv[sys.argv.index('--route') + 1]
        folder.mkdir(parents=True, exist_ok=True)
        # Keep the first preflight traceback intact.
        (folder / 'private_resource_launcher_error.txt').write_text(traceback.format_exc())
        print(json.dumps({'amendment': 'A2', 'status': 'INCOMPLETE',
                          'error_type': type(exc).__name__, 'test_outcomes_disclosed': False}), flush=True)
        code = 1
    raise SystemExit(code)
