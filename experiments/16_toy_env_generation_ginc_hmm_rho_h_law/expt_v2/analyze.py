"""Freeze held-out-scale choices and report complete Night 2 results with paired uncertainty."""
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr, kendalltau
from rl4cv.utility_model import Observation, fit_utility_model, RHO_H, RHO_ONLY, H_ONLY, BUDGET_SCALE_ONLY, pairwise_rank_accuracy
from rl4cv.forecast import freeze_forecast, verify_forecast
from .run import HERE, SCALES, STEPS, BATCH, GROUP, K, read, write, sha, specs

BUDGETS=[s*BATCH*GROUP*K for s in STEPS]
FEATURES=[RHO_H,RHO_ONLY,H_ONLY,BUDGET_SCALE_ONLY]

def training_rows(out):
    paths=sorted(p for s in ('n1','n2','n3') for p in out.glob(f'{s}_*_seed*.json'))
    rows=[r for p in paths for r in read(p)['rows']]
    expected={(s,e.name,seed,b) for s in ('n1','n2','n3') for e in specs(out) for seed in (0,1) for b in BUDGETS}
    actual={(r['scale'],r['env'],r['seed'],r['tokens']) for r in rows}
    if actual!=expected or len(rows)!=len(expected): raise ValueError(f'incomplete training matrix: {len(rows)}/288')
    return rows,paths

def observations(out,rows):
    probes={(s,r['env']):r for s in SCALES for r in read(out/f'{s}_probe.json')}
    params={s:read(out/f'{s}_meta.json')['n_params'] for s in SCALES}
    cells={}
    for r in rows: cells.setdefault((r['scale'],r['env'],r['tokens']),[]).append(r['utility'])
    return [Observation(params[s],e,b,float(np.mean(u)),probes[s,e]['rho'],probes[s,e]['H']) for (s,e,b),u in sorted(cells.items())]

def ties(values):
    top=max(values.values())
    return sorted(k for k,v in values.items() if v==top)

def freeze(out):
    if list(out.glob('n4_*_seed*.json')): raise RuntimeError('n4 outcomes already exist; cannot claim a prospective freeze')
    rows,paths=training_rows(out)
    obs=observations(out,rows)
    pp=read(out/'n4_probe.json')
    n4=read(out/'n4_meta.json')['n_params']
    reference=(read(out/'n1_meta.json')['n_params'],read(out/'n3_meta.json')['n_params'])
    forecasts={}
    for feat in FEATURES:
        m=fit_utility_model(obs,feat,ref_scales=reference)
        predictions={str(b):{p['env']:m.predict(n4,b,p['rho'],p['H']) for p in pp} for b in BUDGETS}
        forecasts[feat.name]={'coefficients':m.coefficients(),'C0':m.C0,'predictions':predictions,
                              'choices':{b:ties(values) for b,values in predictions.items()}}
    n3={e.name:float(np.mean([r['utility'] for r in rows if r['scale']=='n3' and r['env']==e.name])) for e in specs(out)}
    constant={'uniform-random':sorted(p['env'] for p in pp),'best-fixed-n3':ties(n3),
              'highest-pass-variance':ties({p['env']:p['pass_variance'] for p in pp}),
              'highest-mixed-share':ties({p['env']:p['q_mixed_empirical'] for p in pp})}
    for name,choice in constant.items(): forecasts[name]={'choices':{str(b):choice for b in BUDGETS}}
    receipt=freeze_forecast({'primary':'joint exact-match utility','train_scales':['n1','n2','n3'],
                            'train_cells':len(rows),'methods':forecasts,
                            'input_hashes':{p.name:sha(p) for p in paths+[out/f'{s}_probe.json' for s in SCALES]+[out/f'{s}_meta.json' for s in SCALES]}},out,'forecast_n4')
    print(json.dumps(receipt),flush=True)
    return receipt

def interval(x, samples):
    lo,hi=np.quantile(samples,[.025,.975])
    return {'estimate':float(x),'lo':float(lo),'hi':float(hi)}

def fmt(d, mult=1):
    return f'{d["estimate"]*mult:.4f} [{d["lo"]*mult:.4f}, {d["hi"]*mult:.4f}]'

def signflip(seed_values):
    v=np.asarray(seed_values)
    null=np.array([np.mean(v*np.array(sign)) for sign in itertools.product((-1,1),repeat=len(v))])
    return float((null >= v.mean()-1e-14).mean())

