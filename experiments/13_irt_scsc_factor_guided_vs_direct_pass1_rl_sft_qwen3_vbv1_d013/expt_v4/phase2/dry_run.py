"""TLDR: Exercise v4 command-line stage order, six trajectories, crash recovery and a no-resampling stop on CPU."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from common import digest, write_new
from stage_ledger import read
from runner import STAGES


def run(root,admission):
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='':raise ValueError('CUDA_VISIBLE_DEVICES must be empty')
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    runner=Path(__file__).with_name('runner.py');commands=[]
    def call(stage,scenario,extra=(),expected=0):
        argv=[sys.executable,str(runner),stage,'--work',str(root/scenario),
              '--admission',str(admission),'--engine','stub',*extra]
        p=subprocess.run(argv,capture_output=True,text=True,timeout=300)
        name=f'{len(commands):02d}_{scenario}_{stage}'
        (root/(name+'.stdout')).write_text(p.stdout);(root/(name+'.stderr')).write_text(p.stderr)
        commands.append({'argv':argv,'returncode':p.returncode,'expected':expected,'log':name})
        if p.returncode!=expected:raise RuntimeError(f'dry-run command failed: {name}: {p.stderr[-1000:]}')
        return p
    call('G0_GENERATE','order',expected=1)
    call('sequence','full')
    call('T1','crash',('--crash','probe'),expected=1)
    call('T1','crash',('--recover',))
    call('sequence','stop',('--no-signal',))
    call('T3','stop',expected=1)
    receipts={stage:{'path':str(root/'full'/stage/'receipt.json'),
                     'sha256':digest(root/'full'/stage/'receipt.json'),
                     'status':read(root/'full'/stage/'receipt.json')['status']} for stage in STAGES}
    rows=read(root/'full/PILOT30/receipt.json')['result']['rows']+read(root/'full/PILOT60/receipt.json')['result']['rows']
    summary={'tldr':'Synthetic CPU stage sequence, extension, order rejection, crash recovery, and no-signal stop verified.',
             'synthetic':True,'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],
             'admission_sha256':digest(admission),'commands':commands,'stage_receipts':receipts,
             'synthetic_completed_updates':len(rows),'real_optimizer_steps':0,'model_generations':0,'gpu_allocations':0,
             'trajectories':sorted({f"{r['arm']}/{r['seed']}" for r in rows}),
             'T5_30':read(root/'full/T5_30/receipt.json')['result']['decision']['action'],
             'T5_60':read(root/'full/T5_60/receipt.json')['result']['decision']['action'],
             'T2_no_signal':read(root/'stop/T2/receipt.json')['status'],
             'crash_attempts':len(list((root/'crash/T1/probe').glob('attempt_*'))),
             'api_spend_usd':0,'is_gate_evidence':False}
    write_new(root/'summary.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--admission',type=Path,required=True);a=p.parse_args()
    result=run(a.root,a.admission)
    print(json.dumps({k:v for k,v in result.items() if k not in ('commands','stage_receipts')}))
