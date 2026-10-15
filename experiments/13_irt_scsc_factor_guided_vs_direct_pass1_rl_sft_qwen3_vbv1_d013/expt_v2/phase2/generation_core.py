"""Generate a declared train-only technical batch with the unchanged admitted S2 engine and sampler."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PHASE1=HERE.parent/'phase1'
if str(PHASE1) not in sys.path:sys.path.insert(0,str(PHASE1))
from anchor_runtime import build_engine
from runtime import check_lease,numerical_dtype
from panel import validate_generation
from training_checkpoint import write_new,digest


def validate_cells(cells,train_ids):
    if not cells or len(cells)>256 or len({c['cell_id'] for c in cells})!=len(cells):
        raise ValueError('technical batch must declare 1 to 256 unique train cells')
    allowed=set(train_ids)
    for cell in cells:
        if cell['split']!='train' or cell['task_id'] not in allowed:raise ValueError('held-out generation prohibited')
        if type(cell['seed']) is not int or not 0<=cell['seed']<2**63:raise ValueError('invalid fixed rollout seed')
        prompt=cell['prompt_token_ids']
        if not prompt or len(prompt)>15945-8192 or any(type(t) is not int or t<0 for t in prompt):
            raise ValueError('prompt exceeds frozen training context')
    return cells


def sampler(terminal_token_ids,seed):
    from vllm import SamplingParams
    return SamplingParams(n=1,temperature=1.,top_p=1.,top_k=-1,min_p=0.,
        repetition_penalty=1.,presence_penalty=0.,frequency_penalty=0.,max_tokens=8192,min_tokens=0,
        ignore_eos=False,stop=None,stop_token_ids=terminal_token_ids,seed=seed,logprobs=0,
        include_stop_str_in_output=True)


def generate(config,cells,*,root):
    """An exclusive attempt retains every receipt; reruns require an external admitted recovery rule."""
    from transformers import AutoTokenizer
    cells=validate_cells(cells,Path(config['train_ids']).read_text().splitlines())
    if numerical_dtype(config)!='float16' or config['batch_size']!=32:
        raise ValueError('S2 numerical or generator batch setting changed')
    contract={'max_model_len':15945,'terminal_token_ids':config['terminal_token_ids']}
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'cells.json',cells)
    write_new(root/'attempt.json',{'condition':'v2-S2','declared':len(cells),'cells_sha256':digest(root/'cells.json'),
        'model':config['model'],'tokenizer':config['tokenizer'],'numerical_dtype':'float16','rerun_admitted':False})
    rows=[]
    try:
        check_lease(config)
        tokenizer=AutoTokenizer.from_pretrained(config['tokenizer'],local_files_only=True)
        engine=build_engine(config,contract)
        for offset in range(0,len(cells),32):
            check_lease(config);chunk=cells[offset:offset+32]
            requests=engine.generate([{'prompt_token_ids':c['prompt_token_ids']} for c in chunk],
                [sampler(contract['terminal_token_ids'],c['seed']) for c in chunk],use_tqdm=False)
            if len(requests)!=len(chunk):raise ValueError('generator changed response count')
            failures=[]
            for index,(cell,request) in enumerate(zip(chunk,requests),start=offset):
                try:
                    if len(request.outputs)!=1:raise ValueError('generator changed per-cell multiplicity')
                    output=request.outputs[0];tokens=list(output.token_ids)
                    if output.logprobs is None or len(output.logprobs)!=len(tokens):
                        raise ValueError('generator omitted selected-token probabilities')
                    lp=[float(values[token].logprob) if token in values and math.isfinite(values[token].logprob) else None
                        for token,values in zip(tokens,output.logprobs)]
                    row={**cell,'condition':'v2-S2','prompt_token_ids':list(request.prompt_token_ids),
                        'output_token_ids':tokens,'generation_logprobs':lp,'finish_reason':output.finish_reason,
                        'completion':tokenizer.decode(tokens,skip_special_tokens=False),'at_token_cap':output.finish_reason=='length'}
                    # Preserve unsupported-action receipts for the final gate's
                    # explicit count. This validator checks tokens and masks, not probability finiteness.
                    validate_generation(cell,row,contract)
                    write_new(root/f'{index:05d}.generation.json',row);rows.append(row)
                except Exception as exc:
                    write_new(root/f'{index:05d}.error.json',{'error_type':type(exc).__name__,'error':str(exc)})
                    failures.append(type(exc).__name__)
            if failures:raise ValueError('technical batch contains invalid generation receipts')
        result={'condition':'v2-S2','status':'COMPLETE','declared':len(cells),'completed':len(rows),
            'generated_tokens':sum(len(r['output_token_ids']) for r in rows),
            'capped_responses':sum(r['at_token_cap'] for r in rows),
            'unsupported_selected_tokens':sum(v is None for r in rows for v in r['generation_logprobs']),
            'optimizer_updates':0}
        write_new(root/'result.json',result);return result
    except Exception as exc:
        write_new(root/'error.json',{'condition':'v2-S2','status':'INCOMPLETE','declared':len(cells),
            'completed':len(rows),'error_type':type(exc).__name__,'error':str(exc),'rerun_admitted':False})
        raise
