"""TLDR: Define the v4 raw-logprob sampler contract without constructing a generation engine."""
from context_contract import validate_lengths


def sampling_kwargs(seed,terminal_token_ids):
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('invalid fixed rollout seed')
    return {'n':1,'temperature':.6,'top_p':.95,'top_k':20,'min_p':0.,
            'repetition_penalty':1.,'presence_penalty':0.,'frequency_penalty':0.,
            'max_tokens':12288,'min_tokens':0,'ignore_eos':False,'stop':None,
            'stop_token_ids':list(terminal_token_ids),'seed':seed,'logprobs':20,
            'include_stop_str_in_output':True}


def validate_engine(config,context):
    validate_lengths(config['max_tokens'],config['max_model_len'],context,'generator')
    if config.get('dtype')!='float16' or config.get('logprobs_mode')!='raw_logprobs' or config.get('max_logprobs',0)<20:
        raise ValueError('generator must return raw top-20 with S2 numerics')
    if config.get('vllm_version')!='0.10.0' or config.get('sampler_backend')!='native':
        raise ValueError('unverified generator sampler implementation')


def extract_raw(output):
    """Preserve the sampled token and every raw returned entry; never pretend they certify support."""
    tokens=list(output.token_ids)
    if output.logprobs is None or len(output.logprobs)!=len(tokens):raise ValueError('missing generation log-probabilities')
    rows=[]
    for pos,(token,entries) in enumerate(zip(tokens,output.logprobs)):
        if token not in entries or len(entries)<20:raise ValueError('incomplete top-20 raw receipt')
        rows.append({'position':pos,'token':token,
                     'raw_logprobs':{str(k):float(v.logprob) for k,v in entries.items()},
                     'complete_topk_certified':False})
    return rows
