"""Assemble every selected task with exact comment integrity, pinned formatting, and explicit verification eligibility."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import sys
import time

import prefer_explicit as selection
from prefer_explicit import base
from comment_integrity import insert_comments
from finalize_annotations import materialize_first_valid


def main():
    from transformers import AutoTokenizer
    sys.path.insert(0,str(base.REPO/'src'))
    sys.path.insert(0,str(selection.HERE.parent/'expt_v1/scripts'))
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    root=selection.ROOT
    rows=base.read_rows(root/'selection.jsonl')
    annotations=root/'annotations'
    materialize_first_valid(annotations,base.read_rows(annotations/'manifest.jsonl'))
    tiny={r['task_id']:r for r in base.read_rows(selection.RUN/'curriculum/training.jsonl')}
    workbook=json.loads(base.SOURCE.read_text())
    tokenizer='/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
    tok=AutoTokenizer.from_pretrained(tokenizer,local_files_only=True)
    final=root/'final';final.mkdir(exist_ok=True)
    reports=[];candidates=[];verified=[];tiny_training=[];followups=[]
    for row in rows:
        tid=row['task_id'];record=dict(task_id=tid,kind=row['kind'],format_check='NOT_RUN',comment_integrity='NOT_RUN',
            proof_index=row.get('proof_index'),changed=row['changed'],kernel_verified=False,training_admitted=False,
            no_qualifying_alternative=row['no_qualifying_alternative'])
        try:
            issue='';decision='';verified_proof=False
            if row['kind']=='tiny':
                assert not row['changed'],'tiny replacements require explicit current verification before admission'
                source=row['lean'];old=tiny[tid]
                match=re.fullmatch(r'FILE: ([^\n]+)\n```lean\n(.*)```\n',old['messages'][-1]['content'],re.S)
                path,oldsource=match.groups();assert oldsource==source
                prior=json.loads((selection.RUN/'curriculum/examples'/tid/'receipts/verification.json').read_text())
                assert prior['accepted'] and prior['lean_sha256']==base.sha(source)
                annotations_path=selection.BASELINE/'annotations/examples'/tid/'comments.json'
                if not annotations_path.exists():annotations_path=selection.BASELINE/'annotations/workers'/row['topic']/'annotations'/f'{tid}.json'
                comments=json.loads(annotations_path.read_text())
                lean=insert_comments(source,comments,require_sketch=False,allow_existing_prefix=True)
                assert lean==(Path(row['baseline_comment_folder'])/'Solution.lean').read_text()
                messages=[dict(m) for m in old['messages'][:2]]
                metadata=dict(old,source='tiny_curriculum_explicit_preference_v9')
                verified_proof=True;record['verification_basis']='prior_accepted_receipt_identical_code'
                record['differential_cases_reused']=32
            else:
                record['no_qualifying_alternative']=not any(not selection.automations(p) for p in workbook[row['source_row']]['proof'])
                review=root/'review/cases'/tid
                if review.exists():
                    result=json.loads((review/'decision.json').read_text())
                    decision=result['decision'];record['review_decision']=decision;record['review_model']=result.get('review_model','gpt-6.1-sol');record['rationale']=result['rationale']
                    if not result['verified']:
                        raise ValueError('Review '+decision+': '+result['rationale'])
                    index=result['proof_index'];record['proof_index']=index
                    source=selection.assemble(row,workbook[row['source_row']]['proof'][index])
                    assert result['source_sha256']==base.sha(source)
                    check=json.loads((review/'checks'/f'proof_{index:02d}'/'result.json').read_text())
                    assert check['passed'] and check['source_sha256']==base.sha(source)
                    lean=insert_comments(source,result['comments'])
                    assert lean==(review/'Commented.lean').read_text()
                    verified_proof=True;record['verification_basis']='pinned_frozen_kernel_inspector'
                else:
                    source=row['lean']
                    comment_folder=annotations/'examples'/tid if row['changed'] or not (Path(row['baseline_comment_folder'])/'Solution.lean').exists() else Path(row['baseline_comment_folder'])
                    result=json.loads((comment_folder/'comments.json').read_text())
                    issue=result['annotation_issue']
                    if issue:
                        followups.append(dict(task_id=tid,issue=issue))
                        raise ValueError('unreconciled annotation issue: '+issue)
                    lean=insert_comments(source,result['comments'])
                    assert lean==(comment_folder/'Solution.lean').read_text()
                    record['verification_basis']='public_proof_candidate_current_compatibility_pending'
                path=f'/home/user/lean_project/Veribench/{tid}.lean'
                goal=re.sub(r'\s*:=\s*by\s+sorry\s*$','',row['formal_statement'])
                messages=[dict(role='system',content='You write clear, complete Lean 4 files using Mathlib. Return only the requested FILE marker and one lean code fence. Prove the supplied statement with no sorry, admit, new axioms or native_decide. Include a brief English proof sketch as Lean comments at the top and focused explanations of meaningful proof steps.'),
                    dict(role='user',content=f'Prove the following theorem in a complete Lean 4 file at `{path}`. Preserve its statement and name. Use `import Mathlib` and `open BigOperators Nat Real Rat`.\n\nInformal statement: {row["natural_language_statement"]}\n\n```lean\n{goal}\n```\n\nReturn FILE: {path} followed by a lean code fence containing the complete file.')]
                metadata=dict(source='lean_workbook_explicit_preference_v9',source_revision='2e066e310b2c6d2c27616927ae131f82901c8f1c',source_row=row['source_row'],source_split=row['source_split'],proof_index=record['proof_index'])
                metadata['formal_statement']=row['formal_statement']
            response=f'FILE: {path}\n```lean\n{lean}```\n'
            assert extract_lean(response,[path],root=selection.RUN/'repo/external/veribench').lean==lean
            messages.append(dict(role='assistant',content=response))
            template=render(tok,messages[0]['content'],messages[1]['content'],response)
            assert all(template[k] for k in ('byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'))
            if row['kind']=='tiny':assert template['n_assistant_tokens']<1000
            tactics=selection.automations(source)
            record.update(format_check='PASS',comment_integrity='PASS',source_sha256=base.sha(source),annotated_sha256=base.sha(lean),
                kernel_verified=verified_proof,training_admitted=verified_proof,n_assistant_tokens=template['n_assistant_tokens'],
                n_total_tokens=template['n_total_tokens'],remaining_automation=tactics)
            metadata.update(task_id=tid,messages=messages,lean_sha256=base.sha(lean),response_sha256=base.sha(response),
                current_kernel_verified=verified_proof,training_admitted=verified_proof,remaining_automation=tactics,
                n_assistant_tokens=template['n_assistant_tokens'],selection_policy='prefer existing explicit proofs, retain fallback when no qualifying verified alternative',review_decision=decision,review_model=record.get('review_model'))
            target=final/'examples'/tid;target.mkdir(parents=True,exist_ok=True)
            (target/'Solution.lean').write_text(lean);base.write(target/'receipt.json',record)
            if row['kind']=='tiny':tiny_training.append(metadata)
            else:
                candidates.append(metadata)
                if verified_proof:verified.append(metadata)
        except Exception as exc:
            record['error']=str(exc)
        reports.append(record)
    from rl4cv.screens import screen,normalize
    protected={}
    vb=selection.RUN/'repo/external/veribench'
    for item in csv.DictReader((selection.HERE.parent/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ('validation','test'):
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text()
            protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in base.read_rows(selection.RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    combined=tiny_training+verified
    protected_report=screen({r['task_id']:r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for r in combined},protected)
    base.write(final/'protected_screen.json',protected_report)
    clean=set(protected_report['clean_ids']);seen={};byid={r['task_id']:r for r in reports}
    admitted=[]
    for item in combined:
        duplicate=None
        if item.get('formal_statement'):
            key=normalize(re.sub(r'\btheorem\s+\S+','theorem TARGET',item['formal_statement']))
            duplicate=seen.get(key);seen.setdefault(key,item['task_id'])
        if item['task_id'] not in clean or duplicate:
            item['training_admitted']=False;byid[item['task_id']]['training_admitted']=False
            byid[item['task_id']]['duplicate_of']=duplicate
            byid[item['task_id']]['admission_exclusion']='duplicate_statement' if duplicate else 'protected_screen'
        else:admitted.append(item)
    # Admission can change after duplicate screening; receipts must reflect the final decision.
    for record in reports:
        target=final/'examples'/record['task_id']
        if target.exists():base.write(target/'receipt.json',record)
    outputs={'tiny_training.jsonl':tiny_training,'workbook_candidates.jsonl':candidates,'workbook_verified_reviewed.jsonl':verified,
        'combined_verified_training.jsonl':admitted}
    hashes={}
    for name,data in outputs.items():
        text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data)
        (final/name).write_text(text);hashes[name]=base.sha(text)
    keys=['task_id','kind','format_check','comment_integrity','changed','proof_index','kernel_verified','training_admitted','no_qualifying_alternative',
        'remaining_automation','n_assistant_tokens','n_total_tokens','review_decision','review_model','verification_basis','source_sha256','annotated_sha256','duplicate_of','admission_exclusion','rationale','error']
    with (final/'row_results.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(reports)
    base.write(root/'review_followups.json',followups)
    base.write(root/'finalization.json',dict(declared=len(rows),tiny_formatted=len(tiny_training),workbook_formatted=len(candidates),
        workbook_kernel_verified=len(verified),training_rows=len(admitted),
        excluded_or_missing=sum(r['format_check']!='PASS' for r in reports),followups=len(followups),output_sha256=hashes,
        unexpected_failures=sum(r['format_check']!='PASS' and not r.get('error','').startswith(('Review reject_statement:','Review unresolved:','Review needs_sol:','unreconciled annotation issue:')) for r in reports),
        tokenizer_revision='ea980cb0a6c2ae4b936e82123acc929f1cec04c1',observed_unix=time.time(),rows=reports))
    print(json.dumps(dict(tiny=len(tiny_training),workbook_candidates=len(candidates),workbook_verified=len(verified),followups=len(followups))),flush=True)


if __name__=='__main__':main()
