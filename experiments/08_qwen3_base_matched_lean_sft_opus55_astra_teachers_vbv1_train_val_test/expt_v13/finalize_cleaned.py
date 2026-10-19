"""Freeze checked proof replacements and retain every original training row with explicit fallback accounting."""
import argparse
import csv
import json
import os
import sys
import time
import clean_existing as clean
from clean_existing import base

def main(partial=False):
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from transformers import AutoTokenizer
    sys.path[:0]=[str(clean.RUN/'repo/src'),str(clean.HERE.parent/'expt_v1/scripts')]
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen
    tok=AutoTokenizer.from_pretrained(clean.TOKENIZER,local_files_only=True)
    kernel=clean.kernel_module();rows=base.read_rows(clean.SOURCE);reports=[];replacements=[];output=[]
    for i,original in enumerate(rows):
        folder=clean.ROOT/'cases'/f'existing_{i:04d}';status=json.loads((folder/'status.json').read_text())
        record=dict(example_index=i,task_id=original['task_id'],state=status['state'],replaced=False,source='original_fallback',reason=status.get('reason',''))
        row=dict(original)
        if status.get('verified'):
            try:
                source=(folder/'Solution.lean').read_text();digest=base.sha(source)
                receipt_path=folder/'checks'/digest/'result.json';receipt=json.loads(receipt_path.read_text())
                assert receipt['passed'] and kernel.valid_report(receipt['kernel_report'])
                assert receipt['kernel_report']['source_sha256']==digest
                envelope=json.loads((folder/'envelope.json').read_text());answer=envelope['prefix']+source+envelope['suffix']
                assert extract_lean(answer,[envelope['path']],root=clean.RUN/'repo/external/veribench').lean==source
                messages=[dict(m) for m in original['messages']];messages[-1]['content']=answer
                checked=render(tok,messages[0]['content'],messages[1]['content'],answer)
                assert all(checked[k] for k in ['byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'])
                replacement=dict(example_index=i,original_response_sha256=original['response_sha256'],messages=messages,lean_sha256=digest,response_sha256=base.sha(answer),verification_receipt=str(receipt_path),verification_receipt_sha256=base.sha(receipt_path.read_bytes()),n_prompt_tokens=checked['n_prompt_tokens'],n_assistant_tokens=checked['n_assistant_tokens'],n_total_tokens=checked['n_total_tokens'],model=clean.MODEL,reasoning_effort=clean.EFFORT)
                replacements.append(replacement);row.update(messages=messages,lean_sha256=digest,response_sha256=base.sha(answer),n_prompt_tokens=checked['n_prompt_tokens'],n_assistant_tokens=checked['n_assistant_tokens'],proof_cleanup_v13=dict(model=clean.MODEL,effort=clean.EFFORT,verified=True,original_response_sha256=original['response_sha256'],receipt=str(receipt_path)))
                row['original_provenance']=original.get('provenance')
                row['provenance']=dict(envelope='Original FILE envelope; only parser-owned proof terms rewritten, sketch inserted after imports',proof_cleanup='v13',original_response_sha256=original['response_sha256'])
                row.pop('lean_norm_hash',None)
                record.update(replaced=True,source='kernel_and_format_checked_replacement',reason='',lean_sha256=digest,n_assistant_tokens=checked['n_assistant_tokens'])
            except Exception as exc:record['reason']=repr(exc)
        if not record['replaced']:row['proof_cleanup_v13']=dict(verified=False,original_fallback=True,state=status['state'],reason=record['reason'])
        output.append(row);reports.append(record)
    # Keep protected material inside this ordinary coordinator, never in teacher prompts.
    protected={};vb=clean.RUN/'repo/external/veribench'
    for item in csv.DictReader((clean.HERE.parent/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ['validation','test']:
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text()
            protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in base.read_rows(clean.RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    screening=screen({str(r['example_index']):r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for r in replacements},protected)
    allowed=set(screening['clean_ids']);retained=[]
    for replacement in replacements:
        i=replacement['example_index']
        if str(i) in allowed:retained.append(replacement)
        else:
            output[i]=dict(rows[i],proof_cleanup_v13=dict(verified=False,original_fallback=True,state='SCREEN_REJECTED'))
            reports[i].update(replaced=False,source='original_fallback',reason='Protected exact/near screen rejection')
    final=clean.ROOT/('calibration' if partial else 'final');final.mkdir(exist_ok=True)
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in retained);(final/'replacements.jsonl').write_text(text)
    alltext=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output);(final/'cleaned_existing_training.jsonl').write_text(alltext)
    base.write(final/'protected_screen.json',screening)
    keys=['example_index','task_id','state','replaced','source','reason','lean_sha256','n_assistant_tokens']
    with (final/'row_results.csv').open('w') as stream:
        w=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(reports)
    summary=dict(state='CALIBRATION' if partial else 'DONE' if all(r['state'] in ['DONE','UNCHANGED'] and (r['replaced'] or r['state']=='UNCHANGED') for r in reports) else 'DONE_PARTIAL',declared=2585,accounted=len(reports),replacements=len(retained),original_fallbacks=2585-len(retained),replacements_sha256=base.sha(text),training_sha256=base.sha(alltext),source_sha256=clean.SOURCE_SHA,protected_references=764,protected_exact=screening['n_exact'],protected_near=screening['n_near'],observed_unix=time.time())
    base.write(final/'summary.json',summary)
    if not partial:base.write(clean.ROOT/'completion.json',summary)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');a=p.parse_args();main(a.partial)
