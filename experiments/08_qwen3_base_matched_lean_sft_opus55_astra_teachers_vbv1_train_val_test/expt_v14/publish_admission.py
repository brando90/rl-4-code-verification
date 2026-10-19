"""Publish a hash-checked stable pointer to completed V14 admission without changing frozen training artifacts."""
import hashlib
import json
from pathlib import Path
import time

ROOT=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training/public_gap_sources_v14')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path,value):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');tmp.replace(path)


def main():
    version=ROOT/'admission_v2';summary=json.loads((version/'completion.json').read_text())
    assert summary['state']=='DONE' and summary['accounted']==summary['declared']==688
    training=version/'training.jsonl';assert sha(training)==summary['training_sha256']
    rows=[json.loads(line) for line in training.read_text().splitlines()]
    assert len(rows)==summary['admitted'] and all(row['training_admitted'] for row in rows)
    assert len({row['task_id'] for row in rows})==len(rows)
    for name in ('protected_full_exact','protected_full_near','protected_statement_exact','protected_statement_near'):assert summary[name]==0
    assert summary['protected_references']==764 and summary['model_calls']==0
    pointer=dict(state='READY',version='admission_v2',path=str(training),training_jsonl=str(training),training_path=str(training),
        training_sha256=summary['training_sha256'],rows=len(rows),declared=688,admitted_by_source=summary['admitted_by_source'],
        completion_json=str(version/'completion.json'),completion_sha256=sha(version/'completion.json'),
        row_results_csv=str(version/'row_results.csv'),row_results_sha256=sha(version/'row_results.csv'),
        freeze_json=str(version/'freeze.json'),freeze_sha256=sha(version/'freeze.json'),
        assistant_loss_tokens=summary['assistant_loss_tokens'],published_unix=time.time(),supersedes='admission_v1',
        intended_use='Supplement a separately frozen future training regime; current V12 remains unchanged',
        scope='Formal proof exercises with deterministic visible-step comments; no English semantic alignment claim',
        includes_provisional_deepseek=True,model_calls=0)
    write(ROOT/'latest_admission.json',pointer)
    previous=ROOT/'admission_v1';old=json.loads((previous/'completion.json').read_text())
    assert sha(previous/'training.jsonl')==old['training_sha256']
    write(previous/'superseded.json',dict(state='SUPERSEDED',replacement=str(ROOT/'latest_admission.json'),
        replacement_version='admission_v2',original_training_sha256=old['training_sha256'],
        reason='Four comment headers now correctly describe direct let-bindings; descriptive extraction exclusions',
        original_training_file_modified=False,observed_unix=time.time()))
    print(json.dumps(pointer,sort_keys=True))


if __name__=='__main__':main()
