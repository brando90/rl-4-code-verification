"""Freeze an accepted-only explicit Python-to-Lean pool with a complete 2,585-row exclusion ledger."""
from __future__ import annotations
import csv
import json
import os
import re
from pathlib import Path
import sys
import time
import repair_batches as repair
from repair_batches import ROOT,RUN,HERE,base,read,write

def main(available_only=False):
    repair.assert_inspector()
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from transformers import AutoTokenizer
    sys.path[:0]=[str(RUN/'repo/src'),str(HERE.parent/'expt_v1/scripts')]
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen
    assert base.sha(repair.prior.SOURCE.read_bytes())==repair.prior.SOURCE_SHA
    original=base.read_rows(repair.prior.SOURCE);manifest=read(ROOT/'manifest.json');assert len(original)==len(manifest)==2585
    admission=read(ROOT/'available_snapshot_admission.json') if available_only else None
    frozen={r['task_id']:r for r in admission['rows']} if admission else {}
    if available_only:
        assert (ROOT/'user_stop_paid_generation.json').exists()
        assert read(ROOT/'paid_generation_stop_receipt.json')['state']=='STOPPED'
    else:assert all(read(p)['state']=='DONE' for p in (ROOT/'batches').glob('*/status.json')),'Declared repair batches are not all terminal.'
    tok=AutoTokenizer.from_pretrained(repair.prior.TOKENIZER,local_files_only=True)
    kernel=repair.prior.kernel_module();reports=[];candidates=[];replacements=[]
    for item in manifest:
        tid=item['task_id'];i=item['example_index'];folder=ROOT/'cases'/tid;status=read(folder/'status.json')
        record=dict(task_id=tid,example_index=i,state=status['state'],kernel_verified=False,admitted=False,exclusion=status.get('reason',''))
        try:
            if available_only:
                assert tid in frozen,'Not kernel-accepted at the user-requested snapshot cutoff; preserved outside training.'
            assert status['state'].startswith('ACCEPTED'),status.get('reason','Explicit proof not established within the recorded attempts.')
            assert base.sha((folder/'input.json').read_bytes())==item['original_input_sha256']
            source=(folder/'Solution.lean').read_text();digest=base.sha(source)
            if available_only:
                assert digest==frozen[tid]['source_sha256']
            assert status['source_sha256']==digest
            receipt_path=Path(status['receipt']);receipt=read(receipt_path)
            assert receipt['passed'] and kernel.valid_report(receipt['kernel_report'])
            report=receipt['kernel_report'];assert report['n_theorems']>=1 and report['n_theorems']==report['n_honest']
            assert report['source_sha256']==digest
            assert (receipt_path.parent/'Solution.lean').read_text()==source
            assert receipt['scope_gate'] in ['construction_only_original_proof_terms','byte_identical_original_no_targeted_automation']
            record['kernel_verified']=True
            if available_only:
                assert frozen[tid]['header_proof_sketch'] and frozen[tid]['english_inline_comments']>0,'Missing requested proof-sketch header or English inline comments; kernel-accepted artifact preserved outside training.'
                assert re.search(r'/-\s*Proof sketch\s*:',source,re.I)
                assert any(re.search('[A-Za-z]{3}',m.group(1)) for m in re.finditer(r'(?m)^\s*--([^\n]+)',source))
            envelope=read(folder/'envelope.json');answer=envelope['prefix']+source+envelope['suffix']
            assert extract_lean(answer,[envelope['path']],root=RUN/'repo/external/veribench').lean==source
            messages=[dict(m) for m in original[i]['messages']];messages[-1]['content']=answer
            checked=render(tok,messages[0]['content'],messages[1]['content'],answer)
            assert all(checked[k] for k in ['byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'])
            repaired_by_model=status['state'] in ['ACCEPTED_INHERITED','ACCEPTED_REPAIRED','ACCEPTED_SAVED_CANDIDATE']
            row=dict(original[i],uid=f'python:{i:05d}:{original[i]["task_id"]}',example_index=i,pool='python',messages=messages,lean_sha256=digest,response_sha256=base.sha(answer),original_response_sha256=original[i]['response_sha256'],n_prompt_tokens=checked['n_prompt_tokens'],n_assistant_tokens=checked['n_assistant_tokens'],n_total_tokens=checked['n_total_tokens'],current_kernel_verified=True,automation_cleanup_v18=dict(state=status['state'],no_automated_fallback=True,receipt=str(receipt_path),receipt_sha256=base.sha(receipt_path.read_bytes()),model=repair.MODEL if repaired_by_model else None,effort=repair.EFFORT if repaired_by_model else None))
            row.pop('lean_norm_hash',None);row['original_provenance']=original[i].get('provenance')
            row['provenance']=dict(original_response_sha256=original[i]['response_sha256'],phase='V18 explicit original-pool cleanup',automated_fallback=False)
            replacement=dict(example_index=i,original_response_sha256=original[i]['response_sha256'],messages=messages,lean_sha256=digest,response_sha256=base.sha(answer),verification_receipt=str(receipt_path),verification_receipt_sha256=base.sha(receipt_path.read_bytes()),n_assistant_tokens=checked['n_assistant_tokens'],n_total_tokens=checked['n_total_tokens'])
            candidates.append((i,row,replacement));record.update(kernel_verified=True,exclusion='',lean_sha256=digest,n_assistant_tokens=checked['n_assistant_tokens'],source_receipt=str(receipt_path))
        except Exception as exc:record['exclusion']=repr(exc)
        reports.append(record)
    protected={};vb=RUN/'repo/external/veribench'
    for item in csv.DictReader((HERE.parent/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ['validation','test']:
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text()
            protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in base.read_rows(RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    screening=screen({str(i):r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for i,r,_ in candidates},protected)
    allowed=set(screening['clean_ids']);accepted=[]
    byindex={r['example_index']:r for r in reports}
    for i,row,replacement in candidates:
        if str(i) not in allowed:byindex[i]['exclusion']='Protected exact/near overlap screen';continue
        accepted.append(row);byindex[i]['admitted']=True
        if row['lean_sha256']!=original[i]['lean_sha256']:replacements.append(replacement)
    final=ROOT/'final';final.mkdir(exist_ok=True)
    portable=[];receipt_dir=final/'proof_receipts';receipt_dir.mkdir(exist_ok=True)
    for row in accepted:
        i=row['example_index'];meta=row['automation_cleanup_v18'];source_receipt=Path(meta['receipt'])
        raw=source_receipt.read_bytes();assert base.sha(raw)==meta['receipt_sha256']
        rel=f'proof_receipts/existing_{i:04d}.json';target=final/rel;target.write_bytes(raw)
        assert base.sha(target.read_bytes())==meta['receipt_sha256']
        meta['portable_receipt']=rel
        portable.append(dict(example_index=i,source_sha256=row['lean_sha256'],portable_receipt=rel,receipt_sha256=meta['receipt_sha256'],original_receipt_path=str(source_receipt)))
    portable_by_index={r['example_index']:r for r in portable}
    for row in replacements:
        row['portable_verification_receipt']=portable_by_index[row['example_index']]['portable_receipt']
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in accepted)
    reptext=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in replacements)
    (final/'fully_cleaned_existing_training.jsonl').write_text(text);(final/'replacements.jsonl').write_text(reptext)
    excluded=[r for r in reports if not r['admitted']]
    (final/'excluded_rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in excluded))
    write(final/'protected_screen.json',screening)
    write(final/'proof_receipts_manifest.json',portable)
    keys=['task_id','example_index','state','kernel_verified','admitted','exclusion','lean_sha256','n_assistant_tokens','source_receipt']
    with (final/'row_results.csv').open('w') as stream:
        w=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(reports)
    summary=dict(state='USER_STOPPED_PARTIAL' if available_only else ('DONE' if not excluded else 'DONE_WITH_EXCLUSIONS'),declared=2585,accounted=len(reports),accepted=len(accepted),excluded=len(excluded),changed_source_replacements=len(replacements),kernel_verified=sum(r['kernel_verified'] for r in reports),training_sha256=base.sha(text),replacements_sha256=base.sha(reptext),row_results_sha256=base.sha((final/'row_results.csv').read_bytes()),protected_references=764,protected_exact=screening['n_exact'],protected_near=screening['n_near'],no_automated_fallbacks=True,all_remaining_batches_attempted=not available_only,original_pool_sha256=repair.prior.SOURCE_SHA,prior_v13_completion_sha256=base.sha((repair.OLD/'completion.json').read_bytes()),observed_unix=time.time())
    if available_only:summary.update(user_override='Stop paid proof generation; train now on available strict no-automation, sketch and inline-comment sources.',available_kernel_verified=admission['source_count'],missing_commentary=sum(not(r['header_proof_sketch'] and r['english_inline_comments']>0) for r in admission['rows']),admission_sha256=base.sha((ROOT/'available_snapshot_admission.json').read_bytes()),accepted_source_indices=[r['example_index'] for r in accepted])
    summary.update(protected_screen_sha256=base.sha((final/'protected_screen.json').read_bytes()),proof_receipts_manifest_sha256=base.sha((final/'proof_receipts_manifest.json').read_bytes()),protected_reference_sha256=base.sha(json.dumps({k:base.sha(v) for k,v in protected.items()},sort_keys=True)))
    write(final/'summary.json',summary);write(ROOT/'completion.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':
    main('--available-only' in sys.argv)
