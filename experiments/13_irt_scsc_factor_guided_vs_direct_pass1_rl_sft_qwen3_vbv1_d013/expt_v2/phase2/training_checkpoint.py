"""Persist actual NeMo state and verify a lossless, local export before any generator refit."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):value.update(block)
    return value.hexdigest()


def write_new(path,value):
    path=Path(path)
    with path.open('x') as out:
        json.dump(value,out,sort_keys=True,allow_nan=False);out.write('\n');out.flush();os.fsync(out.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def file_bindings(root):
    root=Path(root)
    files=sorted(p for p in root.rglob('*') if p.is_file())
    if any(p.is_symlink() for p in root.rglob('*')):raise ValueError('checkpoint contains a symlink')
    return [{'relative_path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]



def sync_tree(root):
    """Make native tensor files durable before publishing their successful receipt."""
    root=Path(root)
    for path in root.rglob('*'):
        if path.is_symlink():raise ValueError('checkpoint contains a symlink')
        if path.is_file():
            with path.open('rb') as stream:os.fsync(stream.fileno())
    for path in [*sorted((p for p in root.rglob('*') if p.is_dir()),reverse=True),root]:
        fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)


def verify_files(root,bindings):
    root=Path(root)
    names=[b['relative_path'] for b in bindings]
    if not bindings or len(names)!=len(set(names)):raise ValueError('empty or duplicate checkpoint bindings')
    for binding in bindings:
        relative=Path(binding['relative_path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('checkpoint binding escapes its root')
        path=root/relative
        if path.is_symlink() or path.stat().st_size!=binding['bytes'] or digest(path)!=binding['sha256']:
            raise ValueError('checkpoint file changed: '+str(relative))
    return True


def owned_call(policy,function,*args):
    """Use only this Policy's worker handles, never Ray discovery or an existing cluster."""
    import ray
    workers=policy.worker_group.workers
    if not workers:raise ValueError('owned policy has no workers')
    return ray.get([worker.__ray_call__.remote(function,*args) for worker in workers])



def capture_empty_optimizer(worker,path):
    """Retain the exact empty state before PyTorch's native saver materializes Adam moments."""
    import torch
    if worker.optimizer.state:return {'captured':False}
    path=Path(path)
    with path.open('xb') as out:
        torch.save({'optimizer':worker.optimizer.state_dict(),'scheduler':worker.scheduler.state_dict()},out)
        out.flush();os.fsync(out.fileno())
    return {'captured':True,'sha256':digest(path)}


def restore_empty_optimizer(worker,path):
    """Undo only the saver's zero-learning-rate dummy step, not an experiment update."""
    import torch
    path=Path(path)
    if not path.exists():return {'restored':False}
    state=torch.load(path,map_location='cpu',weights_only=True)
    if state['optimizer']['state']:raise ValueError('initial optimizer override is not empty')
    worker.optimizer.load_state_dict(state['optimizer']);worker.scheduler.load_state_dict(state['scheduler'])
    return {'restored':True}


def save(policy,root,*,provenance):
    """Save native weights/optimizer/scheduler and each worker's random state exactly once."""
    from worker_state import parameter_digest,optimizer_digest,save_rng
    import ray
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'attempt.json',{'condition':'v2-S2','operation':'save','provenance':provenance})
    initial=ray.get([worker.__ray_call__.remote(capture_empty_optimizer,str(root/f'empty_optimizer_{rank:04d}.pt'))
                     for rank,worker in enumerate(policy.worker_group.workers)])
    try:
        policy.save_checkpoint(str(root/'weights'),str(root/'optimizer'),str(root/'tokenizer'))
    finally:
        ray.get([worker.__ray_call__.remote(restore_empty_optimizer,str(root/f'empty_optimizer_{rank:04d}.pt'))
                 for rank,worker in enumerate(policy.worker_group.workers)])
    # Native bytes retain the installed format. An explicitly bound empty-state
    # supplement cancels the saver's dummy step on both save and restore.
    parameters=owned_call(policy,parameter_digest);optimizers=owned_call(policy,optimizer_digest)
    random_states=ray.get([worker.__ray_call__.remote(save_rng,str(root/f'rng_{rank:04d}.pt'))
                          for rank,worker in enumerate(policy.worker_group.workers)])
    sync_tree(root)
    result={'condition':'v2-S2','status':'COMPLETE','provenance':provenance,
            'parameters':parameters,'optimizers':optimizers,'random_states':random_states,'empty_optimizer_supplements':initial,
            'worker_count':len(parameters),'bindings':file_bindings(root)}
    write_new(root/'receipt.json',result)
    return result


