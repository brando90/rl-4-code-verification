"""Apply the unchanged pinned scorer and V6 non-vacuity/binary analysis to the complete native GX10 validation cohort."""
import argparse
import concurrent.futures
from dataclasses import asdict
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from common import ROOT,REPO,EXP,HERE,NATIVE,LAKE_BIN,FROZEN,clean_env,digest,write,run_stage

def check_frozen():
    scorer=REPO/'external/veribench_scorer'
    for relative,h in FROZEN.items():assert digest(scorer/relative)==h,relative
    toolchain=(NATIVE/'mathlib4/lean-toolchain').read_text().strip()
    assert toolchain=='leanprover/lean4:v4.22.0',toolchain
    revision=subprocess.check_output(['git','-C',str(NATIVE/'mathlib4'),'rev-parse','HEAD'],text=True).strip()
    assert revision=='79e94a093aff4a60fb1b1f92d9681e407124c2ca',revision
    return dict(frozen_scorer_sha256=FROZEN,lean_toolchain=toolchain,mathlib_revision=revision,lake_wrapper_sha256=digest(LAKE_BIN/'lake'))

def controls():
    evidence=check_frozen();os.environ.update(clean_env(''))
    path=REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py'
    spec=importlib.util.spec_from_file_location('gx19_pinned_kernel',path);kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
    cases=[('positive','import Mathlib\ntheorem gx19Positive (a b : Nat) : a+b=b+a := by exact Nat.add_comm a b\nexample : 1+1=2 := by native_decide\n',True),('sorry','import Mathlib\ntheorem gx19Sorry : False := by sorry\n',False),('axiom','import Mathlib\naxiom gx19Fake : False\ntheorem gx19Axiom : False := by exact gx19Fake\n',False),('named_native','import Mathlib\ntheorem gx19Native : (1:Nat)+1=2 := by native_decide\n',False)]
    records=[]
    for name,source,wanted in cases:
        folder=ROOT/'controls/kernel'/name;folder.mkdir(parents=True,exist_ok=True);sourcepath=folder/'Solution.lean';sourcepath.write_text(source)
        report=asdict(kernel.check_file(str(sourcepath),str(NATIVE/'mathlib4'),timeout=60,allow_native_decide=False,keep_dir=str(folder/'kernel')))
        write(folder/'kernel_report.json',report);accepted=bool(kernel.valid_report(report) and report['n_theorems']>=1 and report['n_honest']==report['n_theorems'] and report['source_sha256']==digest(sourcepath))
        assert accepted==wanted,(name,report)
        records.append(dict(name=name,expected=wanted,accepted=accepted,source_sha256=digest(sourcepath)))
    result=dict(evidence,status='PASS',controls=records,observed_unix=time.time());write(ROOT/'controls/kernel_controls.json',result);print(json.dumps(result),flush=True)

def check_generation(label):
    rawpath=ROOT/'validation'/label/'raw.jsonl';raw=[json.loads(s) for s in rawpath.read_text().splitlines()]
    ids=(REPO/EXP/'expt_v1/results/split/vbv1_validation_task_ids.txt').read_text().splitlines();wanted={(tid,k) for tid in ids for k in range(8)}
    assert len(raw)==len({(r['task_id'],r['sample_idx']) for r in raw})==len(wanted)==1080
    assert {(r['task_id'],r['sample_idx']) for r in raw}==wanted
    old=json.loads((ROOT/'evaluation/validation_preflight.json').read_text());assert old['status']=='PASS'
    for row in raw:
        assert all(row[k]==v for k,v in old['prompts'][row['task_id']].items())
        want=dict(temperature=.6,top_p=.95,top_k=20,max_tokens=12288,seed=91*100003+row['sample_idx'],thinking='on',stop_tokens=['<|im_end|>'])
        assert row['sampling']==want,(row['task_id'],row['sample_idx'],'sampling changed')
    result=dict(status='PASS',cells=1080,raw_sha256=digest(rawpath),test_split_evaluated=False);write(rawpath.parent/'generation_verified.json',result)
    return ids

def summarize(label):
    import numpy as np
    check_frozen();ids=check_generation(label)
    os.environ['TINY_RUN_ROOT']=str(ROOT);sys.path[:0]=[str(REPO/'src'),str(REPO/EXP/'expt_v6')]
    import analyze as old
    old.RUN=ROOT;folder=ROOT/'validation'/label
    scored=old.collect(folder/'raw.jsonl',folder/'scores',label)
    (folder/'scored.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in scored))
    result,vector=old.evaluate(label,old.read(folder/'raw.jsonl'),scored,ids)
    draws=np.random.default_rng(0).integers(0,135,(10000,135));result['success_rate_ci95']=np.quantile(vector[draws].mean(axis=1),[.025,.975]).tolist()
    result.update(status='COMPLETE',target=.25,target_reached=result['successes']>=270,bootstrap_unit='task retaining all8samples',bootstrap_draws=10000,seed=0,p_value=None,formal_specification_coverage='not measured',test_split_evaluated=False,inference_backend='Transformers GPU fallback; differs from V12vLLM unless actual runtime says otherwise',training_runtime_change='GX10/PyTorch2.9 versus A100/PyTorch2.7; not a data-only causal ablation')
    import csv
    split={r['task_id']:r for r in csv.DictReader((REPO/EXP/'expt_v1/results/split/vbv1_split_manifest.csv').open())};groups={}
    for flag,name in [('1','core'),('0','industry')]:
        indices=[i for i,tid in enumerate(ids) if split[tid]['core']==flag];values=vector[indices];n=len(values);boot=np.random.default_rng(0).integers(0,n,(10000,n))
        groups[name]=dict(tasks=n,attempts=8*n,successes=round(float(values.sum()*8)),success_rate=float(values.mean()),task_bootstrap_ci95=np.quantile(values[boot].mean(axis=1),[.025,.975]).tolist(),interval_limitation='Allzero/allone task samples produce a degenerate percentile interval; not a probability bound.' if len(set(values.tolist()))==1 else '')
    result['core_industry']=groups;write(ROOT/'analysis'/f'{label}_summary.json',result);print(json.dumps(result),flush=True)

def score(label):
    check_frozen();assert json.loads((ROOT/'controls/kernel_controls.json').read_text())['status']=='PASS';check_generation(label)
    env=clean_env('');run_stage(label,'materialize',[sys.executable,'-m','rl4cv.veribench.jobs','--gen',str(ROOT/'validation'/label/'raw.jsonl'),'--out-root',str(ROOT/'validation'/label/'jobs'),'--name',label],env,600)
    scorer=REPO/'external/veribench_scorer'
    def one(sample):
        cmd=[sys.executable,str(scorer/'experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py'),'--job-dir',str(ROOT/'validation'/label/'jobs'/f'{label}_s{sample}'),'--pack',str(ROOT/'validation_pack'),'--name',f'{label}_s{sample}','--gold-dir',str(scorer/'veribench_dataset/lean_src/veribench'),'--lake-dir',str(NATIVE/'mathlib4'),'--skip-tc','--out-dir',str(ROOT/'validation'/label/'scores'/f'{label}_s{sample}')]
        return run_stage(label,f'score_{sample}',cmd,env,24*3600)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(one,range(8)))
    summarize(label)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['controls','run','summarize']);parser.add_argument('--label',default='v19_final_cleaned_gx10');args=parser.parse_args()
    controls() if args.mode=='controls' else score(args.label) if args.mode=='run' else summarize(args.label)
