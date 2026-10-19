"""Substitute verified proof-cleaned answers into the frozen current pool while preserving every row and batch identity."""
from __future__ import annotations
import collections
import csv
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
from assemble import ROOT,RUN,HERE,REPO,START,SEED,INSPECTOR_SHA,digest,read,sha,write

def main():
    os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    from transformers import AutoTokenizer
    sys.path[:0]=[str(REPO/'src'),str(HERE.parent/'expt_v1/scripts')]
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen
    spec=importlib.util.spec_from_file_location('cleaned_frozen_kernel_v12',REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py')
    kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel);assert digest(spec.origin)==INSPECTOR_SHA
    current=ROOT/'current/data';source_receipt=json.loads((current/'prepare_receipt.json').read_text())
    assert source_receipt['status']=='PASS' and digest(current/'training.jsonl')==source_receipt['training_sha256']
    for name,h in source_receipt['source_sha256'].items():assert digest(HERE/name)==h,name
    cleanup=RUN/'lean_corpus_v13';completion=json.loads((cleanup/'completion.json').read_text())
    assert completion['state'] in ('DONE','DONE_PARTIAL')
    assert completion['declared']==completion['accounted']==2585,'cleanup must account for the whole original pool'
    replacement_file=cleanup/'final/replacements.jsonl';replacements=read(replacement_file)
    expected=completion.get('replacements_sha256') or completion.get('replacement_sha256')
    assert expected and digest(replacement_file)==expected,'cleanup completion must bind exact replacement file'
    byindex={int(r['example_index']):r for r in replacements};assert len(byindex)==len(replacements)
    assert completion['replacements']==len(replacements)
    original=read(RUN/'onep7/data/existing.jsonl');assert len(original)==2585
    tok=AutoTokenizer.from_pretrained(START,local_files_only=True);rows=read(current/'training.jsonl');tokens=[];reports=[];proposed=[]
    protected={};vb=REPO/'external/veribench'
    for item in csv.DictReader((HERE.parent/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ('validation','test'):
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text()
            protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in read(RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    for row in rows:
        report=dict(uid=row['uid'],task_id=row['task_id'],replacement=False,reason='source outside original pool')
        if row['pool']=='python':
            index=int(row['uid'].split(':',2)[1]);report['example_index']=index;report['reason']='no verified replacement supplied'
            if index in byindex:
                replacement=byindex[index]
                try:
                    assert replacement['original_response_sha256']==row['response_sha256']==original[index]['response_sha256']
                    assert replacement['messages'][:2]==row['messages'][:2],'changed frozen input prompt'
                    checkpath=Path(replacement['verification_receipt'])
                    assert digest(checkpath)==replacement['verification_receipt_sha256'],'replacement receipt changed'
                    check=json.loads(checkpath.read_text())
                    assert check.get('passed',check.get('accepted',False)) and kernel.valid_report(check['kernel_report'])
                    assert check['scope_gate']=='construction_only_original_proof_terms'
                    assert check['kernel_report']['n_theorems']>=1 and check['kernel_report']['n_theorems']==check['kernel_report']['n_honest']
                    answer=replacement['messages'][-1]['content'];marker=re.search(r'^FILE:\s*([^\n]+)',answer,re.M);assert marker
                    lean=extract_lean(answer,[marker[1].strip()],root=REPO/'external/veribench').lean
                    assert sha(lean.encode())==replacement['lean_sha256']==check['kernel_report']['source_sha256']
                    assert sha(answer.encode())==replacement['response_sha256']
                    rendered=render(tok,row['messages'][0]['content'],row['messages'][1]['content'],answer)
                    assert all(rendered[k] for k in ('byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'))
                    row=dict(row,messages=replacement['messages'],lean_sha256=replacement['lean_sha256'],response_sha256=replacement['response_sha256'],original_response_sha256=row['response_sha256'],verification_basis='v13_frozen_kernel_explicit_replacement')
                    report.update(replacement=True,reason='verified replacement',verification_receipt=replacement['verification_receipt'])
                except Exception as exc:report['reason']='verified original fallback: '+repr(exc)
        proposed.append(row);reports.append(report)
    screening=screen({r['uid']:r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for r in proposed},protected);clean=set(screening['clean_ids'])
    # Never change the declared row manifest to recover a failed replacement screen.
    for i,row in enumerate(proposed):
        if row['uid'] not in clean:
            assert reports[i]['replacement'],'previously frozen original unexpectedly fails the identical screen'
            proposed[i]=rows[i];reports[i].update(replacement=False,reason='verified original fallback: replacement protected-screen hit')
    for i,row in enumerate(proposed):
        messages=row['messages'];prefix=tok.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True)
        pids=tok.encode(prefix,add_special_tokens=False);aids=tok.encode('<think>\n\n</think>\n\n'+messages[2]['content']+'<|im_end|>\n'+tok.eos_token,add_special_tokens=False)
        assert len(pids)+len(aids)<=16384
        tokens.append(dict(index=i,uid=row['uid'],task_id=row['task_id'],pool=row['pool'],source=row['source'],ids=pids+aids,prompt=len(pids),loss_tokens=len(aids)))
        row.update(n_assistant_tokens=len(aids)-1,n_total_tokens=len(pids)+len(aids))
    old_schedule=json.loads((current/'schedule.json').read_text());batches=[];consumed=0
    for batch in old_schedule:
        consumed+=sum(tokens[i]['loss_tokens'] for i in batch['indices']);batches.append(dict(indices=batch['indices'],cumulative_loss_tokens=consumed))
    assert [r['uid'] for r in proposed]==[r['uid'] for r in rows]
    data=ROOT/'cleaned/data';data.mkdir(parents=True,exist_ok=True);assert not (data/'prepare_receipt.json').exists(),'already frozen'
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in proposed);(data/'training.jsonl').write_text(text);torch.save(tokens,data/'tokens.pt');write(data/'schedule.json',batches)
    (data/'initial_manifest.json').write_bytes((current/'initial_manifest.json').read_bytes());write(data/'protected_screen.json',screening)
    write(data/'token_manifest.json',[{k:v for k,v in t.items() if k!='ids'}|dict(ids_sha256=sha(json.dumps(t['ids']).encode())) for t in tokens])
    keys=['uid','task_id','example_index','replacement','reason','verification_receipt']
    with (data/'row_results.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(reports)
    receipt=dict(source_receipt,prepared_unix=time.time(),rows=len(tokens),loss_tokens=consumed,training_sha256=digest(data/'training.jsonl'),tokens_sha256=digest(data/'tokens.pt'),schedule_sha256=digest(data/'schedule.json'),longest_sequence=max(len(t['ids']) for t in tokens),replacements=sum(r['replacement'] for r in reports),original_pool_fallbacks=sum(r['pool']=='python' for r in rows)-sum(r['replacement'] for r in reports),current_training_sha256=source_receipt['training_sha256'],v13_completion_sha256=digest(cleanup/'completion.json'),v13_replacements_sha256=digest(replacement_file),matched_row_order=True,matched_token_budget=False,source_sha256=dict(source_receipt['source_sha256'],**{'assemble_cleaned.py':digest(HERE/'assemble_cleaned.py')}))
    write(data/'prepare_receipt.json',receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
