"""Bootstrap paired pretraining-policy probes without treating budgets as independent samples."""
import json
import numpy as np
from scipy.stats import spearmanr, kendalltau
from .run import HERE, SCALES, read, write


def summarize(out=HERE/'results/pilot_v3',draws=2000):
    rows=[r for s in SCALES for r in read(out/f'{s}_probe.json')]
    envs=sorted({r['env'] for r in rows})
    rng=np.random.default_rng(1617)
    n=len(rows[0]['group_rewards'])
    ix={e:rng.integers(n,size=(draws,n)) for e in envs}
    rho_boot=[];h_boot=[];entropy_boot=[]
    for r in rows:
        rewards=np.array(r['group_rewards']);g=rewards.shape[1]
        mass=np.abs(rewards-(rewards.sum(1,keepdims=True)-rewards)/(g-1)).sum(1)
        mm=mass[ix[r['env']]]
        rho_boot.append(1e6*mm.mean(1)/(g*4))
        h_boot.append(mm.mean(1)**2/np.square(mm).mean(1))
        entropy_boot.append(np.array(r['entropy_per_prompt'])[ix[r['env']]].mean(1))
    x=np.log(np.array(rho_boot).T);yb=np.array(h_boot).T;eb=np.array(entropy_boot).T
    def pearson_batch(a,b):
        a=a-a.mean(1,keepdims=True);b=b-b.mean(1,keepdims=True)
        return (a*b).sum(1)/np.sqrt((a*a).sum(1)*(b*b).sum(1))
    result={}
    for scale in ['pooled',*SCALES]:
        indices=[i for i,r in enumerate(rows) if scale=='pooled' or r['scale']==scale]
        observed_x=np.log([rows[i]['rho'] for i in indices])
        result[scale]={}
        for key,boot in [('H',yb),('conditional_entropy_nats',eb)]:
            observed_y=[rows[i][key] for i in indices]
            bs=pearson_batch(x[:,indices],boot[:,indices])
            result[scale][key]={'pearson':float(np.corrcoef(observed_x,observed_y)[0,1]),
                               'lo':float(np.quantile(bs,.025)),'hi':float(np.quantile(bs,.975)),
                               'spearman':float(spearmanr(observed_x,observed_y).statistic),
                               'kendall':float(kendalltau(observed_x,observed_y).statistic),'n':len(indices)}
    write(out/'probe_statistics.json',{'correlations':result,'bootstrap_draws':draws,'seed':1617,
                                      'unit':'prompt groups resampled within environment, paired across model scales; fixed candidate pool'})
    gate=read(out/'gate.json')
    lines=['# Probe results: 16_toy_env_generation_ginc_hmm_rho_h_law Night 2','',
       '**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/ub9/e16-toy-env-generation/experiments/16_toy_env_generation_ginc_hmm_rho_h_law/expt_v2/results/pilot_v3/RESULTS_probes.md>','',
       f'**TLDR:** The original-law pooled coverage gate {"passes" if gate["passed"] else "fails"}. Conditional entropy is a different quantity and is reported separately.','',
       '| Scale | Coordinate | Pearson [95% bootstrap interval] | Spearman | Kendall | Cells |', '|---|---|---:|---:|---:|---:|']
    for scale,values in result.items():
        for key,v in values.items():
            lines.append(f'| {scale} | {key} | {v["pearson"]:.4f} [{v["lo"]:.4f}, {v["hi"]:.4f}] p-val=n/a | {v["spearman"]:.4f} | {v["kendall"]:.4f} | {v["n"]} |')
    lines+=['','Intervals: 2,000 resamples of 512 prompt groups within each fixed environment, paired across scales, seed 1617. They cover probe-prompt noise conditional on these starting checkpoints and candidates; they exclude pretraining and environment-family uncertainty. Spearman and Kendall are descriptive point estimates. No null-hypothesis test is used for these diagnostics. The user-chosen gate is absolute pooled Pearson correlation below 0.85 for log usable signal density versus the original law’s effective coverage H. Entropy uses eight sampled continuations per prompt scored by exact forward probabilities; it is not the law’s H. See the prospective protocol clarification for the distinction.','',
       '| Scale | Environment | rho | H | Four-token entropy (nats) | Mixed-group share |', '|---|---|---:|---:|---:|---:|']
    for r in rows: lines.append(f'| {r["scale"]} | {r["env"]} | {r["rho"]:.1f} | {r["H"]:.4f} | {r["conditional_entropy_nats"]:.4f} | {r["q_mixed_empirical"]:.4f} |')
    lines+=['','**TLDR-end:** [rl4cv: 16_toy_env_generation_ginc_hmm_rho_h_law] Probe measurements keep effective coverage and conditional entropy distinct; all 64 cells are preserved.']
    (out/'RESULTS_probes.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result['pooled']),flush=True)

if __name__=='__main__': summarize()
