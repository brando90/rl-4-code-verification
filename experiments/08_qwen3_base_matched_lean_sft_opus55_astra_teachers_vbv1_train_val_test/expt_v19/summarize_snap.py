"""Apply the original V6/V12 binary analysis to the full SNAP V19 cohort."""
import json
import csv
from pathlib import Path
import sys
import numpy as np
RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training');ROOT=RUN/'corpus_training_v19';REPO=RUN/'repo';EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test');LABEL='v19_final_cleaned_snap'
sys.path[:0]=[str(REPO/'src'),str(REPO/EXP/'expt_v6')]
import analyze
from common import write

def main():
    ids=(REPO/EXP/'expt_v1/results/split/vbv1_validation_task_ids.txt').read_text().splitlines();folder=ROOT/'validation'/LABEL;analyze.RUN=ROOT
    raw=analyze.read(folder/'raw.jsonl');scored=analyze.collect(folder/'raw.jsonl',folder/'scores',LABEL);assert len(raw)==len(scored)==1080
    (folder/'scored.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in scored));result,vector=analyze.evaluate(LABEL,raw,scored,ids)
    draws=np.random.default_rng(0).integers(0,135,(10000,135));result.update(status='COMPLETE',success_rate_ci95=np.quantile(vector[draws].mean(axis=1),[.025,.975]).tolist(),target=.25,target_reached=result['successes']>=270,bootstrap_unit='135 tasks retaining8samples',formal_specification_coverage='not measured',test_split_evaluated=False,inference_backend='Original V6/V12 vLLM path',runtime='Original SNAP PyTorch2.7 runtime; actual identity separately bound',causal_limitations='Changed accepted row identities/lengths and unequal loss-token budget; not strict row/token-matched ablation')
    split={r['task_id']:r for r in csv.DictReader((REPO/EXP/'expt_v1/results/split/vbv1_split_manifest.csv').open())};groups={}
    for flag,name in [('1','core'),('0','industry')]:
        indices=[i for i,tid in enumerate(ids) if split[tid]['core']==flag];values=vector[indices];n=len(values);boot=np.random.default_rng(0).integers(0,n,(10000,n))
        groups[name]=dict(tasks=n,attempts=8*n,successes=round(float(values.sum()*8)),success_rate=float(values.mean()),task_bootstrap_ci95=np.quantile(values[boot].mean(axis=1),[.025,.975]).tolist(),interval_limitation='Allzero/allone task samples yield a degenerate percentile interval, not a probability bound' if len(set(values.tolist()))==1 else '')
    result['core_industry']=groups
    write(ROOT/'analysis'/f'{LABEL}_summary.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
