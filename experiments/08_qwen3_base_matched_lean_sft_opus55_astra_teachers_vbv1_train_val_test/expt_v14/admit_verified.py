"""Admit the full verified public-source cohort through comment-only, format, protection and global dedup gates."""
from __future__ import annotations
import collections
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

HERE=Path(__file__).resolve().parent
RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
REPO=RUN/'repo'
ROOT=RUN/'public_gap_sources_v14'
BULK=ROOT/'bulk_validation'
OUT=ROOT/'admission_v2'
EXP=REPO/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test'
CURRENT=RUN/'corpus_training_v12/current/data'
INSPECTOR_SHA='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'
RULES={
 'intro':('introduce quantified arguments and hypotheses','Introduce the next quantified arguments or implication hypotheses.'),
 'rintro':('introduce and unpack hypotheses','Introduce arguments and unpack the displayed hypothesis patterns.'),
 'apply':('apply named lemmas','Apply the displayed lemma, leaving its required premises as new goals.'),
 'rw':('rewrite with displayed equalities','Rewrite the goal or hypotheses using the displayed equalities.'),
 'erw':('rewrite with displayed equalities','Rewrite using the displayed equalities with the tactic\'s elaboration behavior.'),
 'refine':('construct explicit proof terms','Build the displayed proof term, with any placeholders becoming subgoals.'),
 'constructor':('prove constructor fields','Use the goal\'s constructor and prove its required fields.'),
 'cases':('split into constructor cases','Split the displayed value or hypothesis into its constructor cases.'),
 'rcases':('unpack the displayed cases','Unpack the displayed value or hypothesis according to the supplied pattern.'),
 'induction':('use induction','Use induction on the displayed object and prove each resulting case.'),
 'have':('name intermediate facts','Name the displayed intermediate fact for later proof steps.'),
 'obtain':('extract witnesses and hypotheses','Extract the displayed witnesses and hypotheses from the supplied result.'),
 'show':('state the next goal explicitly','State the form of the goal established by the following proof.'),
 'change':('expose definitionally equal goals','Replace the goal by the displayed definitionally equal expression.'),
 'calc':('chain equality or order steps','Chain the displayed equality or order steps using their justifications.'),
 'subst':('substitute equal expressions','Substitute using the displayed equality and continue with the resulting context.'),
 'unfold':('expand named definitions','Expand the named definitions before continuing the proof.'),
 'split':('split the conditional or match','Split the conditional or match expression into its relevant cases.'),
 'assumption':('use available hypotheses','Close the goal using a matching hypothesis already in the context.'),
 'specialize':('instantiate hypotheses','Instantiate the displayed hypothesis with the given arguments.'),
 'rfl':('close reflexive equalities by reduction','Both sides reduce to the same expression, so reflexivity closes the goal.'),
}


def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n');tmp.replace(path)


def read(path):return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod


def exact_comment_roundtrip(original,annotated):
    old=original.splitlines(keepends=True);i=0
    for line in annotated.splitlines(keepends=True):
        if i<len(old) and line==old[i]:i+=1
        else:assert line.lstrip().startswith('-- '),'A non-comment source byte changed'
    assert i==len(old),'Original source bytes missing'


