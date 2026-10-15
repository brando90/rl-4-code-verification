"""Admit and collect the frozen train-audit judge pack through the validated hosted command-line route."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import statistics
import time
import zipfile

from audit_coverage import helper, combine, SUITE, SYSTEM
from coverage_controls import CONFIGS, REPO
from technical_ledger import published as publication
from training_checkpoint import digest, write_new
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


def admit(plan, member):
    if member not in CONFIGS: raise ValueError('unregistered judge member')
    lock, config, m, transport, manifest = authorize(plan)
    if not manifest['cells']: return {'condition': 'v2-S2', 'status': 'NO_COMPILED_FILES', 'requests': 0}
    spec = m.suite_spec(SUITE); transport.endpoint(spec['benchmark'], Path(config['work'])/'private')
    with (m.RESULTS/'admission.lock').open('a') as fence:
        fcntl.flock(fence, fcntl.LOCK_EX)
        state = m.load_state(); key = SYSTEM+'/'+member; attempt = m.RESULTS/(member+'_attempt.json')
        if key in state['runs'] or attempt.exists(): raise ValueError('prior judge admission exists; never resubmit')
        ids = m.RESULTS/('task_ids_'+member+'.txt')
        with ids.open('x') as out: out.write(''.join(c['task_id']+'\n' for c in manifest['cells']))
        cfg = m.judge_config(member)
        kwargs = {'judge_config': member, 'max_tokens': str(cfg['max_tokens']), 'benchmark': m.request_benchmark(spec, member)}
        for field in ('reasoning_effort', 'compute_effort'):
            if cfg.get(field): kwargs[field] = cfg[field]
        args = ['run', 'start', '--agent', 'vb103_judge', '--benchmark', spec['benchmark'], '--dataset', 'default',
                '--model', cfg['selector'], '--concurrency', str(lock['concurrency']), '--label', 'e13v2-S2-train-audit-'+member,
                '--task-ids-file', str(ids)]
        for k, v in kwargs.items(): args += ['-k', k, v]
        row = {'config': member, 'selector': cfg['selector'], 'kwargs': kwargs, 'expected_cells': len(manifest['cells']),
               'suite': SUITE, 'benchmark': spec['benchmark'], 'phase': 'admitting', 'admitted_at': m.stamp(),
               'command': args, 'task_ids_sha256': digest(ids), 'lock_sha256': plan['lock']['sha256'], **transport.identity()}
        write_new(attempt, row); state['runs'][key] = row; m.save_state(state)
        try:
            result = transport.run(args, timeout=180)
            (m.RESULTS/(member+'_admission.log')).write_text(result.stdout+result.stderr)
            match = re.search(r'Run ID:\s*([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})', result.stdout)
            if result.returncode or not match: raise RuntimeError('ambiguous hosted admission; recover retained receipt')
            row.update(phase='running', run_id=match.group(1)); m.save_state(state)
        except BaseException as exc:
            row.update(phase='admission_failed', error_type=type(exc).__name__, automatic_retry=False)
            m.save_state(state); raise
        return {'condition': 'v2-S2', 'member': member, 'run_id': row['run_id'], 'declared_ratings': len(manifest['cells'])}


def collect(plan):
    lock, config, m, transport, manifest = authorize(plan)
    root = Path(config['work'])
    if (root/'evaluation_attempt.json').exists(): raise ValueError('prior evaluation exists; never recompute')
    inputs = json.loads(Path(config['inputs']).read_text())
    cpu_rows = json.loads(Path(config['cpu_rows']).read_text())
    harvested = {}
    if manifest['cells']:
        if m.poll() != 0: raise RuntimeError('both declared hosted runs must reach terminal state')
        state = m.load_state()
        if set(state['runs']) != {SYSTEM+'/'+name for name in CONFIGS}: raise ValueError('judge member cohort changed')
        m.harvest(SUITE, list(CONFIGS))
        for member in CONFIGS:
            harvest = json.loads((m.RESULTS/'harvests'/('cells_'+SYSTEM+'__'+member+'.json')).read_text())
            harvested[member] = harvest
            inventory = harvest['receipt_inventory']
            expected_ids = {c['task_id'] for c in manifest['cells']}
            if len(harvest['cells']) != len(expected_ids) or {c['task_id'] for c in harvest['cells']} != expected_ids:
                raise ValueError('hosted audit harvest denominator changed')
            if inventory['extra'] or inventory['duplicates']:
                raise ValueError('hosted audit returned undeclared or duplicate receipts')
        expected = {name: digest(Path(config['bundle'])/name) for name in ('judge_call.py', 'setup.sh', 'contract.yaml')}
        for member in CONFIGS:
            archives = list((root/'judge/raw'/(SYSTEM+'__'+member)/'artifacts').glob('vb103_judge.zip'))
            if len(archives) != 1: raise ValueError('actual hosted judge executable unavailable')
            with zipfile.ZipFile(archives[0]) as archive:
                for name, sha in expected.items():
                    matches = [p for p in archive.namelist() if Path(p).name == name]
                    if len(matches) != 1 or hashlib.sha256(archive.read(matches[0])).hexdigest() != sha:
                        raise ValueError('actual judge executable differs from frozen validated bundle')
        write_new(root/'evaluation_attempt.json', {'condition': 'v2-S2', 'started_unix': time.time(), 'automatic_retry': False})
        if m.fsc(SYSTEM) != 0: raise RuntimeError('frozen judge aggregation did not complete')
        fsc = json.loads((m.RESULTS/('fsc_'+SYSTEM+'.json')).read_text())
    else:
        write_new(root/'evaluation_attempt.json', {'condition': 'v2-S2', 'started_unix': time.time(), 'automatic_retry': False})
        fsc = {'cells': {}, 'n_ratings_declared': 0, 'n_ratings_measured': 0}
    result = combine(inputs, cpu_rows, fsc, train=Path(config['train_ids']).read_text().splitlines())
    result.update(stage='TRAIN_AUDIT_HOSTED', lock_sha256=plan['lock']['sha256'], actual_bundle_verified=bool(manifest['cells']),
                  declared_ratings=manifest['n_declared_ratings'], measured_ratings=fsc['n_ratings_measured'],
                  scientific_settings='unchanged validated prompts, members, efforts and three-repeat aggregation',
                  requested_identity_verified=(all(c.get('transport_matches') is True for h in harvested.values() for c in h['cells'])
                      if harvested else None), actual_provider_returned_identity_checked=False)
    result['charges'] = {}
    result['repeat_variability'] = {}
    for member, harvest in harvested.items():
        charges = [c.get('cost_usd') for c in harvest['cells']]
        result['repeat_variability'][member] = repeat_variability(harvest['cells'])
        result['charges'][member] = {'declared_ratings': len(charges), 'known_charges': sum(v is not None for v in charges),
            'model_usd': sum(charges) if all(v is not None for v in charges) else None, 'sandbox_usd': None,
            'request_attempts': sum(c.get('requests_sent') or 0 for c in harvest['cells']),
            'request_attempts_known': sum(c.get('requests_sent') is not None for c in harvest['cells'])}
    write_new(root/'result.json', result); return result


def repeat_variability(cells):
    """Describe all measured repeats on the native 0–5 scale without inferring missing ratings."""
    groups = {}
    for cell in cells:
        key = cell['task_id_vb']+'#'+str(cell['sample_idx'])
        groups.setdefault(key, [])
        if cell.get('status') == 'measured': groups[key].append(cell['score_raw'])
    return {key: {'measured_repeats': len(values), 'declared_repeats': 3,
                  'minimum_0_5': min(values) if values else None,
                  'maximum_0_5': max(values) if values else None,
                  'sample_standard_deviation_0_5': statistics.stdev(values) if len(values)>1 else None}
            for key, values in groups.items()}


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
