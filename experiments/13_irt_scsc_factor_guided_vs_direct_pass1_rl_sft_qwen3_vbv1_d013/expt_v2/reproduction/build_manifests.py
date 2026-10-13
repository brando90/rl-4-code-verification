#!/usr/bin/env python3
"""Bind the historical union in a separate metadata-only process, exposing only counts and hashes."""
import csv
import hashlib
import json
from pathlib import Path
import os
import traceback
import struct

REPO=Path(__file__).resolve().parents[4]
V2=Path(__file__).resolve().parent.parent
BASE=Path('/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_phase0/sealed_base_audit_v1/sealed_manifest.jsonl')
LADDER=Path('/lfs/skampere1/0/brando9/agent-recovery-10-09-2026/workers/rl4cv13_review/phase0_controls/validation_source_manifest.jsonl')
SPLIT=REPO/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_split_manifest.csv'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    root=Path(os.environ['WR'])/'R2';root.mkdir(exist_ok=False)
    try:
        if sha(BASE)!='06fcbcda0d7406156f99754d69814a699fe4dbf29fee40e377fa190ccd03f1b6':raise ValueError('base binding')
        if sha(LADDER)!='c88b9e7ba58b9c0b0334b1e55af12c1ae54985ac20721bc710967abdd6a7bafa':raise ValueError('ladder binding')
        split={r['task_id']:r for r in csv.DictReader(SPLIT.open())}
        cells={}
        for line in BASE.open():
            row=json.loads(line);task=split[row['task_id']]
            if row['split']!=task['split'] or row['group_id']!=task['group_id']:raise ValueError('split binding')
            cell={**row,'family':'base','known':True,'expectations':[{'family':'base','value':row['old_kernel_binary'],'status':'scored','policy':row['model']}],'source_alias_paths':[]}
            if row['cell_id'] in cells:raise ValueError('duplicate base')
            cells[row['cell_id']]=cell
        if len(cells)!=21504:raise ValueError('base denominator')
        overlap=0;ladder_count=0
        for line in LADDER.open():
            row=json.loads(line);ladder_count+=1;task=split[row['task_id']]
            if row['split']!='validation' or task['split']!='validation' or row['group_id']!=task['group_id']:raise ValueError('ladder split binding')
            expected={'family':'ladder','value':row['kernel_binary'],'status':'scored' if row['kernel_binary'] is not None else 'unmeasured','policy':row['policy']}
            if row['policy'].endswith('_e05'):
                model='qwen3-'+row['policy'].split('_')[1].replace('p','.').replace('B','b')+'-base'
                cell=cells[f"{model}/{row['task_id']}/{row['sample_idx']}"]
                if cell['source_sha256']!=row['response_sha256']:raise ValueError('overlap source differs')
                cell['expectations'].append(expected);cell['source_alias_paths'].append(row['source_path']);overlap+=1
            else:
                cell={**row,'source_sha256':row['response_sha256'],'family':'ladder','known':row['kernel_binary'] is not None,
                      'truncated':False,'expectations':[expected],'source_alias_paths':[]}
                # Preserve cap metadata from the historical ladder table without executing any source.
                csv_path=REPO/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/ladder'/f"{row['policy']}_validation_cells.csv"
                # Cache metadata once per policy.
                if row['policy'] not in cap_cache:
                    cap_cache[row['policy']]={(r['task_id'],int(r['sample_idx'])):r['capped']=='True' for r in csv.DictReader(csv_path.open())}
                cell['truncated']=cap_cache[row['policy']][(row['task_id'],row['sample_idx'])]
                if row['cell_id'] in cells:raise ValueError('duplicate ladder')
                cells[row['cell_id']]=cell
        if ladder_count!=20520 or overlap!=3240 or len(cells)!=38784:raise ValueError('union denominator')
        for cell in cells.values():
            for source in [cell['source_path'],*cell['source_alias_paths']]:
                if sha(source)!=cell['source_sha256']:raise ValueError('source integrity')
        for route in ('ordinary','opaque'):
            path=root/(route+'_manifest.jsonl')
            with path.open('x') as f:
                for key,cell in sorted(cells.items()):
                    if (cell['split']=='test')==(route=='opaque'):f.write(json.dumps(cell,sort_keys=True)+'\n')
        write_indexes(root)
        folds=[{'task_id':t,'group_id':r['group_id'],'split':r['split'],
                'outer_fold':None if r['split']=='test' else int(hashlib.sha256(r['group_id'].encode()).hexdigest(),16)%5}
               for t,r in sorted(split.items())]
        (root/'folds.json').write_text(json.dumps(folds,indent=2)+'\n')
        counts={s:sum(c['split']==s for c in cells.values()) for s in ('train','validation','test')}
        if counts!={'train':12936,'validation':20520,'test':5328}:raise ValueError('split denominator')
        receipt={'unique_cells':len(cells),'source_readbacks':21504+20520,'overlap_reused':overlap,
                 'counts':counts,'unavailable_parent_ladder_cells':5400,'factors_computed':0,
                 'inputs_sha256':{str(BASE):sha(BASE),str(LADDER):sha(LADDER),str(SPLIT):sha(SPLIT)},
                 'manifest_sha256':{n:sha(root/n) for n in ['ordinary_manifest.jsonl','opaque_manifest.jsonl','ordinary_manifest.index','opaque_manifest.index','folds.json']},
                 'sealed_test_outcomes_disclosed':False}
        (root/'manifest_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt))
        return 0
    except Exception as exc:
        (root/'private_manifest_error.txt').write_text(traceback.format_exc())
        print(json.dumps({'status':'INTEGRITY_DEFECT','error_type':type(exc).__name__,'test_details_disclosed':False}))
        return 1


def write_indexes(root):
    for route in ('ordinary','opaque'):
        with (root/(route+'_manifest.jsonl')).open('rb') as source, (root/(route+'_manifest.index')).open('xb') as index:
            while True:
                offset=source.tell()
                if not source.readline():break
                index.write(struct.pack('<Q',offset))


cap_cache={}
if __name__=='__main__':raise SystemExit(main())
