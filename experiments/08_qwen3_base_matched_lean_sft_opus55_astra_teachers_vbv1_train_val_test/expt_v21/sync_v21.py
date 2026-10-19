"""Publish compact tiny-repair receipts from SNAP without copying prompts or provider logs."""
from __future__ import annotations
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('campaign_publication', HERE.parent / 'expt_v15/sync_campaign.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


def file_map(host):
    assert host == 'snap'
    names = ['dispatch.json', 'progress.json', 'watch_heartbeat.json', 'completion.json', 'provider_hold.json', 'coordinator_attention.json', 'budget_hold.json', 'row_progress.csv', 'runtime_manifest.json', 'launch_source_manifest.json']
    names += ['final/' + x for x in ['completion.json', 'row_results.csv', 'protected_screen.json', 'proof_receipts_manifest.json']]
    return {name: HERE / 'results' / 'live_snap' / name for name in names}


def fetch(host):
    if host == 'snap':
        control = Path('/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control')
        if not control.is_socket():
            return {}, 'Authenticated control socket absent; no network login attempted.'
        command = ['ssh', '-S', str(control), '-o', 'BatchMode=yes', '-o',
                   'ProxyCommand=/usr/bin/false', 'eth127@skampere1.stanford.edu']
        root = '/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v21'
    else:
        command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'cactushacks-gx10']
        root = '/home/lethan3/workspace/rl4cv-gx10/experiment-v19'
    code = '''import pathlib,json,base64,hashlib,time
root=pathlib.Path(%r);out={}
for name in %r:
 p=root/name
 if p.is_file():
  raw=p.read_bytes()
  if len(raw)>10000000:raise RuntimeError('Unexpectedly large compact receipt: '+name)
  out[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),data=base64.b64encode(raw).decode())
rawpath=root/'validation'/%r/'raw.jsonl'
if rawpath.is_file():
 with rawpath.open('rb') as stream:count=sum(line.endswith(b'\\n') for line in stream)
 name='validation/'+%r+'/publication_generation_progress.json'
 raw=json.dumps(dict(completed_newline_rows=count,declared_cells=1080,observed_unix=time.time(),scope='Progress only; uniqueness, scoring and full-manifest verification are separate.')).encode()
 out[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),data=base64.b64encode(raw).decode())
print(json.dumps(out))
''' % (root, list(file_map(host)), 'v21_tiny', 'v21_tiny')
    try:
        raw = subprocess.check_output(command + ['python3 -c ' + shlex.quote(code)],
                                      stderr=subprocess.PIPE, timeout=45)
        return json.loads(raw), None
    except (subprocess.SubprocessError, OSError, ValueError) as error:
        return {}, type(error).__name__ + ': ' + str(error)[:180]


def collect():
    paths = []
    status = {'observed_unix': time.time(), 'hosts': {}}
    milestones = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(fetch, ['snap']))
    for host, (payload, error) in zip(['snap'], results):
        mapping = file_map(host)
        objects = {}
        for name, item in payload.items():
            assert name in mapping
            raw = base64.b64decode(item['data'])
            assert hashlib.sha256(raw).hexdigest() == item['sha256']
            if name.endswith('.json'):
                objects[name] = json.loads(raw)
            elif name.endswith('.csv'):
                rows = list(csv.reader(io.StringIO(raw.decode(), newline='')))
                output = io.StringIO(newline='')
                csv.writer(output, lineterminator='\n').writerows(rows)
                normalized = output.getvalue().encode()
                assert list(csv.reader(io.StringIO(normalized.decode(), newline=''))) == rows
                raw = normalized
            target = mapping[name]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            paths.append(target)
        label = 'v21_tiny'
        summary = objects.get('final/completion.json')
        progress = objects.get('progress.json', {})
        generated = objects.get('validation/' + label + '/publication_generation_progress.json', {})
        terminal = objects.get('terminal.json', {})
        status['hosts'][host] = dict(fresh=error is None, error=error, receipts=len(payload),
            production_host=objects.get('production_host.json'), progress=progress,
            generation_progress=generated, terminal=terminal, summary=summary)
        milestones.append((host, error is None, len(payload), progress.get('verified', 0) // 25,
                           terminal.get('status') or terminal.get('state'),
                           objects.get('completion.json', {}).get('state'),
                           generated.get('completed_newline_rows', 0) // 100,
                           summary.get('successes') if summary else None))
    target = HERE / 'results' / 'publication_status.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(status, indent=2) + '\n')
    paths.append(target)
    return paths, tuple(milestones), status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    previous = None
    while True:
        try:
            paths, mark, status = collect()
            publication.mirror(paths)
            if args.publish and mark != previous:
                publication.publish(paths)
                previous = mark
            print(json.dumps(status), flush=True)
        except Exception as error:
            print(json.dumps({'error': repr(error), 'observed_unix': time.time()}), flush=True)
            if not args.watch:
                raise
        if not args.watch:
            return
        time.sleep(120)


if __name__ == '__main__':
    main()
