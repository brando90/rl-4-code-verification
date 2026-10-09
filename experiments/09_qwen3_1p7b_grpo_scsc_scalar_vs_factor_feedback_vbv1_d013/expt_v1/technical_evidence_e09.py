"""TLDR: Summarize the preserved failed control without generation, optimization or judging."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2].parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    control = ROOT / 'technical_control/profile_scope_fix'
    replay = ROOT / 'technical_control/replay_probability_diagnostic'
    diagnostic = json.loads((replay / 'probability_diagnostic.json').read_text())
    files = sorted((replay / 'probability_diagnostics').glob('microbatch_*.pt'))
    assert len(files) == 32
    frozen = torch.load(control / 'batch_0.pt', weights_only=False, map_location='cpu')
    # This is our own preserved technical fixture, never an untrusted checkpoint.
    prefixes = {}
    span_counts = {1: {'finite': 0, 'exceeding': 0, 'unsupported': 0},
                   2: {'finite': 0, 'exceeding': 0, 'unsupported': 0}}
    reconstruction_errors = []
    tokens = unsupported = exceeding = 0
    details = []
    errors = []
    for path in files:
        data = torch.load(path, weights_only=True, map_location='cpu')
        row = int(path.stem.split('_')[-1])
        teacher, behavior = data['teacher_logq'], data['generation_logq']
        assert torch.isfinite(behavior).all()
        finite = torch.isfinite(teacher)
        delta = (teacher[finite] - behavior[finite]).abs()
        errors.append(delta)
        tokens += len(teacher)
        unsupported += int((~finite).sum())
        exceeding += int((delta > .05).sum())
        cursor, assistant_spans = 0, []
        for message in frozen['rollout']['message_log'][row]:
            end = cursor + len(message['token_ids'])
            if message['role'] == 'assistant':
                assistant_spans.append((cursor, end))
            cursor = end
        for index in range(len(teacher)):
            position = int(data['positions'][index, 1]) + 1
            ids = frozen['train_data']['input_ids'][row, :position+1]
            assert int(ids[-1]) == int(data['targets'][index])
            assert float(frozen['train_data']['generation_logprobs'][row, position]) == float(behavior[index])
            span = next(j+1 for j, (a, b) in enumerate(assistant_spans) if a <= position < b)
            stat = span_counts[span]
            if finite[index]:
                stat['finite'] += 1
                stat['exceeding'] += int(abs(float(teacher[index] - behavior[index])) > .05)
                count = int(data['kept_count'][index])
                assert count <= 24
                reconstructed = data['target_scaled_logits'][index].item() - data['top24_scaled_logits'][index, :count].logsumexp(0).item()
                reconstruction_errors.append(abs(reconstructed - float(teacher[index])))
            else:
                stat['unsupported'] += 1
            key = hashlib.sha256(ids.numpy().tobytes()).hexdigest()
            prefixes.setdefault(key, []).append({'row': row, 'span': span,
                'teacher': float(teacher[index]) if finite[index] else None,
                'generation': float(behavior[index])})
        for index in (~finite).nonzero().flatten().tolist():
            ranked = data['top24_token_ids'][index].tolist()
            target = int(data['targets'][index])
            details.append({'microbatch': int(path.stem.split('_')[-1]),
                'shifted_action_position': data['positions'][index].tolist(),
                'token_id': target,
                'generation_logq': float(behavior[index]),
                'recomputed_logq': None, 'recomputed_status': 'negative_infinity_outside_support',
                'target_scaled_logit': float(data['target_scaled_logits'][index].item()),
                'recomputed_retained_count': int(data['kept_count'][index]),
                'target_rank_in_top24': ranked.index(target) + 1 if target in ranked else None})
    assert (tokens, unsupported, exceeding) == (4077, 4, 367)
    assert tokens == diagnostic['assistant_tokens']
    errors = torch.cat(errors)
    assert abs(float(errors.max()) - diagnostic['supported_actions_max_logq_error']) < 1e-7
    duplicates = [rows for rows in prefixes.values() if len(rows) > 1 and all(r['teacher'] is not None for r in rows)]
    teacher_spread = max(max(r['teacher'] for r in rows) - min(r['teacher'] for r in rows) for rows in duplicates)
    generation_spread = max(max(r['generation'] for r in rows) - min(r['generation'] for r in rows) for rows in duplicates)
    varying = [rows for rows in duplicates if max(r['generation'] for r in rows) != min(r['generation'] for r in rows)]
    result = {'schema_version': 1,
        'written_utc': datetime.now(timezone.utc).isoformat(),
        'run_id': json.loads((ROOT / 'run_identity.json').read_text())['run_id'],
        'status': 'FAILED_TECHNICAL_GATE', 'reason': 'failed_probability_support_gate',
        'control': 'real pinned NeMo two-turn rollout followed by old-policy recomputation',
        'source_repository_control_commit': 'c8cdf81',
        'technical_responses': {'generated': 64, 'prospective_maximum': 65,
                               'post_update_refit_probe_generated': 0},
        'actual_rollout_audit': json.loads((control / 'batch_0_audit.json').read_text()),
        'sampling': {'temperature': .6, 'top_p': .95, 'top_k': 20},
        'candidate_loss': {'reference_kl_coefficient': 0, 'updates_per_fresh_batch': 1,
                           'actual_optimizer_updates': 0},
        'probabilities': {'assistant_tokens': tokens, 'outside_recomputed_support': unsupported,
            'permitted_support_mismatches': 0, 'finite_action_denominator': tokens - unsupported,
            'finite_actions_exceeding_logq_tolerance': exceeding,
            'prospective_absolute_logq_tolerance': .05,
            'maximum_finite_absolute_logq_error': float(errors.max()),
            'mean_finite_absolute_logq_error': float(errors.mean()),
            'unsupported_action_details': details},
        'replay': {'new_responses': 0, 'optimizer_updates': 0, 'microbatches': len(files),
                   'input_is_exact_preserved_control_batch': True,
                   'loss_forbidden_under_diagnostic_flag': True},
        'saved_tensor_addendum': {'new_model_computation': False, 'span_counts': span_counts,
            'duplicated_exact_prefix_target_groups': len(duplicates),
            'maximum_duplicate_teacher_logq_spread': teacher_spread,
            'maximum_duplicate_generation_logq_spread': generation_spread,
            'example_generation_variation': varying[0] if varying else None,
            'teacher_normalization_reconstruction_max_error': max(reconstruction_errors),
            'interpretation': 'Stable teacher values but differing generation probabilities for identical saved token prefixes support scheduling/backend numerical variation; no causal mechanism or drop-in correction is established.'},
        'further_readonly_backend_diagnostic': {
            'status': 'NOT_RUN_REQUIRES_NEW_INSTRUMENTATION',
            'reason': 'Pinned VllmGenerationWorker exposes generate/generate_text, not a raw-logit or top24 read-only method. Native SamplingParams rejects max_tokens<1. A five-prefix zero-response raw-logit diagnostic would require new runtime instrumentation; not performed under the bounded diagnostic instruction.',
            'source_sha256': {
                'vllm_worker.py': sha(ROOT / 'nemo_rl/nemo_rl/models/generation/vllm/vllm_worker.py'),
                'sampling_params.py': sha(ROOT / 'nemo_rl/.venv/lib/python3.12/site-packages/vllm/sampling_params.py')},
            'new_gpu_leases': 0, 'new_responses': 0, 'new_judge_calls': 0},
        'not_passed': ['current_policy_gradient_probability_control', 'disposable_optimizer_step',
            'optimizer_rng_sampler_save_reload', 'post_update_generation_refit',
            'full_context_optimizer_memory', 'on_policy_six_rating_transport',
            'calibration_informativeness', 'full_pipeline_capacity'],
        'interpretation': 'Observed generation/recomputed truncated-policy support disagreement at unchanged weights. Backend finite-precision differences are a plausible cause, not a proven exclusive cause. This candidate is not admitted; no claim of intrinsic impossibility or of a negative learning effect.',
        'forbidden_workarounds_not_used': ['sampling substitution', 'epsilon probability floor',
            'sample deletion or replacement', 'relaxed tolerance', 'zero missing-FSC reward'],
        'hashes': {str(p.relative_to(ROOT)): sha(p) for p in
            [control / 'batch_0.pt', control / 'batch_0_audit.json', control / 'resolved_config.json',
             control / 'prospective_budget.json', control / 'failure.json',
             replay / 'probability_diagnostic.json', replay / 'resolved_config.json', *files]},
        'scientific_admission': False, 'resource_deadline_exhausted': False,
        'learning_conclusion': None}
    (HERE / 'results/technical_gate.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result['probabilities'], indent=2))


if __name__ == '__main__':
    main()
