"""TLDR: Prove lease refusals and empty failures from CPU-only durable-file fixtures."""
import json
from pathlib import Path

import pytest

from common import digest, write_new
from device_guard import Busy
import effect_receipts as effects
from recovery import inspect
from stage_ledger import Ledger, RecoveryRequired
import stage_worker


def operation(tmp_path):
    """Create only ledger identities, without any runtime/model invocation."""
    work = tmp_path / 'work'
    attempt = work / 'T1' / 'probe' / 'attempt_01'
    write_new(attempt.parent / 'intent.json', {'fixture': True})
    write_new(attempt / 'started.json', {'synthetic': False})
    return work, attempt


def failed_worker(attempt, *, kind='stage_failure', component='R0', trial='trial_01'):
    root = attempt / component / 'lease_trials' / trial
    config = {'effect_root': str(root), 'stage_root': str(root / 'output'),
              'synthetic': False, 'stage': 'generate'}
    write_new(root / 'runtime.json', config)
    identity = {'runtime_sha256': digest(root / 'runtime.json'), 'effects_schema': 1}
    write_new(root / 'worker_started.json', identity)
    terminal = {**identity, 'effects': {}, 'kind': kind,
                'error_type': 'Busy' if kind == 'lease_refused' else 'RuntimeError',
                'error': 'fixture failure before any scientific effect'}
    write_new(root / 'worker_failed.json', terminal)
    write_new(root / 'execution.json', {'exit_code': 1, 'synthetic': False})
    if kind == 'lease_refused':
        write_new(root / 'lease_refused.json', terminal)
    return root, config


def replace_json(path, **changes):
    value = json.loads(path.read_text())
    value.update(changes)
    path.write_text(json.dumps(value))


def mark_before_failure(root, config, effect):
    """Model a write-ahead effect followed by the worker's terminal receipt."""
    effects.mark(config, effect)
    observed = {name: digest(root / (name + '.json')) for name in effects.EFFECTS
                if (root / (name + '.json')).exists()}
    replace_json(root / 'worker_failed.json', effects=observed)
    if (root / 'lease_refused.json').exists():
        replace_json(root / 'lease_refused.json', effects=observed)


def test_proved_empty_failure_writes_exact_recovery_fields(tmp_path):
    work, attempt = operation(tmp_path)
    root, config = failed_worker(attempt)
    # Loading an engine may consume an attempt, but it does not prove generation.
    mark_before_failure(root, config, 'engine_started')
    assert effects.worker_proof(root)
    assert not effects.worker_proof(root, pre_engine=True)
    assert effects.record_failure(attempt)
    assert json.loads((attempt / 'infrastructure_failure.json').read_text()) == effects.EMPTY
    assert not (attempt / 'lease_refused.json').exists()
    assert effects.verified_failure(attempt)
    assert inspect(work)['action'] == 'RETRY_EMPTY'


@pytest.mark.parametrize('missing', ['worker_started.json', 'worker_failed.json',
                                    'runtime.json', 'execution.json'])
def test_missing_positive_proof_stays_partial(tmp_path, missing):
    work, attempt = operation(tmp_path)
    root, _ = failed_worker(attempt)
    (root / missing).unlink()
    assert not effects.worker_proof(root)
    assert not effects.record_failure(attempt)
    assert not (attempt / 'infrastructure_failure.json').exists()
    assert inspect(work)['action'] == 'STOP_PARTIAL'


@pytest.mark.parametrize('file,changes', [
    ('worker_started.json', {'runtime_sha256': 'wrong'}),
    ('worker_started.json', {'effects_schema': 99}),
    ('worker_failed.json', {'runtime_sha256': 'wrong'}),
    ('worker_failed.json', {'effects_schema': 99}),
    ('execution.json', {'exit_code': 0}),
    ('runtime.json', {'stage': 'changed'}),
])
def test_inconsistent_worker_proof_stays_partial(tmp_path, file, changes):
    work, attempt = operation(tmp_path)
    root, _ = failed_worker(attempt)
    replace_json(root / file, **changes)
    assert not effects.worker_proof(root)
    assert not effects.record_failure(attempt)
    assert inspect(work)['action'] == 'STOP_PARTIAL'


def test_runtime_must_name_the_actual_effect_directory(tmp_path):
    _, attempt = operation(tmp_path)
    root, _ = failed_worker(attempt)
    replace_json(root / 'runtime.json', effect_root=str(tmp_path / 'elsewhere'))
    runtime_sha256 = digest(root / 'runtime.json')
    for name in ('worker_started.json', 'worker_failed.json'):
        replace_json(root / name, runtime_sha256=runtime_sha256)
    assert not effects.worker_proof(root)


