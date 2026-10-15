"""Generate an immutable evaluation segment with the exact historical sampler and S2 numerical precision."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'phase1'))
from runtime import numerical_dtype,check_lease
from training_checkpoint import write_new,digest
from evaluation_contract import sampling_parameters,identities,POPULATIONS


def validate_manifest(manifest,allowlist):
    purpose=manifest['purpose'];cells=manifest['cells'];allowed=set(allowlist)
    if manifest.get('condition')!='v2-S2' or not cells or len({c['cell_id'] for c in cells})!=len(cells):
        raise ValueError('unique complete evaluation manifest required')
    if purpose=='T4_train_cost':
        if len(cells)!=8 or len({c['task_id'] for c in cells})!=8 or any(c['split']!='train' for c in cells):
            raise ValueError('cost probe must be eight distinct train tasks')
    elif purpose in POPULATIONS:
        expected=identities(sorted(allowed),purpose,arm=manifest['arm'],run_seed=manifest['run_seed'],boundary=manifest['boundary'])
        table={c['cell_id']:c for c in cells}
        if set(table)!={c['cell_id'] for c in expected}:raise ValueError('evaluation manifest population changed')
        for row in expected:
            if any(table[row['cell_id']].get(k)!=v for k,v in row.items()):raise ValueError('evaluation identity changed')
    else:raise ValueError('unregistered evaluation purpose')
    for cell in cells:
        if cell['task_id'] not in allowed or type(cell['sample_idx']) is not int or not 0<=cell['sample_idx']<16:
            raise ValueError('evaluation cell outside its split or sample range')
        if cell['seed']!=91*100003+cell['sample_idx']:raise ValueError('historical evaluation seed changed')
        if not isinstance(cell['prompt_text'],str) or hashlib.sha256(cell['prompt_text'].encode()).hexdigest()!=cell['chat_text_sha256']:
            raise ValueError('evaluation prompt text changed')
        tokens=cell['prompt_token_ids']
        if not tokens or len(tokens)>32768-12288 or any(type(t) is not int or t<0 for t in tokens):
            raise ValueError('evaluation prompt exceeds frozen context')
        if not cell.get('required_paths'):raise ValueError('evaluation extraction paths missing')
    return cells


def build_engine(config):
    from vllm import LLM
    if numerical_dtype(config)!='float16' or config['batch_size']!=32 or config['max_model_len']!=32768:
        raise ValueError('evaluation precision or engine resource contract changed')
    # Explicit auto retains the historical generation-config default. Scientific
    # sampler arguments are supplied per request by the unchanged contract.
    return LLM(model=config['model'],tokenizer=config['tokenizer'],dtype='float16',tensor_parallel_size=1,
        max_model_len=32768,gpu_memory_utilization=config['gpu_memory_utilization'],enforce_eager=True,
        max_num_seqs=32,trust_remote_code=False,enable_prefix_caching=False,generation_config='auto',seed=91)


def generate(config,manifest,indexes,*,root):
    """The caller binds the complete population and one exclusive segment before any device launch."""
    from transformers import AutoTokenizer
    cells=validate_manifest(manifest,Path(config['allowlist']).read_text().splitlines())
    if (not indexes or len(indexes)>256 or len(indexes)!=len(set(indexes))
            or indexes!=sorted(indexes) or any(type(i) is not int or not 0<=i<len(cells) for i in indexes)):
        raise ValueError('evaluation segment must contain at most 256 unique ordered indexes')
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'cells.json',[cells[i] for i in indexes])
    write_new(root/'attempt.json',{'condition':'v2-S2','purpose':manifest['purpose'],'indexes':indexes,
        'declared_segment':len(indexes),'declared_population':len(cells),'cells_sha256':digest(root/'cells.json'),
        'automatic_retry':False,'model':config['model'],'numerical_dtype':'float16'})
    completed=[]
    try:
        check_lease(config);tokenizer=AutoTokenizer.from_pretrained(config['tokenizer'],local_files_only=True)
        engine=build_engine(config)
        for offset in range(0,len(indexes),32):
            check_lease(config);chunk=indexes[offset:offset+32]
            selected=[cells[i] for i in chunk]
            for cell in selected:
                if list(tokenizer.encode(cell['prompt_text']))!=cell['prompt_token_ids']:
                    raise ValueError('evaluation tokenizer differs from the frozen prompt encoding')
            requests=engine.generate([c['prompt_text'] for c in selected],
                [sampling_parameters(tokenizer,c['sample_idx']) for c in selected],use_tqdm=False)
            if len(requests)!=len(selected):raise ValueError('evaluation response count changed')
            errors=[]
            for index,cell,request in zip(chunk,selected,requests):
                try:
                    if len(request.outputs)!=1 or list(request.prompt_token_ids)!=cell['prompt_token_ids']:
                        raise ValueError('evaluation output multiplicity or prompt changed')
                    output=request.outputs[0];tokens=list(output.token_ids)
                    if (not tokens or len(tokens)>12288 or any(type(t) is not int or t<0 for t in tokens)
                            or output.finish_reason not in ('stop','length') or not isinstance(output.text,str)):
                        raise ValueError('invalid evaluation output')
                    row={**cell,'condition':'v2-S2','output_token_ids':tokens,'completion':output.text,
                         'finish_reason':output.finish_reason,'at_token_cap':output.finish_reason=='length',
                         'prompt_tokens':len(request.prompt_token_ids),'generated_tokens':len(tokens)}
                    write_new(root/f'{index:05d}.generation.json',row);completed.append(row)
                except Exception as exc:
                    write_new(root/f'{index:05d}.error.json',{'error_type':type(exc).__name__,'error':str(exc)})
                    errors.append(type(exc).__name__)
            if errors:raise ValueError('evaluation segment has invalid receipts; valid neighbors retained')
        result={'condition':'v2-S2','status':'COMPLETE','purpose':manifest['purpose'],'declared':len(indexes),
                'completed':len(completed),'generated_tokens':sum(r['generated_tokens'] for r in completed),
                'capped_responses':sum(r['at_token_cap'] for r in completed),'optimizer_updates':0}
        write_new(root/'result.json',result);return result
    except Exception as exc:
        write_new(root/'error.json',{'condition':'v2-S2','status':'INCOMPLETE','declared':len(indexes),
            'completed':len(completed),'error_type':type(exc).__name__,'error':str(exc),'automatic_retry':False})
        raise
