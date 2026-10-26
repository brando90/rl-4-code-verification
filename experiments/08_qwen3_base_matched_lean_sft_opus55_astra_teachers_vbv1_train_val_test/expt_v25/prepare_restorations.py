"""Compose original automation proof terms into exact V20 contexts, with no teacher calls."""
from collections import Counter, defaultdict
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from audit_counterparts import RUN, ROOT, EXP, lean, read, sha, module


def setup():
    kernel=module('restoration_kernel',RUN/'repo/external/veribench_scorer/scripts/scsc/kernel_axioms.py')
    prep=module('restoration_mask',RUN/'public_gap_sources_v14/prepare_candidates.py')
    return kernel,prep


def stage():
    rows=read(RUN/'corpus_training_v20/base/data/training.jsonl')
    candidates=read(ROOT/'counterpart_audit/candidates.jsonl')
    paths=[]
    for item in candidates:
        folder=ROOT/'counterpart_sources'/f'{item["index"]:04d}';folder.mkdir(parents=True,exist_ok=True)
        for name,source in [('Baseline.lean',lean(rows[item['index']])),('Original.lean',item['original_lean'])]:
            path=folder/name
            if path.exists():assert path.read_text()==source
            else:path.write_text(source)
            paths.append(str(path))
    listing=ROOT/'counterpart_sources/source_paths.txt';listing.write_text('\n'.join(paths)+'\n')
    env=dict(os.environ,PATH=str(RUN/'bin')+':/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin:'+os.environ['PATH'],CUDA_VISIBLE_DEVICES='')
    sys.path.insert(0,str(EXP/'expt_v24/future_logging'))
    from durable_capture import DurableCapture
    capture=DurableCapture(ROOT/'counterpart_sources/parser_diagnostics','/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin/lean',dict(scope='Syntax-only range extraction, no theorem elaboration',source_list_sha256=sha(listing.read_bytes())))
    result=capture.run_logged(['lake','env','lean','--run',str(EXP/'expt_v13/proof_ranges.lean'),str(listing)],capture_output=True,text=True,cwd=str(RUN/'grading'),env=env,timeout=900,check=False)
    assert result.returncode==0,result.stderr
    (ROOT/'counterpart_sources/parse_results.jsonl').write_text(result.stdout)
    print(json.dumps(dict(parsed_files=len(paths),native_parser_exit=result.returncode)))


EXPLANATIONS={
 'simp':'Simplify using the displayed definitions, hypotheses and simplification lemmas.',
 'simpa':'Simplify the goal and the displayed proof to the same proposition.',
 'omega':'Discharge the displayed linear natural-number or integer arithmetic goals.',
 'linarith':'Combine the available linear equalities and inequalities to prove the goal.',
 'nlinarith':'Use the displayed polynomial relations and arithmetic inequalities.',
 'ring':'Normalize the displayed polynomial expressions to establish the identity.',
 'ring_nf':'Normalize the displayed polynomial expressions before continuing.',
 'norm_num':'Evaluate and normalize the displayed numerical expressions.',
 'decide':'Evaluate the decidable proposition and construct its checked proof.',
 'exact?':'Search for a matching proof term, which Lean then checks.',
 'apply?':'Search for an applicable lemma and discharge its required goals.',
 'aesop':'Search the displayed proof context using the tactic rules and checked proof terms.',
}


