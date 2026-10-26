"""Retain exclusive hosted judge admissions and full declared receipts under a caller's published scientific authority."""
from __future__ import annotations

import fcntl,hashlib,json,re,statistics,time,zipfile
from pathlib import Path
from coverage_controls import CONFIGS
from training_checkpoint import digest,write_new

def admit(plan, member, *, authorize, suite, system, label_prefix):
    if member not in CONFIGS: raise ValueError('unregistered judge member')
    lock, config, m, transport, manifest = authorize(plan)
    if not manifest['cells']: return {'condition': 'v2-S2', 'status': 'NO_COMPILED_FILES', 'requests': 0}
    spec = m.suite_spec(suite); transport.endpoint(spec['benchmark'], Path(config['work'])/'private')
    with (m.RESULTS/'admission.lock').open('a') as fence:
        fcntl.flock(fence, fcntl.LOCK_EX)
        state = m.load_state(); key = system+'/'+member; attempt = m.RESULTS/(member+'_attempt.json')
        if key in state['runs'] or attempt.exists(): raise ValueError('prior judge admission exists; never resubmit')
        ids = m.RESULTS/('task_ids_'+member+'.txt')
        with ids.open('x') as out: out.write(''.join(c['task_id']+'\n' for c in manifest['cells']))
        cfg = m.judge_config(member)
        kwargs = {'judge_config': member, 'max_tokens': str(cfg['max_tokens']), 'benchmark': m.request_benchmark(spec, member)}
        for field in ('reasoning_effort', 'compute_effort'):
            if cfg.get(field): kwargs[field] = cfg[field]
        args = ['run', 'start', '--agent', 'vb103_judge', '--benchmark', spec['benchmark'], '--dataset', 'default',
                '--model', cfg['selector'], '--concurrency', str(lock['concurrency']), '--label', label_prefix+member,
                '--task-ids-file', str(ids)]
        for k, v in kwargs.items(): args += ['-k', k, v]
        row = {'config': member, 'selector': cfg['selector'], 'kwargs': kwargs, 'expected_cells': len(manifest['cells']),
               'suite': suite, 'benchmark': spec['benchmark'], 'phase': 'admitting', 'admitted_at': m.stamp(),
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


def collect(plan, *, authorize, combine, suite, system, stage):
    lock, config, m, transport, manifest = authorize(plan)
    root = Path(config['work'])
    if (root/'evaluation_attempt.json').exists(): raise ValueError('prior evaluation exists; never recompute')
    inputs = json.loads(Path(config['inputs']).read_text())
    cpu_rows = json.loads(Path(config['cpu_rows']).read_text())
    harvested = {}
    if manifest['cells']:
        if m.poll() != 0: raise RuntimeError('both declared hosted runs must reach terminal state')
        state = m.load_state()
        if set(state['runs']) != {system+'/'+name for name in CONFIGS}: raise ValueError('judge member cohort changed')
        m.harvest(suite, list(CONFIGS))
        for member in CONFIGS:
            harvest = json.loads((m.RESULTS/'harvests'/('cells_'+system+'__'+member+'.json')).read_text())
            harvested[member] = harvest
            inventory = harvest['receipt_inventory']
            expected_ids = {c['task_id'] for c in manifest['cells']}
            if len(harvest['cells']) != len(expected_ids) or {c['task_id'] for c in harvest['cells']} != expected_ids:
                raise ValueError('hosted audit harvest denominator changed')
            if inventory['extra'] or inventory['duplicates']:
                raise ValueError('hosted audit returned undeclared or duplicate receipts')
        expected = {name: digest(Path(config['bundle'])/name) for name in ('judge_call.py', 'setup.sh', 'contract.yaml')}
        for member in CONFIGS:
            archives = list((root/'judge/raw'/(system+'__'+member)/'artifacts').glob('vb103_judge.zip'))
            if len(archives) != 1: raise ValueError('actual hosted judge executable unavailable')
            with zipfile.ZipFile(archives[0]) as archive:
                for name, sha in expected.items():
                    matches = [p for p in archive.namelist() if Path(p).name == name]
                    if len(matches) != 1 or hashlib.sha256(archive.read(matches[0])).hexdigest() != sha:
                        raise ValueError('actual judge executable differs from frozen validated bundle')
        write_new(root/'evaluation_attempt.json', {'condition': 'v2-S2', 'started_unix': time.time(), 'automatic_retry': False})
        if m.fsc(system) != 0: raise RuntimeError('frozen judge aggregation did not complete')
        fsc = json.loads((m.RESULTS/('fsc_'+system+'.json')).read_text())
    else:
        write_new(root/'evaluation_attempt.json', {'condition': 'v2-S2', 'started_unix': time.time(), 'automatic_retry': False})
        fsc = {'cells': {}, 'n_ratings_declared': 0, 'n_ratings_measured': 0}
    result = combine(inputs, cpu_rows, fsc, train=Path(config['train_ids']).read_text().splitlines())
    result.update(stage=stage, lock_sha256=plan['lock']['sha256'], actual_bundle_verified=bool(manifest['cells']),
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
