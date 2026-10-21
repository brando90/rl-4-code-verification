"""TLDR: Construct the pinned top-64 generator only after admission and a device lease; retain every response."""
import importlib.metadata
from pathlib import Path
from admission import check_admission
from common import digest, write_new
from device_guard import check
from generation_contract import engine_kwargs, sampling_kwargs, extract_raw


def generate(config, cells, *, root, full):
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
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'intent.json',{'admission_sha256':digest(config['admission']),'cells':cells,'full_receipts':full})
    tokenizer=AutoTokenizer.from_pretrained(config['tokenizer'],local_files_only=True)
    engine=LLM(**engine_kwargs(config['model'],config['tokenizer'],context))
    total=certified=0
    for offset in range(0,len(cells),32):
        check(config);chunk=cells[offset:offset+32]
        params=[SamplingParams(**sampling_kwargs(c['seed'],[151643,151645])) for c in chunk]
        requests=engine.generate([{'prompt_token_ids':c['prompt_token_ids']} for c in chunk],params,use_tqdm=False)
        if len(requests)!=len(chunk):raise ValueError('generation count changed; no resampling')
        for index,(cell,request) in enumerate(zip(chunk,requests),start=offset):
            if len(request.outputs)!=1 or request.prompt_token_ids!=cell['prompt_token_ids']:
                raise ValueError('generation identity changed')
            output=request.outputs[0]
            receipt=extract_raw(output,vocab_size=config['vocab_size'],full=full)
            row={**cell,'output_token_ids':list(output.token_ids),'receipt':receipt,
                 'completion':tokenizer.decode(output.token_ids,skip_special_tokens=False),
                 'finish_reason':output.finish_reason,'at_token_cap':output.finish_reason=='length',
                 'admission_sha256':digest(config['admission'])}
            write_new(root/f'{index:05d}.generation.json',row)
            total+=len(receipt);certified+=sum(p['certified'] for p in receipt)
    if total==0:raise ValueError('empty generated response evidence')
    result={'declared':len(cells),'generated_responses':len(cells),'positions':total,'certified_positions':certified,
            'certified_fraction':certified/total,'admission_sha256':digest(config['admission'])}
    write_new(root/'result.json',result)
    return result
