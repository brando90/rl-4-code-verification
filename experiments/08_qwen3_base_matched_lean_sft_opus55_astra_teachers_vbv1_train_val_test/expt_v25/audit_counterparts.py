"""Inventory exact V20 row lineages before prospective restoration; no compiler/model calls."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
ROOT=RUN/'corpus_training_v25'
EXP=RUN/'repo/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test'

def sha(s):return hashlib.sha256(s if isinstance(s,bytes) else s.encode()).hexdigest()
def read(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def lean(row):
    answer=row['messages'][-1]['content'];m=re.search(r'^FILE:\s*([^\n]+)\n```lean\n(.*)```\s*$',answer,re.M|re.S)
    assert m,row['task_id']
    return m[2]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main():
    ROOT.mkdir(exist_ok=True)
    kernel=module('counterpart_frozen_kernel',RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py')
    prep=module('counterpart_lex',RUN/'public_gap_sources_v14/prepare_candidates.py')
    policy=prep.TACTICS
    original_path=RUN/'onep7/data/existing.jsonl'
    existing=read(original_path)
    workbook_path=RUN/'lean_corpus_v8/workbook_annotations/manifest.jsonl'
    workbook={r['task_id']:r for r in read(workbook_path)}
    annotated_path=RUN/'lean_corpus_v8/workbook_annotations/normalized_candidates.jsonl'
    annotated={r['task_id']:r for r in read(annotated_path)}
    current_path=RUN/'corpus_training_v20/base/data/training.jsonl'
    rows=read(current_path);assert len(rows)==3568
    reports=[];candidates=[]
    for index,row in enumerate(rows):
        current=lean(row);report=dict(index=index,uid=row['uid'],pool=row['pool'],task_id=row['task_id'],v20_lean_sha256=sha(current),v20_response_sha256=row['response_sha256'],status='UNCHANGED_NO_PROOF_CLEANUP_PREDECESSOR')
        if row['pool']=='python':
            old=existing[row['example_index']];assert old['task_id']==row['task_id'];assert old['response_sha256']==row['original_response_sha256']
            original=lean(old);report.update(counterpart_path=str(original_path),counterpart_index=row['example_index'],counterpart_response_sha256=old['response_sha256'],same_original_prompt=old['messages'][:2]==row['messages'][:2])
        elif row['pool'] in ('workbook','repair'):
            old=workbook[row['task_id']];assert old['source_row']==row['source_row'];assert old['formal_statement']==row['formal_statement']
            original=old['lean'];assert sha(original)==old['source_sha256']
            report.update(counterpart_path=str(workbook_path),counterpart_index=row['source_row'],counterpart_lean_sha256=sha(original),counterpart_proof_index=0)
            if row['task_id'] in annotated:
                prior=annotated[row['task_id']];prior_source=lean(prior)
                assert kernel.strip_comments(prior_source).split()==kernel.strip_comments(original).split()
                report.update(annotated_counterpart_path=str(annotated_path),annotated_counterpart_sha256=sha(prior_source),prior_annotation_issue=prior.get('annotation_issue',''))
        else:
            report['public_source_previously_automation_free']=True
            reports.append(report);continue
        report['counterpart_lean_sha256']=sha(original)
        original_code=kernel.strip_comments(original)
        current_code=kernel.strip_comments(current)
        report['original_automation']=sorted(set(policy.findall(original_code)))
        report['noncomment_source_changed']=original_code.split()!=current_code.split()
        report['contains_holes_or_declared_axioms']=bool(re.search(r'\b(?:sorry|admit|axiom)\b',original_code))
        if report['noncomment_source_changed']:
            report['status']='RESTORATION_CANDIDATE_REQUIRES_PROOF_SPAN_AND_KERNEL_BINDING'
            candidates.append(dict(index=index,uid=row['uid'],pool=row['pool'],task_id=row['task_id'],original_lean=original))
        else:
            report['status']='UNCHANGED_IDENTICAL_NONCOMMENT_SOURCE'
        reports.append(report)
    out=ROOT/'counterpart_audit';out.mkdir(exist_ok=True)
    (out/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reports))
    (out/'candidates.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in candidates))
    summary=dict(status='INVENTORY_ONLY_NOT_TRAINING_ADMISSION',rows=3568,by_pool=dict(Counter(r['pool'] for r in reports)),statuses=dict(Counter(r['status'] for r in reports)),candidate_by_pool=dict(Counter(r['pool'] for r in candidates)),missing_counterparts=0,model_calls=0,compiler_calls=0,cohort_dropped=0,
        source_sha256={str(p):sha(p.read_bytes()) for p in (current_path,original_path,workbook_path,annotated_path)})
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
