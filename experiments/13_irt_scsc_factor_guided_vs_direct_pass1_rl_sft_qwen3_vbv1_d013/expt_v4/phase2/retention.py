"""TLDR: Retire only completed pilot tensor payloads after a newer durable checkpoint; keep all hash receipts."""
from pathlib import Path
import json
from common import digest,write_new

TENSORS={'.pt','.bin','.safetensors','.distcp'}


def tensor_payload(path,root):
    """Native/export receipts bind tensor bytes; stage ledgers bind those receipts."""
    path=Path(path);parts=path.relative_to(root).parts
    return path.suffix in TENSORS and (path.name=='batch.pt' or any(p in ('before','after','export') for p in parts))


def retire_completed(work,arm,seed,update):
    work=Path(work).resolve()
    if arm not in ('A','B','P') or seed not in (1301,1302) or not 1<=update<=60:raise ValueError('invalid pilot retention identity')
    stage='PILOT30' if update<=30 else 'PILOT60'
    current=work/stage/f'{arm}_{seed}/update_{update:05d}'
    summary=json.loads((current/'summary.json').read_text())
    if summary.get('completed') is not True:raise ValueError('new update is not durable')
    # Verify the replacement native/export receipts exist before discarding old tensors.
    for p in (Path(summary['checkpoint'])/'receipt.json',Path(summary['model'])/'export_receipt.json'):
        if work not in p.resolve().parents or not p.is_file():raise ValueError('replacement checkpoint unavailable')
    targets=[current]
    if update>1:
        prior_stage='PILOT30' if update-1<=30 else 'PILOT60'
        targets.append(work/prior_stage/f'{arm}_{seed}/update_{update-1:05d}')
    for root in targets:
        if root.is_symlink() or work not in root.resolve().parents:raise ValueError('retirement escaped owned run')
        for p in sorted(root.rglob('*')):
            if not p.is_file() or not tensor_payload(p,root):continue
            # Current after/export is the sole continuation; T2/T3 are never targets.
            relative=p.relative_to(root)
            if root==current and 'before' not in relative.parts and p.name!='batch.pt':continue
            if p.is_symlink():raise ValueError('refuse linked payload')
            receipt=p.with_name(p.name+'.retired.json')
            if not receipt.exists():write_new(receipt,{'sha256':digest(p),'bytes':p.stat().st_size,
                'replacement_summary_sha256':digest(current/'summary.json'),'reason':'completed pilot checkpoint superseded'})
            p.unlink()
