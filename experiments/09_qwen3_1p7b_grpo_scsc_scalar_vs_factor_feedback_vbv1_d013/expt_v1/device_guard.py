"""TLDR: Fail closed if the physically leased GPU contains any foreign process."""
import os
from pathlib import Path
import subprocess


def proc(pid):
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    return int(fields[1]), fields[19]


def verify_exclusive_device():
    root = int(os.environ['E09_DRIVER_PID'])
    assert proc(root)[1] == os.environ['E09_DRIVER_START']
    expected = os.environ['E09_LEASED_GPU_UUID']
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader'],
                            capture_output=True, text=True, check=True, timeout=30)
    for line in result.stdout.splitlines():
        uuid, value = line.strip().split(', ')
        if uuid != expected:
            continue
        pid = int(value)
        ancestry, cursor = set(), pid
        while cursor > 1 and cursor not in ancestry and cursor != root:
            ancestry.add(cursor)
            cursor = proc(cursor)[0]
        if cursor != root:
            raise RuntimeError(f'Physical lease conflict on {expected}: foreign PID {pid}; no sharing admitted')
    return expected
