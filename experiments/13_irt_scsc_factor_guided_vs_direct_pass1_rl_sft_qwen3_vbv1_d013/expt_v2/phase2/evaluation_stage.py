"""Materialize one immutable leased evaluation stage without changing its pre-main numerical or sampling contract."""
from __future__ import annotations

import copy
from pathlib import Path

from technical_driver import bindings
from training_checkpoint import digest,write_new


def materialize(snapshot,learning_config,contract,stage,stage_key,indexes,lease,snapshot_sha):
    root=Path(snapshot['configuration']['root']);directory=root/stage_key
    if stage not in ('evaluation_preflight','evaluation_generate'):raise ValueError('undeclared evaluation stage')
    if (stage=='evaluation_preflight')!= (indexes is None):raise ValueError('health stage cannot contain evaluation indexes')
    runtime=copy.deepcopy(learning_config['runtime']);runtime.update(contract)
    paths={Path(b['path']) for b in snapshot['bindings']}
    for b in snapshot['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('evaluation snapshot changed before materialization')
    prefix=f"{snapshot['purpose']}_b{snapshot['boundary']}"
    if stage=='evaluation_generate':paths.update(root/(prefix+'_preflight')/name for name in ('health/preflight.json','dispatch/result.json'))
    runtime.update(condition='v2-S2',stage=stage,stage_key=stage_key,purpose=snapshot['purpose'],arm=snapshot['arm'],
        run_seed=snapshot['run_seed'],boundary=snapshot['boundary'],model=snapshot['model'],
        model_binding_sha256=snapshot['model_binding_sha256'],snapshot_sha256=snapshot_sha,
        manifest=snapshot['configuration']['manifest'],allowlist=snapshot['configuration']['allowlist'],
        indexes=indexes,stage_root=str(directory/'output'),attempt_root=str(directory/'health'),ray_temp=str(directory/'ray'),
        lease_id=lease['id'],lease_path=str(directory/'lease.json'),bindings=bindings(paths))
    seconds=learning_config['evaluation']['stage_seconds'][stage]
    directory.mkdir(parents=True,exist_ok=False);(directory/'health').mkdir()
    write_new(directory/'lease.json',lease);write_new(directory/'runtime.json',runtime)
    write_new(root/(stage_key+'.json'),{'condition':'v2-S2','L2_sha256':snapshot['L2_sha256'],
        'snapshot_sha256':snapshot_sha,'stage':stage,'stage_key':stage_key,'indexes':indexes,
        'configuration_sha256':digest(directory/'runtime.json'),'lease_id':lease['id'],'maximum_seconds':seconds,
        'automatic_retry':False})
    return {'config':str(directory/'runtime.json'),'reservation':str(root/(stage_key+'.json')),
        'dispatch_root':str(directory/'dispatch'),'maximum_seconds':seconds,'stage':stage,'stage_key':stage_key}
