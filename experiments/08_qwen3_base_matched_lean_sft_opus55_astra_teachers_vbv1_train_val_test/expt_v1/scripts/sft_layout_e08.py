#!/usr/bin/env python3
"""Resolve recorded SFT layouts only after invariant, execution and numerical admission."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import yaml

EXPV = Path(__file__).resolve().parents[1]
REGISTRY = EXPV / 'results/sft_layout_admission_14B.json'
REQUIRED_CHECKS = {'static_invariants', 'execution', 'numerics', 'resume', 'performance', 'semantic_equivalence'}
# Protocol sections 8/14 permit only these infrastructure differences in this route.
ALLOWED = {('cluster', 'gpus_per_node'), ('policy', 'dtensor_cfg', 'tensor_parallel_size'),
           ('policy', 'dtensor_cfg', 'cpu_offload'), ('policy', 'dtensor_cfg', 'env_vars'),
           ('policy', 'dtensor_cfg', 'activation_checkpointing'), ('policy', 'train_micro_batch_size')}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def differences(a, b, prefix=()):
    if isinstance(a, dict) and isinstance(b, dict):
        return set().union(*(differences(a.get(k), b.get(k), prefix+(k,)) for k in a.keys() | b.keys()))
    return set() if a == b else {prefix}

def invariant_config(base, candidate):
    diff = differences(base, candidate)
    forbidden = {p for p in diff if not any(p[:len(a)] == a for a in ALLOWED)}
    if forbidden:
        raise ValueError('scientific config change: ' + ', '.join('.'.join(p) for p in sorted(forbidden)))
    p = candidate['policy']; c = candidate['cluster']; tp = p['dtensor_cfg']['tensor_parallel_size']
    if c['num_nodes'] != 1 or c['gpus_per_node'] != tp or p['train_global_batch_size'] % p['train_micro_batch_size']:
        raise ValueError('layout must preserve DP1 and whole global batches')
    env = p['dtensor_cfg'].get('env_vars', {})
    if set(env) - {'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'}:
        raise ValueError('production worker environment contains unadmitted overrides')
    return sorted('.'.join(p) for p in diff)

def admitted_layouts(registry=REGISTRY, expv=EXPV):
    """Hash-check every admitted route; pending/blocked candidates never launch."""
    registry, expv = Path(registry), Path(expv)
    doc = json.loads(registry.read_text())
    for key, p in [('protocol_sha256', expv.parent/'PROTOCOL.md'), ('schedule_sha256', expv/'results/sft_schedule.json')]:
        if digest(p) != doc[key]:
            raise ValueError(f'layout admission {key} mismatch')
    original = expv/'configs/e08_sft_14B.yaml'
    base = yaml.safe_load(original.read_text())
    routes=[]
    for entry in doc['routes']:
        if entry['status'] != 'admitted':
            continue
        config = (expv / entry['config']).resolve()
        if not config.is_relative_to(expv.resolve()) or digest(config) != entry['config_sha256']:
            raise ValueError('admitted layout config hash/path mismatch')
        candidate = yaml.safe_load(config.read_text())
        invariant_config(base,candidate)
        if (entry['gpus'] != candidate['cluster']['gpus_per_node'] or
            entry['tensor_parallel_size'] != candidate['policy']['dtensor_cfg']['tensor_parallel_size'] or
            entry['cpu_offload'] != candidate['policy']['dtensor_cfg']['cpu_offload']):
            raise ValueError('admitted resource shape differs from config')
        if entry['admission_kind'] == 'historical_protocol':
            if config != original.resolve() or entry['gpus'] != 8 or entry['cpu_offload']:
                raise ValueError('historical admission cannot authorize a changed layout')
        elif entry['admission_kind'] == 'prospective_layout':
            evidence=entry.get('evidence',{})
            if set(evidence.get('checks',{})) != REQUIRED_CHECKS or any(v != 'PASS' for v in evidence['checks'].values()):
                raise ValueError('prospective layout checks incomplete')
            if not evidence.get('files'):
                raise ValueError('prospective layout evidence missing')
            for item in evidence['files']:
                p=(expv/item['path']).resolve()
                if not p.is_relative_to(expv.resolve()) or digest(p) != item['sha256']:
                    raise ValueError('prospective layout evidence changed')
        else:
            raise ValueError('unknown admission kind')
        routes.append(dict(entry,config_path=str(config)))
    if not routes:
        raise ValueError('no admitted training layout')
    return sorted(routes,key=lambda r:r['gpus'])

def choose_layout(available, layout_id=None, registry=REGISTRY, expv=EXPV):
    return next((r for r in admitted_layouts(registry,expv) if r['gpus']<=available and (layout_id is None or r['id']==layout_id)),None)

def run_layout_id(root):
    receipt = Path(root)/'layout_receipt.json'
    return json.loads(receipt.read_text())['layout']['id'] if receipt.exists() else None

def required_devices(root=None):
    layout_id = run_layout_id(root) if root is not None else None
    routes = [r for r in admitted_layouts() if layout_id is None or r['id'] == layout_id]
    if not routes:
        raise ValueError('running layout no longer admitted')
    return min(r['gpus'] for r in routes)

def record_run(root, layout):
    """Pin the admitted route across segment/resume without adopting a disposable checkpoint."""
    root = Path(root)
    receipt = root/'layout_receipt.json'
    identity = {k: layout[k] for k in ('id', 'gpus', 'tensor_parallel_size', 'cpu_offload', 'config_sha256')}
    if receipt.exists():
        if json.loads(receipt.read_text())['layout'] != identity:
            raise ValueError('cannot resume a production checkpoint under another layout')
        return
    if any((root/'checkpoints').glob('step_*')) and layout['admission_kind'] != 'historical_protocol':
        raise ValueError('new layout must start from pinned Base, not existing checkpoints')
    root.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({'layout': identity, 'registry_sha256': digest(REGISTRY),
                                  'initialization': 'pinned Base; disposable probe checkpoints excluded'}, indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--gpus',type=int,required=True);p.add_argument('--layout-id');p.add_argument('--root',type=Path);a=p.parse_args()
    layout=choose_layout(a.gpus,a.layout_id)
    if layout is None or layout['gpus'] != a.gpus:
        p.error('no admitted layout for the exact visible device count')
    if a.root: record_run(a.root, layout)
    print(layout['config_path'])
if __name__=='__main__': main()
