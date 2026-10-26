"""TLDR: Prove empty failures from durable write-ahead effects and terminal worker receipts."""
import json
from pathlib import Path
from common import digest, write_new

EMPTY = {'generated_responses': 0, 'optimizer_started': False, 'statistics_started': False}
EFFECTS = ('engine_started', 'generation_started', 'optimizer_started')


class LeaseRefused(RuntimeError):
    """Bounded lease retries ended before this component loaded an engine."""


def mark(config, effect):
    """Synchronize BEFORE an effect; a crash after this marker is conservative."""
    if effect not in EFFECTS:
        raise ValueError('unknown effect')
    root = Path(config['effect_root'])
    path = root / (effect + '.json')
    if not path.exists():
        write_new(path, {'effect': effect, 'runtime_sha256': digest(root/'runtime.json')})


def read(path):
    return json.loads(Path(path).read_text())


def bindings(root, *, exclude=()):
    return {str(p.relative_to(root)): digest(p) for p in sorted(Path(root).rglob('*'))
            if p.is_file() and p.name not in exclude}


def no_effect_files(root, *, pre_engine=False):
    root = Path(root)
    forbidden = {'generation_started.json', 'optimizer_started.json', 'optimizer_intent.json',
                 'statistics_reserved.json', 'statistic.json', 'generations.json', 'generation.json',
                 'batch.pt', 'complete.json', 'output.json'}
    if pre_engine:
        forbidden.add('engine_started.json')
    if any(p.is_file() and (p.name in forbidden or p.name.endswith('.generation.json'))
           for p in root.rglob('*')):
        return False
    # Statistics belong to the stage, outside the operation attempt.
    return not any((p/'statistics_reserved.json').exists() or (p/'statistic.json').exists()
                   for p in (root, *root.parents[:3]))


def worker_proof(root, *, pre_engine=False):
    """Missing files alone never suffice: require a bound terminal worker receipt."""
    root = Path(root)
    try:
        terminal = read(root/'worker_failed.json')
        runtime = digest(root/'runtime.json')
        started = read(root/'worker_started.json')
        execution = read(root/'execution.json')
        if (terminal['runtime_sha256'] != runtime or started['runtime_sha256'] != runtime
                or type(execution['exit_code']) is not int or execution['exit_code'] == 0
                or terminal['effects_schema'] != 1 or started['effects_schema'] != 1):
            return False
        actual_effects = {name: digest(root/(name+'.json')) for name in EFFECTS
                          if (root/(name+'.json')).exists()}
        if terminal['effects'] != actual_effects:
            return False
        if pre_engine and (terminal['kind'] != 'lease_refused'
                           or read(root/'lease_refused.json') != terminal):
            return False
        config = read(root/'runtime.json')
        if Path(config['effect_root']).resolve() != root.resolve():
            return False
        return no_effect_files(root, pre_engine=pre_engine) and no_effect_files(
            Path(config['stage_root']), pre_engine=pre_engine)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def operation_proof(attempt, *, pre_engine=False):
    attempt = Path(attempt)
    if not no_effect_files(attempt, pre_engine=pre_engine):
        return False
    trials = [p.parent for p in attempt.rglob('runtime.json')]
    # Only invocation directories carry worker_started; the parent compatibility
    # runtime is a copy of an accepted invocation, never an additional execution.
    trials = [p for p in trials if p.parent.name == 'lease_trials']
    return bool(trials) and all(worker_proof(p, pre_engine=pre_engine) for p in trials)


def record_failure(attempt):
    """Called by the ledger after the component has exited and released its lease."""
    attempt = Path(attempt)
    refused = operation_proof(attempt, pre_engine=True)
    if not refused and not operation_proof(attempt):
        return False
    evidence = {'schema': 1, 'classification': 'PRE_ENGINE_LEASE_REFUSAL' if refused else 'ZERO_EFFECT_FAILURE',
                'consumed_a4_attempt': not refused,
                'bindings': bindings(attempt, exclude=('zero_effect_evidence.json',
                    'infrastructure_failure.json', 'lease_refused.json'))}
    write_new(attempt/'zero_effect_evidence.json', evidence)
    write_new(attempt/('lease_refused.json' if refused else 'infrastructure_failure.json'),
              {'classification': 'PRE_ENGINE_LEASE_REFUSAL', 'consumed_a4_attempt': False,
               'evidence_sha256': digest(attempt/'zero_effect_evidence.json')} if refused else EMPTY)
    return True


def verified_failure(attempt, *, refused=False):
    attempt = Path(attempt)
    try:
        evidence = read(attempt/'zero_effect_evidence.json')
        expected = 'PRE_ENGINE_LEASE_REFUSAL' if refused else 'ZERO_EFFECT_FAILURE'
        if evidence['classification'] != expected or evidence['consumed_a4_attempt'] is refused:
            return False
        if any(digest(attempt/name) != sha for name, sha in evidence['bindings'].items()):
            return False
        if refused:
            receipt = read(attempt/'lease_refused.json')
            if receipt != {'classification': expected, 'consumed_a4_attempt': False,
                           'evidence_sha256': digest(attempt/'zero_effect_evidence.json')}:
                return False
        elif read(attempt/'infrastructure_failure.json') != EMPTY:
            return False
        if evidence.get('legacy_traceback_proof'):
            # The one historical receipt binds its complete original tree and
            # admitted source separately; it is never inferred for new failures.
            from readmission import verify_legacy_refusal
            return refused and verify_legacy_refusal(attempt, evidence)
        return operation_proof(attempt, pre_engine=refused)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def retryable_empty(attempt):
    try:
        # Existing labelled CPU fixtures remain separate from measured evidence.
        if read(Path(attempt)/'started.json').get('synthetic') is True:
            return read(Path(attempt)/'infrastructure_failure.json') == EMPTY
    except (OSError, ValueError):
        return False
    return verified_failure(attempt)
