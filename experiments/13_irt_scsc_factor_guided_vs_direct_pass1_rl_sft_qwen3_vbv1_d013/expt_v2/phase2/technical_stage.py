"""Bind a technical stage to its numbered admission and execute it on the owned numeric device."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'phase1'))
from device_binding import launch_environment
from lp1 import cleanup
from anchor_lease import release
from technical_ledger import pilot_lock, check_preflight
from training_checkpoint import digest, write_new

STAGES = {'T1': {'generate': 'generate', 'probabilities': 'probabilities'},
          'T2': {'generate_update': 'generate', 'update': 'update', 'export': 'export',
                 'generate_refit': 'generate', 'probabilities_refit': 'probabilities'},
          'T3': {'replay': 'replay'},
          'T4': {'evaluation_generate': 'evaluation_generate'}}


def prepare(*, LP, repository, gate, stage_key, config_path, maximum_seconds,
            preparation_root, attempt_path=None, preflight=None):
    """Write immutable execution/config bindings; this function makes no device call."""
    lock, science_sha = pilot_lock(LP, repository)
    config_path = Path(config_path).resolve(); config = json.loads(config_path.read_text())
    stage = config['stage']; health = stage in ('preflight','evaluation_preflight')
    if gate not in STAGES or (not health and STAGES[gate].get(stage_key) != stage):
        raise ValueError('unregistered technical gate stage')
    if health and (stage=='evaluation_preflight')!=(gate=='T4'):raise ValueError('T4 requires the evaluation-context engine preflight')
    if health and stage_key != 'preflight': raise ValueError('health stage key changed')
    if config.get('condition') != 'v2-S2': raise ValueError('technical stage is not S2')
    lease = json.loads(Path(config['lease_path']).read_text())
    if (lease['owner'] != 'e13v2' or lease['status'] != 'ACTIVE' or config['lease_id'] != lease['id']
            or lease['phase'] != 'v2-S2-technical'):
        raise ValueError('technical stage lacks its owned technical allocation')
    if not 90 < maximum_seconds <= lease['expires_unix']-lease['started_unix']:
        raise ValueError('stage duration exceeds the lease or cleanup reserve')
    if health:
        if attempt_path is not None or preflight is not None:
            raise ValueError('non-probe preflight cannot count an admission attempt')
        attempt = 0; status = 'PREFLIGHT_RESERVED'
    else:
        attempt_path = Path(attempt_path)
        admission = json.loads(attempt_path.read_text())
        if (admission['gate'] != gate or admission['status'] != 'ADMITTED' or admission['LP_sha256'] != LP['sha256']
                or admission['science_sha256'] != science_sha or not 1 <= admission['attempt'] <= 3):
            raise ValueError('stage has no matching numbered admission')
        expected = Path(lock['configuration']['technical_ledger'])/gate/f"attempt_{admission['attempt']}"/'attempt.json'
        if attempt_path.resolve() != expected.resolve(): raise ValueError('stage admission moved outside its frozen ledger')
        if any((attempt_path.parent/name).exists() for name in ('evaluation_attempt.json', 'result.json')):
            raise ValueError('closed or evaluated gate cannot dispatch another stage')
        check_preflight(preflight)
        attempt = admission['attempt']; status = 'ADMITTED'
    source_bindings = {str(Path(r['path']).resolve()): r['sha256'] for r in lock['bindings']}
    for path in (Path(__file__).resolve(), HERE/'technical_supervisor.py', HERE/'technical_runtime.py',
                 HERE.parent/'phase1/device_binding.py', HERE.parent/'phase1/lp1.py', HERE.parent/'phase1/anchor_lease.py'):
        if source_bindings.get(str(path)) != digest(path): raise ValueError('stage dispatch implementation unbound')
    for binding in config['bindings']:
        if digest(binding['path']) != binding['sha256']: raise ValueError('stage configuration input changed')
    root = Path(preparation_root).resolve()
    if not health:
        claims = attempt_path.parent/'stages'; claims.mkdir(exist_ok=True)
        # Moving a preparation directory must never replay a stage of the same
        # gate. This reservation precedes all launch files and device activity.
        write_new(claims/(stage_key+'.json'), {'stage': stage, 'configuration_sha256': digest(config_path),
                  'preparation_root': str(root), 'lease_id': lease['id']})
    root.mkdir(parents=True, exist_ok=False)
    entry = {'stage': stage, 'config_sha256': digest(config_path), 'lease_id': lease['id'],
             'maximum_seconds': maximum_seconds}
    if not health:
        entry.update(preflight=preflight['path'], preflight_sha256=preflight['sha256'])
    record = {'condition': 'v2-S2', 'status': status, 'gate': gate, 'attempt': attempt,
              'LP_sha256': LP['sha256'], 'science_sha256': science_sha,
              'admission_statistics_computed': False, 'stages': {stage_key: entry},
              'admission_path': str(attempt_path) if attempt_path else None,
              'admission_sha256': digest(attempt_path) if attempt_path else None}
    write_new(root/'execution.json', record)
    plan = {'repository': str(repository), 'lock': LP['path'], 'published_revision': LP['revision'],
            'execution': str(root/'execution.json'), 'config': str(config_path), 'stage': stage,
            'stage_key': stage_key, 'maximum_seconds': maximum_seconds,
            'supervisor_root': str(root/'supervisor')}
    write_new(root/'plan.json', plan)
    return root/'plan.json'


def launch_local(plan_path, *, lease_root, route_environment):
    """Run one prepared stage and retire its lease on exit; no automatic next stage or retry."""
    # Reuse the supervisor's publication/config/receipt checks before creating a
    # launch. A fresh physical UUID census occurs in launch_environment too.
    from technical_supervisor import authorize
    plan, config = authorize(plan_path)
    execution = json.loads(Path(plan['execution']).read_text())
    if execution.get('admission_path'):
        admission = Path(execution['admission_path'])
        if digest(admission) != execution['admission_sha256']:
            raise ValueError('numbered admission changed before dispatch')
        if any((admission.parent/name).exists() for name in ('result.json', 'evaluation_attempt.json')):
            raise ValueError('gate closed before dispatch')
    lease = json.loads(Path(config['lease_path']).read_text())
    if lease['host'] != socket.gethostname().split('.')[0]:
        raise ValueError('local stage cannot launch a remote device')
    canonical = json.loads((Path(lease_root)/(lease['id']+'.json')).read_text())
    if canonical != lease: raise ValueError('stage lease differs from the canonical registry')
    root = Path(plan_path).parent
    launch = root/'dispatch.json'
    if launch.exists(): raise RuntimeError('technical stage already dispatched; reconcile retained receipts')
    marker = lease['id']; result = {'condition': 'v2-S2', 'gate': execution['gate'], 'stage': plan['stage'],
                                   'admission_statistics_computed': False, 'lease_id': marker}
    try:
        env = launch_environment(lease, execution['gate'], {**os.environ, **route_environment})
        write_new(launch, {**result, 'plan_sha256': digest(plan_path), 'visible_index': env['CUDA_VISIBLE_DEVICES'],
                           'pid': os.getpid(), 'automatic_retry': False})
        with (root/'dispatch.log').open('x') as stream:
            child = subprocess.run([sys.executable, str(HERE/'technical_supervisor.py'), '--plan', str(plan_path)],
                env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True,
                timeout=plan['maximum_seconds']+30)
        result['exit_code'] = child.returncode
        receipt = Path(plan['supervisor_root'])/'result.json'
        result['supervisor_receipt'] = {'path': str(receipt), 'sha256': digest(receipt)} if receipt.exists() else None
        result['status'] = 'RUNTIME_FINISHED' if child.returncode == 0 and receipt.exists() else 'INCOMPLETE_INFRA'
    except BaseException as exc:
        result.update(status='INCOMPLETE_INFRA', error_type=type(exc).__name__, error=str(exc))
    finally:
        cleaned = cleanup(marker)
        write_new(root/'dispatch_cleanup.json', cleaned)
        released = release(lease_root, marker, cleanup_verified=cleaned['verified'])
        result.update(cleanup_verified=cleaned['verified'], released=released,
                      status=result.get('status', 'INCOMPLETE_INFRA') if cleaned['verified'] else 'CLEANUP_REQUIRED')
        write_new(root/'dispatch_result.json', result)
    return result
