#!/usr/bin/env python3
"""Apply Amendment A2 in separate routes while retaining the original frozen R2 run."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path
import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback

import psutil

HERE = Path(__file__).resolve().parent
V2 = HERE.parent
sys.path.insert(0, str(V2))
sys.path.insert(0, str(HERE))
import watchdog_e13v2 as watchdog
from run_route import alive_group

RUN = 'e13v2_a1'
DENOMINATORS = {'ordinary': 33456, 'opaque': 5328}
CEILINGS = {'ordinary': 33, 'opaque': 5}
TYPED = {'measured', 'deterministic_resource_limit', 'integrity_defect', 'transient_infrastructure'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def untyped(row):
    return row['status'] not in TYPED


def reserve_retry(db, cell, source_hash):
    """Append A2 attempt 2 without relabelling or rewriting attempt 1."""
    prior = list(db.execute('SELECT * FROM attempts WHERE run=? AND cell=? ORDER BY attempt', (RUN, cell)))
    if len(prior) != 1 or prior[0]['attempt'] != 1 or not untyped(prior[0]):
        raise RuntimeError('A2 requires one terminal untyped original attempt')
    if prior[0]['source_hash'] != source_hash:
        raise RuntimeError('A2 source binding changed')
    db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,NULL)',
               (RUN, cell, 2, source_hash, 'running', watchdog.now()))
    db.commit()


def command_for(execution, route, ordinal):
    return ['prlimit', f"--as={execution['address_space_bytes']}", '--', sys.executable,
            str(HERE / 'cell_worker.py'), '--route', route, '--ordinal', str(ordinal), '--attempt', '2']


def public_receipt(route, rows, retry_rows, hashes):
    """Only counts, hashes and admission statuses leave either private route."""
    measured = [r for r in rows if r['status'] == 'measured']
    limits = sum(r['status'] == 'deterministic_resource_limit' for r in rows)
    integrity = sum(r['status'] == 'integrity_defect' for r in rows)
    unresolved = sum(untyped(r) or r['status'] == 'transient_infrastructure' for r in rows)
    equal = all(r.get('oracle_equal') is True for r in measured)
    consistent = all(not r.get('consistency', 'untyped_missing').startswith('untyped') for r in measured)
    accounted = len(rows) == DENOMINATORS[route]
    admitted = accounted and equal and consistent and not integrity and unresolved <= CEILINGS[route]
    return {'amendment': 'A2', 'route': route, 'declared': DENOMINATORS[route],
            'accounted': len(rows), 'measured': len(measured), 'typed_deterministic_limits': limits,
            'integrity_defects': integrity, 'retried_untyped_cells': len(retry_rows),
            'retry_outcome_classes': dict(Counter(r['status'] for r in retry_rows)),
            'unresolved': unresolved, 'unresolved_maximum': CEILINGS[route],
            'equality_among_measured': 'PASS' if equal else 'FAIL',
            'component_consistency': 'PASS' if consistent else 'FAIL',
            'status': 'PASS' if admitted else 'FAIL', 'admitted': admitted,
            'complete_accounting': accounted, 'hashes': hashes, 'test_outcomes_disclosed': False}


def combine(receipts):
    by_route = {r['route']: r for r in receipts}
    if set(by_route) != set(DENOMINATORS):
        raise ValueError('A2 requires both routes')
    for route, r in by_route.items():
        if r['declared'] != DENOMINATORS[route] or r['unresolved_maximum'] != CEILINGS[route]:
            raise ValueError('A2 denominator or tolerance changed')
    admitted = all(r['admitted'] for r in receipts)
    return {'gate': 'R2', 'amendment': 'A2', 'status': 'PASS' if admitted else 'FAIL',
            'admitted': admitted, 'declared': 38784,
            **{k: sum(r[k] for r in receipts) for k in
               ('accounted', 'measured', 'typed_deterministic_limits', 'integrity_defects',
                'retried_untyped_cells', 'unresolved')},
            'routes': receipts, 'test_outcomes_disclosed': False,
            'chronology': 'A2 tolerance chosen after original opaque completeness receipt; no test details inspected'}


def verify_bindings(original):
    execution = json.loads((original / 'execution_lock.json').read_text())
    l1_path = V2 / 'locks/L1v2.json'
    if sha(l1_path) != execution['L1v2_sha256']:
        raise RuntimeError('original L1v2 changed')
    a2 = json.loads((V2 / 'locks/A2_reconciliation.json').read_text())
    for path, expected in a2['hashes'].items():
        if sha(path) != expected:
            raise RuntimeError('A2 binding changed')
    for path, expected in json.loads(l1_path.read_text())['hashes'].items():
        allowed = a2['authorized_document_supersessions'].get(path)
        if allowed and allowed['original_sha256'] != expected:
            raise RuntimeError('invalid document supersession')
        if sha(path) != (allowed['amended_sha256'] if allowed else expected):
            raise RuntimeError('frozen implementation/input changed')
    cgroup = next(line.split(':', 2)[2] for line in Path('/proc/self/cgroup').read_text().splitlines()
                  if line.startswith('0::'))
    if not cgroup.endswith('/' + a2['aggregate_systemd_scope']):
        raise RuntimeError('A2 aggregate scope absent')
    actual_limit = (Path('/sys/fs/cgroup') / cgroup.lstrip('/') / 'memory.max').read_text().strip()
    if actual_limit != str(execution['aggregate_memory_max_bytes']):
        raise RuntimeError('A2 aggregate memory limit changed')
    return execution


def reconcile_route(route, resume=False):
    original = Path(os.environ['WR']) / 'R2'
    target = original.parent / 'R2_A2'
    # Original coordinator must finish by itself before this process reads route results.
    if not (original / 'public_result.json').is_file():
        raise RuntimeError('original R2 is still running')
    launch = json.loads((original / 'launch_receipt.json').read_text())
    if any(watchdog.live(r) for r in launch['coordinators']):
        raise RuntimeError('original route coordinator remains alive')
    execution = verify_bindings(original)
    target.mkdir(exist_ok=True)
    fence = (target / (route + '.lock')).open('a')
    fcntl.flock(fence, fcntl.LOCK_EX | fcntl.LOCK_NB)
    folder = target / route
    folder.mkdir(exist_ok=resume)
    manifest_path = original / (route + '_manifest.jsonl')
    manifest = [json.loads(line) for line in manifest_path.open()]
    if any((r['split'] == 'test') != (route == 'opaque') for r in manifest):
        raise RuntimeError('A2 route isolation failed')
    old_path = original / route / 'results.jsonl'
    old = [json.loads(line) for line in old_path.open()]
    if len(old) != len(manifest) or len(old) != DENOMINATORS[route]:
        raise RuntimeError('original cohort accounting incomplete')
    by_ordinal = {r['ordinal']: r for r in old}
    if set(by_ordinal) != set(range(len(manifest))):
        raise RuntimeError('duplicate or missing original ordinal')
    for ordinal, row in by_ordinal.items():
        if row['cell_id'] != manifest[ordinal]['cell_id']:
            raise RuntimeError('original cell binding changed')
    selected = sorted(i for i, r in by_ordinal.items() if untyped(r))
    a2_lock = json.loads((V2 / 'locks/A2_reconciliation.json').read_text())
    if route == 'opaque':
        if len(selected) != a2_lock['observed_opaque_untyped_cells']:
            raise RuntimeError('opaque retry count differs from A2 disclosure')
        if sha(original / 'opaque_public_receipt.json') != a2_lock['original_opaque_public_receipt_sha256']:
            raise RuntimeError('original opaque public receipt changed')
    inventory = {'original_results_sha256': sha(old_path), 'manifest_sha256': sha(manifest_path),
                 'retry_cells': [{'ordinal': i, 'cell_id': manifest[i]['cell_id'],
                                  'source_sha256': manifest[i]['source_sha256']} for i in selected]}
    inventory_path = folder / 'private_retry_inventory.json'
    if inventory_path.exists():
        if json.loads(inventory_path.read_text()) != inventory:
            raise RuntimeError('retry inventory changed')
    else:
        inventory_path.write_text(json.dumps(inventory, indent=2) + '\n')
    wd = original.parent / 'watchdog'
    with watchdog.locked(wd):
        db = watchdog.database(wd)
        watchdog.register(db, RUN, 'r2_a2_' + route, os.getpid())
        db.close()

    def retry(ordinal):
        row = manifest[ordinal]
        cell = 'R2/' + row['cell_id']
        receipt = original / route / 'cells' / f'{ordinal:05d}' / 'attempt_2/receipt.json'
        child = None
        identity = None
        while True:
            with watchdog.locked(wd):
                db = watchdog.database(wd)
                slots = list(db.execute('SELECT * FROM r2_slots WHERE run=?', (RUN,)))
                living = [s for s in slots if alive_group(json.loads(s['identity_json']))]
                for s in slots:
                    if s not in living:
                        db.execute('DELETE FROM r2_slots WHERE run=? AND pid=?', (RUN, s['pid']))
                same_alive = any(s['cell'] == cell for s in living)
                prior = list(db.execute('SELECT * FROM attempts WHERE run=? AND cell=? ORDER BY attempt', (RUN, cell)))
                if not prior or len(prior) > 2 or any(p['source_hash'] != row['source_sha256'] for p in prior):
                    raise RuntimeError('persistent attempt/source binding invalid')
                if len(prior) == 2 and not same_alive:
                    if not resume:
                        raise RuntimeError('A2 retry already reserved')
                    db.commit(); db.close()
                    break
                memory = psutil.virtual_memory()
                admitted = min(execution['max_workers'], int(.5 * memory.available / execution['p99_peak_bytes']))
                if not same_alive and len(living) < admitted and memory.available >= .25 * memory.total:
                    reserve_retry(db, cell, row['source_sha256'])
                    handle = (folder / f'private_retry_{ordinal:05d}.log').open('x')
                    try:
                        child = subprocess.Popen(command_for(execution, route, ordinal), stdout=handle,
                                                 stderr=subprocess.STDOUT, start_new_session=True)
                        identity = watchdog.register(db, RUN, 'r2_a2_cell', child.pid)
                        db.execute('INSERT INTO r2_slots VALUES (?,?,?,?)',
                                   (RUN, child.pid, json.dumps(identity), cell))
                        db.commit()
                    finally:
                        handle.close(); db.close()
                    break
                db.commit(); db.close()
            time.sleep(1)
        if child is not None:
            child.wait()
            while alive_group(identity):
                time.sleep(1)
        if receipt.exists():
            result = json.loads(receipt.read_text())
            if result['cell_id'] != row['cell_id'] or result['source_sha256'] != row['source_sha256'] or result['attempt'] != 2:
                raise RuntimeError('A2 receipt identity changed')
        else:
            result = {**{k: row[k] for k in ('cell_id', 'split', 'task_id', 'group_id', 'sample_idx', 'source_sha256')},
                      'ordinal': ordinal, 'attempt': 2, 'status': 'unresolved_measurement',
                      'reason_code': 'retry_terminated_without_receipt'}
        with watchdog.locked(wd):
            db = watchdog.database(wd)
            db.execute('UPDATE attempts SET status=?,finished=? WHERE run=? AND cell=? AND attempt=2',
                       (result['status'], watchdog.now(), RUN, cell))
            if identity:
                db.execute('DELETE FROM r2_slots WHERE run=? AND pid=?', (RUN, identity['pid']))
            db.commit(); db.close()
        return result

    retries = []
    with ThreadPoolExecutor(max_workers=execution['max_workers']) as pool:
        futures = [pool.submit(retry, ordinal) for ordinal in selected]
        for future in as_completed(futures):
            result = future.result()
            retries.append(result)
            by_ordinal[result['ordinal']] = result
            print(json.dumps({'route': route, 'retried_completed': len(retries), 'retried_declared': len(selected)}), flush=True)
    effective = [by_ordinal[i] for i in range(len(manifest))]
    results_path = folder / 'results.jsonl'
    results_path.write_text(''.join(json.dumps(r) + '\n' for r in effective))
    private_statuses = folder / 'private_nonmeasured_cells.json'
    private_statuses.write_text(json.dumps([
        {'cell_id': r['cell_id'], 'status': r['status'], 'attempt': r['attempt'],
         'reason_code': r.get('exception', r.get('reason_code', r['status']))}
        for r in effective if r['status'] != 'measured'], indent=2) + '\n')
    if sha(old_path) != inventory['original_results_sha256']:
        raise RuntimeError('original results changed')
    public = public_receipt(route, effective, retries,
                            {'manifest': sha(manifest_path), 'original_results': sha(old_path),
                             'effective_results': sha(results_path), 'private_nonmeasured_ledger': sha(private_statuses),
                             'private_retry_inventory': sha(inventory_path),
                             'A2_lock': sha(V2 / 'locks/A2_reconciliation.json')})
    (target / (route + '_public_receipt.json')).write_text(json.dumps(public, indent=2) + '\n')
    print(json.dumps(public), flush=True)
    return public


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--route', choices=tuple(DENOMINATORS))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    target = Path(os.environ['WR']) / 'R2_A2'
    if args.route:
        receipt = reconcile_route(args.route, args.resume)
        return 0 if receipt['admitted'] else 1
    target.mkdir(exist_ok=args.resume)
    # Each route is a distinct process. The parent only reads sanitized public receipts.
    receipts = []
    for route in ('opaque', 'ordinary'):
        path = target / (route + '_public_receipt.json')
        if args.resume and path.is_file():
            receipt = json.loads(path.read_text())
            if receipt['hashes']['effective_results'] != sha(target / route / 'results.jsonl'):
                raise RuntimeError('completed A2 route changed')
            receipts.append(receipt)
            continue
        with (target / (route + '_coordinator.log')).open('a' if args.resume else 'x') as log:
            command = [sys.executable, str(Path(__file__).resolve()), '--route', route]
            if args.resume:
                command.append('--resume')
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
        if not path.is_file():
            print(json.dumps({'amendment': 'A2', 'route': route, 'status': 'INCOMPLETE', 'public_receipt_missing': True}), flush=True)
            return 1
        receipts.append(json.loads(path.read_text()))
    public = combine(receipts)
    (target / 'public_result.json').write_text(json.dumps(public, indent=2) + '\n')
    print(json.dumps(public), flush=True)
    return 0 if public['admitted'] else 1


if __name__ == '__main__':
    try:
        code = main()
    except Exception as exc:
        folder = Path(os.environ['WR']) / 'R2_A2'
        if '--route' in sys.argv:
            folder /= sys.argv[sys.argv.index('--route') + 1]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'private_coordinator_error.txt').write_text(traceback.format_exc())
        print(json.dumps({'amendment': 'A2', 'status': 'INCOMPLETE', 'error_type': type(exc).__name__,
                          'test_outcomes_disclosed': False}), flush=True)
        code = 1
    raise SystemExit(code)