def compose():
    kernel,prep=setup()
    parsed={}
    for line in (ROOT/'counterpart_sources/parse_results.jsonl').read_text().splitlines():
        try:record=json.loads(line)
        except json.JSONDecodeError:continue
        if 'path' in record:parsed[record['path']]=record
    assert len(parsed)==4480,len(parsed)
    rows=read(RUN/'corpus_training_v20/base/data/training.jsonl')
    reports=[];changed=[]
    def ranges(path,source):
        record=parsed[str(path)];assert not record.get('error'),record.get('error')
        raw=source.encode();result=[]
        for span in record['ranges']:
            if span['kind'].endswith('.example'):continue
            a,b=span['start_byte'],span['end_byte'];c=span['command_start_byte']
            header=raw[c:a].decode();key=' '.join(kernel.strip_comments(header,keep_literals=True).split())
            body=raw[a:b].decode();result.append(dict(span,key=key,body=body))
        return result
    def header_update(source,tactics):
        description='; '.join(EXPLANATIONS.get(t.rstrip('?!'),f'Use the displayed `{t}` tactic and its checked proof term.') for t in sorted(tactics))
        replacement='/- Proof sketch:\nPreserve the supplied declarations, assumptions and conclusions.\nThe marked restored proofs use their original tactics: '+', '.join(sorted(tactics))+'.\nTheir displayed proof steps perform the operations explained immediately below.\n-/ '
        count=0
        def replace_block(match):
            nonlocal count
            if re.search(r'proof\s+sketch\s*:',match[0],re.I):count+=1;return replacement
            return match[0]
        source=re.sub(r'/\-.*?\-/',replace_block,source,flags=re.S)
        # Mechanically inserted V14 sketches use consecutive line comments.
        source,n=re.subn(r'(?im)^[ \t]*--[ \t]*Proof sketch:[^\n]*(?:\n[ \t]*--[^\n]*)*',
            '-- Proof sketch: Preserve the supplied statements and context.\n-- The marked restored proofs use their original tactics: '+', '.join(sorted(tactics))+'.',source,count=1)
        return source,count+n
    for item in read(ROOT/'counterpart_audit/candidates.jsonl'):
        index=item['index'];row=rows[index];folder=ROOT/'counterpart_sources'/f'{index:04d}'
        baseline=(folder/'Baseline.lean').read_text();original=(folder/'Original.lean').read_text()
        report=dict(index=index,uid=row['uid'],pool=row['pool'],task_id=row['task_id'],state='UNCHANGED_PAIRING_GAP')
        try:
            current_spans=ranges(folder/'Baseline.lean',baseline);original_spans=ranges(folder/'Original.lean',original)
            groups=defaultdict(list)
            for span in original_spans:groups[span['key']].append(span)
            edits=[];restored=[];unsafe=[];used=Counter()
            for span in current_spans:
                key=span['key'];position=used[key];used[key]+=1
                if position>=len(groups[key]):continue
                prior=groups[key][position];code=kernel.strip_comments(prior['body'],keep_literals=True)
                hits=sorted(set(prep.TACTICS.findall(code)))
                if not hits or kernel.strip_comments(span['body'],keep_literals=True).split()==code.split():continue
                if 'native_decide' in hits or re.search(r'\b(?:sorry|admit|axiom)\b',code):
                    unsafe.append(dict(statement=key,automation=hits,reason='Original named proof violates unchanged honesty/no-holes policy'));continue
                explanation=' '.join(EXPLANATIONS.get(t.rstrip('?!'),f'Apply the displayed `{t}` tactic and check the resulting proof term.') for t in hits)
                edits.append((span['start_byte'],span['end_byte'],prior['body'].encode()))
                edits.append((span['command_start_byte'],span['command_start_byte'],('-- Restored original proof: '+explanation+'\n').encode()))
                restored.append(dict(statement=key,automation=hits,original_proof_sha256=sha(prior['body']),baseline_proof_sha256=sha(span['body'])))
            report.update(restored_proofs=restored,unsafe_original_slots_kept_baseline=unsafe)
            if not restored:raise ValueError('No admissible different original automation-containing proof span')
            raw=baseline.encode()
            for a,b,replacement in sorted(edits,key=lambda x:(x[0],x[1]),reverse=True):raw=raw[:a]+replacement+raw[b:]
            variant=raw.decode()
            tactics={t for proof in restored for t in proof['automation']}
            annotated,header_changes=header_update(variant,tactics)
            assert kernel.strip_comments(variant,keep_literals=True).split()==kernel.strip_comments(annotated,keep_literals=True).split(),'Comment adaptation changed tokens'
            (folder/'Candidate.lean').write_text(annotated)
            report.update(state='PENDING_FULL_SOURCE_VERIFICATION',restored_tactics=sorted(tactics),candidate_sha256=sha(annotated),baseline_sha256=sha(baseline),original_sha256=sha(original),proof_sketch_adaptations=header_changes,
                nonproof_source_bytes_preserved_before_comment_adaptation=True,comment_adaptation_noncomment_tokens_identical=True,
                source_path=str(folder/'Candidate.lean'))
            changed.append(report)
        except Exception as exc:report['reason']=str(exc)
        reports.append(report)
    out=ROOT/'restoration_candidates';out.mkdir(exist_ok=True)
    (out/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reports))
    (out/'pending.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in changed))
    summary=dict(state='PREVERIFICATION_NOT_TRAINING_ADMISSION',candidate_rows=len(changed),candidate_by_pool=dict(Counter(r['pool'] for r in changed)),
        baseline_rows_kept_without_change=3568-len(changed),gaps=dict(Counter(r.get('reason','') for r in reports if r['state']=='UNCHANGED_PAIRING_GAP')),
        restored_proof_spans=sum(len(r['restored_proofs']) for r in changed),unsafe_original_slots_kept_baseline=sum(len(r.get('unsafe_original_slots_kept_baseline',[])) for r in reports),
        tactic_rows=dict(Counter(t for r in changed for t in r['restored_tactics'])),compiler_calls_for_candidate_theorems=0,model_calls=0)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('stage','compose'));args=parser.parse_args()
    stage() if args.phase=='stage' else compose()
