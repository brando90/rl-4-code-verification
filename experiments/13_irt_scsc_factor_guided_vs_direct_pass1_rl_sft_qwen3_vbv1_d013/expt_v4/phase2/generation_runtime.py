"""TLDR: Construct the pinned top-64 generator only after admission and a device lease; retain every response."""
import importlib.metadata
import os
from pathlib import Path
from admission import check_admission
from common import digest, write_new
from device_guard import check
from effect_receipts import mark
from generation_contract import engine_kwargs, sampling_kwargs, extract_raw


def generate(config, cells, *, root, full, receipt=True):
    """Launch-only primitive; stage orchestration must provide frozen train cells and model bindings."""
    admission=check_admission(config['admission'],require_launch=True)
    check(config)
    if importlib.metadata.version('vllm')!='0.10.0':raise ValueError('pinned vLLM version changed')
    allowed=set(Path(config['train_ids']).read_text().splitlines())
    if not cells or len(cells)>1024 or len({c['cell_id'] for c in cells})!=len(cells):
        raise ValueError('complete declared cell inventory required')
    context=admission['context']
    for cell in cells:
        if cell['split']!='train' or cell['task_id'] not in allowed:raise ValueError('held-out generation prohibited')
        ids=cell['prompt_token_ids']
        if not ids or len(ids)>context['engines']['generator']['context']-12288 or any(type(i) is not int or i<0 for i in ids):
            raise ValueError('invalid prompt or retired context')
    os.environ['VLLM_USE_FLASHINFER_SAMPLER']='0'
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    check(config, pre_engine=True)
    mark(config, 'engine_started')
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'intent.json',{'admission_sha256':digest(config['admission']),'cells':cells,'full_receipts':full})
    tokenizer=AutoTokenizer.from_pretrained(config['tokenizer'],local_files_only=True)
    engine=LLM(**engine_kwargs(config['model'],config['tokenizer'],context))
    from sampler_checks import worker_backend
    backend=engine.collective_rpc(worker_backend)
    if not backend or any(r['TopKTopPSampler.forward']!='forward_native' for r in backend):raise ValueError('sampler backend unavailable')
    write_new(root/'worker_backend.json',backend)
    total=certified=0
    for offset in range(0,len(cells),32):
        check(config);chunk=cells[offset:offset+32]
        params=[SamplingParams(**{**sampling_kwargs(c['seed'],[151643,151645]),'logprobs':64 if receipt else None}) for c in chunk]
        mark(config, 'generation_started')
        requests=engine.generate([{'prompt_token_ids':c['prompt_token_ids']} for c in chunk],params,use_tqdm=False)
        if len(requests)!=len(chunk):raise ValueError('generation count changed; no resampling')
        for index,(cell,request) in enumerate(zip(chunk,requests),start=offset):
            if len(request.outputs)!=1 or request.prompt_token_ids!=cell['prompt_token_ids']:
                raise ValueError('generation identity changed')
            output=request.outputs[0]
            positions=extract_raw(output,vocab_size=config['vocab_size'],full=full) if receipt else []
            row={**cell,'output_token_ids':list(output.token_ids),'receipt':positions,'worker_backend':backend,
                 'completion':tokenizer.decode(output.token_ids,skip_special_tokens=False),
                 'finish_reason':output.finish_reason,'at_token_cap':output.finish_reason=='length',
                 'admission_sha256':digest(config['admission'])}
            write_new(root/f'{index:05d}.generation.json',row)
            total+=len(output.token_ids);certified+=sum(p['certified'] for p in positions)
    if total==0:raise ValueError('empty generated response evidence')
    result={'declared':len(cells),'generated_responses':len(cells),'positions':total,'certified_positions':certified,
            'certified_fraction':certified/total,'admission_sha256':digest(config['admission'])}
    write_new(root/'result.json',result)
    return result