def report(out, draws=2000):
    forecast_path=out/'forecast_n4.json'
    if not verify_forecast(forecast_path): raise ValueError('forecast hash mismatch')
    forecast=read(forecast_path)
    for name,digest in forecast['input_hashes'].items():
        if sha(out/name)!=digest: raise ValueError(f'frozen input changed: {name}')
    rows=[r for s in SCALES for p in sorted(out.glob(f'{s}_*_seed*.json')) for r in read(p)['rows']]
    expected={(s,e.name,seed,b) for s in SCALES for e in specs(out) for seed in (0,1) for b in BUDGETS}
    actual={(r['scale'],r['env'],r['seed'],r['tokens']) for r in rows}
    if actual!=expected or len(rows)!=len(expected): raise ValueError(f'incomplete full matrix {len(rows)}/384')
    write(out/'cells.json',[{k:r[k] for k in ('scale','env','seed','tokens','utility','token_utility','last_train_kl')} for r in rows])
    envs=[e.name for e in specs(out)]
    lookup={(r['scale'],r['env'],r['seed'],r['tokens']):r for r in rows}
    start=np.array(read(out/'n4_meta.json')['start_target']['token_hits'])==K
    # A fixed common prompt set enables paired evaluation of every choice.
    hit=np.array([[[np.array(lookup['n4',e,s,b]['target']['token_hits'])==K for b in BUDGETS] for s in (0,1)] for e in envs],dtype=float)
    gain=hit-start[None,None,None,:]
    rng=np.random.default_rng(1616)
    methods=forecast['methods']; scores={}; bootstrap={}
    # Same seed and prompt resamples for all methods retain pairing.
    seed_idx=rng.integers(0,2,(draws,2))
    prompt_idx=rng.integers(0,len(start),(draws,len(start)))
    for name,m in methods.items():
        vals=np.stack([gain[[envs.index(e) for e in m['choices'][str(b)]],:,j,:].mean(0) for j,b in enumerate(BUDGETS)],1)
        boot=np.empty((draws,3))
        for d in range(draws): boot[d]=vals[seed_idx[d]][:,:,prompt_idx[d]].mean((0,2))
        bootstrap[name]=boot
        scores[name]=[{'tokens':b,'choices':m['choices'][str(b)],'utility':interval(vals[:,j].mean(),boot[:,j]),
                       'p_value':signflip(vals[:,j].mean(-1)), 'seed_means':vals[:,j].mean(-1).tolist(),
                       'regret':float(gain.mean((1,3))[:,j].max()-vals[:,j].mean())} for j,b in enumerate(BUDGETS)]
    differences={}
    for name in methods:
        if name=='rho-H':continue
        d=bootstrap['rho-H']-bootstrap[name]
        differences[name]=[{'tokens':b,'difference':interval(scores['rho-H'][j]['utility']['estimate']-scores[name][j]['utility']['estimate'],d[:,j]),
                            'p_value':signflip(np.array(scores['rho-H'][j]['seed_means'])-scores[name][j]['seed_means'])} for j,b in enumerate(BUDGETS)]
    # Prevalence clusters all correlated environments/budgets within each scale/seed.
    positives=np.array([[sum(lookup[s,e,seed,b]['utility']>0 for e in envs for b in BUDGETS)/48 for seed in (0,1)] for s in SCALES])
    prevalence_boot=np.array([np.mean([positives[i,rng.integers(0,2,2)].mean() for i in range(4)]) for _ in range(draws)])
    prevalence=interval(np.mean([r['utility']>0 for r in rows]),prevalence_boot)
    chosen=scores['rho-H'][-1]['utility']
    all_better=all(v[-1]['difference']['lo']>0 for k,v in differences.items() if k!='budget-scale-only')
    if prevalence['estimate']>=.3 and chosen['lo']>0 and all_better: verdict='MEANINGFUL POSITIVE TRANSFER'
    elif chosen['estimate']>0: verdict='TIE WITH BASELINES'
    else: verdict='NO ADVANTAGE'
    # Frozen prediction error: bootstrap candidate environments, retain all budgets together.
    obs=observations(out,[r for r in rows if r['scale']=='n4'])
    regressions={}
    for feat in FEATURES:
        preds=[methods[feat.name]['predictions'][str(int(o.budget))][o.env] for o in obs]
        err=np.array(preds)-[o.utility for o in obs]
        rmse=float(np.sqrt(np.mean(err**2)))
        rank=pairwise_rank_accuracy(obs,preds)
        boots=[]
        for _ in range(draws):
            picked=rng.choice(envs,len(envs),replace=True)
            ix=[i for e in picked for i,o in enumerate(obs) if o.env==e]
            boots.append(float(np.sqrt(np.mean(err[ix]**2))))
        regressions[feat.name]={'rmse':interval(rmse,boots),'rank_accuracy':rank,'mean_bias':float(err.mean()),
                                'predicted_mean':float(np.mean(preds)),'observed_mean':float(np.mean([o.utility for o in obs]))}
    summary={'verdict':verdict,'completed_cells':len(rows),'positive_cells':sum(r['utility']>0 for r in rows),'prevalence':prevalence,
             'positive_final_trajectories':sum(r['utility']>0 for r in rows if r['tokens']==BUDGETS[-1]),
             'scores':scores,'paired_differences':differences,'regressions':regressions,'bootstrap_draws':draws,'bootstrap_seed':1616}
    write(out/'analysis.json',summary)
    lines=['# Night 2 results: 16_toy_env_generation_ginc_hmm_rho_h_law', '',
           '**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/results/pilot_v3/RESULTS_night2.md>', '',
           f'**TLDR:** {verdict}. All 384 budget cells completed; {summary["positive_cells"]}/384 have strictly positive joint target utility.', '',
           f'Positive prevalence: {fmt(prevalence,100)} percent, p-val=n/a (descriptive; user threshold 30%). Final-budget positive trajectories: {summary["positive_final_trajectories"]}/128.', '',
           'Primary target is joint exact-match agreement with the sequential Bayes oracle over 4,000 common target prompts. Units below are percentage points. Intervals use 2,000 paired prompt/seed bootstrap draws (seed 1616), conditional on fixed pretraining checkpoints and frozen selections. Only two training seeds: intervals do not establish broad training robustness or cover forecast-selection uncertainty. One-sided exact seed sign-flip p-values test zero mean advantage; minimum attainable p-value is 0.25.', '',
           '| Budget | Method | Chosen environment(s) | Utility [95% interval] | p-val | Regret |', '|---:|---|---|---:|---:|---:|']
    for name,ss in scores.items():
        for v in ss: lines.append(f'| {v["tokens"]} | {name} | {", ".join(v["choices"])} | {fmt(v["utility"],100)} | {v["p_value"]:.3f} | {100*v["regret"]:.3f} |')
    lines+=['','## Paired advantage of Equation 7 at 51,200 tokens','','| Baseline | Difference [95% interval] | p-val |','|---|---:|---:|']
    for name,vs in differences.items():
        v=vs[-1];lines.append(f'| {name} | {fmt(v["difference"],100)} | {v["p_value"]:.3f} |')
    lines+=['','## Frozen prediction accuracy at n4','','| Features | RMSE [95% candidate bootstrap] | Pairwise rank accuracy | Mean bias (prediction minus observation) |','|---|---:|---:|---:|']
    for name,v in regressions.items():lines.append(f'| {name} | {fmt(v["rmse"],100)} p-val=n/a | {v["rank_accuracy"]:.4f} p-val=n/a | {100*v["mean_bias"]:+.3f} |')
    lines+=['','Candidate bootstrap treats the fixed candidates as a descriptive sampling population, preserving all budgets for each candidate; mixtures share components, so this is not evidence of independent environment-family replication. Pairwise rank accuracy has no inferential interval here (one frozen fit); it is descriptive. Raw per-prompt token hits and cell tables are committed beside this report. Forecast input hashes and the append-only ledger establish chronology.', '',
            '## n4 environment table at 51,200 tokens','','| Environment | Observed joint utility | Predicted utility | Token utility |','|---|---:|---:|---:|']
    for e in envs:
        rr=[lookup['n4',e,s,BUDGETS[-1]] for s in (0,1)]
        lines.append(f'| {e} | {100*np.mean([r["utility"] for r in rr]):+.3f} | {100*methods["rho-H"]["predictions"][str(BUDGETS[-1])][e]:+.3f} | {100*np.mean([r["token_utility"] for r in rr]):+.3f} |')
    lines+=['',f'**TLDR-end:** [rl4cv: 16_toy_env_generation_ginc_hmm_rho_h_law] Night 2 verdict: {verdict}; {summary["positive_cells"]}/384 positive budget cells.']
    (out/'RESULTS_night2.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('scores','paired_differences','regressions')}),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['freeze','report']);ap.add_argument('--out',type=Path,default=HERE/'results/pilot_v3')
    args=ap.parse_args()
    freeze(args.out) if args.stage=='freeze' else report(args.out)
