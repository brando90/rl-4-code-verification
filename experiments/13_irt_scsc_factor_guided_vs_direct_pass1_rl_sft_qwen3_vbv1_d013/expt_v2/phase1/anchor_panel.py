"""Generate bounded segments of a complete frozen anchor panel without repeating completed cells."""
from __future__ import annotations

import fcntl
import json
from pathlib import Path
import time

from panel import check_prerequisites, validate_manifest, validate_generation
from anchor_storage import write_new,mkdir

BATCHES = ('base', 'half', 'full1', 'full2')


def inventory(manifest, train_ids, root):
    cells = validate_manifest(manifest, train_ids)
    if manifest['batch'] not in BATCHES:
        raise ValueError('not an anchor manifest')
    root = Path(root)
    completed = []; pending = []; exhausted = []
    for index, cell in enumerate(cells):
        path = root/f'{index:05d}.generation.json'
        attempts = [n for n in (1, 2) if (root/f'{index:05d}.attempt{n}.json').exists()]
        if (root/f'{index:05d}.attempt3.json').exists() or attempts == [2]:
            raise ValueError('invalid anchor attempt ledger')
        for attempt in attempts:
            prior=json.loads((root/f'{index:05d}.attempt{attempt}.json').read_text())
            if (prior.get('cell_id')!=cell['cell_id'] or prior.get('seed')!=cell['seed']
                    or prior.get('attempt')!=attempt):
                raise ValueError('anchor attempt identity changed')
        if path.exists():
            row = json.loads(path.read_text())
            if any(row.get(k) != cell[k] for k in ('cell_id','task_id','sample','split','seed')):
                raise ValueError('completed anchor identity changed')
            validate_generation(cell, row, manifest)
            if not attempts:
                raise ValueError('completed cell lacks its durable attempt')
            completed.append(index)
        elif len(attempts) < 2:
            pending.append((index, cell, len(attempts)+1))
        else:
            exhausted.append(index)
    return {'declared':len(cells),'completed':completed,'pending':pending,'exhausted':exhausted}


def run_segment(manifest, train_ids, root, *, generate_batch, lease_check,
                prerequisites, segment_id, lease_id, maximum_cells=256, batch_size=32, may_start_batch=lambda: True):
    """One bounded process invocation; interruptions consume only started cell attempts.

    A fresh lease can continue unstarted cells or the one allowed identical retry.
    Existing complete outputs are validated and never sent back to the engine.
    The controller must verify prior-process cleanup before acquiring that lease.
    """
    if type(maximum_cells) is not int or not 1 <= maximum_cells <= 256:
        raise ValueError('segment outside frozen resource envelope')
    if batch_size != 32 or type(segment_id) is not int or segment_id < 0:
        raise ValueError('changed batch size or segment identity')
    check_prerequisites(manifest['batch'], **prerequisites)
    root = Path(root); mkdir(root)
    with (root/'generation.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = inventory(manifest,train_ids,root)
        if (root/'terminal.json').exists():
            return json.loads((root/'terminal.json').read_text())
        selected = before['pending'][:maximum_cells]
        lease_check()
        start = {'segment_id':segment_id,'lease_id':lease_id,'started_unix':time.time(),
                 'declared':before['declared'],'selected':len(selected),
                 'completed_before':len(before['completed']),'maximum_cell_attempts':2}
        write_new(root/f'segment_{segment_id:05d}.started.json',start)
        error = None; attempted = 0
        try:
            for offset in range(0,len(selected),batch_size):
                lease_check()
                if not may_start_batch(): break
                chunk = selected[offset:offset+batch_size]
                for index, cell, attempt in chunk:
                    write_new(root/f'{index:05d}.attempt{attempt}.json',{
                        'cell_id':cell['cell_id'],'seed':cell['seed'],'attempt':attempt,
                        'segment_id':segment_id,'lease_id':lease_id,'started_unix':time.time()})
                attempted += len(chunk)
                raws = generate_batch([cell for _,cell,_ in chunk])
                write_new(root/f'segment_{segment_id:05d}_batch_{offset:05d}.raw.json',raws)
                if len(raws) != len(chunk):
                    raise ValueError('generation omitted or added a response')
                # Preserve all independently valid responses even if another row is bad.
                failures = []
                for (index,cell,attempt),raw in zip(chunk,raws):
                    try:
                        validate_generation(cell,raw,manifest)
                    except (ValueError,KeyError,TypeError) as exc:
                        failures.append(type(exc).__name__)
                        write_new(root/f'{index:05d}.attempt{attempt}.error.json',{
                            'error_type':type(exc).__name__,'error':str(exc)})
                    else:
                        write_new(root/f'{index:05d}.generation.json',{
                            **raw,**cell,'cell_id':cell['cell_id'],'split':'train',
                            'at_token_cap':raw['finish_reason']=='length'})
                if failures:
                    raise ValueError('one or more generation receipts are invalid')
        except BaseException as exc:
            error = {'error_type':type(exc).__name__,'error':str(exc)}
            raise
        finally:
            after = inventory(manifest,train_ids,root)
            status = ('COMPLETE' if len(after['completed'])==after['declared'] else
                      'INCOMPLETE' if not after['pending'] else
                      'INCOMPLETE_INFRA' if error else 'CHECKPOINT')
            receipt = {**start,'status':status,'completed':len(after['completed']),
                       'pending':len(after['pending']),'exhausted':len(after['exhausted']),
                       'ended_unix':time.time(),'attempted_in_segment':attempted,'error':error}
            write_new(root/f'segment_{segment_id:05d}.result.json',receipt)
            if status in ('COMPLETE','INCOMPLETE'):
                write_new(root/'terminal.json',receipt)
        return receipt
