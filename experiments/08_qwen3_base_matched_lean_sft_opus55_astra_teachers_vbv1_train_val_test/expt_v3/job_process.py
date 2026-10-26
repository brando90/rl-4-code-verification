"""Record durable job exits and adopt exact surviving children after scheduler replacement."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from recovery_watch import alive, identity, read, write


def generation_complete(root, label, task_ids):
    path = root / f'ladder/validation/raw/gen_{label}_g8.jsonl'
    if not path.exists():
        return False
    try:
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        keys = [(r['task_id'], int(r['sample_idx'])) for r in rows]
        expected = {(task, sample) for task in task_ids for sample in range(8)}
        return len(keys) == len(expected) and set(keys) == expected
    except (ValueError, KeyError, TypeError):
        return False


class AdoptedProcess:
    """Poll a non-child using boot/start identity, never a bare PID or guessed exit."""
    def __init__(self, job, root, task_ids):
        self.job, self.root, self.task_ids = job, root, task_ids
        self.pid = job['pid']

    def poll(self):
        if alive(self.job['identity']):
            return None
        receipt = read(Path(self.job['exit_receipt']), {}) if self.job.get('exit_receipt') else {}
        if receipt.get('identity') == self.job['identity'] and 'exit_code' in receipt:
            return receipt['exit_code']
        key = self.job['key']
        # The original generation wrappers predate durable exit records. Their
        # atomically merged exact-cell output is the authoritative completion gate.
        if key.startswith('gen_') and generation_complete(self.root, key[4:], self.task_ids):
            self.job['reconciled_by'] = 'exact atomically merged generation manifest'
            return 0
        return 125  # Unknown native outcome requires owner reconciliation.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[0] == '--' else args.command
    record = {'identity': identity(os.getpid()), 'started_unix': time.time(), 'command': command}
    write(args.receipt, record)
    child = subprocess.Popen(command)
    record['child'] = identity(child.pid)
    write(args.receipt, record)
    code = child.wait()
    record.update(exit_code=code, ended_unix=time.time())
    write(args.receipt, record)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
