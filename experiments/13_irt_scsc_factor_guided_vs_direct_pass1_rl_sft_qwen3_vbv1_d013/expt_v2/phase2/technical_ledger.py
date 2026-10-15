"""Fence technical-gate attempts and final statistics under the published pilot lock and A4."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'phase1'))
from g1_driver import verify_publication
from training_checkpoint import digest, write_new

GATES = ('T1', 'T2', 'T3', 'T4')
PREVIOUS = {'T1': (), 'T2': ('T1',), 'T3': ('T2',), 'T4': ('T2', 'T3')}
SCIENCE_KEYS = {'model', 'tokenizer', 'sampler', 'mask', 'numerics', 'optimizer',
                'scheduler', 'probability_probe', 'update_probe', 'seeds', 'thresholds', 'resource_caps'}


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


@contextmanager
def fence(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    with (root/'admission.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield root


def published(reference, repository):
    value = verify_publication(reference['path'], repository, reference['revision'])
    if digest(reference['path']) != reference['sha256']:
        raise ValueError('published receipt hash changed')
    return value


def pilot_lock(reference, repository):
    lock = published(reference, repository)
    if (lock.get('condition'), lock.get('gate'), lock.get('status')) != ('v2-S2', 'LP', 'FROZEN'):
        raise ValueError('a published frozen S2 pilot lock is required')
    if not SCIENCE_KEYS <= set(lock['science']):
        raise ValueError('pilot lock omits scientific settings')
    bound = {}
    for row in lock['bindings']:
        path = str(Path(row['path']).resolve())
        if path in bound or digest(path) != row['sha256']:
            raise ValueError('duplicate or changed pilot binding')
        bound[path] = row['sha256']
    if bound.get(str(Path(__file__).resolve())) != digest(__file__):
        raise ValueError('technical admission implementation is unbound')
    return lock, signature(lock['science'])


def check_preflight(reference):
    path = Path(reference['path'])
    if digest(path) != reference['sha256']:
        raise ValueError('preflight receipt changed')
    receipt = json.loads(path.read_text())
    if (receipt.get('status') != 'PASS' or receipt.get('scope') != 'non-probe infrastructure only'
            or receipt.get('admission_statistics_computed') is not False
            or receipt.get('generated_tokens') != 1
            or not re.fullmatch(r'[0-9]+', receipt.get('visible_index', ''))):
        raise ValueError('actual non-probe numeric-device engine preflight required')
    return receipt


def verify_successor(successor, previous, current, repository, science_sha):
    fix = published(successor, repository)
    if (fix.get('gate') != 'A4_TECHNICAL_FIX' or fix.get('status') != 'FROZEN'
            or fix.get('previous_LP_sha256') != previous['LP']['sha256']
            or fix.get('successor_LP_sha256') != current['sha256']
            or fix.get('science_sha256') != science_sha or not fix.get('changed_bindings')):
        raise ValueError('published A4 successor does not match this attempt')
    old = published(previous['LP'], repository); new = published(current, repository)
    old_bind = {r['path']: r['sha256'] for r in old['bindings']}
    new_bind = {r['path']: r['sha256'] for r in new['bindings']}
    changes = {r['path']: r for r in fix['changed_bindings']}
    changed = {path for path in old_bind.keys() | new_bind.keys() if old_bind.get(path) != new_bind.get(path)}
    if set(changes) != changed or not changed:
        raise ValueError('A4 changed binding inventory incomplete')
    for path in changed:
        row = changes[path]
        if (row.get('previous_sha256') != old_bind.get(path) or row.get('successor_sha256') != new_bind.get(path)
                or not row.get('reason')):
            raise ValueError('A4 binding change not explained exactly')
    test = published(fix['regression_test'], repository)
    if test.get('status') != 'PASS' or test.get('exit_code') != 0 or test.get('reproduced_original_defect') is not True:
        raise ValueError('published regression reproduction and fix verification required')
    prior_result = published(fix['failed_attempt_result'], repository)
    if (prior_result.get('status') != 'INCOMPLETE_INFRA' or prior_result.get('admission_statistics_computed') is not False
            or prior_result.get('attempt_sha256') != previous['attempt_sha256']):
        raise ValueError('failed attempt has not been published')


def admit(root, gate, *, LP, repository, preflight, prerequisites, successor=None):
    """Reserve a numbered attempt only after health preflight; no implicit recovery attempt."""
    if gate not in GATES: raise ValueError('A4 ledger only covers T1 through T4')
    lock, science_sha = pilot_lock(LP, repository)
    check_preflight(preflight)
    if set(prerequisites) != set(PREVIOUS[gate]): raise ValueError('gate prerequisite set changed')
    for name, reference in prerequisites.items():
        result = published(reference, repository)
        if (result.get('gate') != name or result.get('condition') != 'v2-S2'
                or result.get('status') != 'PASS' or result.get('admission_statistics_computed') is not True
                or result.get('science_sha256') != science_sha):
            raise ValueError('preceding technical gate is not an admitted same-science PASS')
    if Path(root).resolve() != Path(lock['configuration']['technical_ledger']).resolve():
        raise ValueError('technical attempt ledger cannot move or reset')
    with fence(root) as root:
        gate_root = root/gate; gate_root.mkdir(exist_ok=True)
        attempts = sorted(gate_root.glob('attempt_*/attempt.json'))
        if len(attempts) >= 3: raise RuntimeError('three technical attempts exhausted')
        for number, path in enumerate(attempts, 1):
            record = json.loads(path.read_text())
            if path.parent.name != f'attempt_{number}' or record['attempt'] != number or record['science_sha256'] != science_sha:
                raise ValueError('technical history or science changed')
            if (path.parent/'evaluation_attempt.json').exists():
                raise RuntimeError('gate statistic evaluation is final, including interrupted evaluation')
        if attempts:
            previous = json.loads(attempts[-1].read_text())
            result_path = attempts[-1].parent/'result.json'
            if not result_path.exists(): raise RuntimeError('previous attempt is still unresolved')
            result = json.loads(result_path.read_text())
            if (result.get('status') != 'INCOMPLETE_INFRA' or result.get('admission_statistics_computed') is not False
                    or result.get('cleanup_verified') is not True):
                raise RuntimeError('previous attempt does not admit infrastructure recovery')
            if successor is None: raise RuntimeError('explicit published A4 fix required before another attempt')
            previous['attempt_sha256'] = digest(attempts[-1])
            verify_successor(successor, previous, LP, repository, science_sha)
        elif successor is not None:
            raise ValueError('first attempt cannot consume a recovery successor')
        number = len(attempts)+1; attempt_root = gate_root/f'attempt_{number}'; attempt_root.mkdir()
        value = {'condition': 'v2-S2', 'gate': gate, 'attempt': number, 'status': 'ADMITTED',
                 'LP': LP, 'LP_sha256': LP['sha256'], 'science_sha256': science_sha,
                 'preflight': preflight, 'prerequisites': prerequisites, 'successor': successor,
                 'started_unix': time.time(), 'admission_statistics_computed': False}
        write_new(attempt_root/'attempt.json', value)
        return attempt_root, value


def finish_infrastructure(attempt_root, *, evidence, cleanup_verified):
    """Preserve a reproducible defect without computing or inventing an admission statistic."""
    root = Path(attempt_root)
    with fence(root):
        if (root/'evaluation_attempt.json').exists(): raise RuntimeError('evaluated gate is final')
        if not cleanup_verified or not evidence.get('reproducible_defect'):
            raise ValueError('verified cleanup and reproducible infrastructure evidence required')
        paths = evidence.get('bindings', [])
        if not paths or any(digest(r['path']) != r['sha256'] for r in paths):
            raise ValueError('private defect evidence is missing or changed')
        attempt = json.loads((root/'attempt.json').read_text())
        result = {**attempt, 'status': 'INCOMPLETE_INFRA', 'cleanup_verified': True, 'evidence': evidence,
                  'attempt_sha256': digest(root/'attempt.json'), 'ended_unix': time.time()}
        write_new(root/'result.json', result)
        return result


def evaluate_once(attempt_root, inputs, evaluator):
    """Bind complete raw receipts before the sole admission-statistic computation."""
    root = Path(attempt_root)
    with fence(root):
        if (root/'result.json').exists(): raise RuntimeError('technical attempt already closed')
        if not inputs or len({r['path'] for r in inputs}) != len(inputs):
            raise ValueError('complete unique evaluation bindings required')
        if any(digest(r['path']) != r['sha256'] for r in inputs): raise ValueError('raw admission input changed')
        attempt = json.loads((root/'attempt.json').read_text())
        write_new(root/'evaluation_attempt.json', {'inputs': inputs, 'attempt_sha256': digest(root/'attempt.json')})
        value = evaluator()
        if (value.get('gate') != attempt['gate'] or value.get('condition') != 'v2-S2'
                or value.get('admission_statistics_computed') is not True
                or value.get('status') not in ('PASS', 'FAIL', 'INCONCLUSIVE')):
            raise ValueError('invalid final technical admission result')
        value.update(attempt=attempt['attempt'], LP_sha256=attempt['LP_sha256'],
                     science_sha256=attempt['science_sha256'], attempt_sha256=digest(root/'attempt.json'), inputs=inputs)
        write_new(root/'result.json', value)
        return value