@pytest.mark.parametrize('effect', ['generation_started', 'optimizer_started'])
def test_started_effect_blocks_retry_even_without_output_files(tmp_path, effect):
    work, attempt = operation(tmp_path)
    root, config = failed_worker(attempt)
    mark_before_failure(root, config, effect)
    assert not list(attempt.rglob('*.generation.json'))
    assert not effects.worker_proof(root)
    assert not effects.record_failure(attempt)
    assert inspect(work)['action'] == 'STOP_PARTIAL'


@pytest.mark.parametrize('effect', effects.EFFECTS)
def test_deleted_effect_marker_cannot_turn_failure_into_empty(tmp_path, effect):
    work, attempt = operation(tmp_path)
    root, config = failed_worker(attempt)
    mark_before_failure(root, config, effect)
    (root / (effect + '.json')).unlink()
    assert not effects.worker_proof(root)
    assert not effects.record_failure(attempt)
    assert inspect(work)['action'] == 'STOP_PARTIAL'


@pytest.mark.parametrize('name', ['00000.generation.json', 'optimizer_intent.json',
                                 'statistics_reserved.json', 'statistic.json', 'batch.pt'])
def test_durable_effect_artifact_blocks_empty_record(tmp_path, name):
    work, attempt = operation(tmp_path)
    root, _ = failed_worker(attempt)
    write_new(root / 'output' / name, {})
    assert not effects.record_failure(attempt)
    assert inspect(work)['action'] == 'STOP_PARTIAL'


def test_stage_statistic_reservation_prevents_retry(tmp_path):
    work, attempt = operation(tmp_path)
    failed_worker(attempt)
    write_new(work / 'T1' / 'statistics_reserved.json', {'reserved': True})
    assert not effects.record_failure(attempt)
    assert inspect(work)['action'] == 'STOP_STATISTIC'


def test_bare_empty_record_is_insufficient_for_real_failure(tmp_path):
    work, attempt = operation(tmp_path)
    write_new(attempt / 'infrastructure_failure.json', effects.EMPTY)
    assert not effects.retryable_empty(attempt)
    assert inspect(work)['action'] == 'STOP_PARTIAL'


@pytest.mark.parametrize('refused', [False, True])
@pytest.mark.parametrize('mutation', ['runtime', 'terminal', 'execution', 'new_effect'])
def test_mutation_invalidates_recorded_failure(tmp_path, refused, mutation):
    work, attempt = operation(tmp_path)
    root, config = failed_worker(attempt, kind='lease_refused' if refused else 'stage_failure')
    assert effects.record_failure(attempt)
    assert effects.verified_failure(attempt, refused=refused)
    if mutation == 'new_effect':
        effects.mark(config, 'generation_started')
    elif mutation == 'runtime':
        replace_json(root / 'runtime.json', changed=True)
    elif mutation == 'terminal':
        replace_json(root / 'worker_failed.json', error='changed')
    else:
        replace_json(root / 'execution.json', exit_code=2)
    assert not effects.verified_failure(attempt, refused=refused)
    assert inspect(work)['action'] == 'STOP_PARTIAL'


def test_every_failed_invocation_needs_proof(tmp_path):
    _, attempt = operation(tmp_path)
    failed_worker(attempt, trial='trial_01')
    root, _ = failed_worker(attempt, trial='trial_02')
    (root / 'worker_failed.json').unlink()
    assert not effects.operation_proof(attempt)
    assert not effects.record_failure(attempt)


def test_mutated_leaf_lease_receipt_cannot_prove_unconsumed_attempt(tmp_path):
    work, attempt = operation(tmp_path)
    root, _ = failed_worker(attempt, kind='lease_refused')
    assert effects.record_failure(attempt)
    (root / 'lease_refused.json').write_text('{}')
    assert not effects.verified_failure(attempt, refused=True)
    assert inspect(work)['action'] == 'STOP_PARTIAL'


def test_component_refusal_after_prior_generation_stays_partial(tmp_path):
    work, attempt = operation(tmp_path)
    root, _ = failed_worker(attempt, component='R1', kind='lease_refused')
    write_new(attempt / 'R0' / 'output' / '00000.generation.json', {'output_token_ids': [42]})
    assert effects.worker_proof(root, pre_engine=True)
    assert not effects.operation_proof(attempt, pre_engine=True)
    assert not effects.record_failure(attempt)
    assert not (attempt / 'lease_refused.json').exists()
    assert not (attempt / 'infrastructure_failure.json').exists()
    assert inspect(work)['action'] == 'STOP_PARTIAL'


