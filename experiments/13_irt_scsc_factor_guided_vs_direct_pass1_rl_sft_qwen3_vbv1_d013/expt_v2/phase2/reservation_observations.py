"""Reconcile only frozen byte-identical copies of historical read-only reservation observations."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from training_checkpoint import digest


def reconcile(allocation, lock):
    rows = lock['configuration'].get('reservation_observation_duplicates', [])
    if not rows:
        return allocation
    bound = {str(Path(b['path']).resolve()): b['sha256'] for b in lock['bindings']}
    if bound.get(str(Path(__file__).resolve())) != digest(__file__):
        raise ValueError('reservation reconciliation implementation unbound')
    result = copy.deepcopy(allocation)
    inventory = result['reservation_inventory']
    seen = set(inventory['paths'])
    for row in rows:
        if set(row) != {'path', 'reference_path', 'sha256'}:
            raise ValueError('invalid duplicate observation binding')
        target, reference = Path(row['path']).resolve(), Path(row['reference_path']).resolve()
        if target == reference or str(target) in seen:
            raise ValueError('duplicate observation identity')
        if not any(target.is_relative_to(Path(root).resolve()) for root in inventory['roots']):
            raise ValueError('observation outside frozen reservation roots')
        for path in (target, reference):
            if bound.get(str(path)) != row['sha256'] or digest(path) != row['sha256']:
                raise RuntimeError('reservation observation changed; reconcile before claim')
        if target.read_bytes() != reference.read_bytes():
            raise RuntimeError('reservation observation is not an exact copy')
        observation = json.loads(reference.read_text())
        if (observation.get('scope') != 'Read-only foreign lease/reservation review, not an allocation'
                or observation.get('unreleased_records') != 0):
            raise ValueError('only an inactive historical observation can be reconciled')
        seen.add(str(target))
        inventory['paths'].append(str(target))
        result['reservation_bindings'].append({'path': str(target), 'sha256': row['sha256']})
    inventory['paths'].sort()
    # Only observed paths and their exact bindings change. In particular the
    # caller retains the original allocation hash, caps and live foreign registries.
    return result
