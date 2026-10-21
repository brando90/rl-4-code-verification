"""TLDR: Capture old-weight full logits through a v4 runtime hook and freeze sparse response supports."""
import torch
from filtered_policy import support, filtered_logprobs


def freeze_batch(logits, data, *, allow_outside=False):
    """Construct position-aligned old probabilities and supports before any training step."""
    if hasattr(logits,'to_local'):
        if logits.device_mesh.size()!=1:raise ValueError('one-rank logits required')
        logits=logits.to_local()
    targets=data['input_ids'][:,1:].to(logits.device)
    active=(data['token_mask'][:,1:]*data['sample_mask'][:,None]).to(logits.device).bool()
    if logits.shape[:2]!=data['input_ids'].shape:raise ValueError('trainer forward alignment changed')
    with torch.no_grad():
        keep=support(logits[:,:-1])
        # Inactive prompt/padding positions have finite dummy singleton distributions.
        keep[~active]=False
        keep.scatter_(-1,targets[...,None],keep.gather(-1,targets[...,None]) | ~active[...,None])
        outside=~keep.gather(-1,targets[...,None]).squeeze(-1)
        measured_targets=torch.where(outside,logits[:,:-1].argmax(-1),targets) if allow_outside else targets
        logp,discarded=filtered_logprobs(logits[:,:-1],keep,measured_targets)
        if allow_outside:logp=logp.masked_fill(outside,float('-inf'))
        widths=keep.sum(-1);width=int(widths.max())
        batch,length=data['input_ids'].shape
        ids=torch.zeros((batch,length,width),dtype=torch.long)
        valid=torch.zeros_like(ids,dtype=torch.bool);valid[:,0,0]=True
        for b in range(batch):
            for pos in range(length-1):
                kept=keep[b,pos].nonzero().flatten().cpu()
                ids[b,pos+1,:len(kept)]=kept;valid[b,pos+1,:len(kept)]=True
        old=torch.zeros((batch,length));old[:,1:]=logp.cpu()
        mass=torch.zeros_like(old);mass[:,1:]=discarded.cpu()
        return {'prev_logprobs':old,'v4_support_ids':ids,'v4_support_mask':valid,'v4_discarded_mass':mass}


def collect_old_support(worker,data,allow_outside=False):
    """Launch-only worker callable: hook the actual NeMo model during get_logprobs.

    The hook is removed in finally. No installed file is edited and the inherited
    unfiltered probabilities are deliberately discarded. Single-row calls keep
    output alignment explicit; caller invokes this before saving the replay batch.
    """
    if data['input_ids'].shape[0]!=1:raise ValueError('old support capture uses one sequence per call')
    from worker_hooks import install
    install(worker)
    captured=[]
    def capture(module,args,kwargs,output):
        values=output.logits if hasattr(output,'logits') else output['logits']
        captured.append(freeze_batch(values,data,allow_outside=allow_outside))
    handle=worker.model.register_forward_hook(capture,with_kwargs=True)
    try:
        worker.get_logprobs(data,micro_batch_size=1)
    finally:handle.remove()
    if len(captured)!=1:raise ValueError('expected exactly one full-sequence model forward')
    return captured[0]
