"""Collect the latest V14 admission pointer and compact complete-cohort receipts without moving raw training data."""
import base64
import json
from pathlib import Path
import shlex
import subprocess

HERE=Path(__file__).resolve().parent
ROOT='/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14'


def main():
    code='''import pathlib,json,base64
root=pathlib.Path(ROOT_PATH)
pointer=json.loads((root/'latest_admission.json').read_text());folder=root/pointer['version']
files={'latest_admission.json':root/'latest_admission.json','admission_completion.json':folder/'completion.json',
 'admission_freeze.json':folder/'freeze.json','admission_row_results.csv':folder/'row_results.csv',
 'admission_v1_superseded.json':root/'admission_v1/superseded.json'}
result={name:base64.b64encode(path.read_bytes()).decode() for name,path in files.items()}
screens=json.loads((folder/'protected_screen.json').read_text())
summary={kind:{k:v for k,v in screens[kind].items() if k!='clean_ids'} for kind in ['full','statements']}
result['admission_protected_screen_summary.json']=base64.b64encode((json.dumps(summary,indent=2,sort_keys=True)+'\\n').encode()).decode()
print(json.dumps(result))
'''.replace('ROOT_PATH',repr(ROOT))
    out=subprocess.check_output(['ssh','-S','/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control',
        '-o','BatchMode=yes','-o','ConnectTimeout=10','eth127@skampere1.stanford.edu','python3 -c '+shlex.quote(code)],text=True,timeout=30)
    results=HERE/'results';results.mkdir(exist_ok=True)
    for name,value in json.loads(out).items():(results/name).write_bytes(base64.b64decode(value))
    print((results/'latest_admission.json').read_text())


if __name__=='__main__':main()
