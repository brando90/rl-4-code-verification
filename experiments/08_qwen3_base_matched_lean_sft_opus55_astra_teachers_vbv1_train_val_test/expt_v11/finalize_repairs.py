"""Assemble kernel-verified Sol repairs into screened warm-start conversations with complete per-case accounting."""
import csv
import json
import os
from pathlib import Path
import re
import sys
import time
import repair_proofs as repair
from repair_proofs import base,selection


def main():
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from transformers import AutoTokenizer
    sys.path[:0]=[str(repair.RUN/'repo/src'),str(repair.HERE.parent/'expt_v1/scripts')]
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen,normalize
    tokpath='/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
    tok=AutoTokenizer.from_pretrained(tokpath,local_files_only=True)
    candidates=[];reports=[];kernel=repair.kernel_module()
    manifest=json.loads((repair.ROOT/'manifest.json').read_text())
    preflight='--preflight' in sys.argv
    if preflight:manifest=[r for r in manifest if (repair.ROOT/'cases'/r['task_id']/'Solution.lean').exists()][:1]
    assert manifest
    for item in manifest:
        tid=item['task_id'];folder=repair.ROOT/'cases'/tid;status=json.loads((folder/'status.json').read_text())
        row=json.loads((folder/'input.json').read_text());record=dict(task_id=tid,state=status['state'],kernel_verified=False,format_check='NOT_RUN',training_admitted=False)
        try:
            assert base.sha((folder/'input.json').read_bytes())==item['input_sha256']
            result=json.loads((folder/'decision.json').read_text());record.update(decision=result['decision'],rationale=result['rationale'])
            if not result['verified']:raise ValueError('No repaired kernel-verified proof: '+result['rationale'])
            source=(folder/'Solution.lean').read_text();digest=base.sha(source);assert digest==result['source_sha256']
            receipt=json.loads((folder/'checks'/digest/'result.json').read_text())
            assert receipt['passed'] and not receipt['remaining_automation'] and kernel.valid_report(receipt['kernel_report'])
            assert receipt['kernel_report']['source_sha256']==digest
            record['kernel_verified']=True;record['source_sha256']=digest
            path=f'/home/user/lean_project/Veribench/{tid}.lean'
            answer=f'FILE: {path}\n```lean\n{source}```\n'
            assert extract_lean(answer,[path],root=repair.RUN/'repo/external/veribench').lean==source
            goal=re.sub(r'\s*:=\s*by\s+sorry\s*$','',row['formal_statement'])
            system='You write clear, complete Lean 4 files using Mathlib. Return only the requested FILE marker and one lean code fence. Prove the supplied statement with no sorry, admit, new axioms or native_decide. Include a brief English proof sketch as Lean comments at the top and focused explanations of meaningful proof steps.'
            user=f'Prove the following theorem in a complete Lean 4 file at `{path}`. Preserve its statement and name. Use `import Mathlib` and `open BigOperators Nat Real Rat`.\n\nInformal statement: {row["natural_language_statement"]}\n\n```lean\n{goal}\n```\n\nReturn FILE: {path} followed by a lean code fence containing the complete file.'
            checked=render(tok,system,user,answer)
            assert all(checked[k] for k in ['byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'])
            record.update(format_check='PASS',n_assistant_tokens=checked['n_assistant_tokens'],n_total_tokens=checked['n_total_tokens'])
            candidates.append(dict(task_id=tid,source='lean_workbook_sol_explicit_repair_v11',source_row=row['source_row'],source_revision='2e066e310b2c6d2c27616927ae131f82901c8f1c',formal_statement=row['formal_statement'],messages=[dict(role='system',content=system),dict(role='user',content=user),dict(role='assistant',content=answer)],lean_sha256=digest,response_sha256=base.sha(answer),current_kernel_verified=True,model=repair.MODEL,reasoning_effort=repair.EFFORT,n_assistant_tokens=checked['n_assistant_tokens'],n_total_tokens=checked['n_total_tokens']))
        except Exception as exc:record['error']=str(exc)
        reports.append(record)
    protected={};vb=repair.RUN/'repo/external/veribench'
    for item in csv.DictReader((repair.HERE.parent/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ['validation','test']:
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text()
            protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in base.read_rows(repair.RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    final=repair.ROOT/('format_preflight' if preflight else 'final');final.mkdir(exist_ok=True)
    screening=screen({r['task_id']:r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for r in candidates},protected)
    base.write(final/'protected_screen.json',screening)
    clean=set(screening['clean_ids']);seen={};accepted=[];byid={r['task_id']:r for r in reports}
    for row in candidates:
        tid=row['task_id'];key=normalize(re.sub(r'\btheorem\s+\S+','theorem TARGET',row['formal_statement']))
        if tid not in clean:byid[tid]['exclusion']='protected_screen';continue
        if key in seen:byid[tid]['exclusion']='duplicate_statement';byid[tid]['duplicate_of']=seen[key];continue
        seen[key]=tid;accepted.append(row);byid[tid]['training_admitted']=True
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in accepted)
    (final/'repaired_training.jsonl').write_text(text)
    for record in reports:
        if record['kernel_verified']:
            target=final/'examples'/record['task_id'];target.mkdir(parents=True,exist_ok=True)
            (target/'Solution.lean').write_bytes((repair.ROOT/'cases'/record['task_id']/'Solution.lean').read_bytes());base.write(target/'receipt.json',record)
    keys=['task_id','state','decision','kernel_verified','format_check','training_admitted','n_assistant_tokens','n_total_tokens','source_sha256','exclusion','duplicate_of','rationale','error']
    with (final/'row_results.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(reports)
    summary=dict(declared=len(reports),kernel_verified=sum(r['kernel_verified'] for r in reports),formatted=len(candidates),training_rows=len(accepted),output_sha256=base.sha(text),protected_references=764,protected_exact=screening['n_exact'],protected_near=screening['n_near'],observed_unix=time.time())
    base.write(final/'summary.json',summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
