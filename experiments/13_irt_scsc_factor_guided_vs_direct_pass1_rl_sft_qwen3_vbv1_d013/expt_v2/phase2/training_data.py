"""Build complete-group NeMo batches with explicit missing rewards and unchanged assistant token masks."""
from __future__ import annotations

import math


def validate_groups(groups,*,terminal_token_ids):
    """Validate every slot before tensor construction; never refill or remove a failed score."""
    if not 1<=len(groups)<=32:raise ValueError('an update requires 1 to 32 complete groups')
    seen=set()
    for group in groups:
        if group['group_index'] in seen or len(group['rows'])!=8:raise ValueError('duplicate or incomplete rollout group')
        seen.add(group['group_index'])
        for slot,row in enumerate(group['rows']):
            if row['split']!='train' or row['group_index']!=group['group_index'] or row['slot']!=slot:
                raise ValueError('held-out or misaligned training slot')
            if row['task_id']!=group['task_id']:raise ValueError('task changed within group')
            prompt=row['prompt_token_ids'];output=row['output_token_ids'];lp=row['generation_logprobs']
            if (not prompt or not output or len(output)>8192 or len(prompt)+len(output)>15945
                    or any(type(t) is not int or t<0 for t in prompt+output)):
                raise ValueError('invalid training token receipt')
            if any(t in terminal_token_ids for t in output[:-1]):raise ValueError('output continued after terminal token')
            if (row['finish_reason']=='length' and len(output)!=8192 or row['finish_reason']=='stop' and output[-1] not in terminal_token_ids
                    or row['finish_reason'] not in ('length','stop')):raise ValueError('unfrozen training stop condition')
            if len(lp)!=len(output) or any(v is None or not math.isfinite(v) or v>1e-6 for v in lp):
                raise ValueError('unsupported or misaligned behavior log probabilities')
            reward=row['reward']
            if reward is not None and (not math.isfinite(reward) or not 0<=reward<=1):raise ValueError('invalid observed reward')
        if any(row['prompt_token_ids']!=group['rows'][0]['prompt_token_ids'] for row in group['rows']):
            raise ValueError('prompt changed within the eight-response group')


def build(groups,*,pad_token_id,terminal_token_ids):
    """Use installed NeMo's leave-one-out baseline on group IDs, preserving repeated-task groups separately."""
    import torch
    from nemo_rl.algorithms.utils import calculate_baseline_and_std_per_prompt
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    validate_groups(groups,terminal_token_ids=terminal_token_ids)
    rows=[row for group in groups for row in group['rows']]
    usable=[all(row['reward'] is not None for row in group['rows']) for group in groups]
    # A missing score invalidates the group's advantage, not its token accounting.
    # None remains in the durable input; masked tensor placeholders are never reported as observed rewards.
    sample_mask=torch.tensor([float(ok) for ok in usable for _ in range(8)],dtype=torch.float32)
    rewards=torch.tensor([0. if row['reward'] is None else row['reward'] for row in rows],dtype=torch.float32)
    group_keys=torch.tensor([[i] for i in range(len(groups)) for _ in range(8)],dtype=torch.long)
    baseline,std=calculate_baseline_and_std_per_prompt(group_keys,rewards,sample_mask,leave_one_out_baseline=True)
    advantages=rewards-baseline
    selected=std>0;advantages[selected]/=std[selected]+1e-6
    advantages*=sample_mask
    for i,group in enumerate(groups):
        if usable[i] and len({row['reward'] for row in group['rows']})==1:
            advantages[i*8:(i+1)*8]=0.  # Preserve exact zero signal despite reduction roundoff.
    maximum=max(len(row['prompt_token_ids'])+len(row['output_token_ids']) for row in rows)
    input_ids=torch.full((len(rows),maximum),pad_token_id,dtype=torch.long)
    token_mask=torch.zeros((len(rows),maximum),dtype=torch.float32)
    generation_logprobs=torch.zeros_like(token_mask);token_advantages=torch.zeros_like(token_mask)
    lengths=[]
    for i,row in enumerate(rows):
        prompt=row['prompt_token_ids'];tokens=prompt+row['output_token_ids'];lengths.append(len(tokens))
        input_ids[i,:len(tokens)]=torch.tensor(tokens,dtype=torch.long)
        token_mask[i,len(prompt):len(tokens)]=1.
        generation_logprobs[i,len(prompt):len(tokens)]=torch.tensor(row['generation_logprobs'],dtype=torch.float32)
        token_advantages[i,len(prompt):len(tokens)]=advantages[i]
    data=BatchedDataDict({'input_ids':input_ids,'input_lengths':torch.tensor(lengths,dtype=torch.long),
        'token_mask':token_mask,'sample_mask':sample_mask,'generation_logprobs':generation_logprobs,
        'advantages':token_advantages,'reference_policy_logprobs':torch.zeros_like(token_mask)})
    counts={'declared_groups':len(groups),'declared_slots':len(rows),'measured_rewards':sum(row['reward'] is not None for row in rows),
        'usable_groups':sum(usable),'unmeasured_groups':len(groups)-sum(usable),
        'generated_tokens':sum(len(row['output_token_ids']) for row in rows),
        'prompt_tokens':sum(len(row['prompt_token_ids']) for row in rows),
        'optimized_tokens':int((token_mask*sample_mask[:,None]).sum()),
        'nonzero_advantage_slots':int((advantages!=0).sum()),'all_measured_advantages_zero':bool(sum(usable)>0 and (advantages==0).all()),
        'partial_batch_normalization':'actual unmasked assistant tokens across complete admitted groups',
        'all_zero_measured_batch':'advance installed optimizer/scheduler, recording zero policy-gradient signal',
        'all_missing_batch':'unmeasured update; no fabricated reward or optimizer call'}
    return data,counts
