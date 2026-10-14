"""Run frozen vLLM generation or the installed NeMo trainer log-probability path."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import math
import subprocess

from panel import digest, generate_once, write_new
from device_binding import check_visible_device


def check_bindings(config):
    import importlib.metadata
    model = Path(config['model'])
    required = {Path(__file__).resolve(), Path(__file__).with_name('panel.py').resolve(),
                Path(__file__).with_name('probability.py').resolve(), Path(__file__).with_name('lp1.py').resolve(),
                Path(config['manifest']).resolve(), Path(config['train_ids']).resolve(),
                Path(config['policy_config']).resolve(), Path(__file__).with_name('device_binding.py').resolve()}
    model_files = [p for p in model.iterdir() if p.is_file()]
    if not any(p.suffix in ('.bin', '.safetensors') for p in model_files):
        raise ValueError('no frozen model weights')
    required.update(p.resolve() for p in model_files)
    bound = {Path(b['path']).resolve() for b in config['bindings']}
    if not required <= bound:
        raise ValueError('runtime configuration omits required source, input or export bindings')
    for binding in config['bindings']:
        if digest(binding['path']) != binding['sha256']:
            raise ValueError('runtime hash mismatch: ' + binding['path'])
    for package, version in config['runtime_versions'].items():
        if importlib.metadata.version(package) != version:
            raise ValueError('runtime package version mismatch: '+package)


def check_lease(config):
    # Re-query UUID/index mapping at every model stage; never pass UUIDs to vLLM.
    lease = json.loads(Path(config['lease_path']).read_text())
    check_visible_device(lease)
    query = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'],
                           capture_output=True, text=True, check=True, timeout=15)
    marker = ('E13_EXECUTION_ID='+lease['id']).encode()
    for line in query.stdout.splitlines():
        gpu, pid = [part.strip() for part in line.split(',')]
        if gpu == lease['uuid']:
            try:
                if marker not in Path('/proc', pid, 'environ').read_bytes().split(b'\0'):
                    raise RuntimeError('another execution now occupies the leased device')
            except FileNotFoundError:
                pass  # Process ended between the census and identity read.


def build_engine(config, manifest):
    from vllm import LLM
    return LLM(model=config['model'], tokenizer=config['model'], dtype='bfloat16',
        tensor_parallel_size=1, max_model_len=manifest['max_model_len'],
        gpu_memory_utilization=config['gpu_memory_utilization'], enforce_eager=True,
        max_num_seqs=config['batch_size'], trust_remote_code=False, enable_prefix_caching=False,
        generation_config='vllm', seed=1302100, logprobs_mode='raw_logprobs')


def preflight(config):
    """Exercise engine startup and one non-probe token before counting a gate attempt."""
    from vllm import SamplingParams
    import torch
    lease = json.loads(Path(config['lease_path']).read_text())
    check_lease(config)
    actual_uuid = str(torch.cuda.get_device_properties(0).uuid)
    if actual_uuid.removeprefix('GPU-') != lease['uuid'].removeprefix('GPU-'):
        raise RuntimeError('CUDA physical device does not match leased UUID')
    manifest = json.loads(Path(config['manifest']).read_text())
    engine = build_engine(config, manifest)
    # This authored health prompt contains no dataset/probe material. Neither its
    # text nor its output enters any gate statistic, fitting or model selection.
    prompt = 'Reply with one word: ready.'
    outputs = engine.generate([prompt], SamplingParams(max_tokens=1, temperature=0.,
                              seed=1302100, logprobs=None), use_tqdm=False)
    if len(outputs) != 1 or len(outputs[0].outputs) != 1 or not outputs[0].outputs[0].token_ids:
        raise RuntimeError('engine health request did not complete')
    write_new(Path(config['attempt_root'])/'preflight.json',
              {'status':'PASS', 'scope':'non-probe infrastructure only',
               'device_uuid':actual_uuid, 'visible_index':os.environ['CUDA_VISIBLE_DEVICES'],
               'prompt':prompt, 'generated_tokens':len(outputs[0].outputs[0].token_ids),
               'admission_statistics_computed':False})


def generation(config):
    import vllm
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer
    if vllm.__version__ != '0.10.0':
        raise RuntimeError('generation version differs from technical pin')
    manifest = json.loads(Path(config['manifest']).read_text())
    train_ids = Path(config['train_ids']).read_text().splitlines()
    tokenizer = AutoTokenizer.from_pretrained(config['model'], local_files_only=True)
    # Lazy model initialization: attempt ledger is durable before GPU work starts.
    engines = []
    def generate_batch(cells):
        if not engines:
            engines.append(build_engine(config, manifest))
        sampling = [SamplingParams(n=1, temperature=1., top_p=1., top_k=-1, min_p=0.,
            repetition_penalty=1., presence_penalty=0., frequency_penalty=0.,
            max_tokens=8192, min_tokens=0, ignore_eos=False, stop=None,
            stop_token_ids=manifest['terminal_token_ids'], seed=cell['seed'], logprobs=0,
            include_stop_str_in_output=True) for cell in cells]
        requests = engines[0].generate([{'prompt_token_ids': cell['prompt_token_ids']} for cell in cells],
                                      sampling, use_tqdm=False)
        rows = []
        for request in requests:
            if len(request.outputs) != 1: raise ValueError('unexpected generation multiplicity')
            output = request.outputs[0]
            ids = list(output.token_ids)
            rows.append({'prompt_token_ids': list(request.prompt_token_ids), 'output_token_ids': ids,
                'generation_logprobs': [float(lp[token].logprob) if math.isfinite(lp[token].logprob) else None
                                       for lp, token in zip(output.logprobs, ids)],
                'finish_reason': output.finish_reason,
                'completion': tokenizer.decode(ids, skip_special_tokens=False)})
        return rows
    prerequisites = {key: json.loads(Path(path).read_text()) if path else None
                     for key, path in config['prerequisites'].items()}
    return generate_once(manifest, train_ids, config['generation_root'], None,
                         lease_check=lambda: check_lease(config), prerequisites=prerequisites,
                         batch_size=config['batch_size'], generate_batch=generate_batch)


def trainer(config):
    import ray
    import torch
    from transformers import AutoTokenizer
    from nemo_rl.distributed.batched_data_dict import BatchedDataDict
    from nemo_rl.distributed.virtual_cluster import RayVirtualCluster
    from nemo_rl.distributed.ray_actor_environment_registry import ACTOR_ENVIRONMENT_REGISTRY
    from nemo_rl.models.policy.lm_policy import Policy
    root = Path(config['generation_root'])
    terminal = json.loads((root / 'terminal.json').read_text())
    if terminal['status'] != 'COMPLETE':
        raise ValueError('probability admission requires the complete probe')
    write_new(root / 'trainer_attempt.json', {'responses': terminal['declared'], 'optimizer_updates': 0})
    tokenizer = AutoTokenizer.from_pretrained(config['model'], local_files_only=True)
    policy_config = json.loads(Path(config['policy_config']).read_text())
    if policy_config['model_name'] != config['model']:
        raise ValueError('trainer/generator model mismatch')
    ACTOR_ENVIRONMENT_REGISTRY['nemo_rl.models.policy.dtensor_policy_worker.DTensorPolicyWorker'] = sys.executable
    # Explicitly new, owned Ray instance. Never connect to another experiment.
    ray.init(address='local', num_gpus=1, num_cpus=4, include_dashboard=False,
             _temp_dir=config['ray_temp'], log_to_driver=True)
    cluster = RayVirtualCluster([1], num_gpus_per_node=1, name='e13v2-lp1')
    try:
        policy = Policy(cluster, policy_config, tokenizer, name_prefix='e13v2-lp1',
                        init_optimizer=False, init_reference_model=False)
        for index in range(terminal['declared']):
            check_lease(config)
            row = json.loads((root / f'{index:05d}.generation.json').read_text())
            tokens = row['prompt_token_ids'] + row['output_token_ids']
            mask = [0] * len(row['prompt_token_ids']) + [1] * len(row['output_token_ids'])
            data = BatchedDataDict({'input_ids': torch.tensor([tokens], dtype=torch.long),
                'input_lengths': torch.tensor([len(tokens)], dtype=torch.long),
                'token_mask': torch.tensor([mask], dtype=torch.float32),
                'sample_mask': torch.ones(1, dtype=torch.float32)})
            lp = policy.get_logprobs(data)['logprobs'][0, :len(tokens)].detach().cpu().tolist()
            write_new(root / f'{index:05d}.probability.json', {**row, 'trainer_input_ids': tokens,
                      'trainer_token_mask': mask, 'trainer_logprobs': [x if math.isfinite(x) else None for x in lp]})
    finally:
        cluster.shutdown()
        ray.shutdown()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--stage', choices=('preflight', 'generate', 'trainer'), required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    check_bindings(config); check_lease(config)
    if args.stage == 'preflight':
        preflight(config)
    elif args.stage == 'generate':
        generation(config)
    else:
        trainer(config)


if __name__ == '__main__':
    main()
