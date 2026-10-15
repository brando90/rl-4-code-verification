"""Render only the fixed selected-test coverage sample with the validated judge recipe and complete missingness."""
from __future__ import annotations

import re
from pathlib import Path

from coverage_controls import helper as controls_helper,CONFIGS
from coverage_pack import combine as combine_pack
from technical_driver import read,reference
from training_checkpoint import digest,write_new
from selected_coverage_inputs import IDENTITY

SUITE='rl4cv-e13v2-selected-test'
SYSTEM='selected_test'


def helper(config):
    if not re.fullmatch(r'rl4cv_e13v2_[a-zA-Z0-9_]+',config['private_namespace']):
        raise ValueError('owned selected-test input namespace required')
    m=controls_helper(config)
    m.PRIVATE=m.E103/'private/judge'/config['private_namespace']
    m.suite_spec=lambda suite:{'suite':SUITE,'system':SYSTEM,'benchmark':config['benchmark_prefix']+'-selected-test',
        'pack_receipt':m.RESULTS/'judge_pack_selected_test.json','key_prefix':SYSTEM+'/','part_field':'cells'}
    m.request_benchmark=lambda spec,name:'rl4cv-e13v2-S2-selected-test-'+name
    return m


def validate(inputs,allowed):
    if (inputs.get('condition'),inputs.get('stage'),inputs.get('split'),inputs.get('declared'),inputs.get('sample_idx'))!=('v2-S2','SELECTED_TEST_COVERAGE_INPUTS','test',222,0):
        raise ValueError('complete fixed selected-test coverage inputs required')
    cells=inputs['cells'];allowed=set(allowed)
    if len(cells)!=222 or len({c['cell_id'] for c in cells})!=222 or len(allowed)!=222 or {c['task_id'] for c in cells}!=allowed:
        raise ValueError('complete selected-test population changed')
    table={}
    for cell in cells:
        if cell['split']!='test' or cell['sample_idx']!=0 or any(cell[k]!=inputs[k] for k in ('arm','run_seed','boundary')):
            raise ValueError('selected-test sample or checkpoint changed')
        strict=read(cell['strict']);saved=read(strict['strict_receipt'])
        if any(strict.get(k)!=cell[k] or saved.get(k)!=cell[k] for k in IDENTITY):
            raise ValueError('selected-test official evidence identity changed')
        if strict.get('cleanup_verified') is not True or saved.get('cleanup_verified') is not True:
            raise ValueError('selected-test official cleanup unresolved')
        gate=strict.get('compile')
        if gate is not None and type(gate) is not bool:raise ValueError('official compile gate must be a known Boolean')
        if cell.get('source') and digest(cell['source']['path'])!=cell['source']['sha256']:
            raise ValueError('selected-test candidate changed')
        if gate is not None:
            oracle=read(strict['oracle_receipt'])
            if strict['status']!='measured' or saved['status']!='measured' or oracle.get('compile') is not gate or saved.get('compile') is not gate:
                raise ValueError('compile gate differs from official evidence')
            if cell.get('source') is None or strict['source_sha256']!=cell['source']['sha256'] or saved['source_sha256']!=cell['source']['sha256']:
                raise ValueError('official compile gate source changed')
        table[cell['cell_id']]={**strict,'strict_receipt':cell['strict']}
    return table