def restore_worker(worker,root,rank,expected):
    """Restore the installed native state first, verify it, then restore random state last."""
    from nemo_rl.utils.native_checkpoint import load_checkpoint
    from worker_state import parameter_digest,optimizer_digest,restore_rng
    root=Path(root)
    load_checkpoint(worker.model,str(root/'weights'),worker.optimizer,worker.scheduler,str(root/'optimizer'))
    supplement=root/f'empty_optimizer_{rank:04d}.pt'
    recorded=expected['empty_optimizer_supplements'][rank]
    if recorded['captured']:
        if digest(supplement)!=recorded['sha256']:raise ValueError('initial optimizer supplement changed')
        restore_empty_optimizer(worker,supplement)
    elif supplement.exists():raise ValueError('unrecorded initial optimizer override')
    if parameter_digest(worker)!=expected['parameters'][rank]:raise ValueError('restored weights differ')
    if optimizer_digest(worker)!=expected['optimizers'][rank]:raise ValueError('restored optimizer/scheduler differ')
    rng=root/f'rng_{rank:04d}.pt'
    if digest(rng)!=expected['random_states'][rank]['sha256']:raise ValueError('random-state checkpoint changed')
    return restore_rng(worker,str(rng))


def restore(policy,root):
    import ray
    root=Path(root);expected=json.loads((root/'receipt.json').read_text())
    if expected.get('status')!='COMPLETE' or expected.get('condition')!='v2-S2':raise ValueError('incomplete checkpoint')
    verify_files(root,expected['bindings'])
    if len(policy.worker_group.workers)!=expected['worker_count']:raise ValueError('checkpoint worker topology changed')
    return ray.get([worker.__ray_call__.remote(restore_worker,str(root),rank,expected)
                   for rank,worker in enumerate(policy.worker_group.workers)])


def export(root,target,*,model_config,tokenizer):
    """Convert with installed NeMo, then compare every exported tensor with the saved worker digest."""
    import torch
    from types import SimpleNamespace
    from nemo_rl.utils.native_checkpoint import convert_dcp_to_hf
    from worker_state import parameter_digest
    root=Path(root);target=Path(target);receipt=json.loads((root/'receipt.json').read_text())
    if receipt.get('status')!='COMPLETE' or receipt.get('condition')!='v2-S2':raise ValueError('incomplete checkpoint')
    verify_files(root,receipt['bindings'])
    if len({entry['sha256'] for entry in receipt['parameters']})!=1:
        raise ValueError('full parameter digests disagree across workers')
    if not Path(model_config).is_dir() or not Path(tokenizer).is_dir():raise ValueError('export requires local frozen configuration and tokenizer')
    convert_dcp_to_hf(str(root/'weights'),str(target),str(model_config),str(tokenizer),overwrite=False,hf_overrides={})
    state=torch.load(target/'pytorch_model.bin',map_location='cpu',weights_only=True)
    actual=parameter_digest(SimpleNamespace(model=SimpleNamespace(state_dict=lambda:state)))
    if actual!=receipt['parameters'][0]:raise ValueError('exported tensor contents differ from saved policy')
    sync_tree(target)
    result={'condition':'v2-S2','status':'COMPLETE','native_receipt_sha256':digest(root/'receipt.json'),
            'parameters':actual,'bindings':file_bindings(target),
            'common_tokenizer':str(tokenizer),'generation_tokenizer_rule':'use the original frozen tokenizer explicitly'}
    write_new(target/'export_receipt.json',result)
    return result
