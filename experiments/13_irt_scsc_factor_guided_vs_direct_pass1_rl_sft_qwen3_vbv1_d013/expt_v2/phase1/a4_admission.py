"""Enforce A4's attempt bound, statistic finality and unchanged scientific configuration."""
from copy import deepcopy
from pathlib import Path

STATISTICS = ('unsupported_tokens', 'median_absolute_logprob_error',
              'p99_absolute_logprob_error', 'importance_truncation_fraction')


def admit_attempt(number, previous):
    if number not in (2, 3) or len(previous) != number-1:
        raise ValueError('A4 requires consecutive attempts, at most three')
    for result in previous:
        if result.get('admission_statistics_computed') or any(result.get(k) is not None for k in STATISTICS):
            raise ValueError('admission statistics were computed; attempt is final')
        if result.get('status') not in ('INCOMPLETE', 'INCOMPLETE-INFRA'):
            raise ValueError('only documented incomplete infrastructure attempts are eligible')
        if result.get('scientific_probability_verdict', 'UNMEASURED') != 'UNMEASURED':
            raise ValueError('scientific verdict is final')


def unchanged_science(previous, current):
    """Allow only new output paths, numbered accounting and named infrastructure code."""
    old, new = deepcopy(previous), deepcopy(current)
    old.pop('status', None); new.pop('status', None)
    if len(old['routes']) != len(new['routes']):
        raise ValueError('device routes changed')
    for before, after in zip(old['routes'], new['routes']):
        for key in ('config_path', 'lease_path'):
            after[key] = before[key]
        a, b = before['runtime'], after['runtime']
        if b.pop('attempt_number', None) not in (2, 3):
            raise ValueError('missing A4 attempt number')
        for key in ('attempt_root', 'generation_root', 'ray_temp'):
            if a[key] == b[key]:
                raise ValueError('A4 must preserve previous output paths')
            b[key] = a[key]
        original = {x['path']:x['sha256'] for x in a['bindings']}
        revised = {x['path']:x['sha256'] for x in b['bindings']}
        if len(revised) != len(b['bindings']) or not original.keys() <= revised.keys():
            raise ValueError('missing or duplicate previous bindings')
        code = Path(before['lp1_script']).parent
        mutable = {str(code/name) for name in ('runtime.py','lp1.py')}
        for path, sha in original.items():
            if path not in mutable and revised[path] != sha:
                raise ValueError('scientific binding changed: '+path)
        if set(revised)-set(original) != {str(code/'device_binding.py')}:
            raise ValueError('unexpected new runtime binding')
        b['bindings'] = a['bindings']
    if old != new:
        raise ValueError('scientific setting or resource cap changed')
