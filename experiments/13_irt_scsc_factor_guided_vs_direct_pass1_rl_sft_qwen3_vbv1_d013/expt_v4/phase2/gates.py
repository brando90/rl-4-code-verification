"""TLDR: Evaluate v4 technical gates from complete, finite, hash-bound measurements."""
import math
import numpy as np
from common import object_digest


def probability_agreement(positions, *, expected_positions, expected_responses=8):
    if not positions or len(positions) != expected_positions:
        raise ValueError('full declared token denominator required')
    keys = {(p['response'], p['position']) for p in positions}
    if len(keys) != len(positions) or len({p['response'] for p in positions}) != expected_responses:
        raise ValueError('duplicate positions or incomplete response probe')
    for response in {p['response'] for p in positions}:
        idx = sorted(p['position'] for p in positions if p['response'] == response)
        if idx != list(range(len(idx))):
            raise ValueError('missing response position')
    error, discarded, outside, identical, truncated, uncertified = [], [], 0, 0, 0, 0
    for p in positions:
        trainer = set(p['trainer_support'])
        if not trainer or not math.isfinite(p['trainer_logp']) or not math.isfinite(p['discarded_mass']) or not 0 <= p['discarded_mass'] <= 1:
            raise ValueError('invalid trainer probability evidence')
        outside += p['token'] not in trainer
        discarded.append(p['discarded_mass'])
        if not p['certified']:
            uncertified += 1
            continue
        if not p['top_k_certified'] or not p['nucleus_certified']:
            raise ValueError('inconsistent certificate')
        gen = set(p['generator_support'])
        if not gen or p['token'] not in gen or not math.isfinite(p['generator_logp']):
            raise ValueError('invalid certified generator support')
        error.append(abs(p['generator_logp']-p['trainer_logp']))
        identical += gen == trainer
        truncated += p['trainer_logp']-p['generator_logp'] > math.log(2)
    n = len(positions)
    result = {'gate': 'V4-T1', 'positions': n, 'responses': expected_responses,
              'certified_positions': n-uncertified, 'uncertified_positions': uncertified,
              'certified_fraction': (n-uncertified)/n,
              'outside_support': outside, 'identical_support_fraction': identical/n,
              'median_absolute_error': float(np.quantile(error, .5)) if error else None,
              'p99_absolute_error': float(np.quantile(error, .99)) if error else None,
              'importance_truncated_known': truncated,
              'importance_truncated_fraction_lower': truncated/n,
              'importance_truncated_fraction_upper': (truncated+uncertified)/n,
              'importance_truncated_fraction': truncated/n if not uncertified else None,
              'median_discarded_mass': float(np.quantile(discarded, .5)),
              'p99_discarded_mass': float(np.quantile(discarded, .99))}
    # Unknown importance corrections are bounded, never invented. Admission
    # separately blocks measured execution until their training semantics exist.
    result['status'] = 'PASS' if (outside == 0 and identical/n >= .99 and error and
        result['median_absolute_error'] <= .01 and result['p99_absolute_error'] <= .10 and
        (truncated+uncertified)/n <= .01) else 'FAIL'
    return result


