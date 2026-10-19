"""Check commented answers, render the pinned training envelope, and retain explicit proof-verification status."""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from comment_integrity import insert_comments, safe_line_starts

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
RUN=Path(os.environ.get('TINY_RUN_ROOT','/lfs/skampere1/0/eth127/rl4cv_tiny_training'))
ROOT=RUN/'lean_corpus_v8'


def sha(value):
    return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');tmp.replace(path)


def materialize_first_valid(folder,manifest):
    """Retain the earliest mechanically valid annotation from the bounded native attempts."""
    originals={r['task_id']:r for r in manifest}
    chosen={}
    pending={}
    for batch in sorted((folder/'batches').glob('batch_*')):
        for output in sorted(batch.glob('output_*.json')):
            try:returned=json.loads(output.read_text())['annotations']
            except (json.JSONDecodeError,KeyError):continue
            for record in returned:
                tid=record.get('task_id')
                if tid in chosen or tid not in originals:
                    continue
                try:
                    annotated=insert_comments(originals[tid]['lean'],record['comments'])
                    assert isinstance(record['annotation_issue'],str)
                except (ValueError,KeyError,AssertionError):
                    pending.setdefault(tid,[]).append((output,record))
                    continue
                target=folder/'examples'/tid
                write(target/'comments.json',record)
                (target/'Solution.lean').write_text(annotated)
                write(target/'receipt.json',dict(task_id=tid,comment_integrity='PASS',source_sha256=originals[tid]['source_sha256'],
                    annotated_sha256=sha(annotated),comments=len(record['comments']),annotation_issue=record['annotation_issue'],
                    native_output=str(output.relative_to(folder)),current_toolchain_verification='pending',compilation_rerun=False))
                chosen[tid]=str(output.relative_to(folder))
    # A comment accidentally placed inside an original block comment is moved
    # before that block, retaining the model's exact words and every source byte.
    for tid,attempts in pending.items():
        if tid in chosen:
            continue
        original=originals[tid]
        for output,record in attempts:
            fixed=json.loads(json.dumps(record));moves=[]
            safe=safe_line_starts(original['lean'])
            for comment in fixed['comments']:
                line=comment['before_line']
                if type(line) is int and 1<=line<=len(original['lean'].splitlines()) and line not in safe:
                    previous=max(n for n in safe if n<line)
                    moves.append(dict(from_line=line,to_line=previous,text=comment['text']))
                    comment['before_line']=previous
            if not moves:
                continue
            try:annotated=insert_comments(original['lean'],fixed['comments'])
            except ValueError:continue
            target=folder/'examples'/tid
            write(target/'comments.json',fixed);(target/'Solution.lean').write_text(annotated)
            write(target/'receipt.json',dict(task_id=tid,comment_integrity='PASS',source_sha256=original['source_sha256'],
                annotated_sha256=sha(annotated),comments=len(fixed['comments']),annotation_issue=fixed['annotation_issue'],
                native_output=str(output.relative_to(folder)),coordinator_comment_position_repairs=moves,
                current_toolchain_verification='pending',compilation_rerun=False))
            chosen[tid]=str(output.relative_to(folder))+' (comment positions repaired)'
            break
    write(folder/'annotation_selection.json',dict(policy='earliest mechanically valid native attempt, preserving completed annotations',selected=len(chosen),rows=chosen))


