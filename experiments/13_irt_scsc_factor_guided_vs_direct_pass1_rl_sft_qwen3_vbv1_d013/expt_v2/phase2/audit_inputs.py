"""Prepare all fixed train audit variants from hash-bound original scoring evidence before new measurements."""
from __future__ import annotations

import json
from pathlib import Path

from audit_mutations import construct
from training_checkpoint import digest, write_new

VARIANTS = ('original', 'padding', 'deletion', 'substitution')


def checked(reference):
    path = Path(reference['path'])
    if digest(path) != reference['sha256']: raise ValueError('audit input changed')
    return path


def prepare(cohort, evidence, *, train_ids, output):
    """Retain every declared source/variant; absent source or frontend yields explicit missing variants."""
    cells = cohort['cells']; allowed = set(train_ids)
    if (cohort['condition'] != 'v2-S2' or len(cells) != 32 or cohort['audit_tasks'] != 32
            or len({c['task_id'] for c in cells}) != 32 or len({c['group_id'] for c in cells}) != 32
            or len({c['audit_id'] for c in cells}) != 32):
        raise ValueError('audit requires the complete fixed 32-group train cohort')
    for cell in cells:
        if (cell['split'] != 'train' or cell['task_id'] not in allowed
                or cell['baseline_batch'] != 'full1' or cell['baseline_sample'] != 0):
            raise ValueError('audit baseline selection changed or contains held-out data')
    table = {r['task_id']: r for r in evidence}
    if len(table) != len(evidence) or set(table) != {c['task_id'] for c in cells}:
        raise ValueError('complete original evidence inventory required')
    root = Path(output); root.mkdir(parents=True, exist_ok=False)
    result = []; inputs = []
    for index, cell in enumerate(cells):
        supplied = table[cell['task_id']]
        original = supplied.get('source'); frontend = supplied.get('frontend'); score = supplied.get('score')
        metadata = {'audit_id': cell['audit_id'], 'task_id': cell['task_id'], 'group_id': cell['group_id'],
                    'split': 'train', 'condition': 'v2-S2', 'baseline_batch': 'full1', 'baseline_sample': 0}
        # Input preparation never measures or uses a reward to choose a target.
        # Pairing must be supplied by the published full1 scoring inventory.
        source_bytes = checked(original).read_bytes() if original else None
        if original: inputs.append(original)
        old = json.loads(checked(score).read_text()) if score else None
        if score: inputs.append(score)
        if old is not None and (old.get('task_id') != cell['task_id'] or old.get('sample_idx') != 0 or old.get('batch') != 'full1' or old.get('policy') != 'sft_4B_f1p0'):
            raise ValueError('original score identity differs from the fixed baseline')
        if old is not None and old.get('status') == 'measured':
            if original is None or old.get('source_sha256') != original['sha256']:
                raise ValueError('original measurement does not bind these source bytes')
        built = None
        if source_bytes is not None and frontend is not None:
            # A complete original measurement couples source and frontend from
            # the same immutable evidence directory; no detached-span guessing.
            if old is None or old.get('status') != 'measured':
                raise ValueError('frontend/source pair lacks measured original provenance')
            front_path = checked(frontend); inputs.append(frontend)
            if front_path.resolve() != (checked(score).parent/'evidence/components/frontend.json').resolve():
                raise ValueError('frontend is detached from its original scoring receipt')
            front = json.loads(front_path.read_text())
            if front.get('terminal') is True:
                built = construct(source_bytes, front, expected_sha256=original['sha256'])
        folder = root/f'{index:03d}'; folder.mkdir()
        for variant in VARIANTS:
            row = {**metadata, 'variant': variant, 'cell_id': cell['audit_id']+'/'+variant,
                   'original_source': original, 'original_score': score, 'original_frontend': frontend}
            if variant == 'original' and source_bytes is not None:
                contents = source_bytes; row.update(status='PREPARED', original_measurement_reused=old is not None and old.get('status') == 'measured')
            elif variant != 'original' and built is not None:
                mutation = built[variant]; contents = mutation['source']
                row.update({k: v for k, v in mutation.items() if k != 'source'})
                row['status'] = 'PREPARED'; row['mutation_status'] = mutation['status']
            else:
                contents = None; row.update(status='MISSING_INPUT', reason='source_or_complete_bound_frontend_unavailable')
            if contents is not None:
                path = folder/(variant+'.lean')
                with path.open('xb') as out: out.write(contents)
                row['source'] = {'path': str(path), 'sha256': digest(path)}
            else: row['source'] = None
            result.append(row)
    manifest = {'condition': 'v2-S2', 'status': 'PREPARED_NOT_ADMITTED', 'split': 'train',
                'declared_tasks': 32, 'declared_variants': 128, 'variants': list(VARIANTS), 'cells': result,
                'missing_inputs': sum(r['status'] == 'MISSING_INPUT' for r in result),
                'original_bindings': inputs, 'new_measurements': 0,
                'selection': 'fixed cohort and source-order transformations; no outcome-based choice'}
    write_new(root/'inputs.json', manifest)
    return manifest
