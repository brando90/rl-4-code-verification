"""TLDR: Verify narrow readmission and leased execution retries using only CPU file fixtures."""
from contextlib import contextmanager
import json
import os
from pathlib import Path

import pytest

from common import digest, object_digest, write_new
import effect_receipts as effects
import readmission
from stage_ledger import Ledger


@pytest.fixture
def migration(tmp_path, monkeypatch):
    """Model old/new identities without accepting any historical production proof."""
    work = tmp_path / 'run'
    prior = tmp_path / 'prior_admission.json'
    write_new(prior, {'synthetic_fixture': True})
    old = digest(prior)
    monkeypatch.setattr(readmission, 'OLD_ADMISSION', old)
    payload = {'responses': 8, 'full': True, 'compare_receipt_on_off': True}
    identity = {'condition': 'e13v4', 'admission_sha256': old, 'synthetic': True}
    originals = {
        'T1/intent.json': {**identity, 'stage': 'T1', 'predecessors': {}},
        'T1/probe/intent.json': {**identity, 'payload': payload,
                                 'payload_sha256': object_digest(payload)},
    }
    for name, value in originals.items():
        write_new(work / name, value)
    attempt = work / 'T1/probe/attempt_01'
    write_new(attempt / 'started.json', identity)
    write_new(attempt / 'zero_effect_evidence.json', {'synthetic_fixture': True})
    admission = tmp_path / 'new_admission.json'
    record = {'readmission': {
        'work': str(work), 'prior_admission_sha256': old,
        'intents': {name: digest(work / name) for name in originals},
        'evidence_sha256': digest(attempt / 'zero_effect_evidence.json'),
    }}
    write_new(admission, record)
    proof_calls = []

    def proof(path, *, refused=False):
        proof_calls.append((Path(path), refused))
        return Path(path) == attempt and refused

    monkeypatch.setattr(effects, 'verified_failure', proof)
    import stage_ledger
    monkeypatch.setattr(stage_ledger, 'verified_failure', proof)
    return work, admission, originals, payload, attempt, proof_calls


@pytest.mark.parametrize('relative', ['T1/intent.json', 'T1/probe/intent.json'])
def test_readmission_accepts_only_admission_substitution(migration, relative):
    work, admission, originals, _, _, proof_calls = migration
    before = {name: (work / name).read_bytes() for name in originals}
    expected = {**originals[relative], 'admission_sha256': digest(admission)}
    assert readmission.accepts(admission, work, work / relative, expected)
    assert proof_calls and proof_calls[-1][1] is True
    assert before == {name: (work / name).read_bytes() for name in originals}


def test_readmitted_ledger_preserves_history_and_completes_under_new_admission(migration):
    work, admission, originals, payload, attempt, _ = migration
    before = {p: p.read_bytes() for p in work.rglob('*') if p.is_file()}
    ledger = Ledger(work, admission, synthetic=True)
    assert ledger.begin('T1', []) is None
    calls = []

    def action(path, data):
        calls.append((path, data))
        return {'synthetic_fixture': True}

    assert ledger.operation('T1', 'probe', payload, action, recover=True) == {'synthetic_fixture': True}
    assert calls == [(attempt.with_name('attempt_02'), payload)]
    receipt = ledger.finish('T1', {'status': 'PASS', 'synthetic_fixture': True})
    assert receipt['admission_sha256'] == digest(admission)
    assert ledger.completed('T1') == receipt
    assert before == {p: p.read_bytes() for p in before}
    assert not (work / 'T1/statistics_reserved.json').exists()


@pytest.mark.parametrize('relative,changes', [
    ('T1/intent.json', {'synthetic': False}),
    ('T1/intent.json', {'predecessors': {'other': 'digest'}}),
    ('T1/intent.json', {'stage': 'G0_GENERATE'}),
    ('T1/probe/intent.json', {'payload': {'responses': 16}}),
    ('T1/probe/intent.json', {'payload_sha256': 'changed'}),
    ('T1/probe/intent.json', {'synthetic': False}),
    ('T1/probe/intent.json', {'condition': 'other'}),
])
def test_readmission_rejects_scientific_or_identity_changes(migration, relative, changes):
    work, admission, originals, _, _, _ = migration
    expected = {**originals[relative], 'admission_sha256': digest(admission), **changes}
    assert not readmission.accepts(admission, work, work / relative, expected)


@pytest.mark.parametrize('fault', ['missing_evidence', 'changed_evidence', 'changed_intent',
                                  'missing_transition', 'wrong_work', 'wrong_prior',
                                  'wrong_intent_binding', 'wrong_evidence_binding', 'failed_proof'])