@pytest.mark.parametrize('effect,kind', [(None, 'lease_refused'),
                                      ('engine_started', 'stage_failure'),
                                      ('generation_started', 'stage_failure'),
                                      ('optimizer_started', 'stage_failure')])
def test_worker_receipt_records_refusal_only_before_engine(tmp_path, monkeypatch, effect, kind):
    root = tmp_path / 'invocation'
    config = {'effect_root': str(root), 'stage_root': str(root / 'output')}
    write_new(root / 'runtime.json', config)
    def fail(runtime, stub=False):
        assert (root / 'worker_started.json').exists()
        if effect:
            effects.mark(runtime, effect)
        raise Busy('foreign process fixture')
    monkeypatch.setattr(stage_worker, '_run', fail)
    with pytest.raises(Busy, match='foreign process fixture'):
        stage_worker.run(config)
    terminal = json.loads((root / 'worker_failed.json').read_text())
    assert terminal['kind'] == kind
    assert terminal['runtime_sha256'] == digest(root / 'runtime.json')
    assert (root / 'lease_refused.json').exists() is (kind == 'lease_refused')


def test_worker_records_non_busy_failure_as_real_failure(tmp_path, monkeypatch):
    root = tmp_path / 'invocation'
    config = {'effect_root': str(root), 'stage_root': str(root / 'output')}
    write_new(root / 'runtime.json', config)
    def fail(*args, **kwargs):
        raise ValueError('runtime dependency failure')
    monkeypatch.setattr(stage_worker, '_run', fail)
    with pytest.raises(ValueError, match='runtime dependency failure'):
        stage_worker.run(config)
    terminal = json.loads((root / 'worker_failed.json').read_text())
    assert terminal['kind'] == 'stage_failure'
    assert not (root / 'lease_refused.json').exists()


def test_lease_refusal_does_not_reduce_three_real_attempt_allowance(tmp_path):
    admission = tmp_path / 'admission.json'
    write_new(admission, {'fixture': 'admission identity only'})
    ledger = Ledger(tmp_path / 'work', admission, synthetic=False)
    calls = []
    def refused(path, payload):
        calls.append(('refused', path))
        failed_worker(path, kind='lease_refused')
        raise effects.LeaseRefused('bounded idle retry exhausted')
    def empty(path, payload):
        calls.append(('empty', path))
        root, config = failed_worker(path)
        mark_before_failure(root, config, 'engine_started')
        raise RuntimeError('engine construction failed before generation')
    with pytest.raises(effects.LeaseRefused):
        ledger.operation('T1', 'probe', {'responses': 8}, refused)
    refused_path = calls[-1][1]
    assert effects.verified_failure(refused_path, refused=True)
    for index in range(3):
        with pytest.raises(RuntimeError, match='engine construction failed before generation'):
            # A proved pre-engine refusal can proceed without A4 recovery.
            ledger.operation('T1', 'probe', {'responses': 8}, empty, recover=index > 0)
        assert effects.verified_failure(calls[-1][1])
    assert len(calls) == 4
    assert refused_path.exists()
    with pytest.raises(RecoveryRequired):
        ledger.operation('T1', 'probe', {'responses': 8}, empty, recover=True)
    assert len(calls) == 4
    assert inspect(tmp_path / 'work')['action'] == 'STOP_A4_CAP'


def test_durable_refusal_limit_blocks_more_stage_launches(tmp_path):
    admission = tmp_path / 'admission.json'
    write_new(admission, {'fixture': 'admission identity only'})
    ledger = Ledger(tmp_path / 'work', admission, synthetic=False)
    calls = []
    def refused(path, payload):
        calls.append(path)
        for trial in range(120):
            failed_worker(path, kind='lease_refused', trial=f'trial_{trial:03d}')
        raise effects.LeaseRefused('bounded idle retry exhausted')
    with pytest.raises(effects.LeaseRefused):
        ledger.operation('T1', 'probe', {'responses': 8}, refused)
    assert effects.verified_failure(calls[0], refused=True)
    assert inspect(tmp_path / 'work')['action'] == 'STOP_LEASE_CAP'
    with pytest.raises(RecoveryRequired, match='lease refusal cap'):
        ledger.operation('T1', 'probe', {'responses': 8}, refused, recover=True)
    assert len(calls) == 1
