"""Combine V18's fully processed original pool with immutable admitted non-original data and retain exact exclusion accounting."""
from collections import Counter
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import time

EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test')
KERNEL_SHA='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'
BASE_SHA='deefba0e3dc86c6910a1d5d3b3137cd18510efc1cb943395cff5f372b9356d6c'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def read(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--base-data',type=Path,required=True);p.add_argument('--v18-root',type=Path,required=True);p.add_argument('--receipt-root',type=Path);p.add_argument('--initial',type=Path,required=True);p.add_argument('--frozen-source',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--kernel',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    import os
    os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    from transformers import AutoTokenizer
    sys.path[:0]=[str(a.repo/'src'),str(a.repo/EXP/'expt_v1/scripts')]
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    assert digest(a.kernel)==KERNEL_SHA
    spec=importlib.util.spec_from_file_location('v19_admission_kernel',a.kernel);kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
    prior=json.loads((a.base_data/'prepare_receipt.json').read_text());assert prior['status']=='PASS' and prior['rows']==10940
    assert prior['training_sha256']==digest(a.base_data/'training.jsonl')==BASE_SHA
    for name,h in prior['source_sha256'].items():assert digest(a.frozen_source/name)==h,name
    initial=json.loads((a.base_data/'initial_manifest.json').read_text());assert digest(a.base_data/'initial_manifest.json')==prior['initial_manifest_sha256']
    for name,h in initial.items():assert Path(name).name==name and digest(a.initial/name)==h,name
    completion=json.loads((a.v18_root/'completion.json').read_text())
    assert completion['state'] in ('DONE','DONE_WITH_EXCLUSIONS') and completion['declared']==completion['accounted']==2585
    assert completion['no_automated_fallbacks'] is True
    final=a.v18_root/'final';accepted_path=final/'fully_cleaned_existing_training.jsonl';table_path=final/'row_results.csv';replacement_path=final/'replacements.jsonl'
    assert digest(accepted_path)==completion['training_sha256'] and digest(table_path)==completion['row_results_sha256'] and digest(replacement_path)==completion['replacements_sha256']
    assert completion['protected_references']==764 and completion['protected_exact']==completion['protected_near']==0
    assert digest(final/'proof_receipts_manifest.json')==completion['proof_receipts_manifest_sha256']
    protected=final/'protected_screen.json'
    if not protected.exists():protected=a.v18_root/'protected_screen.json'
    assert digest(protected)==completion['protected_screen_sha256']
    assert len(completion['protected_reference_sha256'])==64
    final_originals=read(accepted_path);assert len(final_originals)==completion['accepted'] and len(final_originals)+completion['excluded']==2585
    accepted={int(r['example_index']):r for r in final_originals};assert len(accepted)==len(final_originals)
    old=read(a.base_data/'training.jsonl');assert len(old)==len({r['uid'] for r in old})==10940
    tok=AutoTokenizer.from_pretrained(a.initial,local_files_only=True);rows=[];tokens=[];reports=[]
    for index,baseline in enumerate(old):
        uid=baseline['uid'];row=dict(baseline);record=dict(uid=uid,task_id=row['task_id'],pool=row['pool'],admitted=True,base_index=index)
        if row['pool']=='python':
            example=int(uid.split(':',2)[1]);record['example_index']=example
            if example not in accepted:
                record.update(admitted=False,exclusion='V18 honest unresolved exclusion; no broad-automation original fallback retained');reports.append(record);continue
            replacement=dict(accepted[example]);assert replacement['uid']==uid and replacement['task_id']==baseline['task_id'] and replacement['pool']=='python'
            original_hash=baseline.get('original_response_sha256',baseline['response_sha256']);assert replacement['original_response_sha256']==original_hash
            assert replacement['messages'][:2]==baseline['messages'][:2],'Frozen Python task prompt changed'
            checkmeta=replacement['automation_cleanup_v18'];receipt=Path(checkmeta['receipt'])
            if not receipt.exists():
                assert a.receipt_root,'Portable proof receipt root required';receipt=a.receipt_root/f'existing_{example:04d}.json'
            assert digest(receipt)==checkmeta['receipt_sha256'];check=json.loads(receipt.read_text())
            assert check['passed'] and kernel.valid_report(check['kernel_report'])
            assert check['kernel_report']['n_theorems']>=1 and check['kernel_report']['n_honest']==check['kernel_report']['n_theorems']
            assert check['scope_gate'] in ('construction_only_original_proof_terms','byte_identical_original_no_targeted_automation')
            row=replacement;record.update(verification_receipt_sha256=digest(receipt),scope_gate=check['scope_gate'])
        messages=row['messages'];assert [m['role'] for m in messages]==['system','user','assistant']
        answer=messages[2]['content'];assert sha(answer)==row['response_sha256'];marker=re.search(r'^FILE:\s*([^\n]+)',answer,re.M);assert marker
        lean=extract_lean(answer,[marker[1].strip()],root=a.repo/'external/veribench').lean;assert lean and sha(lean)==row['lean_sha256']
        if row['pool']=='python':assert check['kernel_report']['source_sha256']==sha(lean)
        checked=render(tok,messages[0]['content'],messages[1]['content'],answer);assert all(checked[k] for k in ('byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'))
        prefix=tok.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True);pids=tok.encode(prefix,add_special_tokens=False)
        aids=tok.encode('<think>\n\n</think>\n\n'+answer+'<|im_end|>\n'+tok.eos_token,add_special_tokens=False)
        assert len(pids)+len(aids)<=16384 and len(aids)==checked['n_assistant_tokens']+1
        row.update(n_assistant_tokens=len(aids)-1,n_total_tokens=len(pids)+len(aids));rows.append(row)
        tokens.append(dict(index=len(tokens),uid=uid,task_id=row['task_id'],pool=row['pool'],source=row['source'],ids=pids+aids,prompt=len(pids),loss_tokens=len(aids)))
        record.update(source_sha256=sha(lean),loss_tokens=len(aids),total_tokens=len(pids)+len(aids));reports.append(record)
    assert len(rows)==8355+len(final_originals) and sum(r['pool']=='python' for r in rows)==len(final_originals)
    indices={r['uid']:i for i,r in enumerate(rows)};old_schedule=json.loads((a.base_data/'schedule.json').read_text());old_order=[old[i]['uid'] for batch in old_schedule for i in batch['indices']]
    order=[indices[uid] for uid in old_order if uid in indices];assert sorted(order)==list(range(len(rows)))
    batches=[];consumed=0
    for position in range(0,len(order),2):
        batch=order[position:position+2];consumed+=sum(tokens[i]['loss_tokens'] for i in batch);batches.append(dict(indices=batch,cumulative_loss_tokens=consumed))
    a.output.mkdir(parents=True,exist_ok=True);assert not (a.output/'prepare_receipt.json').exists(),'Final data already frozen'
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows);(a.output/'training.jsonl').write_text(text);torch.save(tokens,a.output/'tokens.pt');write(a.output/'schedule.json',batches)
    (a.output/'initial_manifest.json').write_bytes((a.base_data/'initial_manifest.json').read_bytes())
    write(a.output/'token_manifest.json',[{k:v for k,v in t.items() if k!='ids'}|dict(ids_sha256=sha(json.dumps(t['ids']))) for t in tokens])
    fields=['uid','task_id','pool','base_index','example_index','admitted','source_sha256','scope_gate','verification_receipt_sha256','loss_tokens','total_tokens','exclusion']
    with (a.output/'row_results.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(reports)
    receipt=dict(status='PASS',seed=20261019,rows=len(rows),by_pool=dict(Counter(r['pool'] for r in rows)),by_source=dict(Counter(r['source'] for r in rows)),loss_tokens=consumed,steps=len(batches),longest_sequence=max(len(r['ids']) for r in tokens),training_sha256=digest(a.output/'training.jsonl'),tokens_sha256=digest(a.output/'tokens.pt'),schedule_sha256=digest(a.output/'schedule.json'),initial=str(a.initial),initial_manifest_sha256=digest(a.output/'initial_manifest.json'),source_sha256=prior['source_sha256'],preparation_code_sha256=digest(Path(__file__)),v18_completion_sha256=digest(a.v18_root/'completion.json'),v18_training_sha256=completion['training_sha256'],original_pool_admitted=len(final_originals),original_pool_excluded=completion['excluded'],no_automated_original_fallbacks=True,nonoriginal_policy='byte-identical V12 admitted rows; prior verified fallback policy retained',protected_references=764,protected_exact=0,protected_near=0,protected_screen_basis='Bound V18 accepted-original screen plus byte-identical previously screened non-original rows',relative_logical_row_order_preserved=True,matched_row_manifest=completion['excluded']==0,matched_token_budget=False,test_split_opened=False,prepared_unix=time.time())
    write(a.output/'prepare_receipt.json',receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
