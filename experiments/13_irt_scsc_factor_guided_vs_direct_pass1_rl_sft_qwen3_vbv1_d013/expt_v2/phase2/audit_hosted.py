"""Admit and collect the frozen train-audit judge pack through the validated hosted command-line route."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_coverage import helper, combine, SUITE, SYSTEM
from coverage_controls import CONFIGS, REPO
from technical_ledger import published as publication
from training_checkpoint import digest
from rl4cv.valkyrie_transport import Transport


def authorize(plan):
    lock = publication(plan['lock'], plan['repository'])
    if (lock.get('gate'), lock.get('condition'), lock.get('status')) != ('TRAIN_AUDIT_HOSTED', 'v2-S2', 'FROZEN'):
        raise ValueError('published S2 hosted audit lock required')
    bound = {b['path']: b['sha256'] for b in lock['bindings']}
    if len(bound) != len(lock['bindings']): raise ValueError('duplicate hosted audit binding')
    for path, sha in bound.items():
        if digest(path) != sha: raise ValueError('hosted audit binding changed')
    config = lock['configuration']
    required = {str(Path(__file__).resolve()), str(Path(__file__).resolve().parent/'audit_coverage.py'),
                str(Path(__file__).resolve().parent/'coverage_pack.py'),
                str(Path(__file__).resolve().parent/'hosted_coverage.py'),
                config['prepared'], config['inputs'], config['cpu_rows'], config['train_ids'], config['route_identity'],
                str(Path(__file__).resolve().parent/'coverage_controls.py'),
                str(REPO/'src/rl4cv/valkyrie_transport.py')}
    if not required <= set(bound): raise ValueError('hosted audit implementation or manifest is unbound')
    prepared = json.loads(Path(config['prepared']).read_text())
    if prepared['configuration'] != config: raise ValueError('prepared audit configuration changed')
    for item in prepared['bindings']:
        if digest(item['path']) != item['sha256']: raise ValueError('prepared judge pack changed')
    controls = publication(lock['coverage_controls_result'], plan['repository'])
    if controls.get('status') != 'PASS' or controls.get('condition') != 'v2-S2' or controls.get('actual_bundle_verified') is not True:
        raise ValueError('validated hosted route controls have not passed')
    for previous_name in ('coverage_controls_lock', 'cpu_execution_lock'):
        previous = publication(lock[previous_name], plan['repository'])
        for item in previous['bindings']:
            if digest(item['path']) != item['sha256']: raise ValueError('prior route or audit implementation changed')
    cpu = publication(lock['cpu_result'], plan['repository'])
    if (cpu.get('accounted') != 128 or cpu.get('condition') != 'v2-S2'
            or cpu.get('cleanup_unresolved') != 0 or cpu.get('rows_sha256') != digest(config['cpu_rows'])):
        raise ValueError('processor audit is not completely accounted and cleaned')
    m = helper(config); spec = m.suite_spec(SUITE)
    manifest = json.loads(Path(spec['pack_receipt']).read_text())
    prepared_bound = {b['path']: b['sha256'] for b in prepared['bindings']}
    if len(prepared_bound) != len(prepared['bindings']): raise ValueError('duplicate prepared audit binding')
    for path in [Path(spec['pack_receipt']), *[Path(config['bundle'])/n for n in ('judge_call.py','setup.sh','contract.yaml')]]:
        if prepared_bound.get(str(path)) != digest(path): raise ValueError('judge pack or bundle is unbound')
    if (manifest['verdict'] != 'PASS' or manifest['split'] != 'train' or manifest['declared_audit_cells'] != 128
            or manifest['n_declared_ratings'] != lock['declared_ratings']
            or lock['members'] != list(CONFIGS) or manifest['repeats'] != [1, 2, 3]
            or len(manifest['cells']) != manifest['compiled_files']*3
            or prepared['pack_sha256'] != digest(spec['pack_receipt'])):
        raise ValueError('hosted audit pack or repeat denominator changed')
    transport = Transport(Path(config['work'])/'private/unused.yaml')
    transport.preflight(); route = json.loads(Path(config['route_identity']).read_text())
    transport.require_receipt(route)
    if route.get('verdict') != 'PASS' or not route.get('vals_managed_credential_provenance_verified'):
        raise ValueError('hosted Vals route provenance unresolved')
    return lock, config, m, transport, manifest


def admit(plan,member):
    from hosted_coverage import admit as shared_admit
    return shared_admit(plan,member,authorize=authorize,suite=SUITE,system=SYSTEM,label_prefix='e13v2-S2-train-audit-')


def collect(plan):
    from hosted_coverage import collect as shared_collect
    return shared_collect(plan,authorize=authorize,combine=combine,suite=SUITE,system=SYSTEM,stage='TRAIN_AUDIT_HOSTED')


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
