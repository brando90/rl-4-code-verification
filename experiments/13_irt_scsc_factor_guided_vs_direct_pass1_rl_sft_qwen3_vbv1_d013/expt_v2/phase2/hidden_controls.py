"""Freeze and run train-only controls for the unchanged corrected hidden-test adapter."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys

from hidden_runtime import Runtime, E12, HERE
from training_checkpoint import digest, write_new
from extract_hidden_tests import extract
from adapter_e12 import renamed_control
from controls_e12 import mutations, remove_propositions

REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent/'phase1'))
from score_anchor_ledger import MemorySlots

SALT = 'rl4cv-e13-s2-hidden-controls-1302261:'
TASKS = 64
MAX_MUTANTS = 40


def prepare(config_path):
    config = json.loads(Path(config_path).read_text())
    root = Path(config['work']); root.mkdir(parents=True, exist_ok=False)
    train = Path(config['train_ids']); allowed = train.read_text().splitlines()
    features = json.loads(Path(config['features']).read_text())
    if len(allowed) != 539 or len(set(allowed)) != 539 or set(features) != set(allowed):
        raise ValueError('control preparation requires the complete frozen train pool')
    candidates = []
    for task in sorted(allowed, key=lambda t: hashlib.sha256((SALT+t).encode()).hexdigest()):
        gold = Path(config['pack'])/task/'tests/gold.lean'
        suite = extract(gold.read_text())
        if suite['n_tests']:
            candidates.append({'task_id': task, 'group_id': features[task]['group_id'],
                               'gold': str(gold), 'gold_sha256': digest(gold), 'suite': suite})
    selected = []; groups = set()
    for row in candidates:
        if row['group_id'] in groups: continue
        groups.add(row['group_id']); selected.append(row)
        if len(selected) == TASKS: break
    if len(selected) != TASKS: raise ValueError('insufficient train groups with extracted tests')
    cells = []; counts = []
    for index, row in enumerate(selected):
        dest = root/'inputs'/f'{index:03d}'; dest.mkdir(parents=True)
        raw = Path(row['gold']).read_text()
        renamed, rename_map = renamed_control(raw, row['suite']['symbols'])
        wrong = selected[(index+1) % TASKS]
        suite_path = dest/'suite.json'; write_new(suite_path, row['suite'])
        sources = {'C1': raw, 'C2': renamed, 'C4': Path(wrong['gold']).read_text()}
        mutant_meta = []
        for j, (source, metadata) in enumerate(itertools.islice(mutations(remove_propositions(raw), row['suite']['symbols']), MAX_MUTANTS)):
            kind = f'C3_{j:02d}'; sources[kind] = source; mutant_meta.append({'kind': kind, **metadata})
        for kind, source in sources.items():
            (dest/(kind+'.lean')).write_text(source)
        cells.append({'task_id': row['task_id'], 'split': 'train', 'group_id': row['group_id'],
            'index': index, 'suite': str(suite_path), 'n_tests': row['suite']['n_tests'],
            'sources': {kind: str(dest/(kind+'.lean')) for kind in sources}, 'mutants': mutant_meta,
            'rename_map': rename_map, 'gold_sha256': row['gold_sha256'], 'wrong_gold_sha256': wrong['gold_sha256'],
            'wrong_task_id': wrong['task_id']})
        counts.append(len(mutant_meta))
    inputs = root/'inputs.json'; write_new(inputs, {'cells': cells})
    paths = [Path(config_path), train, Path(config['features']), inputs, HERE/'hidden_runtime.py',
             HERE/'hidden_controls.py', HERE/'training_checkpoint.py',
             HERE.parent/'phase1/score_anchor_ledger.py', HERE.parent/'phase1/score_anchor.py',
             Path(config['lake'])/'lean-toolchain', Path(config['lake'])/'lake-manifest.json',
             REPO/'external/deps.lock.json', Path(config['lake_bin'])]
    paths += [E12/'expt_v2/scripts/adapter_v2.py']
    paths += [E12/'expt_v1/scripts'/name for name in ('adapter_e12.py', 'extract_hidden_tests.py',
        'fixture_inputs_e12.py', 'controls_e12.py', 'mutation_helpers_e12.py', 'runtime_e12.py', 'compile_reproduction.py')]
    paths += [Path(row['gold']) for row in selected]
    paths += [p for p in (root/'inputs').rglob('*') if p.is_file()]
    manifest = {'condition': 'v2-S2', 'stage': 'train hidden adapter controls', 'configuration': config,
        'selection': {'salt': SALT, 'train_pool': 539, 'eligible_with_tests': len(candidates),
                      'tasks': TASKS, 'groups': TASKS, 'rule': 'first eligible task per group in salted SHA256 order'},
        'mutant_candidates': {'maximum_per_task': MAX_MUTANTS, 'minimum': min(counts), 'maximum': max(counts), 'total': sum(counts)},
        'inputs': str(inputs), 'bindings': [{'path': str(p.resolve()), 'sha256': digest(p)} for p in sorted(set(paths))]}
    write_new(root/'prepared.json', manifest)
    return {k: manifest[k] for k in ('condition', 'selection', 'mutant_candidates')}


def evaluate_task(row, config, slots):
    root = Path(config['work'])/'execution'/f"{row['index']:03d}"
    root.mkdir(parents=True, exist_ok=False)
    write_new(root/'attempt.json', {'index': row['index'], 'task_id': row['task_id'], 'split': 'train'})
    suite = json.loads(Path(row['suite']).read_text())
    results = {'task_id': row['task_id'], 'n_tests': row['n_tests']}
    with slots:
        runtime = Runtime(root, config['lake'], config['lake_bin'])
        def module(kind):
            return 'E13Hidden'+hashlib.sha256((row['task_id']+'/'+kind).encode()).hexdigest()[:24]
        for kind in ('C1', 'C2', 'C4'):
            result = runtime.evaluate(suite, Path(row['sources'][kind]).read_text(), module(kind))
            write_new(root/(kind+'.json'), result); results[kind] = result
        attempts = []; chosen = None
        for mutation in row['mutants']:
            kind = mutation['kind']; source = Path(row['sources'][kind]).read_text()
            _, compiled = runtime.compile(source, module(kind))
            receipt = {'mutation': mutation, 'compile': compiled, 'source_sha256': hashlib.sha256(source.encode()).hexdigest()}
            write_new(root/(kind+'_compile.json'), receipt); attempts.append(receipt)
            if compiled['status'] == 'ok':
                chosen = runtime.evaluate(suite, source, module(kind), compiled)
                chosen['mutation'] = mutation
                break  # Selection uses compilation only, never the hidden outcome.
            if compiled['status'] != 'error':
                break  # A timeout/unknown cannot select the next mutant.
        results['C3'] = chosen or {'status': 'no_compiling_mutant', 'hidden_all_pass': None}
        results['C3']['compile_attempts'] = attempts
        write_new(root/'C3.json', results['C3'])
    write_new(root/'result.json', results)
    return results


def summarize(rows, declared=TASKS):
    if len(rows) != declared or len({r['task_id'] for r in rows}) != declared:
        raise ValueError('hidden-control denominator incomplete or duplicated')
    ntests = sum(r['n_tests'] for r in rows)
    passed = sum(r['C1'].get('n_pass', 0) for r in rows)
    eligible = [r for r in rows if r['C1'].get('hidden_all_pass') is True]
    recovered = sum(r['C2'].get('hidden_all_pass') is True for r in eligible)
    mutants = [r for r in rows if r['C3'].get('compile', {}).get('status') == 'ok']
    killed = sum(r['C3'].get('n_evaluable', 0) > r['C3'].get('n_pass', 0) for r in mutants)
    rejected = sum(r['C4'].get('compile', {}).get('status') == 'ok' and
                   (r['C4'].get('n_mapped') == 0 or r['C4'].get('n_evaluable', 0) > r['C4'].get('n_pass', 0)) for r in rows)
    controls = {
        'C1': {'n_tests': ntests, 'n_pass': passed, 'threshold': .98, 'pass': ntests > 0 and 100*passed >= 98*ntests},
        'C2': {'eligible_C1_tasks': len(eligible), 'recovered': recovered, 'threshold': .95,
               'pass': bool(eligible) and 100*recovered >= 95*len(eligible)},
        'C3': {'compiling_mutants': len(mutants), 'killed': killed, 'minimum_compiling': 50, 'threshold': .60,
               'pass': len(mutants) >= 50 and 100*killed >= 60*len(mutants)},
        'C4': {'declared': declared, 'rejected_or_failing': rejected, 'threshold': .95, 'pass': 100*rejected >= 95*declared}}
    return {'condition': 'v2-S2', 'declared': declared, 'completed': len(rows), 'controls': controls,
            'status': 'PASS' if all(r['pass'] for r in controls.values()) else 'FAIL',
            'cell_status_counts': {kind: dict(Counter(r[kind]['status'] for r in rows)) for kind in ('C1', 'C2', 'C3', 'C4')},
            'per_test_unknown_counts': {kind: sum(r[kind].get('n_unmapped', 0)+r[kind].get('n_type_unknown', 0) for r in rows)
                                        for kind in ('C1', 'C2', 'C3', 'C4')},
            'admission_statistics_computed': True, 'model_calls': 0, 'device_hours': 0}


def run(plan_path):
    plan = json.loads(Path(plan_path).read_text()); lock_path = Path(plan['lock'])
    lock = json.loads(lock_path.read_text())
    if (lock.get('gate'), lock.get('status'), lock.get('condition')) != ('TRAIN_HIDDEN_CONTROLS', 'FROZEN', 'v2-S2'):
        raise ValueError('hidden controls require a frozen S2 lock')
    subprocess.run(['git', 'merge-base', '--is-ancestor', plan['published_revision'], 'origin/main'], cwd=REPO, check=True)
    raw = subprocess.check_output(['git', 'show', plan['published_revision']+':'+str(lock_path.relative_to(REPO))], cwd=REPO)
    if raw != lock_path.read_bytes(): raise ValueError('hidden lock not published')
    for binding in lock['bindings']:
        if digest(binding['path']) != binding['sha256']: raise ValueError('hidden lock binding changed')
    prepared = Path(lock['private_prepared'])
    if str(prepared) not in {b['path'] for b in lock['bindings']}: raise ValueError('hidden prepared manifest unbound')
    manifest = json.loads(prepared.read_text())
    for binding in manifest['bindings']:
        if digest(binding['path']) != binding['sha256']: raise ValueError('private hidden binding changed')
    config = manifest['configuration']; root = Path(config['work'])
    rows = json.loads(Path(manifest['inputs']).read_text())['cells']
    allowed = set(Path(config['train_ids']).read_text().splitlines())
    if (len(rows) != TASKS or len({r['task_id'] for r in rows}) != TASKS
            or any(r['split'] != 'train' or r['task_id'] not in allowed or r['wrong_task_id'] not in allowed for r in rows)):
        raise ValueError('hidden cohort is not exactly the frozen train cohort')
    write_new(root/'attempt.json', {'condition': 'v2-S2', 'lock_sha256': digest(lock_path), 'declared': TASKS, 'automatic_retries': 0})
    slots = MemorySlots()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda row: evaluate_task(row, config, slots), rows))
    write_new(root/'evaluation_attempt.json', {'declared': TASKS, 'lock_sha256': digest(lock_path)})
    result = summarize(results)
    result['lock_sha256'] = digest(lock_path)
    result['rows_sha256'] = hashlib.sha256(json.dumps(results, sort_keys=True).encode()).hexdigest()
    write_new(root/'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare', type=Path); group.add_argument('--plan', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.prepare) if args.prepare else run(args.plan)))
