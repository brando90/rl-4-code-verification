#!/usr/bin/env python3
"""Combine new and immutable reused test factors, reproduce version 1, and score the frozen matched-budget forecasts."""
from __future__ import annotations
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

EXP = Path(__file__).resolve().parents[1]
V1 = EXP.parent / 'expt_v1'
REPO = EXP.parents[2]
sys.path.insert(0, str(REPO / 'src'))
from rl4cv.forecast import verify_forecast
spec = importlib.util.spec_from_file_location('e08_v1_analysis', V1 / 'scripts/analyze_test.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
FACTORS = ('IC_tests', 'IC_proofs', 'fsc_compiled')
KEYS = (*FACTORS, 'kernel_binary')


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n')


def scalar_summary(values, indices):
    known = ~np.isnan(values)
    if not known.any():
        return dict(point=None, bootstrap95=None, n_known=0)
    means=[]
    for ix in indices:
        sample=values[ix]
        if not np.isnan(sample).all(): means.append(float(np.nanmean(sample)))
    return dict(point=float(np.nanmean(values)), bootstrap95=list(map(float,np.percentile(means,[2.5,97.5]))), n_known=int(known.sum()))


def pair(cells_a, cells_b, tasks, indices):
    A,ka=a.factor_arrays(cells_a,tasks); B,kb=a.factor_arrays(cells_b,tasks)
    shared=ka & kb
    K1=np.array([[cells_a[(t,k)]['kernel_binary'] for k in range(8)] for t in tasks], dtype=float)
    K2=np.array([[cells_b[(t,k)]['kernel_binary'] for k in range(8)] for t in tasks], dtype=float)
    kshared=~np.isnan(K1)&~np.isnan(K2)
    def diff(ix):
        sh=shared[ix].reshape(-1); ks=kshared[ix].reshape(-1)
        av=A[ix].reshape(-1,3); bv=B[ix].reshape(-1,3)
        sc=a.scsc_of(*av[sh].mean(axis=0))-a.scsc_of(*bv[sh].mean(axis=0)) if sh.any() else np.nan
        kernel=float((K1[ix].reshape(-1)[ks]-K2[ix].reshape(-1)[ks]).mean()) if ks.any() else np.nan
        return kernel,sc
    point=diff(np.arange(len(tasks))); boots=np.array([diff(ix) for ix in indices])
    metrics={}
    for j,key in enumerate(('kernel_binary','SCSC')):
        vals=boots[:,j]; vals=vals[~np.isnan(vals)]
        metrics[key]=dict(point=None if np.isnan(point[j]) else float(point[j]),bootstrap95=list(map(float,np.percentile(vals,[2.5,97.5]))) if len(vals) else None)
    bounds=[]
    for arr in [A,B]:
        bounds.append([a.scsc_of(*np.nan_to_num(arr,nan=value).reshape(-1,3).mean(axis=0)) for value in [0.,1.]])
    metrics['SCSC']['full_manifest_bounds']=[bounds[0][0]-bounds[1][1],bounds[0][1]-bounds[1][0]]
    metrics['kernel_binary']['full_manifest_bounds']=[float(np.nan_to_num(K1,nan=0.).mean()-np.nan_to_num(K2,nan=1.).mean()),float(np.nan_to_num(K1,nan=1.).mean()-np.nan_to_num(K2,nan=0.).mean())]
    return dict(n_shared_known_cells=int(shared.sum()),n_missing_pairs=int(shared.size-shared.sum()),kernel_missing_pairs=int(kshared.size-kshared.sum()),**metrics,p_val='n/a')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=EXP/'results/test_manifest_v2.json')
    args=parser.parse_args()
    forecast_path=EXP/'forecasts/e08v2_matched_step658_test.json'
    assert verify_forecast(forecast_path), 'Frozen forecast changed'
    manifest=json.loads(args.manifest.read_text()); forecast=json.loads(forecast_path.read_text())
    assert a.sha(forecast_path.read_text().rstrip('\n').encode())==manifest['forecast_sha256']
    ids=a.read_ids(V1/'results/split/vbv1_test_task_ids.txt')
    with (V1/'results/split/vbv1_split_manifest.csv').open() as f:
        core={r['task_id']:int(r['core']) for r in csv.DictReader(f)}
    scopes={'all':ids,'core':[t for t in ids if core[t]],'industryset':[t for t in ids if not core[t]]}
    rng=np.random.default_rng(0)
    indices={scope:rng.integers(0,len(tasks),size=(10000,len(tasks))) for scope,tasks in scopes.items()}
    old=json.loads((V1/'results/test_eval.json').read_text())
    systems=manifest['systems']+manifest['diagnostic_systems']; results={}; cells_by={}; rows=[]; regression={}
    for system in systems:
        label=system['label']; source=EXP if system['generation']=='new' else V1
        # Missing whole receipts remain explicit unknown cells, never zeros.
        path=source/f'results/ladder/{label}_test_cells.csv'
        if path.exists():
            cells=a.load_system(label,source/'results/ladder',source/'results/judge',ids)
            with path.open() as f:
                raw=list(csv.DictReader(f))
            identities=[(r['task_id'],int(r['sample_idx'])) for r in raw]
            assert len(identities)==len(set(identities)), f'Duplicate kernel cells: {label}'
            assert set(identities)<=set(cells), f'Extra kernel cells: {label}'
        else:
            cells={(t,k):{key:None for key in KEYS} for t in ids for k in range(8)}
        cells_by[label]=cells; per_scope={}
        for scope,tasks in scopes.items():
            arr,known=a.factor_arrays(cells,tasks)
            summary=a.summarize(arr,known,rng,indices[scope])
            if not known.any(): summary['point_common_cohort']={key:None for key in (*FACTORS,'SCSC')}
            kv=np.array([[cells[(t,k)]['kernel_binary'] for k in range(8)] for t in tasks],dtype=float)
            summary['kernel_binary_mean_pass_rate']=float(np.nanmean(kv)) if not np.isnan(kv).all() else None
            summary['kernel_binary_known_cells']=int((~np.isnan(kv)).sum())
            if system['generation']=='reused':
                assert summary==old['systems'][label]['scopes'][scope], f'Version 1 regression: {label}/{scope}'
            summary['kernel_binary_bootstrap95']=scalar_summary(kv,indices[scope])['bootstrap95']
            per_scope[scope]=summary
        if system['generation']=='reused': regression[label]='EXACT: every original scope field, factor, bound and interval'
        unknown=[f'{t}#{k}' for (t,k),c in cells.items() if any(c[key] is None for key in FACTORS)]
        results[label]=dict(system=system,scopes=per_scope,n_unknown_cells=len(unknown),unknown_cells=unknown)
        for (task,k),c in cells.items():
            rows.append(dict(system=label,size=system['size'],role=system['role'],matched=system in manifest['systems'],generation=system['generation'],task_id=task,sample_idx=k,core=core[task],known=all(c[key] is not None for key in FACTORS),**c))
    paired={}; trained={s['size']:s['label'] for s in manifest['systems'] if s['role']=='trained'}; base={s['size']:s['label'] for s in manifest['systems'] if s['role']=='base'}
    for size,label in trained.items():
        paired[size]={scope:dict(trained=label,base=base[size],**pair(cells_by[label],cells_by[base[size]],tasks,indices[scope])) for scope,tasks in scopes.items()}
    adjacent={}
    for small,big in [('1.7B','4B'),('4B','8B'),('8B','14B')]:
        adjacent[f'{big}-{small}']={scope:dict(larger=trained[big],smaller=trained[small],**pair(cells_by[trained[big]],cells_by[trained[small]],tasks,indices[scope])) for scope,tasks in scopes.items()}
    diagnostic={scope:pair(cells_by[trained['14B']],cells_by['test_sft_14B_f0p5'],tasks,indices[scope]) for scope,tasks in scopes.items()}
    out=dict(written_utc=a.stamp(),manifest_sha256=a.sha(args.manifest.read_bytes()),n_declared_matched_cells=14208,n_new_declared_cells=5328,scopes={s:len(t) for s,t in scopes.items()},bootstrap=dict(n_resamples=10000,seed=0,unit='task; eight samples together; one training run, not training-seed variation'),systems=results,paired_differences=paired,adjacent_size_differences=adjacent,diagnostic_14B_step658_minus_step334=diagnostic,reused_regression=regression,p_val='n/a')
    write(EXP/'results/test_eval_v2.json',out)
    with (EXP/'results/test_factor_cells_v2.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    scores={}
    F=forecast['forecasts']
    for label,prediction in F['F1_validation_level_carries_to_test']['predicted_test_kernel_binary_mean'].items():
        r=results[label]['scopes']['all']; ci=r['kernel_binary_bootstrap95']; complete=r['kernel_binary_known_cells']==1776
        scores[f'F1/{label}']=dict(prediction=prediction,observed=r['kernel_binary_mean_pass_rate'],bootstrap95=ci,verdict=('PASS' if ci[0]<=prediction<=ci[1] else 'FAIL') if complete else 'UNRESOLVED')
    for label,baseline in F['F2_sft_beats_base']['pairs'].items():
        size=results[label]['system']['size']; p=paired[size]['all']
        for metric in ['kernel_binary','SCSC']:
            complete=p['kernel_missing_pairs' if metric=='kernel_binary' else 'n_missing_pairs']==0
            ci=p[metric]['bootstrap95']; scores[f'F2/{label}/{metric}']=dict(**p[metric],verdict=('PASS' if ci[0]>0 else 'FAIL') if complete else 'UNRESOLVED')
    ordered=[trained[size] for size in ['1.7B','4B','8B','14B']]; values=[results[l]['scopes']['all']['point_common_cohort']['SCSC'] for l in ordered]
    complete=all(results[l]['n_unknown_cells']==0 for l in ordered)
    scores['F3']=dict(ordered_systems=ordered,observed=values,verdict=('PASS' if all(x<y for x,y in zip(values,values[1:])) else 'FAIL') if complete else 'UNRESOLVED')
    write(EXP/'results/forecast_evaluation_v2.json',dict(verified_forecast_sha256=manifest['forecast_sha256'],scores=scores,p_val='n/a'))
    print(json.dumps(dict(cells=len(rows),reused_regression=regression,unknown={l:r['n_unknown_cells'] for l,r in results.items()})))


if __name__=='__main__': main()