def build(config,inputs,*,module=None):
    """Parent requires selected-test authority and freezes this complete pack before any hosted admission."""
    table=validate(inputs,Path(config['test_ids']).read_text().splitlines());m=module or helper(config)
    m.RESULTS.mkdir(parents=True,exist_ok=True);root=m.PRIVATE/'inputs';root.mkdir(parents=True,exist_ok=False)
    rendered=m.PRIVATE/'rendered';rendered.mkdir();rows=[];items=[];skipped=[];bindings=[]
    for index,cell in enumerate(inputs['cells']):
        measured=table[cell['cell_id']];gate=measured['compile']
        official=read(cell['strict']);bindings.extend([cell['strict'],official['strict_receipt']])
        if official.get('oracle_receipt'):bindings.append(official['oracle_receipt'])
        if gate is not True:
            skipped.append({'cell_id':cell['cell_id'],'compile':gate,'compiled_FSC':0. if gate is False else None,
                'reason':'known_compile_failure' if gate is False else 'unresolved_compile'});continue
        source=Path(cell['source']['path']);gold=m.PACK/cell['task_id']/'tests/gold.lean';instruction=m.PACK/cell['task_id']/'instruction.md'
        text=source.read_text();gold_text=gold.read_text();item=f'selected_{index:03d}';folder=root/item;folder.mkdir()
        (folder/'solution.lean').write_bytes(source.read_bytes());(folder/'gold.lean').write_bytes(gold.read_bytes())
        (folder/'source.py').write_text(m.python_of(cell['task_id']))
        metadata={'item':item,'task':cell['task_id'],'split':cell['task_id'].split('__',1)[0],
            'system':SYSTEM,'sample_idx':0,'candidate_file':'solution.lean','gold_file_name':'gold.lean',
            'candidate_path':m.relative(folder/'solution.lean'),'ref_ann_path':m.relative(folder/'gold.lean'),
            'py_ann_path':m.relative(folder/'source.py'),'ref_placeholder_at_annotation':False,
            'n_ref_theorems_ann':len(m.build_inputs.statements(gold_text)),'is_audit_only':False,
            'selected_cell_id':cell['cell_id'],'source_task_id':cell['task_id']}
        items.append(metadata);system,user=m.prompts.render(m.RUBRIC,metadata,text,'solution.lean')
        fingerprint=m.sha((system+'\n\n'+user).encode())
        for repeat in (1,2,3):
            key=item+f'__r{repeat}';write_new(rendered/(key+'.json'),{'system':system,'user':user})
            rows.append({'cell':key,'item':item,'task':cell['task_id'],'repeat':repeat,'kind':'main','system':SYSTEM,
                'sample_idx':0,'is_audit_only':False,'candidate_sha256':cell['source']['sha256'],
                'prompt_sha256':fingerprint,'selected_cell_id':cell['cell_id']})
        bindings.extend([cell['source'],reference(gold),reference(instruction)])
    write_new(m.PRIVATE/'items.json',items);receipt=m.PRIVATE/'cells_receipt.json';write_new(receipt,{'cells':rows})
    pack=m.PRIVATE/'pack'
    if pack.exists():raise ValueError('selected-test judge pack already exists')
    m.judge_pack.RENDERED=rendered;manifest=m.judge_pack.build(pack,receipt,'judge',smoke_items=0)
    manifest['round_trip']=m.judge_pack.verify(pack,manifest);by_cell={r['cell']:r for r in rows}
    for row in manifest['cells']:
        original=by_cell[row['cell']];row.update(system=SYSTEM,sample_idx=0,task_id_vb=original['selected_cell_id'],
            selected_cell_id=original['selected_cell_id'],source_task_id=original['task'],is_audit_only=False)
    manifest.update(condition='v2-S2',split='test',declared=222,compiled_files=len(items),repeats=[1,2,3],configs=list(CONFIGS),
        n_declared_ratings=len(rows)*2,cells_not_judged=skipped,pack_abs=str(pack),rubric=m.RUBRIC,
        rubric_fingerprint=m.prompts.rubric_fingerprint(m.RUBRIC),source_bindings=bindings,model_calls=0,
        verdict='FAIL' if manifest['round_trip']['failures'] else 'PASS',**{k:inputs[k] for k in ('arm','run_seed','boundary')})
    write_new(m.suite_spec(SUITE)['pack_receipt'],manifest);return manifest


def combine(inputs,fsc,*,test_ids):
    table=validate(inputs,test_ids)
    return combine_pack(inputs,table,fsc,declared=222,identity_keys=IDENTITY,configs=CONFIGS)
