"""Summarize the complete fixed validation manifest using the existing binary-success definition."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys
from assemble import HERE,ROOT,write

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--condition',default='base');args=parser.parse_args()
    sys.path.insert(0,str(HERE.parent/'expt_v6'))
    import analyze
    import numpy as np
    label='v23_'+args.condition;folder=ROOT/'validation'/label
    ids=(HERE.parent/'expt_v1/results/split/vbv1_validation_task_ids.txt').read_text().splitlines()
    scored=analyze.collect(folder/'raw.jsonl',folder/'scores',label)
    (folder/'scored.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in scored))
    # Existing evaluation writes per-cell/per-task tables in its RUN/analysis directory.
    analyze.RUN=ROOT;results,vector=analyze.evaluate(label,analyze.read(folder/'raw.jsonl'),scored,ids)
    draws=np.random.default_rng(0).integers(0,135,(10000,135))
    results['success_rate_ci95']=np.quantile(vector[draws].mean(axis=1),[.025,.975]).tolist()
    results.update(status='COMPLETE',test_split_opened=False,formal_specification_coverage='not measured',target=0.25,target_metric='success_rate; same per-attempt binary criterion as V6',target_reached=bool(float(vector.mean())>=.25),bootstrap_unit='task retaining all eight samples',p_value=None)
    write(ROOT/'analysis'/f'{label}_summary.json',results);print(json.dumps(results),flush=True)

if __name__=='__main__':main()
