"""TLDR: Run one launch-only maximum-length trainer forward/backward without an optimizer step."""
import time


def probe(worker, *, maximum_train_prompt, response_cap, admission_check, lease_check):
    """Use the actual admitted worker model, activation checkpointing and v4 filtered loss.

    Invoke only through the worker RPC at launch; never part of CPU preparation.
    It does not call train(), optimizer.step(), or scheduler.step().
    """
    admission_check(); lease_check()
    import torch
    from filtered_policy import support, filtered_logprobs
    from nemo_objective import FilteredClippedPGLossFn
    if response_cap!=12288:raise ValueError('retired response cap')
    length=maximum_train_prompt+response_cap
    device=next(worker.model.parameters()).device
    if device.type!='cuda':raise ValueError('maximum-length probe is launch-only on the admitted trainer GPU')
    torch.cuda.reset_peak_memory_stats(device)
    rng=torch.get_rng_state(); cuda_rng=torch.cuda.get_rng_state(device)
    was_training=worker.model.training
    started=time.monotonic()
    try:
        worker.model.train();worker.model.zero_grad(set_to_none=True)
        ids=torch.full((1,length),100,dtype=torch.long,device=device)
        output=worker.model(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False)
        logits=output.logits
        if hasattr(logits,'to_local'):
            if logits.device_mesh.size()!=1:raise ValueError('one-rank model required')
            logits=logits.to_local()
        data=synthetic_batch(logits,ids,maximum_train_prompt)
        loss,_=FilteredClippedPGLossFn()(logits.float()/.6,data,torch.tensor(1.,device=device),data['token_mask'].sum())
        loss.backward();torch.cuda.synchronize(device);lease_check()
        return {'probe_forward_backward':True,'probe_sequence_length':length,
                'peak_memory_bytes':torch.cuda.max_memory_allocated(device),
                'wall_seconds':time.monotonic()-started,'optimizer_steps':0}
    finally:
        worker.model.zero_grad(set_to_none=True);worker.model.train(was_training)
        torch.set_rng_state(rng);torch.cuda.set_rng_state(cuda_rng,device)


def synthetic_batch(logits,input_ids,prompt_length):
    """Build supported synthetic targets without mutating embedding indices saved for backward."""
    import torch
    from filtered_policy import support,filtered_logprobs
    length=input_ids.shape[1]
    if input_ids.shape[0]!=1 or not 1<=prompt_length<length:
        raise ValueError('one complete prompt/response sequence required')
    with torch.no_grad():
        old=support(logits[:,:-1]);targets=logits[:,:-1].argmax(-1)
        target_ids=input_ids.clone();target_ids[:,1:]=targets
        width=int(old.sum(-1).max())
        sparse=torch.zeros((1,length,width),dtype=torch.long,device=logits.device)
        mask=torch.zeros_like(sparse,dtype=torch.bool);mask[:,0,0]=True
        for pos in range(length-1):
            kept=old[0,pos].nonzero().flatten()
            sparse[0,pos+1,:len(kept)]=kept;mask[0,pos+1,:len(kept)]=True
        lp,_=filtered_logprobs(logits[:,:-1],old,targets)
        lp=torch.cat([torch.zeros_like(lp[:,:1]),lp],1)
    token_mask=torch.zeros((1,length),device=logits.device);token_mask[:,prompt_length:]=1
    return {'input_ids':target_ids,'token_mask':token_mask,'sample_mask':torch.ones(1,device=logits.device),
            'advantages':torch.ones((1,length),device=logits.device),'prev_logprobs':lp,'generation_logprobs':lp,
            'reference_policy_logprobs':torch.zeros_like(lp),'v4_support_ids':sparse,'v4_support_mask':mask}
