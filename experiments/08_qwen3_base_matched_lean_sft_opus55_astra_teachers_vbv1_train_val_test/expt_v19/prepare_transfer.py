"""Freeze exact SNAP training, initialization and source files for a single encrypted GX10 relay."""
import argparse
import hashlib
import json
from pathlib import Path
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
EXP=RUN/'repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    data=RUN/'corpus_training_v12/cleaned/data';receipt=json.loads((data/'prepare_receipt.json').read_text())
    assert receipt['status']=='PASS' and receipt['rows']==10940 and receipt['replacements']==818
    assert receipt['loss_tokens']==13420616 and receipt['steps']==5470
    expected={k:receipt[k+'_sha256'] for k in ('tokens','schedule','training')}
    weights=RUN/'onep7/runs/mixed/weights_manifest.json';initial=json.loads(weights.read_text())
    assert digest(data/'initial_manifest.json')==receipt['initial_manifest_sha256']
    assert json.loads((data/'initial_manifest.json').read_text())==initial
    entries=[]
    def add(source,destination,wanted=None):
        assert source.is_file() and not source.is_symlink(),str(source)
        h=digest(source);assert wanted is None or h==wanted,(str(source),h,wanted)
        entries.append(dict(source=str(source),destination=destination,bytes=source.stat().st_size,sha256=h))
    for name in ('tokens.pt','schedule.json','prepare_receipt.json','initial_manifest.json','training.jsonl','token_manifest.json','protected_screen.json','row_results.csv'):
        add(data/name,'conditions/partial818/data/'+name,expected.get(name.split('.')[0]))
    for name,h in receipt['source_sha256'].items():
        assert Path(name).name==name;add(EXP/'expt_v12'/name,'code/expt_v12_frozen/'+name,h)
    add(weights,'source_weights_manifest.json')
    for name,h in initial.items():
        assert Path(name).name==name;add(RUN/'onep7/runs/mixed/hf'/name,'initial_hf/'+name,h)
    add(RUN/'onep7/runs/mixed/hf/SHA256SUMS','initial_hf/SHA256SUMS')
    value=dict(identity='initial',declared_files=len(entries),total_bytes=sum(r['bytes'] for r in entries),
        entries=entries,source_receipt_sha256=digest(data/'prepare_receipt.json'),initial_manifest_sha256=digest(weights),
        source_training_sha256=receipt['training_sha256'],rows=10940,replacements=818,loss_tokens=13420616,
        intended_use='Disposable longest-sequence smoke only; no partial818 production',observed_unix=time.time())
    args.output.parent.mkdir(parents=True,exist_ok=True);assert not args.output.exists(),'Preserve the existing frozen transfer manifest'
    args.output.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in value.items() if k!='entries'},sort_keys=True))


if __name__=='__main__':main()