def annotate(source,prep,integrity):
    code=prep.mask_comments_strings(source)
    assert not re.search(r'\b(?:__LINE__|__FILE__|elab|elab_rules|macro|macro_rules|syntax)\b|^\s*#(?:eval|check)',code,re.M),'source-position/metaprogramming context needs its own check'
    safe=integrity.safe_line_starts(source);lines=code.splitlines();events=[]
    for number,line in enumerate(lines,1):
        match=re.match(r'\s*(?:·\s*)?([A-Za-z_]+)\b(.*)',line)
        if not match or number not in safe:continue
        tactic,tail=match.groups()
        if tactic in RULES:events.append((number,*RULES[tactic]))
        elif tactic=='exact':
            term=tail.strip()
            if term=='rfl':events.append((number,*RULES['rfl']))
            elif term.startswith('⟨'):events.append((number,'build explicit constructor values','Build the required constructor value from the displayed components.'))
            elif term.startswith('fun '):events.append((number,'give explicit functions','Give the explicit function on the displayed arguments as the required proof.'))
            else:
                name=re.match(r"[A-Za-z_\u0080-\uffff][A-Za-z_0-9\u0080-\uffff'.]*",term)
                if name:events.append((number,'finish with explicit named proof terms',f'Use the named proof term `{name[0]}` with the displayed arguments.'))
    # Direct term declarations are common in Mathlib; their first identifier is an explicit proof term.
    if not events:
        declarations=list(prep.DECL.finditer(code));assert declarations,'No supported named declaration'
        target=declarations[-1];split=prep.assignment(code,target.end());tail=code[split+2:].lstrip()
        token=re.match(r"(?:\(*\s*)([A-Za-z_\u0080-\uffff][A-Za-z_0-9\u0080-\uffff'.]*)",tail)
        assert token and token[1] not in ('by','where'),'No supported visible proof operation'
        number=code.count('\n',0,target.start())+1;assert number in safe
        if token[1]=='fun':event=('give an explicit function proof','Use the displayed function term as a proof of the quantified statement.')
        elif token[1]=='let':event=('introduce local bindings','Introduce the displayed local bindings, then use the resulting proof term.')
        elif token[1]=='match':event=('construct the proof by cases','Match on the displayed object and provide the proof in each branch.')
        elif token[1]=='if':event=('construct a conditional proof','Use the displayed conditional expression and its branch proofs.')
        elif token[1]=='show':event=('state the proof type explicitly','State the displayed type and provide its explicit proof term.')
        elif token[1]=='calc':event=RULES['calc']
        elif token[1]=='have':event=RULES['have']
        else:event=('apply an explicit named proof term',f'Use the explicit term beginning with `{token[1]}` to prove the stated declaration.')
        events.append((number,*event))
    operations=list(dict.fromkeys(event[1] for event in events))[:4]
    comments=[dict(before_line=1,text='Proof sketch: '+('; '.join(operations)).capitalize()+'.'),
              dict(before_line=1,text='The original formal statements and proof terms are preserved; these comments describe the visible Lean proof operations.')]
    last=-100
    for number,_,explanation in events:
        if number-last>=3:comments.append(dict(before_line=number,text=explanation));last=number
    annotated=integrity.insert_comments(source,comments);exact_comment_roundtrip(source,annotated)
    assert prep.mask_comments_strings(source).split()==prep.mask_comments_strings(annotated).split(),'Non-comment tokens changed'
    return annotated,comments,operations


def statement_key(text,kernel):
    text=kernel.strip_comments(text)
    text=re.sub(r'\s*:=\s*by(?:\s+sorry)?\s*$','',text)
    text=re.sub(r'\b(?:theorem|lemma)\s+\S+','theorem TARGET',text,count=1)
    return ' '.join(text.split())


