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
    """Create inputs only; no hosted service, admission or model calls occur here."""
    m = module or helper(config)
    m.RESULTS.mkdir(parents=True, exist_ok=True)
    table = validate(inputs, cpu_rows, Path(config['train_ids']).read_text().splitlines())
    root = m.PRIVATE/'inputs'
    root.mkdir(parents=True, exist_ok=False)
    rendered = m.PRIVATE/'rendered'; rendered.mkdir()
    rows = []; items = []; skipped = []; source_bindings = []
    for index, cell in enumerate(inputs['cells']):
        measured = table[cell['cell_id']]
        gate = measured.get('compile')
        if gate is not True:
            skipped.append({'cell_id': cell['cell_id'], 'compile': gate,
                'compiled_FSC': 0. if gate is False else None,
                'reason': 'known_compile_failure' if gate is False else 'unresolved_compile'})
            continue
        source = checked(cell['source']); text = source.read_text(encoding='utf-8')
        gold = m.PACK/cell['task_id']/'tests/gold.lean'
        instruction = m.PACK/cell['task_id']/'instruction.md'
        gold_text = gold.read_text(encoding='utf-8')
        item = f'audit_{index:03d}'
        folder = root/item; folder.mkdir()
        (folder/'solution.lean').write_bytes(source.read_bytes())
        (folder/'gold.lean').write_bytes(gold.read_bytes())
        (folder/'source.py').write_text(m.python_of(cell['task_id']), encoding='utf-8')
        metadata = {'item': item, 'task': cell['task_id'], 'split': cell['task_id'].split('__', 1)[0],
            'system': SYSTEM, 'sample_idx': 0, 'candidate_file': 'solution.lean', 'gold_file_name': 'gold.lean',
            'candidate_path': m.relative(folder/'solution.lean'), 'ref_ann_path': m.relative(folder/'gold.lean'),
            'py_ann_path': m.relative(folder/'source.py'), 'ref_placeholder_at_annotation': False,
            'n_ref_theorems_ann': len(m.build_inputs.statements(gold_text)), 'is_audit_only': True,
            'audit_cell_id': cell['cell_id'], 'source_task_id': cell['task_id']}
        items.append(metadata)
        system, user = m.prompts.render(m.RUBRIC, metadata, text, 'solution.lean')
        prompt_sha = m.sha((system+'\n\n'+user).encode())
        for repeat in (1, 2, 3):
            key = item+f'__r{repeat}'
            write_new(rendered/(key+'.json'), {'system': system, 'user': user})
            rows.append({'cell': key, 'item': item, 'task': cell['task_id'], 'repeat': repeat,
                'kind': 'main', 'system': SYSTEM, 'sample_idx': 0, 'is_audit_only': True,
                'candidate_sha256': cell['source']['sha256'], 'prompt_sha256': prompt_sha,
                'audit_cell_id': cell['cell_id']})
        source_bindings += [cell['source'], measured['strict_receipt'],
            {'path': str(gold), 'sha256': digest(gold)}, {'path': str(instruction), 'sha256': digest(instruction)}]
    write_new(m.PRIVATE/'items.json', items)
    receipt = m.PRIVATE/'cells_receipt.json'; write_new(receipt, {'cells': rows})
    pack = m.PRIVATE/'pack'
    if pack.exists(): raise ValueError('judge pack already exists; never rebuild measured inputs')
    m.judge_pack.RENDERED = rendered
    manifest = m.judge_pack.build(pack, receipt, 'judge', smoke_items=0)
    manifest['round_trip'] = m.judge_pack.verify(pack, manifest)
    by_cell = {r['cell']: r for r in rows}
    for row in manifest['cells']:
        original = by_cell[row['cell']]
        # The frozen aggregation groups by (task_id_vb, sample_idx). Each audit
        # variant is its own file key, retaining the actual task separately.
        row.update(system=SYSTEM, sample_idx=0, task_id_vb=original['audit_cell_id'],
                   source_task_id=original['task'], audit_cell_id=original['audit_cell_id'], is_audit_only=True)
    manifest.update(condition='v2-S2', split='train', declared_audit_cells=128,
        compiled_files=len(items), repeats=[1, 2, 3], configs=list(CONFIGS),
        n_declared_ratings=len(rows)*2, cells_not_judged=skipped,
        pack_abs=str(pack), rubric=m.RUBRIC, rubric_fingerprint=m.prompts.rubric_fingerprint(m.RUBRIC),
        verdict='FAIL' if manifest['round_trip']['failures'] else 'PASS',
        source_bindings=source_bindings, model_calls=0)
    write_new(m.suite_spec(SUITE)['pack_receipt'], manifest)
    return manifest


def combine(inputs, cpu_rows, fsc, *, train):
    """Keep all 128 compile-gated outcomes; six complete ratings are required for each compiled file."""
    table = validate(inputs, cpu_rows, train)
    expected = {c['cell_id']+'#0' for c in inputs['cells'] if table[c['cell_id']].get('compile') is True}
    if set(fsc['cells']) != expected: raise ValueError('judge aggregation cohort changed')
    result = []
    for cell in inputs['cells']:
        gate = table[cell['cell_id']].get('compile'); ratings = None
        if gate is True:
            ratings = fsc['cells'][cell['cell_id']+'#0']
            complete = ratings['complete_3x2'] and ratings['repeats_measured'] == dict.fromkeys(CONFIGS, 3)
            value = ratings['FSC'] if complete else None
            if value is not None and not 0 <= value <= 1: raise ValueError('FSC outside the frozen scale')
        else: value = 0. if gate is False else None
        result.append({**{k: cell[k] for k in ('cell_id', 'audit_id', 'task_id', 'split', 'variant')},
            'compile': gate, 'formal_specification_coverage': value, 'ratings': ratings})
    return {'condition': 'v2-S2', 'declared': 128, 'rows': result,
        'coverage_known': sum(r['formal_specification_coverage'] is not None for r in result),
        'rule': 'known compile failure zero; unresolved compile unknown; compiled file median of 3 per member then mean/5; any missing rating unknown'}
