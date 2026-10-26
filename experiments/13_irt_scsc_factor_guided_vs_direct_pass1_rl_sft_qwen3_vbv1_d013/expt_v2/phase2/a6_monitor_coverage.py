"""Bind the fixed 32-cell pilot snapshot to the unchanged validated judge renderer and aggregation."""
from __future__ import annotations

from a6_monitor_points import valid_checkpoint

import json
from pathlib import Path
import re

from audit_inputs import checked
from coverage_controls import helper as controls_helper,CONFIGS
from coverage_pack import build as build_pack,combine as combine_pack

SUITE='rl4cv-e13v2-pilot-monitor'
SYSTEM='pilot_monitor'
IDENTITY=('cell_id','audit_id','task_id','group_id','split','arm','run_seed','update')


def helper(config):
    if not re.fullmatch(r'rl4cv_e13v2_[a-zA-Z0-9_]+',config['private_namespace']):
        raise ValueError('owned monitor input namespace required')
    if not re.fullmatch(r'b-1301-u(?:0|10|20|30|40|50|60)',config['snapshot_name']):
        raise ValueError('fixed monitor snapshot name required')
    m=controls_helper(config);m.PRIVATE=m.E103/'private/judge'/config['private_namespace']
    m.suite_spec=lambda suite:{'suite':SUITE,'system':SYSTEM,
        'benchmark':config['benchmark_prefix']+'-monitor-'+config['snapshot_name'],
        'pack_receipt':m.RESULTS/'judge_pack_pilot_monitor.json','key_prefix':SYSTEM+'/', 'part_field':'cells'}
    m.request_benchmark=lambda spec,name:'rl4cv-e13v2-S2-monitor-'+config['snapshot_name']+'-'+name
    return m


def validate(inputs,rows,train):
    cells=inputs['cells'];allowed=set(train)
    if (inputs.get('condition')!='v2-S2' or inputs.get('declared')!=32 or len(cells)!=32
            or not valid_checkpoint(inputs.get('arm'),inputs.get('run_seed'),inputs.get('update'))
            or len({c['audit_id'] for c in cells})!=32 or len({c['task_id'] for c in cells})!=32):
        raise ValueError('complete fixed monitor snapshot required')
    table={r['cell_id']:r for r in rows}
    if len(table)!=len(rows) or set(table)!={c['cell_id'] for c in cells}:raise ValueError('monitor coverage denominator changed')
    for cell in cells:
        if cell['split']!='train' or cell['task_id'] not in allowed:raise ValueError('monitor coverage is train-only')
        if any(cell[k]!=inputs[k] for k in ('arm','run_seed','update')):raise ValueError('monitor input checkpoint changed')
        row=table[cell['cell_id']]
        if any(row.get(k)!=cell[k] for k in IDENTITY):raise ValueError('monitor coverage identity changed')
        if row.get('cleanup_verified') is not True:raise ValueError('monitor processor cleanup unresolved')
        gate=row.get('compile')
        if gate is not None and type(gate) is not bool:raise ValueError('invalid monitor compile gate')
        if cell.get('source'):checked(cell['source'])
        if gate is not None:
            if row.get('strict_receipt')!=cell['strict']:raise ValueError('monitor strict source receipt changed')
            strict=json.loads(checked(cell['strict']).read_text())
            if strict.get('status')!='measured' or strict.get('compile') is not gate:
                raise ValueError('monitor compile gate detached from official strict evidence')
            if any(strict.get(k)!=cell[k] for k in ('cell_id','task_id','split','arm','run_seed','update')):
                raise ValueError('monitor official measurement belongs to another snapshot')
            if not cell.get('source') or strict.get('source_sha256')!=cell['source']['sha256']:
                raise ValueError('monitor judge candidate differs from official source')
            checked(strict['strict_receipt']);oracle=json.loads(checked(strict['oracle_receipt']).read_text())
            if oracle.get('compile') is not gate:raise ValueError('official oracle compile field changed')
    return table


def build(config,inputs,rows,*,module=None):
    table=validate(inputs,rows,Path(config['train_ids']).read_text().splitlines())
    expected=f"{inputs['arm'].lower()}-{inputs['run_seed']}-u{inputs['update']}"
    if config['snapshot_name']!=expected:raise ValueError('monitor service names another snapshot')
    return build_pack(inputs,table,module=module or helper(config),declared=32,system=SYSTEM,suite=SUITE)


def combine(inputs,rows,fsc,*,train):
    return combine_pack(inputs,validate(inputs,rows,train),fsc,declared=32,configs=CONFIGS,identity_keys=IDENTITY)
