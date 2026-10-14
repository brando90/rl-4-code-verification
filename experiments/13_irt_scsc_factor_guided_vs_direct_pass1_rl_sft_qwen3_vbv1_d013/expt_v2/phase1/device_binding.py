"""Map the leased UUID to a fresh numeric CUDA index before every experiment launch."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import time

PURPOSES = ('LP1', 'anchors', 'LP', 'T1', 'T2', 'T3', 'T4', 'pilot', 'main')


def numeric_index(lease, query=None):
    if query is None:
        query = subprocess.run(['nvidia-smi', '--query-gpu=uuid,index',
                                '--format=csv,noheader,nounits'],
                               capture_output=True, text=True, check=True, timeout=15).stdout
    devices = [tuple(part.strip() for part in line.split(','))
               for line in query.splitlines() if line.strip()]
    if any(len(row) != 2 or not row[1].isdigit() for row in devices):
        raise RuntimeError('invalid UUID/index census')
    matches = [int(index) for uuid, index in devices if uuid == lease['uuid']]
    if len(matches) != 1 or matches[0] != lease['index']:
        raise RuntimeError('leased UUID/index mapping changed or is ambiguous')
    return str(matches[0])


def validate_lease(lease):
    if (lease['status'] != 'ACTIVE' or lease['owner'] != 'e13v2'
            or lease['host'] != socket.gethostname().split('.')[0]
            or lease['expires_unix'] <= time.time()):
        raise RuntimeError('model call has no valid experiment-13 lease')


def launch_environment(lease, purpose, environment=None, query=None):
    if purpose not in PURPOSES:
        raise ValueError('unknown experiment launch purpose')
    validate_lease(lease)
    result = dict(os.environ if environment is None else environment)
    result.update(CUDA_VISIBLE_DEVICES=numeric_index(lease, query),
                  CUDA_DEVICE_ORDER='PCI_BUS_ID', E13_EXECUTION_ID=lease['id'],
                  E13_LAUNCH_PURPOSE=purpose)
    return result


def check_visible_device(lease):
    validate_lease(lease)
    if (os.environ.get('CUDA_VISIBLE_DEVICES') != numeric_index(lease)
            or os.environ.get('E13_EXECUTION_ID') != lease['id']):
        raise RuntimeError('CUDA visibility differs from leased numeric index')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lease', required=True, type=Path)
    parser.add_argument('--purpose', required=True, choices=PURPOSES)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not argv:
        raise ValueError('missing launch command')
    lease = json.loads(args.lease.read_text())
    env = launch_environment(lease, args.purpose)
    os.execvpe(argv[0], argv, env)


if __name__ == '__main__':
    main()
