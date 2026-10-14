"""Construct the complete historical validation grid with A3 exclusions before reading measurements."""
from __future__ import annotations

import json
from pathlib import Path

from panel import digest

EXCLUSION_SHA256 = 'c00b35abaecda874820d4b1b29015655e248c19f319fa574fefa3d0804124128'


def verify_bindings(bindings):
    paths = {}
    for name, binding in bindings.items():
        path = Path(binding['path'])
        if digest(path) != binding['sha256']:
            raise ValueError('G1 input hash mismatch: '+name)
        paths[name] = path
    return paths


def grid(manifest, receipts, exclusions, systems, *, task_count=135, expected_exclusions=217):
    """Canonical-source exclusions propagate to every ladder policy alias."""
    excluded = {r['cell_id'] for r in exclusions}
    if len(excluded) != len(exclusions) or len(excluded) != expected_exclusions:
        raise ValueError('A3 exclusion denominator changed')
    canonical = {}; slots = {}; groups = {}; aliases = set()
    policies = {s['label'] for s in systems}
    for row in manifest:
        if row['split'] not in ('train','validation'): raise ValueError('test is sealed')
        cell = row['cell_id']
        if cell in canonical: raise ValueError('duplicate canonical source')
        canonical[cell] = row
        if row['split'] != 'validation': continue
        task = row['task_id']
        if task in groups and groups[task] != row['group_id']: raise ValueError('changed group identity')
        groups[task] = row['group_id']
        for expectation in row['expectations']:
            if expectation['family'] != 'ladder': continue
            policy = expectation['policy']; key = (policy,task,row['sample_idx'])
            if key in slots or policy not in policies: raise ValueError('unexpected ladder identity')
            slots[key] = cell
            if cell in excluded: aliases.add(f'{policy}/{task}/{row["sample_idx"]}')
    if not excluded <= set(canonical): raise ValueError('exclusion is not an ordinary source')
    if any(canonical[r['cell_id']]['split'] != r['split'] for r in exclusions):
        raise ValueError('exclusion split changed')
    expected = {(p,t,s) for p in policies for t in groups for s in range(8)}
    if len(groups) != task_count or set(slots) != expected: raise ValueError('incomplete ladder denominator')
    measured = {}; seen = set()
    for row in receipts:
        if row['split'] not in ('train','validation'): raise ValueError('test is sealed')
        cell = row['cell_id']
        if cell in seen or cell not in canonical: raise ValueError('unexpected canonical receipt')
        seen.add(cell)
        # Do not inspect excluded statuses, factors or readbacks.
        if cell in excluded or row['split'] != 'validation': continue
        source = canonical[cell]
        if any(row[k] != source[k] for k in ('split','task_id','sample_idx','source_sha256')):
            raise ValueError('source/receipt identity mismatch')
        if row['status'] != 'measured': raise ValueError('unlisted missing historical measurement')
        components = row['components']
        for rb in row['readbacks']:
            if rb['family'] != 'ladder': continue
            key = (rb['policy'],row['task_id'],row['sample_idx'])
            if slots.get(key) != cell or key in measured: raise ValueError('unexpected policy readback')
            if not rb['equal'] or rb['status'] != 'scored' or rb['value'] not in (0,1):
                raise ValueError('unexcluded strict disagreement')
            reward = rb['factored_reward']
            if not isinstance(reward,(int,float)) or not 0 <= reward <= 1:
                raise ValueError('invalid earlier reward')
            if any(row[k] not in (0,1) for k in ('q1','compile','honest')):
                raise ValueError('invalid measured hurdle')
            measured[key] = {'strict':rb['value'], 'strict_status':'scored', 'factored_reward':reward,
                             **{k:row[k] for k in ('q1','compile','honest')},
                             'consistency':rb['consistency'],
                             'component_consistency':components['consistency']}
    rows = []
    for key in sorted(expected):
        policy,task,sample = key; missing = slots[key] in excluded
        if not missing and key not in measured: raise ValueError('unlisted missing policy cell')
        value = ({'strict':None,'strict_status':'excluded','factored_reward':None,
                  'q1':None,'compile':None,'honest':None} if missing else measured[key])
        rows.append({'policy':policy,'task_id':task,'sample_idx':sample,'split':'validation',
                     'group_id':groups[task], 'canonical_cell_id':slots[key], **value})
    return rows, aliases, groups


def load(bindings, systems):
    """Hash every byte before parsing any ordinary measurements; never open the opaque route."""
    paths = verify_bindings(bindings)
    required = {'ordinary_manifest','ordinary_results','exclusions'}
    if not required <= set(paths): raise ValueError('required G1 bindings absent')
    if bindings['exclusions']['sha256'] != EXCLUSION_SHA256: raise ValueError('wrong A3 exclusion identity')
    manifest = [json.loads(line) for line in paths['ordinary_manifest'].read_text().splitlines()]
    exclusions = json.loads(paths['exclusions'].read_text())
    with paths['ordinary_results'].open() as stream:
        return grid(manifest,(json.loads(line) for line in stream),exclusions,systems)
