"""Freeze the exact V20 cohort/order with verified automation-proof counterparts."""
from collections import Counter
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training');REPO=RUN/'repo'
EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test')
HERE=REPO/EXP/'expt_v25';ROOT=RUN/'corpus_training_v25';FROZEN=REPO/EXP/'expt_v12'
BASE=RUN/'corpus_training_v20/base';START=Path('/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1')
SEED=20261019
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()
def sha(text):return hashlib.sha256(text.encode()).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)
def read(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def source(answer):
    match=re.search(r'^FILE:\s*([^\n]+)\n```lean\n(.*)```\s*$',answer,re.M|re.S);assert match;return match


def main():
    os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['TOKENIZERS_PARALLELISM']='false'
    import torch
    from transformers import AutoTokenizer
    sys.path[:0]=[str(REPO/'src'),str(REPO/EXP/'expt_v1/scripts')]
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen
    data=ROOT/'base/data';data.mkdir(parents=True,exist_ok=True);assert not (data/'prepare_receipt.json').exists()
    prior=json.loads((BASE/'data/prepare_receipt.json').read_text());assert prior['status']=='PASS' and prior['rows']==3568
    assert digest(BASE/'data/training.jsonl')==prior['training_sha256']=='0882a88925e862b44fd79b7592d8d525829aec1f2ac1bd12afa1fd43fc6a5de7'
    assert digest(BASE/'data/tokens.pt')==prior['tokens_sha256'] and digest(BASE/'data/schedule.json')==prior['schedule_sha256']
    reference_lines=(BASE/'data/training.jsonl').read_text().splitlines(keepends=True)
    original_rows=[json.loads(line) for line in reference_lines]
    original_tokens=torch.load(BASE/'data/tokens.pt',map_location='cpu',weights_only=False)
    assert len(original_tokens)==len(original_rows)==3568
    schedule=json.loads((BASE/'data/schedule.json').read_text());assert len(schedule)==1784
    lr_rows=list(csv.DictReader((BASE/'run/steps.csv').open()));assert len(lr_rows)==1784 and [int(r['step']) for r in lr_rows]==list(range(1,1785))
    completion=json.loads((ROOT/'restoration_verification/completion.json').read_text());assert completion['state']=='DONE'
    assert digest(ROOT/'restoration_verification/rows.jsonl')==completion['rows_sha256']
    verified={row['index']:row for row in read(ROOT/'restoration_verification/rows.jsonl')}
    candidates={row['index']:row for row in read(ROOT/'restoration_candidates/pending.jsonl')}
    tok=AutoTokenizer.from_pretrained(START,local_files_only=True)
    rows=[];tokens=[];reports=[];lines=[];proposed={}
    for index,(old,old_token,old_line) in enumerate(zip(original_rows,original_tokens,reference_lines)):
        assert old['uid']==old_token['uid']
        row=dict(old);messages=[dict(m) for m in old['messages']];answer=messages[-1]['content'];report=dict(index=index,uid=old['uid'],pool=old['pool'],task_id=old['task_id'],changed=False)
        proof=verified.get(index)
        if proof and proof['passed']:
            candidate=candidates[index];candidate_path=Path(candidate['source_path']);assert digest(candidate_path)==proof['source_sha256']==candidate['candidate_sha256']
            receipt=ROOT/'restoration_verification'/f'{index:04d}'/'result.json'
            assert json.loads(receipt.read_text())==proof
            if proof['basis']=='new_frozen_kernel_full_source':assert digest(proof['kernel_report_path'])==proof['kernel_report_sha256']
            current=source(answer);replacement=candidate_path.read_text();answer=answer[:current.start(2)]+replacement+answer[current.end(2):]
            report.update(proposed=True,restored_proofs=len(candidate['restored_proofs']),restored_tactics=candidate['restored_tactics'],verification_basis=proof['basis'],verification_receipt=str(receipt),verification_receipt_sha256=digest(receipt))
            proposed[old['uid']]=messages[1]['content']+'\n'+answer
        elif proof:report['pairing_gap']='Counterpart full-source verification failed; exact V20 row retained'
        else:report['pairing_gap']='No eligible paired counterpart; exact V20 row retained'
        try:
            marker=source(answer);lean=marker[2];assert extract_lean(answer,[marker[1].strip()],root=REPO/'external/veribench').lean==lean
            checked=render(tok,messages[0]['content'],messages[1]['content'],answer)
            assert all(checked[k] for k in ('byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'))
            prefix=tok.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True);pids=tok.encode(prefix,add_special_tokens=False)
            assert pids==old_token['ids'][:old_token['prompt']]
            aids=tok.encode('<think>\n\n</think>\n\n'+answer+'<|im_end|>\n'+tok.eos_token,add_special_tokens=False)
            assert len(pids)+len(aids)<=16384 and len(aids)==checked['n_assistant_tokens']+1
        except Exception as error:
            assert report.get('proposed'),error
            report['pairing_gap']='Proposed restored answer failed exact template/token cap: '+str(error);report['proposed']=False
            answer=old['messages'][-1]['content'];pids=old_token['ids'][:old_token['prompt']];aids=old_token['ids'][old_token['prompt']:];proposed.pop(old['uid'],None)
        changed=answer!=old['messages'][-1]['content'];report['changed']=changed
        if changed:
            messages[-1]['content']=answer;row.update(messages=messages,response_sha256=sha(answer),lean_sha256=sha(source(answer)[2]),
                automation_restoration_v25=dict(reference_uid=old['uid'],reference_response_sha256=old['response_sha256'],**{k:report[k] for k in ('restored_proofs','restored_tactics','verification_basis','verification_receipt','verification_receipt_sha256')}))
            lines.append(json.dumps(row,ensure_ascii=False)+'\n')
        else:lines.append(old_line)
        rows.append(row);token=dict(old_token,ids=pids+aids,prompt=len(pids),loss_tokens=len(aids));tokens.append(token)
        report.update(assistant_loss_tokens=len(aids),source_sha256=row['lean_sha256']);reports.append(report)
        if index%250==0:write(ROOT/'assembly_progress.json',dict(processed=index+1,total=3568,restored=sum(r['changed'] for r in reports),observed_unix=time.time()))
    protected={};vb=REPO/'external/veribench'
    for item in csv.DictReader((REPO/EXP/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ('validation','test'):
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text();protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in read(RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    screening=screen(proposed,protected);write(data/'protected_screen.json',screening);clean=set(screening['clean_ids'])
    for index,report in enumerate(reports):
        if report['changed'] and report['uid'] not in clean:
            report.update(changed=False,pairing_gap='Restored counterpart protected-source screen; exact V20 row retained')
            rows[index]=original_rows[index];tokens[index]=original_tokens[index];lines[index]=reference_lines[index]
    assert [r['uid'] for r in rows]==[r['uid'] for r in original_rows]
    assert all(r['messages'][:2]==old['messages'][:2] for r,old in zip(rows,original_rows))
    for report,new_line,old_line in zip(reports,lines,reference_lines):
        if not report['changed']:assert new_line==old_line
    (data/'training.jsonl').write_text(''.join(lines));torch.save(tokens,data/'tokens.pt')
    consumed=0;new_schedule=[]
    for batch in schedule:
        indices=batch['indices'];consumed+=sum(tokens[i]['loss_tokens'] for i in indices);new_schedule.append(dict(indices=indices,cumulative_loss_tokens=consumed))
    assert [b['indices'] for b in new_schedule]==[b['indices'] for b in schedule]
    write(data/'schedule.json',new_schedule);write(data/'token_manifest.json',[{k:v for k,v in t.items() if k!='ids'} for t in tokens])
    (data/'initial_manifest.json').write_bytes((BASE/'data/initial_manifest.json').read_bytes())
    fields=sorted({k for r in reports for k in r})
    with (data/'row_results.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(reports)
    owned=['assemble.py','pipeline.py','dispatch.py','outer_watch.py','summarize.py','train.py','entry.py','PROTOCOL.md']
    for name in owned:assert (HERE/name).is_file(),name
    receipt=dict(status='PASS',seed=SEED,rows=3568,by_pool=dict(Counter(r['pool'] for r in rows)),by_source=dict(Counter(r['source'] for r in rows)),loss_tokens=consumed,steps=1784,longest_sequence=max(len(t['ids']) for t in tokens),
        initial=str(START),initial_model='Qwen/Qwen3-1.7B-Base',initial_revision=START.name,initial_manifest_sha256=digest(data/'initial_manifest.json'),
        training_sha256=digest(data/'training.jsonl'),tokens_sha256=digest(data/'tokens.pt'),schedule_sha256=digest(data/'schedule.json'),source_sha256=prior['source_sha256'],
        v25_source_sha256={name:digest(HERE/name) for name in owned},matched_reference=dict(training_sha256=prior['training_sha256'],tokens_sha256=prior['tokens_sha256'],schedule_sha256=prior['schedule_sha256'],steps_sha256=digest(BASE/'run/steps.csv')),
        ids_prompts_row_order_and_batch_indices_identical=True,learning_rate_clock='Exact recorded V20 learning_rate per optimizer update; new token counts retained separately',
        restored_rows=sum(r['changed'] for r in reports),restored_by_pool=dict(Counter(r['pool'] for r in reports if r['changed'])),unchanged_rows=sum(not r['changed'] for r in reports),
        pairing_gaps=dict(Counter(r.get('pairing_gap','') for r in reports if not r['changed'])),restored_tactic_rows=dict(Counter(t for r in reports if r['changed'] for t in r['restored_tactics'])),
        protected_references=764,protected_exact_retained=0,protected_near_retained=0,fresh_optimizer=True,sft_weights_reused=False,test_split_evaluated=False,no_teacher_generation=True,
        verification_completion_sha256=digest(ROOT/'restoration_verification/completion.json'),future_logged_entry_sha256=digest(REPO/EXP/'expt_v24/future_logging/parallel_scoring_logged.py'),prepared_unix=time.time())
    write(data/'prepare_receipt.json',receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':main()
