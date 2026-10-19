"""Mirror compact remote cleanup receipts and refresh the local live report without Git mutations."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import time

HERE=Path(__file__).resolve().parent
REMOTE='/lfs/skampere1/0/eth127/rl4cv_tiny_training/lean_corpus_v13'
FILES=['dispatch.json','manifest.json','progress.json','row_progress.csv','watch_heartbeat.json','guard_controls.json','saved_alternative_summary.json','checker_controls/completion.json','calibration/summary.json','completion.json','final/summary.json','final/row_results.csv','runtime_manifest.json','watch_error.json']

def once():
    code='import json,pathlib; root=pathlib.Path('+repr(REMOTE)+'); files='+repr(FILES)+'; print(json.dumps({name:(root/name).read_text() for name in files if (root/name).exists()}))'
    proc=subprocess.run(['ssh','-S','/Users/lethan3/Documents/veribench-projects/tmp/ssh-tiny-training/control','-o','BatchMode=yes','-o','ConnectTimeout=10','eth127@skampere1.stanford.edu','python3 -c '+shlex.quote(code)],capture_output=True,text=True,timeout=60,check=True)
    data=json.loads(proc.stdout);out=HERE/'results';out.mkdir(exist_ok=True)
    for name,text in data.items():
        path=out/name.replace('/','_');temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(text);temp.replace(path)
    progress=json.loads(data.get('progress.json','{}'));calibration=json.loads(data.get('calibration/summary.json','{}'));final=json.loads(data.get('final/summary.json','{}'))
    states=progress.get('states',{})
    report='''# V13 results: Explicit proof replacements for 2,585 original answers

**Doc link:** [Protocol](PROTOCOL.md)

**TLDR:** The first four Terra/high replacements passed full Lean/kernel, FILE/template and protected-overlap checks. The full remote CPU worker pool is active with shared budget reservations; every original row remains in the denominator.

## Latest measured snapshot

'''
    report+='| Measure | Observed |\n|---|---:|\n'
    for label,value in [('Declared answers',2585),('Original files parsed successfully','2585 / 2585'),('Parsed proof terms',100234),('Answers with targeted automation',2358),('No replacement needed',227),('Current kernel-verified replacements',progress.get('verified',0)),('Running',states.get('RUNNING',0)),('Pending',states.get('PENDING',0)),('Temporary budget holds',states.get('BUDGET_HOLD',0)),('Original fallback outcomes',states.get('FALLBACK',0)),('Calibration final FILE/template passes',calibration.get('replacements',0)),('Calibration protected exact / near',str(calibration.get('protected_exact',0))+' / '+str(calibration.get('protected_near',0))),('Settled ordinary-rate estimate USD',round(progress.get('base_rate_estimate_usd',0),4)),('Settled conservative ledger charge USD',round(progress.get('conservative_charge_usd',0),4)),('In-flight reserved USD',progress.get('reserved_usd',0)),('Second preapproved budget tranche active',progress.get('tranche2activated',False))]:
        report+=f'| {label} | {value} |\n'
    report+='\n'+f"Remote observation Unix time: `{progress.get('observed_unix','unknown')}`. API charges are configured-price estimates, not invoices.\n\n"
    if final:report+='## Frozen result\n\n```json\n'+json.dumps(final,indent=2)+'\n```\n\n'
    report+='''## What was checked

- All 2,585 original files parsed with the pinned Lean parser; exact proof-term ranges protect every unchanged implementation, statement, namespace and test input.
- First four real replacements passed the unmodified frozen kernel inspector, FILE extraction, Qwen chat template, 16,384-token cap and 764 protected-reference screens (zero exact/near hits).
- Positive/unsolved-negative kernel controls, automation rejection, implementation/native-test preservation, actual harmless-child usage termination and dead-driver recovery passed.
- The saved-proof search compared entire non-proof file contexts across all 2,585 originals; no interchangeable explicit saved proof was found.
- The initial parser attempt lacked imported environment extensions. Loading those extensions fixed it; no paid work used the failed extraction.

Full model/compiler logs and immutable candidate bytes remain on skampere1 under `lean_corpus_v13`. Compact progress, 2,585-row outcome tables and source/runtime manifests are mirrored in `results/`. Model-training comparisons are owned by V12; no training score is inferred from these teacher proof checks.
'''
    temp=HERE/'results.md.tmp';temp.write_text(report);temp.replace(HERE/'results.md')
    print(json.dumps(dict(states=states,verified=progress.get('verified'),final=final.get('state'))))
    return bool(final)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--watch',action='store_true');a=p.parse_args()
    while True:
        try:done=once()
        except Exception as exc:print(repr(exc),flush=True);done=False
        if not a.watch or done:break
        time.sleep(60)
