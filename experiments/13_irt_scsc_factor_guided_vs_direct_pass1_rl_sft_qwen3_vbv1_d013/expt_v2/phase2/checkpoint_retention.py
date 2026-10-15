"""Retire obsolete owned learning tensors only after a newer durable opportunity and immutable retention receipt."""
from __future__ import annotations

import json
import fcntl
import os
from pathlib import Path
import re
import shutil
import time

from training_checkpoint import digest,write_new,file_bindings,verify_files
from learning_steps import verify_export


def candidates(run_root,state):
    """Keep latest before/after, every token-boundary export and every incomplete opportunity."""
    root=Path(run_root).resolve()
    if Path(run_root).is_symlink() or not (root/'admission.json').is_file():raise ValueError('owned admitted learning root required')
    admission=json.loads((root/'admission.json').read_text())
    if (admission['execution_lock_sha256']!=state['execution_sha256']
            or any(admission[k]!=state[k] for k in ('phase','arm','run_seed'))):raise ValueError('retention run identity changed')
    live={Path(state['model']).resolve()}
    if state.get('checkpoint'):live.add(Path(state['checkpoint']).resolve())
    newest=state['completed_updates']
    if type(newest) is not int or newest<1:raise ValueError('no durable learning opportunity to retain')
    # A later all-missing update can reference an earlier export at its boundary.
    # Gather every retained boundary before considering any earlier deletion.
    for boundary in root.glob('update_*/boundary.json'):
        if boundary.is_symlink():raise ValueError('boundary receipt cannot be a symlink')
        live.add(Path(json.loads(boundary.read_text())['model']).resolve())
    keep=[];retire=[]
    for directory in sorted(root.glob('update_*')):
        if not re.fullmatch(r'update_[0-9]{5}',directory.name) or directory.is_symlink():raise ValueError('unexpected learning directory')
        update=int(directory.name.split('_')[1]);opportunity=directory/'opportunity.json'
        if not opportunity.is_file():continue
        result=json.loads(opportunity.read_text())
        if (result['condition']!='v2-S2' or result['update']!=update or result['status']!='ACCOUNTED'
                or result['state_after']['execution_sha256']!=state['execution_sha256']):raise ValueError('unbound completed learning opportunity')
        # Every completed opportunity must retain verified scorer and child
        # cleanup; unresolved consumers keep all tensors and halt retirement.
        for stage in ('generate','update','export'):
            stage_root=directory/stage
            if stage=='export' and not stage_root.exists():continue
            dispatch=json.loads((stage_root/'dispatch/result.json').read_text())
            if dispatch.get('cleanup_verified') is not True or dispatch.get('status')!='RUNTIME_EXITED_ZERO':
                raise ValueError('learning child cleanup unresolved')
        scored=json.loads((directory/'score/cells/result.json').read_text())
        if not scored.get('rows') or any(row.get('cleanup_verified') is not True for row in scored['rows']):
            raise ValueError('learning scorer cleanup unresolved')
        if update>=newest:continue
        boundary=directory/'boundary.json'
        if boundary.exists():live.add(Path(json.loads(boundary.read_text())['model']).resolve())
        for relative,kind in [('update/output/before','native'),('update/output/after','native'),('export/output','export')]:
            path=directory/relative
            if not path.exists():continue
            if path.resolve() in live:keep.append(str(path));continue
            if path.is_symlink() or root not in path.resolve().parents or any(p.is_symlink() for p in path.rglob('*')):
                raise ValueError('retirement target escapes owned tensor storage')
            receipt_path=path/('receipt.json' if kind=='native' else 'export_receipt.json')
            receipt=json.loads(receipt_path.read_text())
            if receipt.get('condition')!='v2-S2' or receipt.get('status')!='COMPLETE':raise ValueError('incomplete tensor state must remain for diagnosis')
            if kind=='export':verify_export(path,digest(receipt_path))
            else:verify_files(path,receipt['bindings'])
            inventory=file_bindings(path)
            retire.append({'path':str(path),'kind':kind,'update':update,'receipt':receipt,
                           'receipt_sha256':digest(receipt_path),'inventory':inventory,
                           'logical_bytes':sum(b['bytes'] for b in inventory),'opportunity_sha256':digest(opportunity)})
    return {'condition':'v2-S2','run_root':str(root),'execution_sha256':state['execution_sha256'],
            'latest_completed_update':newest,'kept_tensor_roots':sorted(map(str,live)),'candidates':retire,
            'rule':'retain latest before/after, current model, all boundary exports and all incomplete evidence; never remove raw rollouts/scores/batches'}


def retire(run_root,state,receipt_path,*,controller_fence):
    """Caller holds the sole learning controller fence after verified child cleanup; no model stage runs here."""
    root=Path(run_root).resolve();receipt_path=Path(receipt_path)
    if receipt_path.resolve().parent!=root/'retention':raise ValueError('retention receipt must remain within its run ledger')
    if os.fstat(controller_fence.fileno()).st_ino!=(root/'controller.lock').stat().st_ino:
        raise ValueError('wrong learning controller fence')
    fcntl.flock(controller_fence,fcntl.LOCK_EX|fcntl.LOCK_NB)
    receipt_path.parent.mkdir(exist_ok=True)
    plan=candidates(root,state)
    write_new(receipt_path,{**plan,'status':'PREPARED','created_unix':time.time()})
    removed=[]
    for item in plan['candidates']:
        path=Path(item['path'])
        # Reverify immediately before removal. Prior immutable metadata retains
        # all native/export identities even after their obsolete tensor bytes go.
        if file_bindings(path)!=item['inventory']:raise ValueError('tensor bytes changed after retirement preparation')
        shutil.rmtree(path);removed.append(item['path'])
    result={'condition':'v2-S2','status':'COMPLETE','plan_sha256':digest(receipt_path),'removed':removed,
            'logical_bytes_removed':sum(item['logical_bytes'] for item in plan['candidates']),
            'finished_unix':time.time()}
    write_new(receipt_path.with_name(receipt_path.stem+'_result.json'),result)
    return result
