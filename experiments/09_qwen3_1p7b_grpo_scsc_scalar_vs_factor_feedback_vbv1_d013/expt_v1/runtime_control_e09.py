#!/usr/bin/env python3
"""TLDR: Leased, disposable real-NeMo two-turn/optimizer control; never a scientific trajectory."""
from __future__ import annotations

import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone

ROOT = Path('/lfs/skampere1/0/brando9/rl4cv_e09')
REPO = ROOT / 'rl-4-code-verification'
HERE = Path(__file__).resolve().parent
LEASE_TOOL = Path('/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts/gpu_lease_e08.py')
MODEL = '/lfs/skampere1/0/brando9/rl4cv_e08/ckpt/1.7B/hf/step_658'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    temporary = Path(str(path) + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def lease_command(*args, allow_denied=False):
    result = subprocess.run(['/usr/bin/python3', str(LEASE_TOOL), *args],
                            capture_output=True, text=True, timeout=60)
    if result.returncode and not (allow_denied and result.returncode == 3):
        raise RuntimeError('Lease denied: ' + result.stdout + result.stderr)
    return json.loads(result.stdout)


def plumbing_scorer(metadata, candidate):
    """Synthetic rewards solely for the disposable optimizer/masking control.

    Real scorer controls already passed; this explicitly is NOT a benchmark
    measurement, calibration, held-out response or substitute scientific reward.
    """
    from two_turn_env import MeasuredAnswer
    from rl4cv.rewards import ScoredResponse
    fraction = (int(metadata['rollout_id'].rsplit(':', 1)[-1]) + 1) / 8
    return MeasuredAnswer(ScoredResponse(True, True, 1, 1, 1, fraction),
                          'DISPOSABLE PLUMBING CONTROL: synthetic scorer fixture',
                          'synthetic_control_not_measured')


def run(out):
    import ray
    import torch
    from omegaconf import OmegaConf
    from transformers import AutoTokenizer
    from nemo_rl.algorithms.grpo import setup, grpo_train, refit_policy_generation
    from nemo_rl.algorithms.utils import set_seed
    from nemo_rl.models.generation import configure_generation_config
    from nemo_rl.distributed.ray_actor_environment_registry import ACTOR_ENVIRONMENT_REGISTRY
    from two_turn_env import TwoTurnLeanEnvironment

    assert torch.cuda.device_count() == 1
    from device_guard import verify_exclusive_device
    verify_exclusive_device()
    actual_uuid = str(torch.cuda.get_device_properties(0).uuid)
    assert actual_uuid.removeprefix('GPU-').lower() == os.environ['E09_LEASED_GPU_UUID'].removeprefix('GPU-').lower(), (actual_uuid, 'lease UUID mismatch')
    write_json(out / 'driver_device_identity.json', {'uuid': actual_uuid, 'visibility': os.environ['CUDA_VISIBLE_DEVICES'],
                                                   'device_order': os.environ['CUDA_DEVICE_ORDER']})
    torch.set_num_threads(1)
    OmegaConf.register_new_resolver('mul', lambda a, b: a * b, replace=True)
    cfg = OmegaConf.load(ROOT / 'nemo_rl/examples/configs/grpo_math_1B.yaml')
    cfg.grpo.update(num_prompts_per_step=4, num_generations_per_prompt=8,
                    max_rollout_turns=2, max_num_steps=1, max_num_epochs=1,
                    val_period=0, val_at_start=False, seed=20261008)
    cfg.policy.model_name = MODEL
    cfg.policy.tokenizer.chat_template_kwargs = {'enable_thinking': False}
    cfg.policy.update(train_global_batch_size=32, train_micro_batch_size=1,
                      logprob_batch_size=1, max_total_sequence_length=32768,
                      logprob_chunk_size=16)
    cfg.policy.dtensor_cfg.update(_v2=False, activation_checkpointing=True)
    cfg.policy.sequence_packing.enabled = False
    cfg.policy.dynamic_batching.enabled = False
    # Short disposable plumbing responses. Scientific response cap stays 8192;
    # the separate full-context allocation control is required for admission.
    cfg.policy.generation.update(max_new_tokens=64, temperature=.6, top_k=20, top_p=.95)
    cfg.policy.generation.vllm_cfg.update(enforce_eager=True, gpu_memory_utilization=.45)
    cfg.policy.generation.vllm_kwargs = {'max_num_seqs': 8, 'max_num_batched_tokens': 8192}
    cfg.policy.scheduler = {'name': 'torch.optim.lr_scheduler.ConstantLR',
                            'kwargs': {'factor': 1.0, 'total_iters': 100000}}
    cfg.loss_fn.reference_policy_kl_penalty = 0.0
    cfg.data.update(shuffle=False, num_workers=0)
    cfg.checkpointing.update(checkpoint_dir=str(out / 'checkpoints'),
                             save_period=1, keep_top_k=1, metric_name=None)
    cfg.logger.update(log_dir=str(out / 'logs'), monitor_gpus=False)
    cfg.env = {}
    config = OmegaConf.to_container(cfg, resolve=True)
    write_json(out / 'resolved_config.json', config)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
    config['policy']['generation'] = configure_generation_config(config['policy']['generation'], tokenizer)
    set_seed(config['grpo']['seed'])
    for key in ('nemo_rl.models.policy.dtensor_policy_worker.DTensorPolicyWorker',
                'nemo_rl.models.generation.vllm.vllm_worker.VllmGenerationWorker'):
        ACTOR_ENVIRONMENT_REGISTRY[key] = str(ROOT / 'nemo_rl/.venv/bin/python')
    ray.init(address='local', _temp_dir=os.environ['E09_RAY_DIR'],
             num_cpus=4, num_gpus=1, include_dashboard=False,
             object_store_memory=512 * 1024**2,
             runtime_env={'env_vars': {k: os.environ[k] for k in (
                 'PYTHONPATH', 'E09_FILTERED_POLICY', 'E09_GENERATION_SEED',
                 'VLLM_USE_FLASHINFER_SAMPLER', 'E09_IPC_DIR', 'E09_CONTROL_DIR',
                 'CUDA_DEVICE_ORDER', 'E09_LEASED_GPU_UUID',
                 'E09_DRIVER_PID', 'E09_DRIVER_START',
                 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}})
    try:
        actor = ray.remote(TwoTurnLeanEnvironment).options(num_cpus=1).remote(
            arm='B', scorer=plumbing_scorer, tokenizer=tokenizer,
            receipt_dir=str(out / 'trajectory_receipts'))
        dataset = []
        for i in range(4):
            prompt = tokenizer.apply_chat_template(
                [{'role': 'user', 'content': 'Write a Lean 4 file defining the identity function on Nat, with one example and one theorem. Output only the file.'}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            tokens = tokenizer(prompt, add_special_tokens=False, return_tensors='pt').input_ids[0]
            dataset.append({'message_log': [{'role': 'user', 'content': prompt, 'token_ids': tokens}],
                            'length': len(tokens), 'extra_env_info': {
                                'task_id': f'disposable_control_{i}', 'seed': 20261008, 'schedule_index': i},
                            'loss_multiplier': 1., 'idx': i, 'task_name': 'e09_control', 'stop_strings': None})
        parts = setup(config, tokenizer, dataset, None)
        policy, generation, cluster, loader, val_loader, loss, logger, checkpointer, state, config = parts
        grpo_train(policy, generation, loader, val_loader, tokenizer, loss,
                   {'e09_control': actor}, {}, logger, checkpointer, state, config)
        checkpoint = checkpointer.get_latest_checkpoint_path()
        assert checkpoint is not None, 'Optimizer checkpoint was not saved'
        from nemo_rl.distributed.batched_data_dict import BatchedDataDict
        from filtered_loss import GENERATION_LOGPROB_ATOL
        refit_policy_generation(policy, generation, True)
        ids = dataset[0]['message_log'][0]['token_ids'].unsqueeze(0)
        prompt_length = ids.shape[1]
        probe = BatchedDataDict({'input_ids': ids, 'input_lengths': torch.tensor([prompt_length]),
                                'stop_strings': [None], 'e09_seeds': [2026100801]})
        generated = generation.generate(probe, greedy=False)
        generation.finish_generation()
        mask = torch.zeros_like(generated['output_ids'])
        length = int(generated['unpadded_sequence_lengths'][0])
        mask[:, prompt_length:length] = 1
        assert int(mask.sum()) > 0
        probe_data = BatchedDataDict({'input_ids': generated['output_ids'],
                    'input_lengths': generated['unpadded_sequence_lengths'], 'token_mask': mask,
                    'sample_mask': torch.ones(1)})
        policy.prepare_for_lp_inference()
        teacher = policy.get_logprobs(probe_data)['logprobs']
        maximum_error = (teacher - generated['logprobs'])[mask.bool()].abs().max().item()
        assert maximum_error <= GENERATION_LOGPROB_ATOL
        torch.save({'probe': probe_data, 'generation': generated, 'teacher_logprobs': teacher}, out / 'post_update_refit.pt')
        write_json(out / 'post_update_refit.json', {'status': 'PASS', 'checkpoint': str(checkpoint),
            'optimizer_step': 1, 'max_logprob_error': maximum_error, 'generated_tokens': int(mask.sum()),
            'technical_responses': 1, 'scientific_responses': 0})
        admission_pass = all(json.loads((out / name).read_text()).get('status') == 'PASS'
                             for name in ('save_reload.json', 'full_context.json', 'post_update_refit.json'))
        assert admission_pass
        write_json(out / 'stage_receipt.json', {
            'written_utc': stamp(), 'disposable': True,
            'stage': 'grpo_train_returned_checkpoint_saved', 'checkpoint': str(checkpoint),
            'optimizer_save_reload_verified': True, 'full_context_verified': True,
            'technical_admission_pass': True})
    finally:
        ray.shutdown()


def main():
    identity = json.loads((ROOT / 'run_identity.json').read_text())
    pid = os.getpid()
    start = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19]
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    child = {'pid': pid, 'start_ticks': start, 'boot_id': boot,
             'kind': 'disposable_optimizer_control', 'run_id': identity['run_id']}
    # Register before any change of directory or child runtime creation.
    receipt = json.loads((ROOT / 'child_receipts.json').read_text())
    assert not receipt.get('processes'), 'Adopt prior healthy driver instead of duplicating'
    receipt.update(run_id=identity['run_id'], processes=[child], written_utc=stamp())
    write_json(ROOT / 'child_receipts.json', receipt)
    out = ROOT / 'technical_control' / sys.argv[1]
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / 'identity.json', child)
    write_json(out / 'prospective_budget.json', {
        'written_utc': stamp(), 'max_devices': 1, 'reserved_device_hours': 1.0,
        'disposable_optimizer_steps': 1, 'technical_responses_max': 65,
        'technical_response_tokens_max': 4160, 'new_judge_calls': 0,
        'new_data_estimate_gib': 30, 'new_data_run_limit_gib': 200,
        'scientific_sampler': {'temperature': .6, 'top_p': .95, 'top_k': 20},
        'generation_old_logq_absolute_tolerance': .05,
        'current_old_logq_absolute_tolerance': .005,
        'allowed_support_mismatches': 0, 'reference_kl_coefficient': 0,
        'scientific_training_admitted': False})
    def expired(signum, frame):
        raise TimeoutError('One-hour disposable control deadline reached')
    signal.signal(signal.SIGALRM, expired)
    remaining = int((datetime.fromisoformat('2026-10-09T05:15:00+00:00') - datetime.now(timezone.utc)).total_seconds())
    signal.alarm(max(1, remaining))
    lease = None
    try:
        free = os.statvfs(ROOT)
        assert free.f_bavail / free.f_blocks >= .05
        assert datetime.now(timezone.utc) < datetime.fromisoformat(identity['deadline_utc'])
        while True:
            admission = lease_command('request', '--owner', 'e09', '--n', '1', '--kind', 'technical-control',
                                      '--ttl-hours', '1.0', '--pid', str(pid), '--boundary',
                                      'One disposable 32-trajectory two-turn optimizer control, then release; no calibration admission',
                                      allow_denied=True)
            write_json(out / 'latest_admission.json', admission)
            if admission.get('granted'):
                lease = admission
                signal.alarm(min(3500, max(1, int((datetime.fromisoformat('2026-10-09T05:15:00+00:00') - datetime.now(timezone.utc)).total_seconds()))))
                break
            print(f'WAITING_GPU {stamp()} {admission.get("reason")}', flush=True)
            if datetime.now(timezone.utc) >= datetime.fromisoformat('2026-10-09T04:15:00+00:00'):
                raise TimeoutError('No admitted device by prospective control-start cutoff 04:15 UTC')
            time.sleep(60)
        write_json(out / 'lease.json', lease)
        held = lease.get('lease', lease)
        os.environ['CUDA_VISIBLE_DEVICES'] = held['cuda_visible_devices']
        inventory = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader'],
                                   check=True, capture_output=True, text=True, timeout=30)
        uuid_by_index = dict(line.strip().split(', ') for line in inventory.stdout.splitlines())
        os.environ['E09_LEASED_GPU_UUID'] = uuid_by_index[held['cuda_visible_devices']]
        os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
        os.environ.update(E09_DRIVER_PID=str(pid), E09_DRIVER_START=start)
        os.environ.update(E09_FILTERED_POLICY='1', E09_GENERATION_SEED='20261008',
                          VLLM_USE_FLASHINFER_SAMPLER='0', E09_CONTROL_DIR=str(out),
                          OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                          PYTHONPATH=f'{HERE}:{REPO / "src"}')
        for k in ('PYTHONHOME', 'RAY_ADDRESS'):
            os.environ.pop(k, None)
        ipc = tempfile.mkdtemp(prefix='e09-ipc-')
        runtime = tempfile.mkdtemp(prefix='e09-ray-')
        os.environ.update(E09_IPC_DIR=ipc, E09_RAY_DIR=runtime)
        write_json(out / 'placement.json', {'ray': runtime, 'ipc': ipc, 'gpu': os.environ['CUDA_VISIBLE_DEVICES'],
                                          'admission_utc': stamp(), 'scorer_workers': 0, 'new_judge_calls': 0})
        sys.path[:0] = [str(HERE), str(REPO / 'src')]
        print(f'CONTROL_ADMITTED pid={pid} gpu={os.environ["CUDA_VISIBLE_DEVICES"]} out={out}', flush=True)
        from device_guard import verify_exclusive_device
        # One admission now includes a prospective quiet window, with no model
        # calls or CUDA context. A foreign job cancels, never shares the device.
        for check in range(4):
            verify_exclusive_device()
            if check < 3:
                time.sleep(30)
        run(out)
    except BaseException as exc:
        write_json(out / 'failure.json', {'written_utc': stamp(), 'error': str(exc), 'type': type(exc).__name__,
                                        'traceback': traceback.format_exc(), 'admission_pass': False})
        raise
    finally:
        if lease:
            key = lease.get('lease_id') or lease.get('lease', {}).get('lease_id')
            if key:
                write_json(out / 'release.json', lease_command('release', '--lease-id', key))
        write_json(out / 'exit.json', {'written_utc': stamp(), 'pid': pid,
            'complete_admission': (out / 'stage_receipt.json').exists() and not (out / 'failure.json').exists()})
        receipt['processes'] = []
        receipt['written_utc'] = stamp()
        write_json(ROOT / 'child_receipts.json', receipt)


if __name__ == '__main__':
    main()