def main():
    os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['TOKENIZERS_PARALLELISM']='false'
    sys.path[:0]=[str(REPO/'src'),str(EXP/'expt_v1/scripts')]
    from transformers import AutoTokenizer
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen
    frozen=REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py';assert sha(frozen.read_bytes())==INSPECTOR_SHA
    kernel=module('admission_v14_kernel',frozen)
    prep=module('admission_v14_preparer',ROOT/'prepare_candidates.py')
    integrity=module('admission_v14_comment_integrity',EXP/'expt_v8/comment_integrity.py')
    completion=json.loads((BULK/'completion.json').read_text());assert completion['state']=='DONE' and completion['passed']==688
    assert json.loads((BULK/'controls.json').read_text())['passed']
    bulk_manifest=read(BULK/'manifest.jsonl');records={r['task_id']:r for r in bulk_manifest}
    candidates={r['task_id']:r for name in ('mathlib_candidates.jsonl','deepseek_candidates.jsonl') for r in read(ROOT/name)}
    selected=[]
    for item in bulk_manifest:
        receipt=BULK/'checks'/item['task_id']/'result.json';check=json.loads(receipt.read_text())
        if check['passed']:selected.append(dict(item,proof_receipt_sha256=sha(receipt.read_bytes())))
    assert len(selected)==688
    current_receipt=json.loads((CURRENT/'prepare_receipt.json').read_text());assert current_receipt['status']=='PASS'
    current_path=CURRENT/'training.jsonl';assert sha(current_path.read_bytes())==current_receipt['training_sha256']
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'completion.json').exists(),'Admission already frozen'
    (OUT/'driver_snapshot.py').write_bytes(Path(__file__).read_bytes())
    manifest=''.join(json.dumps(r,sort_keys=True)+'\n' for r in selected);(OUT/'manifest.jsonl').write_text(manifest)
    write(OUT/'freeze.json',dict(declared=688,manifest_sha256=sha(manifest),source_counts=dict(collections.Counter(r['source_family'] for r in selected)),
        bulk_completion_sha256=sha((BULK/'completion.json').read_bytes()),current_training_sha256=current_receipt['training_sha256'],
        current_training_rows=current_receipt['rows'],driver_sha256=sha(Path(__file__).read_bytes()),inspector_sha256=INSPECTOR_SHA,
        candidate_sha256={name:sha((ROOT/name).read_bytes()) for name in ('mathlib_candidates.jsonl','deepseek_candidates.jsonl')},
        observed_unix=time.time(),model_calls=0,annotation='deterministic_visible_proof_operations_only'))
    tok=AutoTokenizer.from_pretrained(RUN/'onep7/runs/mixed/hf',local_files_only=True)
    prior=read(current_path);seen_code={};seen_prompt={};seen_statement={}
    for old in prior:
        answer=old['messages'][2]['content'];marker=re.search(r'^FILE:\s*([^\n]+)',answer,re.M);assert marker
        source=extract_lean(answer,[marker[1].strip()],root=REPO/'external/veribench').lean
        uid=old.get('uid',old['task_id']);seen_code.setdefault(' '.join(kernel.strip_comments(source).split()),uid)
        seen_prompt.setdefault(old['messages'][1]['content'],uid)
        if old.get('formal_statement'):seen_statement.setdefault(statement_key(old['formal_statement'],kernel),uid)
    protected={};vb=REPO/'external/veribench'
    for item in csv.DictReader((EXP/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ('validation','test'):
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text()
            protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in read(RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    reports=[];proposed=[]
    for index,item in enumerate(selected):
        tid=item['task_id'];row=candidates[tid];report=dict(task_id=tid,source=row['source'],admitted=False,format='NOT_RUN',comment_integrity='NOT_RUN',kernel_verified=False)
        try:
            assert not item['semantic_risk_flags'],'quarantined source semantic risk: '+str(item['semantic_risk_flags'])
            check=json.loads((BULK/'checks'/tid/'result.json').read_text());assert sha((BULK/'checks'/tid/'result.json').read_bytes())==item['proof_receipt_sha256']
            raw=json.loads(Path(check['kernel_report_path']).read_text())
            assert check['passed'] and kernel.valid_report(raw) and raw['n_theorems']>0 and raw['n_theorems']==raw['n_honest']
            original=(BULK/'sources'/tid/'Solution.lean').read_text()
            assert sha(original)==row['source_sha256']==item['source_sha256']==raw['source_sha256']
            assert sha((Path(raw['evidence_dir'])/'original.olean').read_bytes())==raw['compiled_module_sha256']
            assert item['exact_source_context_verified'];report['kernel_verified']=True
            annotated,comments,operations=annotate(original,prep,integrity);report['comment_integrity']='PASS'
            path=f'/home/lean_project/Veribench/{tid}.lean';answer=f'FILE: {path}\n```lean\n{annotated}```\n'
            assert extract_lean(answer,[path],root=vb).lean==annotated,'frozen FILE extractor changed source bytes'
            messages=[*row['messages'][:2],dict(role='assistant',content=answer)]
            rendered=render(tok,messages[0]['content'],messages[1]['content'],answer)
            assert all(rendered[k] for k in ('byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'))
            prefix=tok.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True)
            aids=tok.encode('<think>\n\n</think>\n\n'+answer+'<|im_end|>\n'+tok.eos_token,add_special_tokens=False)
            total=len(tok.encode(prefix,add_special_tokens=False))+len(aids);assert total<=16384
            code_key=' '.join(kernel.strip_comments(original).split());stmt=statement_key(row['formal_statement'],kernel)
            duplicate=seen_code.get(code_key) or seen_prompt.get(messages[1]['content']) or seen_statement.get(stmt)
            if duplicate:report['duplicate_of']=duplicate;raise ValueError('lexical duplicate against frozen prior/current admitted pool')
            new=dict(row,messages=messages,source=row['source']+'_visible_step_comments_v14',pool='public_proof',
                lean_sha256=sha(annotated),response_sha256=sha(answer),original_source_sha256=sha(original),original_response_sha256=row['response_sha256'],
                current_kernel_verified=True,verification_basis='v14_exact_kernel_artifact_plus_comment_only_roundtrip',
                n_assistant_tokens=rendered['n_assistant_tokens'],n_total_tokens=total,training_admitted=False,
                semantic_review='formal_exercise_only_no_English_alignment_claim',annotation_method='deterministic_visible_proof_operations',
                needs_comment_policy_check=False,admission_pending=[])
            folder=OUT/'examples'/tid;folder.mkdir(parents=True,exist_ok=True);(folder/'Solution.lean').write_text(annotated)
            write(folder/'comment_binding.json',dict(task_id=tid,original_source_sha256=sha(original),annotated_source_sha256=sha(annotated),
                proof_receipt=str(BULK/'checks'/tid/'result.json'),proof_receipt_sha256=item['proof_receipt_sha256'],
                compiled_module_sha256=raw['compiled_module_sha256'],comments=comments,operations=operations,
                exact_original_byte_roundtrip=True,noncomment_tokens_equal=True,annotated_source_recompiled=False))
            new.update(comment_binding_receipt=str(folder/'comment_binding.json'),comment_binding_receipt_sha256=sha((folder/'comment_binding.json').read_bytes()),
                kernel_report_path=check['kernel_report_path'])
            report.update(format='PASS',lean_sha256=sha(annotated),original_source_sha256=sha(original),loss_tokens=len(aids),total_tokens=total)
            proposed.append((new,code_key,stmt))
            # Reserve against other proposed rows too; exclusions are conservative lexical redundancy.
            seen_code[code_key]=tid;seen_prompt[messages[1]['content']]=tid;seen_statement[stmt]=tid
        except Exception as exc:report['exclusion']=str(exc) or type(exc).__name__
        reports.append(report)
        if (index+1)%50==0:write(OUT/'progress.json',dict(state='CHECKING',declared=688,checked=index+1,proposed=len(proposed),observed_unix=time.time()))
    full=screen({r['task_id']:r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for r,_,_ in proposed},protected)
    statements=screen({r['task_id']:r['formal_statement'] for r,_,_ in proposed},protected)
    write(OUT/'protected_screen.json',dict(full=full,statements=statements,protected_references=764))
    clean=set(full['clean_ids'])&set(statements['clean_ids']);byid={r['task_id']:r for r in reports};admitted=[]
    for row,_,_ in proposed:
        report=byid[row['task_id']]
        if row['task_id'] not in clean:report['exclusion']='protected exact/near screen';continue
        row['training_admitted']=True;report['admitted']=True;admitted.append(row)
    data=''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in admitted);(OUT/'training.jsonl').write_text(data)
    keys=['task_id','source','admitted','kernel_verified','comment_integrity','format','lean_sha256','original_source_sha256','loss_tokens','total_tokens','duplicate_of','exclusion']
    with (OUT/'row_results.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(reports)
    summary=dict(state='DONE',declared=688,accounted=len(reports),admitted=len(admitted),
        admitted_by_source=dict(collections.Counter(row['source'] for row in admitted)),
        exclusions=dict(collections.Counter(r.get('exclusion') for r in reports if not r['admitted'])),
        training_sha256=sha(data),assistant_loss_tokens=sum(r['loss_tokens'] for r in reports if r['admitted']),
        protected_references=764,protected_full_exact=full['n_exact'],protected_full_near=full['n_near'],
        protected_statement_exact=statements['n_exact'],protected_statement_near=statements['n_near'],
        dedup_prior_rows=len(prior),dedup_prior_sha256=current_receipt['training_sha256'],model_calls=0,
        original_sources_recompiled=False,formal_receipts_revalidated=True,comment_only_byte_roundtrips=True,
        observed_unix=time.time(),test_split_evaluated=False)
    assert len(reports)==688 and len(admitted)>=20,'Unexpectedly few admissions; investigate before use'
    write(OUT/'completion.json',summary);write(OUT/'progress.json',summary);print(json.dumps(summary,sort_keys=True),flush=True)


if __name__=='__main__':main()