def main(kind):
    from transformers import AutoTokenizer
    sys.path.insert(0,str(REPO/'src'))
    sys.path.insert(0,str(HERE.parent/'expt_v1/scripts'))
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    tokenizer_path='/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1'
    tok=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True)
    folder=ROOT/('annotations' if kind=='tiny' else 'workbook_annotations')
    manifest=read(RUN/'curriculum/training.jsonl') if kind=='tiny' else read(folder/'manifest.jsonl')
    if kind=='workbook':
        materialize_first_valid(folder,manifest)
    reports,formatted,seen=[],[],{}
    for original in manifest:
        tid=original['task_id'];record=dict(task_id=tid,comment_integrity='FAIL',format_check='NOT_RUN',admitted=False)
        try:
            if kind=='tiny':
                m=re.fullmatch(r'FILE: ([^\n]+)\n```lean\n(.*)```\n',original['messages'][-1]['content'],re.S)
                assert m
                path,source=m.groups()
                annotation_path=folder/'examples'/tid/'comments.json'
                if not annotation_path.exists():annotation_path=folder/'workers'/original['topic']/'annotations'/f'{tid}.json'
                annotations=json.loads(annotation_path.read_text())
                # Earlier workers occasionally included their own -- prefix; preserve it.
                expected=insert_comments(source,annotations,require_sketch=False,allow_existing_prefix=True)
                annotated=(folder/'examples'/tid/'Solution.lean').read_text()
                assert annotated==expected
                receipt_path=RUN/'curriculum/examples'/tid/'receipts/verification.json'
                prior=json.loads(receipt_path.read_text())
                assert prior['accepted'] and prior['lean_sha256']==sha(source)
                assert original['lean_sha256']==sha(source)
                assert prior['checks']['compile_and_axioms']=='PASS'
                assert prior['checks']['differential']==dict(status='PASS',cases=32)
                messages=[dict(m) for m in original['messages'][:2]]
                data=dict(original,source='tiny_curriculum_commented_v8',annotation_model='gpt-5.6-terra',annotation_effort='high')
                record.update(prior_verification='PASS_REUSED_IDENTICAL_CODE',prior_receipt_sha256=sha(receipt_path.read_bytes()),differential_cases_reused=32)
                issue=''
            else:
                if not original['screen_clean']:
                    raise ValueError('protected-screen exclusion')
                source=original['lean'];path=f'/home/user/lean_project/Veribench/{tid}.lean'
                result=json.loads((folder/'examples'/tid/'comments.json').read_text())
                expected=insert_comments(source,result['comments'])
                annotated=(folder/'examples'/tid/'Solution.lean').read_text()
                assert expected==annotated
                issue=result['annotation_issue']
                goal=re.sub(r'\s*:=\s*by\s+sorry\s*$','',original['formal_statement'])
                messages=[dict(role='system',content='You write clear, complete Lean 4 files using Mathlib. Return only the requested FILE marker and one lean code fence. Prove the supplied statement with no sorry, admit, new axioms or native_decide. Include a brief English proof sketch as Lean comments at the top, followed by focused explanations of meaningful proof steps.'),
                    dict(role='user',content=f'Prove the following theorem in a complete Lean 4 file at `{path}`. Preserve its statement and name. Use `import Mathlib` and `open BigOperators Nat Real Rat`.\n\nInformal statement: {original["natural_language_statement"]}\n\n```lean\n{goal}\n```\n\nReturn FILE: {path} followed by a lean code fence containing the complete file.')]
                data=dict(source='lean_workbook_commented_candidates_v8',task_id=tid,source_revision='2e066e310b2c6d2c27616927ae131f82901c8f1c',source_row=original['source_row'],source_split=original['source_split'],proof_index=0,annotation_model='gpt-5.6-terra',annotation_effort='medium',annotation_issue=issue,current_toolchain_verification='pending',training_admitted=False)
                key=sha(re.sub(r'\btheorem\s+\S+', 'theorem TARGET',goal))
                record['duplicate_of']=seen.get(key)
                seen.setdefault(key,tid)
                record['prior_verification']='PUBLIC_CANDIDATE_CURRENT_COMPATIBILITY_PENDING'
            response=f'FILE: {path}\n```lean\n{annotated}```\n'
            assert extract_lean(response,[path],root=RUN/'repo/external/veribench').lean==annotated
            messages.append(dict(role='assistant',content=response))
            template=render(tok,messages[0]['content'],messages[1]['content'],response)
            assert all(template[k] for k in ('byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'))
            record.update(comment_integrity='PASS',format_check='PASS',source_sha256=sha(source),annotated_sha256=sha(annotated),
                n_assistant_tokens=template['n_assistant_tokens'],n_total_tokens=template['n_total_tokens'],
                under_1000_assistant_tokens=template['n_assistant_tokens']<1000,annotation_issue=issue,
                compilation_rerun=False,admitted=kind=='tiny' and template['n_assistant_tokens']<1000)
            data.update(messages=messages,lean_sha256=sha(annotated),response_sha256=sha(response),n_assistant_tokens=template['n_assistant_tokens'])
            if kind!='tiny' or record['admitted']:
                formatted.append(data)
            write(folder/'examples'/tid/'format_receipt.json',record)
        except Exception as exc:
            record['error']=str(exc)
        reports.append(record)
    output=folder/('training.jsonl' if kind=='tiny' else 'normalized_candidates.jsonl')
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in formatted)
    output.write_text(text)
    write(folder/'finalization.json',dict(kind=kind,declared=len(manifest),formatted=len(formatted),
        comment_integrity_pass=sum(r['comment_integrity']=='PASS' for r in reports),format_pass=sum(r['format_check']=='PASS' for r in reports),
        admitted=sum(r['admitted'] for r in reports),annotation_issues=sum(bool(r.get('annotation_issue')) for r in reports),
        under_1000=sum(r.get('under_1000_assistant_tokens',False) for r in reports),
        output_sha256=sha(text),tokenizer_revision='ea980cb0a6c2ae4b936e82123acc929f1cec04c1',compilation_rerun=False,
        rows=reports))
    keys=['task_id','comment_integrity','format_check','admitted','n_assistant_tokens','n_total_tokens','under_1000_assistant_tokens','prior_verification','duplicate_of','annotation_issue','error','source_sha256','annotated_sha256']
    with (folder/'row_results.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(reports)
    print(json.dumps({k:v for k,v in json.loads((folder/'finalization.json').read_text()).items() if k!='rows'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('kind',choices=['tiny','workbook']);args=parser.parse_args();main(args.kind)