def select_t2_reward(groups):
    if len(groups) not in (16, 32) or any(len(g) != 256//len(groups) for g in groups):
        raise ValueError('complete declared T2 subset required')
    for field, arm in [('strict', 'A'), ('factored_reward', 'B')]:
        usable = [[r[field] for r in group] for group in groups
                  if all(r[field] is not None for r in group)]
        if any(any(not math.isfinite(v) or not 0 <= v <= 1 for v in g) for g in usable):
            raise ValueError('invalid reward')
        if any(max(g) > min(g) for g in usable):
            return {'status': 'SELECTED', 'arm': arm, 'field': field,
                    'complete_groups': len(usable), 'resample': False}
    return {'status': 'STOP_NO_SIGNAL', 'arm': None, 'resample': False}


def advantages(groups, field):
    """Leave-one-out, no variance normalization; unknown score masks its entire group."""
    result = []
    for group in groups:
        rewards = [r[field] for r in group]
        if any(r is None for r in rewards):
            result.append({'sample_mask': [0]*len(group), 'advantages': [0.]*len(group)})
        else:
            if len(group) < 2 or any(not math.isfinite(r) or not 0 <= r <= 1 for r in rewards):
                raise ValueError('invalid reward group')
            total = sum(rewards)
            result.append({'sample_mask': [1]*len(group),
                           'advantages': [r-(total-r)/(len(group)-1) for r in rewards]})
    return result


def t2(advantages, preclip_gradient_norm, before_weights, after_weights, refit_positions,
       old_supports, new_supports):
    norm = preclip_gradient_norm
    if isinstance(norm, list):
        if len(norm) != 1: raise ValueError('one-rank gradient receipt required')
        norm = norm[0]
    if not advantages or not refit_positions or len(old_supports) != len(new_supports) or not old_supports:
        raise ValueError('incomplete T2 evidence')
    errors = [abs(p['trainer_logp']-p['generator_logp']) for p in refit_positions]
    outside = sum(p['token'] not in p['trainer_support'] for p in refit_positions)
    median = float(np.median(errors))
    criteria = {'finite_nonzero_advantages': all(math.isfinite(x) for x in advantages) and any(x != 0 for x in advantages),
                'finite_nonzero_preclip_gradient': type(norm) in (int, float) and math.isfinite(norm) and norm > 0,
                'changed_weights': bool(before_weights) and bool(after_weights) and before_weights != after_weights,
                'refit_median': all(math.isfinite(e) for e in errors) and median <= .01,
                'refit_support': outside == 0}
    return {'gate': 'V4-T2', 'status': 'PASS' if all(criteria.values()) else 'FAIL', 'criteria': criteria,
            'preclip_gradient_norm': norm, 'refit_median_absolute_error': median, 'refit_outside_support': outside,
            'support_changed_fraction': sum(set(a) != set(b) for a,b in zip(old_supports,new_supports))/len(old_supports)}


REPLAY_KEYS = ('batch', 'rewards', 'advantages', 'old_support', 'pre_weights', 'random_state',
               'optimizer_state', 'scheduler_state', 'admission')


def replay_binding(**hashes):
    if set(hashes) != set(REPLAY_KEYS) or any(len(v) != 64 or any(c not in '0123456789abcdef' for c in v) for v in hashes.values()):
        raise ValueError('all replay inputs require SHA-256 bindings')
    return {'inputs': hashes, 'sha256': object_digest(hashes)}


def t3(original_loss, replay_loss, original_binding, replayed_binding):
    same = original_binding == replayed_binding and original_binding['sha256'] == object_digest(original_binding['inputs'])
    difference = abs(original_loss-replay_loss)
    return {'gate': 'V4-T3', 'status': 'PASS' if same and math.isfinite(difference) and difference <= 1e-3 else 'FAIL',
            'absolute_loss_error': difference, 'identical_replay_inputs': same}


def t4(*, device_seconds, updates, peak_memory_bytes, probe_sequence_length, maximum_train_prompt,
       probe_forward_backward, generated_tokens, generation_seconds, lean_wall_seconds,
       timeout_count, scoring_slots, storage_growth_bytes):
    vals = [device_seconds, peak_memory_bytes, generated_tokens, generation_seconds,
            lean_wall_seconds, timeout_count, storage_growth_bytes]
    if any(not math.isfinite(x) or x < 0 for x in vals) or updates <= 0 or generation_seconds <= 0 or scoring_slots <= 0 or timeout_count > scoring_slots:
        raise ValueError('invalid cost measurement')
    fits = probe_forward_backward is True and probe_sequence_length == maximum_train_prompt + 12288 and peak_memory_bytes > 0
    return {'gate': 'V4-T4', 'status': 'PASS' if fits else 'FAIL', 'device_hours_per_update': device_seconds/3600/updates,
            'peak_trainer_memory_bytes': peak_memory_bytes, 'probe_sequence_length': probe_sequence_length,
            'maximum_length_forward_backward_fits': fits, 'generated_tokens_per_second': generated_tokens/generation_seconds,
            'lean_wall_seconds': lean_wall_seconds, 'deterministic_timeout_rate': timeout_count/scoring_slots,
            'timeouts': timeout_count, 'scoring_slots': scoring_slots, 'storage_growth_bytes': storage_growth_bytes}
