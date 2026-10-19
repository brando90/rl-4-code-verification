"""Revisit every Workbook and tiny task, preferring saved proofs without broad automation."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE=Path(__file__).resolve().parent
V8=HERE.parent/'expt_v8'
sys.path.insert(0,str(V8))
import annotate_workbook as base

RUN=base.RUN
ROOT=RUN/'lean_corpus_v9'
BASELINE=RUN/'lean_corpus_v8'
AUTOMATION=('exact?','apply?','simp?','simpa?','simp_all','simp','simpa','omega','aesop','aesop?',
            'linarith','nlinarith','ring_nf','ring','norm_num','decide','native_decide','tauto',
            'positivity','field_simp','fun_prop','omega?','exact_mod_cast','norm_cast','norm_num1','decide!',
            'solve_by_elim','apply_rules','simp_rw','ring1','abel','grind','polyrith','finish','itauto',
            'simp_arith','norm_num!','linarith!','nlinarith!','aesop_cat')
PATTERN=re.compile(r"(?<![A-Za-z0-9_'])("+'|'.join(re.escape(x) for x in sorted(AUTOMATION,key=len,reverse=True))+r")(?![A-Za-z0-9_'])")


def automations(source):
    source=re.sub(r'/\-.*?\-/|--[^\n]*',' ',source,flags=re.S)
    return sorted(set(PATTERN.findall(source)))


def assemble(row,proof):
    statement=row['formal_statement']
    match=re.search(r'sorry\s*$',statement)
    assert match and re.search(r':=\s*by\s+sorry\s*$',statement)
    return ('import Mathlib\nopen BigOperators Nat Real Rat\n\n'+statement[:match.start()].rstrip()+'\n'
            +''.join('  '+line+'\n' for line in proof.splitlines()))


def tiny_parts(source):
    """Parse the restricted top-level tiny-file layout; reject unsupported shapes."""
    source=re.sub(r'/\-.*?\-/|--[^\n]*','',source,flags=re.S)
    starts=list(re.finditer(r'^(?:theorem|lemma|example|end)\b',source,re.M))
    ranges=[]
    for i,start in enumerate(starts):
        if start.group()=='end':continue
        finish=starts[i+1].start() if i+1<len(starts) else len(source)
        command=source[start.start():finish]
        marker=command.find(':=')
        if marker<0:raise ValueError('unsupported theorem shape')
        a=start.start()+marker+2
        ranges.append((a,finish))
    if not ranges:raise ValueError('no proof declarations')
    pieces=[];last=0
    for a,b in ranges:pieces.append(source[last:a]);pieces.append(' PROOF\n');last=b
    pieces.append(source[last:])
    skeleton=' '.join(''.join(pieces).split())
    return source,skeleton,ranges


def prepare():
    if (ROOT/'selection.jsonl').exists():raise RuntimeError('selection already frozen')
    ROOT.mkdir(parents=True,exist_ok=True)
    source=BASELINE/'sources/lean_workbook/lean_workbook.json'
    assert base.sha(source.read_bytes())==base.SOURCE_SHA
    workbook=json.loads(source.read_text())
    oldrows={r['task_id']:r for r in base.read_rows(BASELINE/'workbook_annotations/manifest.jsonl')}
    records=[]
    for index,item in enumerate(workbook):
        if not item.get('proof'):continue
        tid=f'workbook_{index:06d}'
        if not oldrows[tid]['screen_clean']:continue
        alternatives=item['proof']
        clean=[i for i,proof in enumerate(alternatives) if not automations(proof)]
        chosen=0 if 0 in clean else clean[0] if clean else 0
        lean=assemble(item,alternatives[chosen])
        old=BASELINE/'workbook_annotations/examples'/tid
        baseline_issue=''
        if (old/'comments.json').exists():baseline_issue=json.loads((old/'comments.json').read_text())['annotation_issue']
        records.append(dict(task_id=tid,kind='workbook',source_row=index,source_split=item['split'],
            natural_language_statement=item['natural_language_statement'],tags=item['tags'],formal_statement=item['formal_statement'],
            proof_index=chosen,proof=alternatives[chosen],lean=lean,source_sha256=base.sha(lean),
            baseline_source_sha256=oldrows[tid]['source_sha256'],changed=chosen!=0,alternatives=len(alternatives),
            qualifying_alternatives=clean,automation=automations(alternatives[chosen]),no_qualifying_alternative=not bool(clean),
            baseline_annotation_issue=baseline_issue,baseline_comment_folder=str(old),screen_clean=True,
            verification='public_candidate_current_compatibility_pending'))
    tiny_rows=base.read_rows(RUN/'curriculum/training.jsonl')
    originals={r['task_id']:r for r in tiny_rows}
    candidates=collections.defaultdict(list)
    for path in (RUN.parent/'rl4cv_tiny_curriculum').rglob('Solution.lean'):
        if path.parent.name in originals:candidates[path.parent.name].append(path)
    for row in tiny_rows:
        tid=row['task_id']
        match=re.fullmatch(r'FILE: [^\n]+\n```lean\n(.*)```\n',row['messages'][-1]['content'],re.S)
        assert match
        source_lean=match.group(1)
        original,skeleton,ranges=tiny_parts(source_lean)
        saved=[]
        for path in sorted(candidates[tid]):
            try:
                code,key,spans=tiny_parts(path.read_text())
                if key==skeleton and len(spans)==len(ranges):saved.append((path,code,spans))
            except (ValueError,UnicodeError):continue
        new=[];last=0;replacements=[]
        for n,(a,b) in enumerate(ranges):
            proof=original[a:b]
            replacement=None
            if automations(proof):
                for path,code,spans in saved:
                    alternative=code[slice(*spans[n])]
                    if not automations(alternative):
                        replacement=(path,alternative)
                        break
            new.append(original[last:a]);new.append(replacement[1] if replacement else proof);last=b
            if replacement:replacements.append(dict(proof_block=n,source_path=str(replacement[0]),proof_sha256=base.sha(replacement[1])))
        new.append(original[last:]);lean=''.join(new)
        if not replacements:lean=source_lean
        assert tiny_parts(lean)[1]==skeleton
        records.append(dict(task_id=tid,kind='tiny',topic=row['topic'],natural_language_statement=row['messages'][1]['content'],
            tags=[row['topic']],lean=lean,source_sha256=base.sha(lean),baseline_source_sha256=base.sha(source_lean),
            changed=bool(replacements),alternatives=len(saved)+1,replacements=replacements,automation=automations(lean),
            no_qualifying_alternative=bool(automations(lean)),baseline_annotation_issue='',
            baseline_comment_folder=str(BASELINE/'annotations/examples'/tid),screen_clean=True,
            verification='replacement_verification_pending' if replacements else 'prior_verified_identical_source'))
    assert len(records)==13323
    (ROOT/'selection.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    counts={kind:dict(rows=sum(r['kind']==kind for r in records),changed=sum(r['kind']==kind and r['changed'] for r in records),
        no_qualifying_alternative=sum(r['kind']==kind and r['no_qualifying_alternative'] for r in records),
        flagged_for_sol=sum(r['kind']==kind and bool(r['baseline_annotation_issue']) for r in records)) for kind in ('workbook','tiny')}
    base.write(ROOT/'selection_summary.json',dict(counts=counts,avoid_tactics=list(AUTOMATION),
        policy='prefer an existing automation-free proof for the identical statement; retain and flag if none exists',
        initial_model='gpt-5.6-terra',initial_effort='medium',review_model='gpt-6.1-sol',review_effort='high',
        proof_creation=False,source_sha256=base.SOURCE_SHA,selector_sha256=base.sha(Path(__file__).read_bytes())))
    print((ROOT/'selection_summary.json').read_text(),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare']);a=ap.parse_args();prepare()
