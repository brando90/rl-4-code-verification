"""TLDR: Request top-64 raw probabilities and retain full or reduced V4-A1 evidence."""
import math
from context_contract import validate_lengths
from filtered_policy import certificate


def sampling_kwargs(seed, terminal_token_ids):
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError('invalid fixed rollout seed')
    return {'n': 1, 'temperature': .6, 'top_p': .95, 'top_k': 20, 'min_p': 0.,
            'repetition_penalty': 1., 'presence_penalty': 0., 'frequency_penalty': 0.,
            'max_tokens': 12288, 'min_tokens': 0, 'ignore_eos': False, 'stop': None,
            'stop_token_ids': list(terminal_token_ids), 'seed': seed, 'logprobs': 64,
            'include_stop_str_in_output': True}


def validate_engine(config, context):
    validate_lengths(config['max_tokens'], config['max_model_len'], context, 'generator')
    if (config.get('dtype') != 'float16' or config.get('logprobs_mode') != 'raw_logprobs'
            or config.get('max_logprobs') != 64):
        raise ValueError('generator must return raw top-64 with S2 numerics')
    if config.get('vllm_version') != '0.10.0' or config.get('sampler_backend') != 'native':
        raise ValueError('unverified generator sampler implementation')


def extract_raw(output, *, vocab_size, full=True):
    """Reduce immediately for updates; preserve full top-64 only for T1/G0/T2 refit."""
    tokens = list(output.token_ids)
    if output.logprobs is None or len(output.logprobs) != len(tokens):
        raise ValueError('missing generation log-probabilities')
    rows = []
    for pos, (token, entries) in enumerate(zip(tokens, output.logprobs)):
        if token not in entries or not math.isfinite(float(entries[token].logprob)) or len(entries) < min(64, vocab_size):
            raise ValueError('incomplete top-64 raw receipt')
        # vLLM adds the sampled token to top-k. Sorting removes that extra entry
        # if it is outside top-64. Equal v64/v20 never receives a certificate.
        top = sorted(entries, key=lambda i: (-float(entries[i].logprob), i))[:min(64, vocab_size)]
        values = [float(entries[i].logprob) for i in top]
        cert = certificate(top, values, token, vocab_size=vocab_size)
        row = {'position': pos, 'token': token, 'sampled_raw_logprob': float(entries[token].logprob),
               **{k: cert[k] for k in ('top_k_certified', 'nucleus_certified', 'certified',
                                       'support_size', 'generator_logp', 'reason')}}
        if full:
            row.update(top_token_ids=top, top_raw_logprobs=values,
                       generator_support=cert['generator_support'])
        rows.append(row)
    return rows


def engine_kwargs(model, tokenizer, context):
    """Concrete pinned vLLM constructor fields, shared by the launch-only adapter."""
    config={'model':str(model),'tokenizer':str(tokenizer),'dtype':'float16','tensor_parallel_size':1,
            'max_model_len':context['engines']['generator']['context'],'max_logprobs':64,
            'logprobs_mode':'raw_logprobs','gpu_memory_utilization':.8,'enforce_eager':True,
            'max_num_seqs':32,'trust_remote_code':False,'enable_prefix_caching':False,
            'generation_config':'vllm','seed':1302100}
    validate_engine({**config,'max_tokens':12288,'vllm_version':'0.10.0','sampler_backend':'native'},context)
    return config
