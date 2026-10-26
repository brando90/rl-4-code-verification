"""Collect compact public-source validation receipts from SNAP without changing Git or remote jobs."""
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import time

HERE=Path(__file__).resolve().parent
REMOTE='/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14/bulk_validation'
FILES=('freeze.json','controls.json','progress.json','row_results.csv','completion.json','watch_status.json','watch_completion.json','driver_history.json')


def main():
    script='import pathlib,json,base64; root=pathlib.Path('+repr(REMOTE)+'); names='+repr(FILES)+'; print(json.dumps({name:base64.b64encode((root/name).read_bytes()).decode() for name in names if (root/name).is_file()}))'
    output=subprocess.check_output(['ssh','-S','/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control',
        '-o','BatchMode=yes','-o','ConnectTimeout=10','eth127@skampere1.stanford.edu','python3 -c '+shlex.quote(script)],text=True,timeout=30)
    data={name:base64.b64decode(value) for name,value in json.loads(output).items()}
    freeze=json.loads(data['freeze.json']);assert freeze['declared']==729
    if 'row_results.csv' in data:
        rows=list(csv.DictReader(io.StringIO(data['row_results.csv'].decode())))
        assert len(rows)==729 and len({r['task_id'] for r in rows})==729
        assert all(r['training_admitted']=='False' for r in rows)
    results=HERE/'results';results.mkdir(exist_ok=True)
    for name,value in data.items():
        target=results/('bulk_'+name);tmp=target.with_suffix(target.suffix+'.tmp');tmp.write_bytes(value);tmp.replace(target)
    summary=dict(observed_unix=time.time(),remote=REMOTE,files={name:hashlib.sha256(value).hexdigest() for name,value in data.items()},
        remote_progress=json.loads(data.get('progress.json',b'{}')),training_admitted=0)
    (results/'bulk_sync.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary['remote_progress'],sort_keys=True))


if __name__=='__main__':main()