def test_readmission_rejects_missing_or_bad_evidence(migration, monkeypatch, fault):
    work, admission, originals, _, attempt, _ = migration
    record = json.loads(admission.read_text())
    if fault == 'missing_evidence':
        (attempt / 'zero_effect_evidence.json').unlink()
    elif fault == 'changed_evidence':
        (attempt / 'zero_effect_evidence.json').write_text('{"changed": true}')
    elif fault == 'changed_intent':
        (work / 'T1/intent.json').write_text(json.dumps({**originals['T1/intent.json'], 'changed': True}))
    elif fault == 'missing_transition':
        record.pop('readmission')
    elif fault == 'wrong_work':
        record['readmission']['work'] = str(work.parent / 'elsewhere')
    elif fault == 'wrong_prior':
        record['readmission']['prior_admission_sha256'] = 'wrong'
    elif fault == 'wrong_intent_binding':
        record['readmission']['intents']['T1/intent.json'] = 'wrong'
    elif fault == 'wrong_evidence_binding':
        record['readmission']['evidence_sha256'] = 'wrong'
    else:
        monkeypatch.setattr(effects, 'verified_failure', lambda *a, **kw: False)
    admission.write_text(json.dumps(record))
    expected = {**originals['T1/intent.json'], 'admission_sha256': digest(admission)}
    assert not readmission.accepts(admission, work, work / 'T1/intent.json', expected)


@pytest.mark.parametrize('relative', ['T2/intent.json', 'T1/other/intent.json'])
def test_readmission_rejects_other_stage_or_operation(migration, relative):
    work, admission, originals, _, _, _ = migration
    write_new(work / relative, originals['T1/intent.json'])
    record = json.loads(admission.read_text())
    record['readmission']['intents'][relative] = digest(work / relative)
    admission.write_text(json.dumps(record))
    expected = {**originals['T1/intent.json'], 'admission_sha256': digest(admission)}
    assert not readmission.accepts(admission, work, work / relative, expected)


def test_readmission_never_rebinds_completed_stage_receipt(migration):
    work, admission, originals, _, _, _ = migration
    write_new(work / 'T1/receipt.json', {**originals['T1/intent.json'], 'status': 'PASS',
                                       'artifacts': {}, 'predecessors': {}})
    with pytest.raises(ValueError, match='receipt admission or mode changed'):
        Ledger(work, admission, synthetic=True).completed('T1')


def test_legacy_proof_mapping_counts_as_one_refusal(tmp_path):
    from recovery import refusal_count
    operation = tmp_path / 'T1/probe'
    write_new(operation / 'attempt_01/zero_effect_evidence.json', {
        'legacy_traceback_proof': {'original_admission': 'synthetic fixture only'}})
    assert refusal_count(operation) == 1


@pytest.mark.parametrize('admission_name,suffix', [('admission_dispatch8.json', '_dispatch8'),
                                                 ('admission_candidate.json', '_candidate')])
def test_candidate_plans_use_chosen_admission_and_versioned_deployment(tmp_path, admission_name, suffix):
    from build_plans import plans
    root = tmp_path / 'checkout/experiments/e13/expt_v4'
    base = tmp_path / 'deployment'
    launch, watchdog = plans(root, base=base, admission_name=admission_name,
                             deployment_suffix=suffix)
    admission = str(root / 'phase2' / admission_name)
    assert launch['admission'] == watchdog['admission'] == admission
    assert watchdog['resume_argv'][-1] == str(base / f'launch_plan{suffix}.json')
    for argv in [*launch['stage_argv'].values(), *(launch[name] for name in
                  ('sequence_argv', 'gates_argv', 'pilot_argv', 'progress_argv'))]:
        assert argv[argv.index('--admission') + 1] == admission
    assert not root.exists() and not base.exists()


