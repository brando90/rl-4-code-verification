"""TLDR: Guard whole updates and isolate V4-A4's detached unit correction from observations."""
import math
import torch

class UncertifiedStop(RuntimeError):
    def __init__(self, report):
        self.report=report
        super().__init__('STOP_V4_A4: uncertified fraction exceeds 0.01')


def guard(data):
    """Called on the full single-rank update before any accumulation or optimizer call."""
    generated=data['token_mask'].bool()
    valid=generated & data['sample_mask'][:,None].bool()
    cert=data.get('v4_certified',torch.ones_like(generated)).bool()
    if cert.shape!=generated.shape:raise ValueError('misaligned certificates')
    n=int(generated.sum());v=int(valid.sum())
    if n==0 or v==0:raise ValueError('empty generated or actor denominator')
    u=int((generated & ~cert).sum());a=int((valid & ~cert).sum())
    report={'generated_positions':n,'valid_actor_tokens':v,'uncertified_generated_positions':u,
            'uncertified_actor_tokens':a,'uncertified_generated_fraction':u/n,
            'uncertified_actor_fraction':a/v,'certified_fraction':1-u/n,
            'threshold':.01,'aggregation':'entire update, all accumulation microbatches, one admitted rank',
            'empirical_bias':'unmeasured','gradient_bound':False}
    if u*100>n or a*100>v:raise UncertifiedStop(report)
    return report


def effective_behavior(data):
    old=data['prev_logprobs'];gen=data['generation_logprobs']
    cert=data.get('v4_certified',torch.ones_like(gen,dtype=torch.bool)).bool()
    active=data['token_mask'].bool() & data['sample_mask'][:,None].bool()
    if old.requires_grad or gen.requires_grad or not torch.isfinite(old[active]).all() or not torch.isfinite(gen[active & cert]).all():
        raise ValueError('old and certified behaviour log-probabilities must be detached and finite')
    # A fresh tensor is passed only to the parent's correction, with KL pinned zero.
    return torch.where(cert,gen,old.detach()).detach()


def diagnostics(data,current,global_valid_toks):
    """Additive bound numerator / global N; certified diagnostics use no imputed values."""
    mask=(data['token_mask'][:,1:]*data['sample_mask'][:,None]).bool().to(current.device)
    cert=data.get('v4_certified',torch.ones_like(data['token_mask'],dtype=torch.bool))[:,1:].bool().to(current.device)
    old=data['prev_logprobs'][:,1:].to(current.device)
    gen=data['generation_logprobs'][:,1:].to(current.device)
    adv=data['advantages'][:,1:].to(current.device)
    ratio=(current-old).exp()
    clipped=torch.maximum(-adv*ratio,-adv*ratio.clamp(.8,1.28))
    known=mask & cert;logw=(old-gen)[known]
    metrics={'v4_perturbation_bound':float(clipped[mask & ~cert].abs().sum()/global_valid_toks),
             'v4_certified_actor_tokens':int(known.sum()),
             'v4_actor_logweight_values':logw.detach().cpu().tolist()}
    if known.any():
        metrics['v4_entropy_numerator_certified_only']=float((-(current[known]-gen[known]).exp()*current[known]).sum())
        metrics['v4_probability_error_sum_certified_only']=float((current[known]-gen[known]).abs().sum())
    else:
        metrics['v4_entropy_numerator_certified_only']=0.
        metrics['v4_probability_error_sum_certified_only']=0.
    return metrics


def summarize(logweights):
    x=torch.as_tensor(logweights,dtype=torch.float64)
    return {'actor_logweight_certified_only':{'p01':float(x.quantile(.01)) if len(x) else None,
        'median':float(x.quantile(.5)) if len(x) else None,'p99':float(x.quantile(.99)) if len(x) else None,
        'clamp_rate':float((x>math.log(2)).double().mean()) if len(x) else None,'tokens':len(x)}}
