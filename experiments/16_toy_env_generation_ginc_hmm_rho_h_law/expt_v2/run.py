"""Resumable CPU Night 2 stages; gate probes before GRPO and freeze predictions before n4."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import torch
from .ginc import BASE, TARGET, K, SETTINGS, EnvSpec, Mixture, make_prompts, pretraining_docs, propose_mixtures, rewards
from .policy import SCALES, TinyLM, pretrain, generate, grpo
from rl4cv.experience import Response, measure_environment
from rl4cv.forecast import freeze_forecast, verify_forecast

HERE = Path(__file__).resolve().parent
PRETRAIN_STEPS = dict(zip(SCALES, (2000,2500,3000,4000)))
STEPS = [25,50,100]
BATCH, GROUP = 16,8
TARGET_N, PROBE_N, POOL_N = 4000,512,20000

def write(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_model(out, scale):
    model=TinyLM(*SCALES[scale])
    if sha(out/f'start_{scale}.pt') != read(out/f'{scale}_meta.json')['checkpoint_sha256']:
        raise RuntimeError('starting checkpoint hash mismatch')
    model.load_state_dict(torch.load(out/f'start_{scale}.pt',weights_only=True,map_location='cpu'))
    return model

def evaluate(model, prompts):
    a = generate(model,prompts.x,greedy=True)[:,0]
    hits = (a == prompts.y).sum(1)
    return {'joint':float((hits==K).mean()), 'token':float(hits.mean()/K), 'token_hits':hits.tolist()}

def probe(model, spec, scale):
    p=make_prompts(spec,PROBE_N,11,entropy=True)
    a=generate(model,p.x,GROUP,torch.Generator().manual_seed(5))
    r,joint=rewards(a,p.y)
    m=measure_environment([[Response(float(v),K,True) for v in row] for row in r])
    return {'scale':scale,'env':spec.name, 'spec':spec.to_dict(), **m.to_dict(),
            'group_rewards':r.tolist(), 'entropy_per_prompt':p.entropy_mc.tolist(),
            'joint_success':float(joint.mean()), 'pass_variance':float(joint.var(1).mean()),
            'reward_variance':float(r.var(1).mean()),'conditional_entropy_nats':float(p.entropy_mc.mean()),
            'oracle_sequence_logprob':float(p.oracle_logprob.mean())}

def specs(out):
    ms=[]
    for d in read(out/'mixtures.json')['mixtures']:
        ms.append(Mixture(d['name'],tuple(EnvSpec(**c) for c in d['components']),tuple(d['weights'])))
    return BASE+ms

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=['pretrain','base-probe','mixtures','probe','gate','rl'])
    ap.add_argument('--out',type=Path,default=HERE/'results/pilot_v3')
    ap.add_argument('--scale',choices=SCALES)
    ap.add_argument('--env',type=int)
    ap.add_argument('--seed',type=int,choices=[0,1])
    args=ap.parse_args()
    out=args.out; out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(1); torch.set_num_interop_threads(1)
    torch.manual_seed(1234)
    started=time.time()
    stage,scale=args.stage,args.scale
    if stage=='pretrain':
        if (out/f'{scale}_meta.json').exists():
            print(f'{scale} pretrain already complete',flush=True); return
        model=TinyLM(*SCALES[scale])
        docs=pretraining_docs(200000,32,7,SETTINGS,64)
        loss=pretrain(model,docs,PRETRAIN_STEPS[scale])
        path=out/f'start_{scale}.pt'; torch.save(model.state_dict(),path)
        baseline=evaluate(model,make_prompts(TARGET,TARGET_N,99))
        write(out/f'{scale}_meta.json',{'scale':scale,'n_params':model.n_params(),'steps':PRETRAIN_STEPS[scale],
              'last50_loss':float(np.mean(loss[-50:])),'start_target':baseline,'checkpoint_sha256':sha(path),
              'seconds':time.time()-started,'torch':torch.__version__,'numpy':np.__version__,'device':'cpu'})
    elif stage in ('base-probe','probe'):
        model=load_model(out,scale)
        candidates=BASE if stage=='base-probe' else specs(out)
        dest=out/f'{scale}_{stage}.json'
        if dest.exists(): print(f'{dest} exists',flush=True); return
        rows=[]
        for spec in candidates:
            row=probe(model,spec,scale); rows.append(row)
            print(f'{scale} {spec.name} rho={row["rho"]:.1f} H={row["H"]:.4f} entropy={row["conditional_entropy_nats"]:.4f}',flush=True)
        write(dest,rows)
    elif stage=='mixtures':
        if (out/'mixtures.json').exists(): return
        rows=read(out/'n3_base-probe.json')
        mix=propose_mixtures(rows)
        freeze_forecast({'source':'n3 start-policy probes only; no RL outcomes',
                         'mixtures':[m.to_dict() for m in mix]},out,'mixtures')
    elif stage=='gate':
        rows=[r for s in SCALES for r in read(out/f'{s}_probe.json')]
        values={}
        for name, rr in [('pooled',rows)]+[(s,[r for r in rows if r['scale']==s]) for s in SCALES]:
            lr=np.log([r['rho'] for r in rr])
            values[name]={'n':len(rr),'logrho_H':float(np.corrcoef(lr,[r['H'] for r in rr])[0,1]),
                          'logrho_entropy':float(np.corrcoef(lr,[r['conditional_entropy_nats'] for r in rr])[0,1])}
        passed=abs(values['pooled']['logrho_H'])<.85
        entropy_passed=all(abs(v['logrho_entropy'])<.85 for v in values.values())
        receipt={'passed':passed,'coverage_passed':passed,'entropy_passed':entropy_passed,
                 'threshold':.85,'gate_metric':'pooled log rho versus original Equation 7 effective coverage H; see protocol clarification','correlations':values,'probe_hashes':{s:sha(out/f'{s}_probe.json') for s in SCALES}}
        if not (out/'gate.json').exists(): freeze_forecast(receipt,out,'gate')
        print(json.dumps(receipt),flush=True)
        if not receipt['passed']: raise SystemExit('Decorrelation gate failed: no GRPO admitted.')
    elif stage=='rl':
        if not verify_forecast(out/'gate.json') or not read(out/'gate.json')['passed']:
            raise RuntimeError('GRPO requires the frozen decorrelation gate to pass')
        if any(read(out/'gate.json')['probe_hashes'][s]!=sha(out/f'{s}_probe.json') for s in SCALES):
            raise RuntimeError('probe inputs changed since gate')
        if scale=='n4' and not verify_forecast(out/'forecast_n4.json'):
            raise RuntimeError('n4 requires a frozen forecast')
        spec=specs(out)[args.env]
        dest=out/f'{scale}_{spec.name}_seed{args.seed}.json'
        if dest.exists(): print(f'{dest} already complete',flush=True); return
        model=load_model(out,scale)
        ref=deepcopy(model).eval()
        for p in ref.parameters(): p.requires_grad_(False)
        target=make_prompts(TARGET,TARGET_N,99)
        pool=make_prompts(spec,POOL_N,13)
        held=make_prompts(spec,512,12)
        baseline=read(out/f'{scale}_meta.json')['start_target']
        def ev(m):
            return {'target':evaluate(m,target),'env_metrics':evaluate(m,held)}
        curve=grpo(model,ref,pool,max(STEPS),STEPS,ev,args.seed,batch=BATCH,group=GROUP,lr=1e-4,kl_coef=1.)
        rows=[]
        for step,v in curve.items():
            rows.append({'scale':scale,'env':spec.name,'seed':args.seed,'step':step,
                         'tokens':step*BATCH*GROUP*K,'utility':v['target']['joint']-baseline['joint'],
                         'token_utility':v['target']['token']-baseline['token'],**v})
        write(dest,{'start_checkpoint_sha256':sha(out/f'start_{scale}.pt'),'rows':rows,'seconds':time.time()-started})
        print(f'{scale} {spec.name} seed={args.seed} joint_U={rows[-1]["utility"]:+.5f} token_U={rows[-1]["token_utility"]:+.5f} seconds={time.time()-started:.1f}',flush=True)
    print(f'{stage} {scale} done seconds={time.time()-started:.1f}',flush=True)

if __name__=='__main__': main()