def fake_execution(tmp_path, monkeypatch, outcomes):
    """Run the real parent loop and worker receipts with fake children and leases."""
    import admission as admission_module
    from device_guard import Busy
    import device_guard
    import stage_process
    import stage_worker

    admission = tmp_path / 'admission.json'
    write_new(admission, {'synthetic_fixture': 'parent loop only; never a model'})
    config = {'stage': 'generate', 'admission': str(admission), 'work': str(tmp_path / 'run'),
              'payload': {}}
    events = []
    active = []
    results = iter(outcomes)
    monkeypatch.setattr(admission_module, 'check_admission', lambda *a, **kw: {})
    monkeypatch.setattr(device_guard, 'census', lambda: ({0: 'fixture-uuid'}, []))

    @contextmanager
    def lease(root, checker):
        checker()
        number = sum(event[0] == 'acquire' for event in events) + 1
        path = tmp_path / 'leases' / f'fixture_{number}.json'
        write_new(path, {'id': f'fixture-{number}', 'uuid': 'fixture-uuid'})
        active.append(path)
        events.append(('acquire', number))
        try:
            yield path
        finally:
            active.remove(path)
            write_new(path.with_suffix('.end.json'), {'status': 'RELEASED'})
            events.append(('release', number))

    def worker(config, stub=False):
        outcome = next(results)
        events.append(('worker', outcome))
        if outcome == 'refuse':
            raise Busy('flapping process fixture')
        if outcome == 'empty_failure':
            effects.mark(config, 'engine_started')
            raise RuntimeError('failed engine fixture before generation')
        return {'synthetic': False, 'fixture_result': 'success'}

    class Child:
        def __init__(self, argv, **kwargs):
            self.pid = os.getpid()  # A readable identity only; no process is created or signalled.
            self.returncode = None
            self.config = json.loads(Path(argv[argv.index('--config') + 1]).read_text())

        def wait(self, timeout=None):
            try:
                result = stage_worker.run(self.config)
            except (Busy, RuntimeError):
                self.returncode = 1
            else:
                write_new(Path(self.config['stage_root']) / 'component_result.json', result)
                self.returncode = 0
            return self.returncode

        def poll(self):
            return self.returncode

    def sleep(seconds):
        assert not active, 'lease must be released before waiting to retry'
        assert events[-1][0] == 'release'
        events.append(('sleep', seconds))

    def forbid_signal(*args):
        raise AssertionError('fake child fixtures must never signal real processes')

    monkeypatch.setattr(stage_process, 'wait_allocation', lease)
    monkeypatch.setattr(stage_process.subprocess, 'Popen', Child)
    monkeypatch.setattr(stage_process.os, 'killpg', forbid_signal)
    monkeypatch.setattr(stage_process.time, 'sleep', sleep)
    monkeypatch.setattr(stage_worker, '_run', worker)
    return stage_process, config, events, active


def test_execute_retries_refusal_after_releasing_lease_without_extra_attempt(tmp_path, monkeypatch):
    stage_process, config, events, active = fake_execution(tmp_path, monkeypatch, ['refuse', 'success'])
    ledger = Ledger(config['work'], config['admission'], synthetic=False)
    result = ledger.operation('T1', 'probe', {},
                              lambda attempt, _: stage_process.execute(config, attempt / 'R0'))
    assert result['fixture_result'] == 'success'
    attempts = list((Path(config['work']) / 'T1/probe').glob('attempt_*'))
    assert len(attempts) == 1
    trial = attempts[0] / 'R0/lease_trials/trial_0001'
    assert (trial / 'lease_refused.json').exists()
    retry = json.loads((trial / 'retry.json').read_text())
    assert retry['lease_released'] and retry['consumed_a4_attempt'] is False
    assert [event[0] for event in events] == ['acquire', 'worker', 'release', 'sleep',
                                             'acquire', 'worker', 'release']
    assert (attempts[0] / 'complete.json').exists() and not active
    assert not (attempts[0] / 'infrastructure_failure.json').exists()


def test_execute_exhaustion_is_bounded_and_proved_unconsumed(tmp_path, monkeypatch):
    stage_process, config, events, active = fake_execution(tmp_path, monkeypatch, ['refuse'] * 3)
    monkeypatch.setattr(stage_process, 'MAX_LEASE_TRIALS', 3)
    ledger = Ledger(config['work'], config['admission'], synthetic=False)
    with pytest.raises(effects.LeaseRefused, match='cap \\(3\\)'):
        ledger.operation('T1', 'probe', {},
                         lambda attempt, _: stage_process.execute(config, attempt / 'R0'))
    attempt = Path(config['work']) / 'T1/probe/attempt_01'
    assert len(list((attempt / 'R0/lease_trials').iterdir())) == 3
    assert sum(event[0] == 'sleep' for event in events) == 2
    assert sum(event[0] == 'release' for event in events) == 3
    assert effects.verified_failure(attempt, refused=True) and not active
    assert not (attempt / 'infrastructure_failure.json').exists()
    assert not (attempt / 'complete.json').exists()


def test_execute_real_zero_effect_failure_reaches_ledger_and_recovery(tmp_path, monkeypatch):
    from recovery import inspect
    stage_process, config, events, active = fake_execution(tmp_path, monkeypatch, ['empty_failure'])
    ledger = Ledger(config['work'], config['admission'], synthetic=False)
    with pytest.raises(RuntimeError, match='generate failed'):
        ledger.operation('T1', 'probe', {},
                         lambda attempt, _: stage_process.execute(config, attempt / 'R0'))
    attempt = Path(config['work']) / 'T1/probe/attempt_01'
    assert json.loads((attempt / 'infrastructure_failure.json').read_text()) == effects.EMPTY
    assert effects.verified_failure(attempt)
    assert not effects.verified_failure(attempt, refused=True)
    assert inspect(config['work'])['action'] == 'RETRY_EMPTY'
    assert [event[0] for event in events] == ['acquire', 'worker', 'release'] and not active
