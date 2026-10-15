"""Enforce the frozen A5 candidate order, numerical-only changes and final confirmation."""
from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path

from panel import digest, validate_manifest
from a4_admission import admit_attempt

MARGIN = {'median_absolute_logprob_error': .008, 'p99_absolute_logprob_error': .08,
          'importance_truncation_fraction': .008}


def qualifies(result):
    if (not result.get('admission_statistics_computed') or result.get('responses') != 8
            or result.get('unsupported_tokens') != 0 or not result.get('cleanup_verified', True)
            or result.get('status') not in ('PASS', 'FAIL')):
        return False
    return all(isinstance(result.get(k), (float, int)) and math.isfinite(result[k])
               and 0 <= result[k] <= limit for k, limit in MARGIN.items())


def numerical_policy(old, new, dtype):
    expected = deepcopy(old)
    expected['precision'] = dtype
    expected['generation']['vllm_cfg']['precision'] = dtype
    if new != expected:
        raise ValueError('A5 permits only identical generator/trainer dtype changes')


def ordered_selection(candidates, receipts, *, confirmation=False):
    """A measured candidate is final; never skip a candidate or continue past a pass."""
    if len(receipts) > len(candidates):
        raise ValueError('too many development results')
    for index, result in enumerate(receipts):
        if (result.get('candidate') != candidates[index]['id']
                or result.get('a5_stage') != 'development'
                or not result.get('admission_statistics_computed')
                or result.get('status') not in ('PASS', 'FAIL')
                or result.get('responses') != 8):
            raise ValueError('missing, nonfinal or out-of-order development measurement')
        if qualifies(result):
            if index != len(receipts)-1:
                raise ValueError('candidate measured after the first qualifying setting')
            if confirmation:
                return candidates[index]
            raise ValueError('development must stop after a qualifying setting')
    if confirmation or len(receipts) == len(candidates):
        raise ValueError('no qualifying candidate for confirmation')
    return candidates[len(receipts)]


def unchanged_science(old, new, dtype, stage):
    if new['maximum_seconds'] != 1800 or not 0 < new['cumulative_limit_hours'] <= 3.6:
        raise ValueError('A5 device budget changed')
    for key in set(old) | set(new):
        if key not in ('status', 'routes', 'cumulative_limit_hours', 'resource_plan') and old.get(key) != new.get(key):
            raise ValueError('A5 changed a nonnumerical dispatch setting: '+key)
    if len(old['routes']) != len(new['routes']):
        raise ValueError('A5 route cohort changed')
    runtime_changes = {'attempt_root', 'generation_root', 'ray_temp', 'attempt_number',
                       'numerical_dtype', 'candidate', 'a5_stage', 'policy_config', 'bindings'}
    if stage == 'development':
        runtime_changes.add('manifest')
    for prior, current in zip(old['routes'], new['routes']):
        for key in set(prior) | set(current):
            if key not in ('runtime', 'config_path', 'lease_path') and prior.get(key) != current.get(key):
                raise ValueError('A5 changed a nonnumerical route setting: '+key)
        a, b = prior['runtime'], current['runtime']
        if {k:v for k,v in a.items() if k not in runtime_changes} != {
                k:v for k,v in b.items() if k not in runtime_changes}:
            raise ValueError('A5 changed a nonnumerical runtime setting')
        if b['numerical_dtype'] != dtype or b['a5_stage'] != stage:
            raise ValueError('A5 condition differs across routes')
        # Every old source/input remains bound unless its replacement is explicitly
        # named here. Frozen old policy and probe are additionally bound by the lock.
        new_bound = {x['path']: x['sha256'] for x in b['bindings']}
        replace_paths = {a['policy_config']}
        if stage == 'development': replace_paths.add(a['manifest'])
        for entry in a['bindings']:
            path = entry['path']
            if path in replace_paths or Path(path).name in ('runtime.py', 'lp1.py', 'panel.py'):
                continue
            if new_bound.get(path) != entry['sha256']:
                raise ValueError('A5 altered an unchanged runtime binding: '+path)


def validate_dispatch(lock, config):
    bound = {b['path'] for b in lock['bindings']}
    required = [lock['candidate_list'], lock['previous_configuration'], lock['baseline_registry']]
    if not set(required) <= bound:
        raise ValueError('unbound A5 provenance')
    declaration = json.loads(Path(lock['candidate_list']).read_text())
    candidates = declaration['candidates']
    if not 1 <= len(candidates) <= 4 or declaration['status'] != 'FROZEN':
        raise ValueError('invalid frozen candidate list')
    if declaration['development_thresholds'] != {'unsupported_tokens':0, **MARGIN}:
        raise ValueError('development margin changed')
    stage = lock['a5_stage']
    if stage not in ('development', 'confirmation'):
        raise ValueError('unknown A5 stage')
    receipts = []
    for entry in lock['development_receipts']:
        if digest(entry['path']) != entry['sha256']:
            raise ValueError('development evidence changed')
        receipts.append(json.loads(Path(entry['path']).read_text()))
    selected = ordered_selection(candidates, receipts, confirmation=stage == 'confirmation')
    if selected['id'] != lock['candidate'] or selected['dtype'] != lock['numerical_dtype']:
        raise ValueError('not the first admitted candidate')
    if stage == 'development' and lock['configuration_sha256'] != selected['configuration_sha256']:
        raise ValueError('candidate configuration differs from the frozen list')
    baseline = json.loads(Path(lock['baseline_registry']).read_text())
    if any(r['status'] != 'RELEASED' for r in baseline['leases']):
        raise ValueError('A5 baseline has an unresolved lease')
    if config['cumulative_limit_hours'] != baseline['device_hours'] + 3.0:
        raise ValueError('A5 cumulative allowance differs from the frozen baseline plus 3 hours')
    old = json.loads(Path(lock['previous_configuration']).read_text())
    unchanged_science(old, config, selected['dtype'], stage)
    # Local and copied remote policies/manifests are hash-bound; identical route
    # hashes are checked by the preparer, then checked again on the claimed host.
    route = config['routes'][0]['runtime']
    prior = old['routes'][0]['runtime']
    numerical_policy(json.loads(Path(prior['policy_config']).read_text()),
                     json.loads(Path(route['policy_config']).read_text()), selected['dtype'])
    manifest = json.loads(Path(route['manifest']).read_text())
    validate_manifest(manifest, Path(route['train_ids']).read_text().splitlines())
    expected_batch = 'lp1_a5_dev' if stage == 'development' else 'lp1'
    if manifest['batch'] != expected_batch:
        raise ValueError('wrong probe for A5 stage')
    if stage == 'development' and digest(route['manifest']) != declaration['development_manifest_sha256']:
        raise ValueError('development manifest differs from the frozen candidate declaration')
    number = lock.get('attempt_number', 1)
    previous = lock.get('previous_attempts', [])
    if number == 1:
        if previous: raise ValueError('first attempt has prior attempts')
    else:
        if not set(previous) <= bound: raise ValueError('unbound infrastructure receipts')
        admit_attempt(number, [json.loads(Path(p).read_text()) for p in previous])
    if any(r['runtime']['attempt_number'] != number or r['runtime']['candidate'] != selected['id']
           for r in config['routes']):
        raise ValueError('A5 attempt/candidate differs across routes')
