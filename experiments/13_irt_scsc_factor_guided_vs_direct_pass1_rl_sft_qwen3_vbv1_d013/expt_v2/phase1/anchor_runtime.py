"""Run the admitted float16 generator on a common frozen tokenizer and resumable train anchors."""
from __future__ import annotations

import argparse
import json
import math
import os
import time
from pathlib import Path

import runtime as admitted
from anchor_panel import run_segment
from panel import digest
from anchor_storage import write_new


def check_bindings(config):
    admitted.check_bindings(config)
    required = {Path(__file__).resolve(),Path(__file__).with_name('anchor_panel.py').resolve(),
                Path(__file__).with_name('anchor_supervisor.py').resolve(),
                Path(__file__).with_name('anchor_storage.py').resolve(),
                Path(config['LP1_S2_result']).resolve(),Path(config['S2_lock']).resolve()}
    required.update(p.resolve() for p in Path(config['tokenizer']).iterdir() if p.is_file()
                    and p.suffix not in ('.bin','.safetensors'))
    if not required <= {Path(b['path']).resolve() for b in config['bindings']}:
        raise ValueError('anchor runtime omits an implementation, tokenizer or S2 binding')
    result = json.loads(Path(config['LP1_S2_result']).read_text())
    if (result.get('status')!='PASS' or result.get('condition')!='v2-S2'
            or not result.get('admission_statistics_computed') or result.get('responses')!=8
            or result.get('a5_stage')!='confirmation' or result.get('numerical_dtype')!='float16'
            or result.get('gate_lock_sha256')!=digest(config['S2_lock'])):
        raise ValueError('anchor generation requires the final admitted S2 confirmation')
    if admitted.numerical_dtype(config)!='float16':
        raise ValueError('every S2 anchor must retain float16')


def build_engine(config,manifest):
    """Same S2 constructor, with explicit common tokenization across anchor policies."""
    from vllm import LLM
    return LLM(model=config['model'],tokenizer=config['tokenizer'],dtype=admitted.numerical_dtype(config),
        tensor_parallel_size=1,max_model_len=manifest['max_model_len'],
        gpu_memory_utilization=config['gpu_memory_utilization'],enforce_eager=True,
        max_num_seqs=config['batch_size'],trust_remote_code=False,enable_prefix_caching=False,
        generation_config='vllm',seed=1302100,logprobs_mode='raw_logprobs')


def generation(config):
    from vllm import SamplingParams
    from transformers import AutoTokenizer
    manifest=json.loads(Path(config['manifest']).read_text())
    tokenizer=AutoTokenizer.from_pretrained(config['tokenizer'],local_files_only=True)
    engines=[]
    def generate_batch(cells):
        if not engines:engines.append(build_engine(config,manifest))
        sampling=[SamplingParams(n=1,temperature=1.,top_p=1.,top_k=-1,min_p=0.,
            repetition_penalty=1.,presence_penalty=0.,frequency_penalty=0.,
            max_tokens=8192,min_tokens=0,ignore_eos=False,stop=None,
            stop_token_ids=manifest['terminal_token_ids'],seed=cell['seed'],logprobs=0,
            include_stop_str_in_output=True) for cell in cells]
        requests=engines[0].generate([{'prompt_token_ids':cell['prompt_token_ids']} for cell in cells],
                                     sampling,use_tqdm=False)
        rows=[]
        for request in requests:
            if len(request.outputs)!=1:raise ValueError('unexpected generation multiplicity')
            output=request.outputs[0];ids=list(output.token_ids)
            rows.append({'prompt_token_ids':list(request.prompt_token_ids),'output_token_ids':ids,
                'generation_logprobs':[float(lp[token].logprob) if math.isfinite(lp[token].logprob) else None
                                      for lp,token in zip(output.logprobs,ids)],
                'finish_reason':output.finish_reason,
                'completion':tokenizer.decode(ids,skip_special_tokens=False)})
        return rows
    prerequisites={key:json.loads(Path(path).read_text()) if path else None
                   for key,path in config['prerequisites'].items()}
    return run_segment(manifest,Path(config['train_ids']).read_text().splitlines(),config['generation_root'],
        generate_batch=generate_batch,lease_check=lambda:admitted.check_lease(config),
        prerequisites=prerequisites,segment_id=config['segment_id'],lease_id=os.environ['E13_EXECUTION_ID'],
        maximum_cells=config['maximum_cells'],batch_size=config['batch_size'],
        may_start_batch=lambda:json.loads(Path(config['lease_path']).read_text())['expires_unix']-time.time()>900)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--stage',choices=('preflight','generate'),required=True)
    args=parser.parse_args();config=json.loads(args.config.read_text())
    check_bindings(config);admitted.check_lease(config)
    if args.stage=='preflight':
        # Reuse the exact admitted non-probe preflight; only the explicitly bound
        # tokenizer path differs for base/half, never the prompt or generation settings.
        admitted.build_engine=build_engine
        admitted.preflight(config)
    else:
        result=generation(config)
        write_new(Path(config['attempt_root'])/'generation_segment.json',result)


if __name__=='__main__':main()
