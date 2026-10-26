"""Build a train-only audit judge pack with frozen rendering and three declared repeats per member."""
from __future__ import annotations

import json
import re
from pathlib import Path

from audit_inputs import checked, VARIANTS
from coverage_controls import helper as controls_helper, CONFIGS
from training_checkpoint import digest, write_new

SUITE = 'rl4cv-e13v2-train-audit'
SYSTEM = 'train_audit'


def helper(config):
    if not re.fullmatch(r'rl4cv_e13v2_[a-zA-Z0-9_]+', config['private_namespace']):
        raise ValueError('owned audit input namespace required')
    m = controls_helper(config)
    m.PRIVATE = m.E103/'private/judge'/config['private_namespace']
    m.suite_spec = lambda suite: {'suite': SUITE, 'system': SYSTEM,
        'benchmark': config['benchmark_prefix']+'-train-audit',
        'pack_receipt': m.RESULTS/'judge_pack_train_audit.json',
        'key_prefix': SYSTEM+'/', 'part_field': 'cells'}
    m.request_benchmark = lambda spec, name: 'rl4cv-e13v2-S2-train-audit-'+name
    return m


def validate(inputs, rows, train):
    cells = inputs['cells']; allowed = set(train)
    if inputs.get('condition') != 'v2-S2' or len(cells) != 128 or inputs['declared_tasks'] != 32:
        raise ValueError('complete frozen train audit manifest required')
    table = {row['cell_id']: row for row in rows}
    if len(table) != len(rows) or set(table) != {c['cell_id'] for c in cells}:
        raise ValueError('audit processor denominator changed')
    identities = set()
    for cell in cells:
        if cell['split'] != 'train' or cell['task_id'] not in allowed or cell['variant'] not in VARIANTS:
            raise ValueError('only declared train audit variants can be judged')
        row = table[cell['cell_id']]
        if any(row[k] != cell[k] for k in ('cell_id', 'audit_id', 'task_id', 'group_id', 'split', 'variant')):
            raise ValueError('audit processor identity changed')
        if not row.get('cleanup_verified'): raise ValueError('audit processor cleanup remains unresolved')
        if row.get('compile') is not None and type(row['compile']) is not bool:
            raise ValueError('compile gate is not a known Boolean')
        if cell.get('source'): checked(cell['source'])
        if row.get('compile') is not None:
            receipt = json.loads(checked(row['strict_receipt']).read_text())
            if receipt.get('status') != 'measured' or receipt.get('compile') is not row['compile']:
                raise ValueError('compile gate is detached from its strict receipt')
            if cell.get('source') is None or receipt.get('source_sha256') != cell['source']['sha256']:
                raise ValueError('compile gate source differs from the judge candidate')
        identities.add((cell['audit_id'], cell['variant']))
    if len(identities) != 128 or len({c['audit_id'] for c in cells}) != 32:
        raise ValueError('audit cohort or variants changed')
    return table


def build(config, inputs, cpu_rows, *, module=None):
    """Create the complete fixed 128-cell audit pack with the unchanged renderer."""
    from coverage_pack import build as build_pack
    table=validate(inputs,cpu_rows,Path(config['train_ids']).read_text().splitlines())
    return build_pack(inputs,table,module=module or helper(config),declared=128,system=SYSTEM,suite=SUITE)


def combine(inputs, cpu_rows, fsc, *, train):
    """Retain all 128 compile-gated audit outcomes under the unchanged aggregation."""
    from coverage_pack import combine as combine_pack
    table=validate(inputs,cpu_rows,train)
    return combine_pack(inputs,table,fsc,declared=128,configs=CONFIGS,
        identity_keys=('cell_id','audit_id','task_id','split','variant'))
