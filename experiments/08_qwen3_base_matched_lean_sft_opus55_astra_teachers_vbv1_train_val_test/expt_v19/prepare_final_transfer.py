"""Bind the complete V18 accepted cohort and exact proof receipts into a portable final-data transfer."""
import argparse
import hashlib
import json
from pathlib import Path
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
REPO=RUN/'repo'
EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test')

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--v18-root',type=Path,default=RUN/'lean_corpus_v18');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    source=args.v18_root;final=source/'final';completion=json.loads((source/'completion.json').read_text())
    assert completion['state'] in ('DONE','DONE_WITH_EXCLUSIONS') and completion['declared']==completion['accounted']==2585
    assert completion['no_automated_fallbacks'] is True and completion['protected_references']==764 and completion['protected_exact']==completion['protected_near']==0
    entries={}
    def add(path,destination,expected=None):
        path=Path(path);assert path.is_file() and not path.is_symlink(),path
        h=digest(path);assert expected is None or h==expected,path
        assert not Path(destination).is_absolute() and '..' not in Path(destination).parts
        row=dict(source=str(path),destination=destination,bytes=path.stat().st_size,sha256=h)
        assert destination not in entries or entries[destination]==row;entries[destination]=row
    add(source/'completion.json','sources/v18/completion.json')
    for name,key in [('fully_cleaned_existing_training.jsonl','training_sha256'),('replacements.jsonl','replacements_sha256'),('row_results.csv','row_results_sha256'),('proof_receipts_manifest.json','proof_receipts_manifest_sha256')]:
        add(final/name,'sources/v18/final/'+name,completion[key])
    screens=[p for folder in (source,final) for p in folder.glob('*.json') if p.is_file() and digest(p)==completion['protected_screen_sha256']]
    assert screens,'Bound V18 protected screen file absent';add(screens[0],'sources/v18/final/protected_screen.json',completion['protected_screen_sha256'])
    accepted=[json.loads(line) for line in (final/'fully_cleaned_existing_training.jsonl').read_text().splitlines() if line.strip()]
    assert len(accepted)==completion['accepted'] and len(accepted)+completion['excluded']==2585
    for row in accepted:
        i=int(row['example_index']);meta=row['automation_cleanup_v18'];path=final/'proof_receipts'/f'existing_{i:04d}.json'
        add(path,f'sources/v18/final/proof_receipts/existing_{i:04d}.json',meta['receipt_sha256'])
    add(REPO/EXP/'expt_v1/scripts/template_check.py',str(Path('repo')/EXP/'expt_v1/scripts/template_check.py'))
    result=dict(identity='final',state='READY',created_unix=time.time(),v18_completion_sha256=digest(source/'completion.json'),declared_originals=2585,accepted_originals=completion['accepted'],excluded_originals=completion['excluded'],declared_files=len(entries),total_bytes=sum(e['bytes'] for e in entries.values()),entries=sorted(entries.values(),key=lambda e:e['destination']))
    args.output.parent.mkdir(parents=True,exist_ok=True);temporary=args.output.with_suffix('.tmp');temporary.write_text(json.dumps(result,indent=2)+'\n');temporary.replace(args.output);print(json.dumps({k:v for k,v in result.items() if k!='entries'}),flush=True)

if __name__=='__main__':main()
