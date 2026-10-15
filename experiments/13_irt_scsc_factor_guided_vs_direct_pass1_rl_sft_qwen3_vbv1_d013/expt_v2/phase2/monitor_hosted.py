"""Admit and collect only the published current-checkpoint pilot monitor pack on the validated hosted route."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from monitor_coverage import helper, combine, SUITE, SYSTEM
from coverage_controls import CONFIGS, REPO
from technical_ledger import published as publication
from training_checkpoint import digest
from rl4cv.valkyrie_transport import Transport


def authorize(plan):
    lock = publication(plan['lock'], plan['repository'])
    if (lock.get('gate'), lock.get('condition'), lock.get('status')) != ('PILOT_MONITOR_HOSTED', 'v2-S2', 'FROZEN'):
        raise ValueError('published S2 hosted monitor lock required')
    bound = {b['path']: b['sha256'] for b in lock['bindings']}
    if len(bound) != len(lock['bindings']): raise ValueError('duplicate hosted monitor binding')
    for path, sha in bound.items():
        if digest(path) != sha: raise ValueError('hosted monitor binding changed')
    config = lock['configuration']
    required = {str(Path(__file__).resolve()), str(Path(__file__).resolve().parent/'monitor_coverage.py'),
                str(Path(__file__).resolve().parent/'coverage_pack.py'),
                str(Path(__file__).resolve().parent/'hosted_coverage.py'),
                config['prepared'], config['inputs'], config['cpu_rows'], config['train_ids'], config['route_identity'],
                str(Path(__file__).resolve().parent/'coverage_controls.py'),
                str(REPO/'src/rl4cv/valkyrie_transport.py')}
    if not required <= set(bound): raise ValueError('hosted monitor implementation or manifest is unbound')
    prepared = json.loads(Path(config['prepared']).read_text())
    if prepared['configuration'] != config: raise ValueError('prepared monitor configuration changed')
    for item in prepared['bindings']:
        if digest(item['path']) != item['sha256']: raise ValueError('prepared judge pack changed')
    controls = publication(lock['coverage_controls_result'], plan['repository'])
    if controls.get('status') != 'PASS' or controls.get('condition') != 'v2-S2' or controls.get('actual_bundle_verified') is not True:
        raise ValueError('validated hosted route controls have not passed')
    for previous_name in ('coverage_controls_lock', 'cpu_execution_lock'):
        previous = publication(lock[previous_name], plan['repository'])
        for item in previous['bindings']:
            if digest(item['path']) != item['sha256']: raise ValueError('prior route or monitor implementation changed')
    cpu = publication(lock['cpu_result'], plan['repository'])
    if (cpu.get('accounted') != 32 or cpu.get('condition') != 'v2-S2'
            or cpu.get('cleanup_unresolved') != 0 or cpu.get('rows_sha256') != digest(config['cpu_rows'])):
        raise ValueError('processor monitor is not completely accounted and cleaned')
    snapshot=publication(lock['snapshot_lock'],plan['repository'])
    pilot=publication(lock['pilot_execution_lock'],plan['repository'])
    if (snapshot.get('gate'),snapshot.get('condition'),snapshot.get('status'))!=('PILOT_MONITOR_SNAPSHOT','v2-S2','FROZEN'):
        raise ValueError('published pre-response monitor snapshot required')
    if (pilot.get('gate'),pilot.get('condition'),pilot.get('status'))!=('LEARNING_PILOT','v2-S2','FROZEN'):
        raise ValueError('monitor belongs to an unadmitted learning pilot')
    if (snapshot['execution_sha256']!=lock['pilot_execution_lock']['sha256']
            or lock['execution_sha256']!=snapshot['execution_sha256']
            or lock['model_binding_sha256']!=snapshot['model_binding_sha256']):
        raise ValueError('monitor execution or checkpoint changed')
    scientific={b['path']:b['sha256'] for b in pilot['bindings']}
    for name in ('monitor_preparation.py','monitor_runtime.py','monitor_cpu.py','monitor_coverage.py',
                 'monitor_hosted.py','coverage_pack.py','hosted_coverage.py','audit_monitor.py'):
        path=Path(__file__).resolve().parent/name
        if scientific.get(str(path))!=digest(path):raise ValueError('monitor implementation was not frozen before learning')
    for b in snapshot['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('pre-response monitor snapshot changed')
    cpu_lock=publication(lock['cpu_execution_lock'],plan['repository'])
    if (cpu_lock.get('gate')!='PILOT_MONITOR_CPU' or cpu_lock.get('snapshot_sha256')!=lock['snapshot_lock']['sha256']
            or cpu.get('stage')!='PILOT_MONITOR_HIDDEN' or cpu.get('snapshot_sha256')!=lock['snapshot_lock']['sha256']
            or cpu.get('execution_sha256')!=lock['cpu_execution_lock']['sha256']):
        raise ValueError('monitor processor evidence belongs to another snapshot')
    inputs=json.loads(Path(config['inputs']).read_text())
    if any(inputs.get(k)!=snapshot[k] or cpu.get(k)!=snapshot[k] for k in ('arm','run_seed','update')):
        raise ValueError('monitor input arm/seed/checkpoint changed')
    m = helper(config); spec = m.suite_spec(SUITE)
    manifest = json.loads(Path(spec['pack_receipt']).read_text())
    prepared_bound = {b['path']: b['sha256'] for b in prepared['bindings']}
    if len(prepared_bound) != len(prepared['bindings']): raise ValueError('duplicate prepared monitor binding')
    for path in [Path(spec['pack_receipt']), *[Path(config['bundle'])/n for n in ('judge_call.py','setup.sh','contract.yaml')]]:
        if prepared_bound.get(str(path)) != digest(path): raise ValueError('judge pack or bundle is unbound')
    if (manifest['verdict'] != 'PASS' or manifest['split'] != 'train' or manifest['declared_audit_cells'] != 32
            or manifest['n_declared_ratings'] != lock['declared_ratings']
            or lock['members'] != list(CONFIGS) or manifest['repeats'] != [1, 2, 3]
            or len(manifest['cells']) != manifest['compiled_files']*3
            or prepared['pack_sha256'] != digest(spec['pack_receipt'])):
        raise ValueError('hosted monitor pack or repeat denominator changed')
    transport = Transport(Path(config['work'])/'private/unused.yaml')
    transport.preflight(); route = json.loads(Path(config['route_identity']).read_text())
    transport.require_receipt(route)
    if route.get('verdict') != 'PASS' or not route.get('vals_managed_credential_provenance_verified'):
        raise ValueError('hosted Vals route provenance unresolved')
    return lock, config, m, transport, manifest


def admit(plan,member):
    from hosted_coverage import admit as shared_admit
    return shared_admit(plan,member,authorize=authorize,suite=SUITE,system=SYSTEM,label_prefix='e13v2-S2-pilot-monitor-')


def collect(plan):
    from hosted_coverage import collect as shared_collect
    return shared_collect(plan,authorize=authorize,combine=combine,suite=SUITE,system=SYSTEM,stage='PILOT_MONITOR_HOSTED')


def repeat_variability(cells):
    from hosted_coverage import repeat_variability as summarize
    return summarize(cells)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('admit','collect'))
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--member', choices=CONFIGS)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    result = admit(plan, args.member) if args.action == 'admit' else collect(plan)
    # Private per-cell outcomes remain in the work-root result, never stdout.
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','repeat_variability')}, sort_keys=True))


if __name__ == '__main__': main()
