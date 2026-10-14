"""Prepare only frozen train/validation source features, without outcomes or test content."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

from panel import digest,write_new

V2=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(V2/'prediction'));sys.path.insert(0,str(V2))
from features_v2 import extract
from historical_oracle_v2 import load


def prepare(split_path,veribench,scorer_root,root):
    rows=list(csv.DictReader(Path(split_path).open()))
    # Explicit filtering occurs before constructing any source path.
    admitted=[r for r in rows if r['split'] in ('train','validation')]
    counts={s:sum(r['split']==s for r in admitted) for s in ('train','validation')}
    if counts!={'train':539,'validation':135}:raise ValueError('source feature split denominator changed')
    if len({r['task_id'] for r in admitted})!=674:raise ValueError('duplicate feature task')
    scorer_root=Path(scorer_root);sys.path.insert(0,str(scorer_root/'scripts/scsc'))
    scorer=load('e13v2_feature_scorer',scorer_root/'scripts/scsc/run_real_eval.py')
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    write_new(root/'attempt.json',{'status':'SOURCE_FEATURES_ONLY','split_manifest_sha256':digest(split_path),'test_sources_opened':0})
    output={s:{} for s in counts};bindings=[]
    for row in admitted:
        base=Path(veribench)/'veribench_dataset'
        py=base/'py_src'/row['py_relpath'];gold=base/'lean_src/veribench'/row['gold_relpath']
        for path,key in ((py,'py_sha256'),(gold,'gold_sha256')):
            if digest(path)!=row[key]:raise ValueError('frozen feature source changed')
            bindings.append({'path':str(path),'sha256':row[key]})
        features=extract(py.read_text(),row['family'],scorer.extract_theorem_text(gold.read_text()))
        output[row['split']][row['task_id']]={'group_id':row['group_id'],'features':features}
    for split,features in output.items():write_new(root/(split+'.json'),features)
    write_new(root/'source_bindings.json',bindings)
    result={'status':'PREPARED_NO_FITS','counts':counts,'test_sources_opened':0,'source_files_bound':len(bindings),
            'domain_definition':'frozen split manifest family; one-hot vocabulary learned within each training fold',
            'artifacts':{s:{'sha256':digest(root/(s+'.json')),'tasks':len(output[s])} for s in output},
            'source_bindings_sha256':digest(root/'source_bindings.json'),
            'split_manifest_sha256':digest(split_path),'scorer_entry_sha256':digest(scorer_root/'scripts/scsc/run_real_eval.py')}
    write_new(root/'preparation.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('split-path','veribench','scorer-root','root'):p.add_argument('--'+name,type=Path,required=True)
    print(json.dumps(prepare(**vars(p.parse_args())),indent=2))
