"""Collect existing E20 artifacts after a gate stop; no scoring, model calls or fitting.

Run on Sherlock after all adopted jobs are terminal. The full 539 x 8 calibration
cell universe is retained, with missing generations and unmeasured scores explicit.
Bulky source/diagnostic artifacts stay in their original paths behind a hash manifest.
"""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write_csv(path, rows, fields):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def collect(root, out):
    out.mkdir(parents=True, exist_ok=False)
    cells, artifacts, ids_all, chunk_summary = [], [], [], []
    for chunk in range(4):
        ids_path = root / ('phase0/ids/chunk_%d.txt' % chunk)
        ids = ids_path.read_text().splitlines()
        ids = [x.strip() for x in ids if x.strip()]
        ids_all.extend(ids)
        raw = root / ('phase0/gen/chunk_%d/raw.jsonl' % chunk)
        observed = {}
        if raw.exists():
            with raw.open('rb') as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    key = (r['task_id'], int(r['sample_idx']))
                    if key in observed or key[0] not in ids or key[1] not in range(8):
                        raise ValueError('duplicate or undeclared cell: %r' % (key,))
                    observed[key] = (r, hashlib.sha256(line).hexdigest())
        for task in ids:
            for k in range(8):
                found = observed.get((task, k))
                r, line_hash = found if found else ({}, '')
                lean = r.get('lean') or ''
                cells.append(dict(chunk=chunk, task_id=task, sample_idx=k,
                    generation_status='generated' if found else 'missing_generation',
                    score_status='not_run_failed_trainer_gate', strict='', factored_reward='',
                    IC_tests='', IC_proofs='', FSC='', compiles='', theorem_count='',
                    generated_tokens=r.get('generated_tokens', ''), prompt_tokens=r.get('prompt_tokens', ''),
                    capped=r.get('truncated', ''), finish_reason=r.get('finish_reason', ''),
                    extraction=r.get('extraction', ''), lean_sha256=hashlib.sha256(lean.encode()).hexdigest() if lean else '',
                    lean_bytes=len(lean.encode()) if found else '', prompt_sha256=r.get('prompt_sha256', ''),
                    seed=(r.get('sampling') or {}).get('seed', ''), raw_line_sha256=line_hash))
        chunk_summary.append(dict(chunk=chunk, declared=len(ids)*8, generated=len(observed)))
    if len(ids_all) != 539 or len(set(ids_all)) != 539 or len(cells) != 4312:
        raise ValueError('declared calibration task universe differs from frozen 539 x 8')
    cells.sort(key=lambda r: (r['task_id'], r['sample_idx']))
    write_csv(out/'phase0_cells_unscored.csv', cells, list(cells[0]))
    smoke = root/'train/runs/A_s0'
    smoke_cells=[]
    for receipt in sorted((smoke/'jobs').glob('*/*/receipt.json')):
        r=json.loads(receipt.read_text()); r['job']=receipt.parent.parent.name
        r['remote_receipt']=str(receipt); smoke_cells.append(r)
    if smoke_cells:
        keys=list(smoke_cells[0]); assert all(list(r)==keys for r in smoke_cells)
        write_csv(out/'smoke_generation_receipts.csv',smoke_cells,keys)
    copy_root=out/'smoke_final';copy_root.mkdir()
    for name in ('log.jsonl','rollouts.jsonl','smoke_logprob_check.json','RUN_DONE'):
        p=smoke/name
        if p.exists(): shutil.copy2(p,copy_root/name)
    for p in smoke.glob('run_manifest_*.json'): shutil.copy2(p,copy_root/p.name)
    # No trained model/optimizer tensors are copied or hashed by this collector.
    roots=[root/'phase0/gen',root/'phase0/ids',smoke/'jobs',smoke/'scores']
    for directory in roots:
        for p in sorted(directory.rglob('*')):
            if p.is_file():
                artifacts.append(dict(remote_path=str(p),bytes=p.stat().st_size,sha256=digest(p)))
    write_csv(out/'remote_artifact_manifest.csv',artifacts,['remote_path','bytes','sha256'])
    generated=[r for r in cells if r['generation_status']=='generated']
    summary=dict(declared_tasks=539,declared_cells=4312,generated_cells=len(generated),
        missing_generations=4312-len(generated),scored_cells=0,strict=None,factored_reward=None,
        generated_tokens=sum(int(r['generated_tokens']) for r in generated),
        capped=sum(bool(r['capped']) for r in generated),chunks=chunk_summary,
        smoke_generated_cells=len(smoke_cells),remote_root=str(root),
        raw_storage_reason='Bulky raw completions, Lean sources and compiler diagnostics retained on Sherlock; exact paths/hashes in remote_artifact_manifest.csv.',
        collection_scope='Existing-artifact reconciliation only; no new scoring, fitting, training or evaluation.')
    (out/'closure_collection.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();collect(args.root,args.out)
