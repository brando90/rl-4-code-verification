"""TLDR: Migrate every policy length and sampler field while preserving the inherited S2 optimizer."""
import copy
from context_contract import validate_lengths

OPTIMIZER={'name':'torch.optim.AdamW','kwargs':{'lr':1e-6,'betas':[.9,.999],'eps':1e-8,
            'weight_decay':.01,'foreach':False,'fused':False}}


def validate(policy,context):
    generation=policy['generation'];engine=generation['vllm_cfg']
    validate_lengths(generation['max_new_tokens'],engine['max_model_len'],context,'generator')
    validate_lengths(generation['max_new_tokens'],policy['max_total_sequence_length'],context,'trainer')
    if any(generation.get(k)!=v for k,v in {'temperature':.6,'top_p':.95,'top_k':20,
            'stop_token_ids':[151643,151645],'eos_token_id':151643,'pad_token_id':151643}.items()):
        raise ValueError('sampler or terminal contract changed')
    if policy['optimizer']!=OPTIMIZER or policy['precision']!='float16' or engine['precision']!='float16':
        raise ValueError('S2 optimizer or numerics changed')
    if (policy['train_global_batch_size']!=256 or policy['train_micro_batch_size']!=1 or policy['max_grad_norm']!=1.
            or policy['logprob_batch_size']!=1 or policy['generation_batch_size']!=32):
        raise ValueError('frozen batching or gradient clipping changed')
    d=policy['dtensor_cfg']
    if (not d['enabled'] or d['_v2'] is not False or d['tensor_parallel_size']!=1 or d['context_parallel_size']!=1
            or not d['activation_checkpointing'] or not d['cpu_offload'] or policy['megatron_cfg']['enabled']
            or policy['dynamic_batching']['enabled'] or policy['sequence_packing']['enabled']
            or engine['tensor_parallel_size']!=1 or engine['enforce_eager'] is not True):
        raise ValueError('frozen single-device training topology changed')
    if policy['scheduler']!={'name':'torch.optim.lr_scheduler.ConstantLR','kwargs':{'factor':1.,'total_iters':10**10}}:
        raise ValueError('constant learning-rate scheduler changed')


def derive(source,context):
    result=copy.deepcopy(source)
    result['generation'].update(temperature=.6,top_p=.95,top_k=20,max_new_tokens=12288)
    result['generation']['vllm_cfg']['max_model_len']=context['engines']['generator']['context']
    result['max_total_sequence_length']=context['engines']['trainer']['context']
    validate(result,context)
    return result
