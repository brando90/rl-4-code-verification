"""Check the explicitly authorized v3 physical device and execution ownership on every stage."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time


def check(config):
    lease = json.loads(Path(config['lease_path']).read_text())
    if (lease['owner'] != 'e13v3' or lease['status'] != 'ACTIVE'
            or socket.gethostname().split('.')[0] != 'skampere1'
            or lease['index'] not in (0, 5, 7) or time.time() >= lease['expires_unix']
            or os.environ.get('CUDA_VISIBLE_DEVICES') != str(lease['index'])
            or os.environ.get('E13_EXECUTION_ID') != lease['id']
            or os.environ.get('HF_HUB_OFFLINE') != '1'):
        raise RuntimeError('invalid offline v3 device allocation')
    query = subprocess.check_output(['nvidia-smi', '--query-gpu=index,uuid',
                                    '--format=csv,noheader,nounits'], text=True)
    mapping = dict(tuple(x.strip() for x in line.split(',')) for line in query.splitlines())
    if mapping[str(lease['index'])] != lease['uuid']:
        raise RuntimeError('physical GPU mapping changed')
    query = subprocess.check_output(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                                    '--format=csv,noheader,nounits'], text=True)
    marker = ('E13_EXECUTION_ID=' + lease['id']).encode()
    for line in query.splitlines():
        uuid, pid = (x.strip() for x in line.split(','))
        if uuid == lease['uuid']:
            try:
                environment = Path('/proc', pid, 'environ').read_bytes().split(b'\0')
            except FileNotFoundError:
                continue
            if marker not in environment:
                raise RuntimeError('foreign process occupies requested GPU')


def install():
    # Only resource ownership is adapted. Original numerical, checkpoint, token,
    # loss and sampler implementations remain imported read-only and hash-bound.
    import runtime
    runtime.check_lease = check
