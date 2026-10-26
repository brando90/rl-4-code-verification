"""Freeze all currently admissible conversations after source, comment, format, overlap and deduplication checks."""
from __future__ import annotations
import collections
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training')
ROOT=RUN/'corpus_training_v12'
START=RUN/'onep7/runs/mixed/hf'
SEED=20261019
EXISTING_SHA='7fa0255741a2b6046ceda0dfda43664334ca603a0aeca9fc2424af43c849726b'
INSPECTOR_SHA='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()
def read(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def comments_only(original,annotated):
    """Recover every original byte while permitting only inserted full-line comments."""
    old=original.splitlines(keepends=True);new=annotated.splitlines(keepends=True);i=0
    for line in new:
        if i<len(old) and line==old[i]:i+=1
        else:assert line.lstrip().startswith('-- '),'non-comment source edit'
    assert i==len(old),'lost original source'
def statement_key(statement):
    return ' '.join(re.sub(r'\btheorem\s+\S+','theorem TARGET',statement,count=1).split())

def main():
    os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    from transformers import AutoTokenizer
    sys.path[:0]=[str(REPO/'src'),str(HERE.parent/'expt_v1/scripts')]
    from template_check import render
    from rl4cv.veribench.exp103 import extract_lean
    from rl4cv.screens import screen
    spec=importlib.util.spec_from_file_location('frozen_kernel_v12',REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py')
    kernel=importlib.util.module_from_spec(spec);sys.modules[spec.name]=kernel;spec.loader.exec_module(kernel)
    assert digest(spec.origin)==INSPECTOR_SHA
    ROOT.mkdir(parents=True,exist_ok=True);data=ROOT/'current/data';data.mkdir(parents=True,exist_ok=True)
    assert not (data/'prepare_receipt.json').exists(),'Frozen preparation exists; do not replace it'
    initial=json.loads((RUN/'onep7/runs/mixed/weights_manifest.json').read_text())
    for name,h in initial.items():assert digest(START/name)==h,name
    write(data/'initial_manifest.json',initial)
    tok=AutoTokenizer.from_pretrained(START,local_files_only=True)
    base=AutoTokenizer.from_pretrained('/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1',local_files_only=True)
    prior=RUN/'lean_corpus_v9';v10=RUN/'lean_corpus_v10';v11=RUN/'lean_corpus_v11'
    receipt9={r['task_id']:r for r in json.loads((prior/'finalization.json').read_text())['rows']}
    selections={r['task_id']:r for r in read(prior/'selection.jsonl')}
    verified10={r['task_id']:r for r in csv.DictReader((v10/'row_results.csv').open()) if r['passed']=='True'}
    assert len(verified10)==9895
    existing=RUN/'onep7/data/existing.jsonl';assert digest(existing)==EXISTING_SHA
    pools=[('python',read(existing)),('tiny',read(prior/'final/tiny_training.jsonl')),
           ('workbook',read(prior/'final/workbook_candidates.jsonl')),('repair',read(v11/'final/repaired_training.jsonl'))]
    assert [len(r) for _,r in pools]==[2585,500,11667,61]
    candidates=[];reports=[]
    for pool,rows in pools:
        for index,row0 in enumerate(rows):
            row=dict(row0);tid=row['task_id'];uid=f'{pool}:{index:05d}:{tid}'
            report=dict(uid=uid,task_id=tid,pool=pool,source=row['source'],admitted=False)
            try:
                answer=row['messages'][-1]['content'];assert sha(answer.encode())==row['response_sha256']
                marker=re.search(r'^FILE:\s*([^\n]+)',answer,re.M);assert marker
                lean=extract_lean(answer,[marker[1].strip()],root=REPO/'external/veribench').lean
                assert sha(lean.encode())==row['lean_sha256'],(tid,'annotated Lean SHA')
                proof_basis='prior_original_pool_admission'
                if pool in ('tiny','workbook'):
                    old=receipt9[tid];assert old['format_check']=='PASS' and old['comment_integrity']=='PASS'
                    assert old['annotated_sha256']==sha(lean.encode())
                    if pool=='tiny':
                        raw=(RUN/'curriculum/examples'/tid/'Solution.lean').read_text()
                        accepted=json.loads((RUN/'curriculum/examples'/tid/'receipts/verification.json').read_text())
                        assert accepted['accepted'] and accepted['lean_sha256']==sha(raw.encode())
                        proof_basis='prior_tiny_kernel_and_32_differential_tests'
                    elif old['kernel_verified']:
                        case=prior/'review/cases'/tid;decision=json.loads((case/'decision.json').read_text())
                        check=json.loads((case/'checks'/f'proof_{decision["proof_index"]:02d}'/'result.json').read_text())
                        assert check['passed'] and kernel.valid_report(check['kernel_report'])
                        assert check['kernel_report']['source_sha256']==old['source_sha256']==check['source_sha256']
                        # The pinned source whose bytes were compiled is retained in the check directory.
                        raw=(case/'checks'/f'proof_{decision["proof_index"]:02d}'/'Solution.lean').read_text() if (case/'checks'/f'proof_{decision["proof_index"]:02d}'/'Solution.lean').exists() else None
                        if raw is None:
                            # Recover inserted comments against exact proof-source snapshot recorded by V9.
                            source_path=Path(check['kernel_report']['path']);raw=source_path.read_text()
                        assert sha(raw.encode())==old['source_sha256']
                        proof_basis='v9_pinned_kernel'
                    else:
                        assert tid in verified10,'no successful current proof receipt'
                        check=json.loads((v10/'checks'/tid/'result.json').read_text())
                        k=json.loads((v10/'checks'/tid/'kernel_report.json').read_text())
                        raw=(v10/'sources'/tid/'Solution.lean').read_text()
                        assert check['passed'] and kernel.valid_report(k) and k['n_theorems']>=1 and k['n_theorems']==k['n_honest']
                        assert sha(raw.encode())==old['source_sha256']==check['source_sha256']==k['source_sha256']
                        proof_basis='v10_pinned_kernel'
                    comments_only(raw,lean);report['unannotated_sha256']=sha(raw.encode())
                elif pool=='repair':
                    case=v11/'cases'/tid;decision=json.loads((case/'decision.json').read_text());h=sha(lean.encode())
                    check=json.loads((case/'checks'/h/'result.json').read_text())
                    assert decision['verified'] and decision['source_sha256']==h and check['passed'] and kernel.valid_report(check['kernel_report'])
                    assert check['kernel_report']['source_sha256']==h
                    proof_basis='v11_pinned_kernel'
                messages=row['messages'];assert [m['role'] for m in messages]==['system','user','assistant']
                rendered=render(tok,messages[0]['content'],messages[1]['content'],answer)
                assert all(rendered[k] for k in ('byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'))
                if pool=='tiny':assert rendered['n_assistant_tokens']<1000
                prefix=tok.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True)
                assert prefix==base.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True)
                pids=tok.encode(prefix,add_special_tokens=False)
                response='<think>\n\n</think>\n\n'+answer+'<|im_end|>\n'
                aids=tok.encode(response+tok.eos_token,add_special_tokens=False)
                assert len(pids)+len(aids)<=16384 and len(aids)==rendered['n_assistant_tokens']+1
                row.update(uid=uid,pool=pool,n_assistant_tokens=rendered['n_assistant_tokens'],n_total_tokens=len(pids)+len(aids),verification_basis=proof_basis)
                row['_tokens']=dict(uid=uid,task_id=tid,pool=pool,source=row['source'],ids=pids+aids,prompt=len(pids),loss_tokens=len(aids))
                report.update(source_sha256=sha(lean.encode()),proof_basis=proof_basis,format='PASS',loss_tokens=len(aids),total_tokens=len(pids)+len(aids))
                candidates.append(row)
            except Exception as exc:report['exclusion']=str(exc)
            reports.append(report)
            if len(reports)%500==0:write(ROOT/'assembly_progress.json',dict(completed=len(reports),formatted=len(candidates),observed_unix=time.time()))
    write(ROOT/'assembly_integrity.json',dict(candidates_by_pool=dict(collections.Counter(r['pool'] for r in candidates)),failures=[r for r in reports if 'exclusion' in r],observed_unix=time.time()))
    assert sum(r['pool']=='python' for r in candidates)==2585,'original pool format failure'
    assert sum(r['pool']=='tiny' for r in candidates)==500,'tiny integrity failure'
    assert sum(r['pool']=='workbook' for r in candidates)==10567,'Workbook receipt/integrity failure'
    assert sum(r['pool']=='repair' for r in candidates)==61,'repair integrity failure'
    protected={};vb=REPO/'external/veribench'
    for item in csv.DictReader((HERE.parent/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
        if item['split'] in ('validation','test'):
            protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text()
            protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
    for item in read(RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
        if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
    assert len(protected)==764
    screening=screen({r['uid']:r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for r in candidates},protected)
    write(data/'protected_screen.json',screening);clean=set(screening['clean_ids']);seen_responses={};seen_statements={};admitted=[];byuid={r['uid']:r for r in reports}
    for row in candidates:
        report=byuid[row['uid']];statement=statement_key(row['formal_statement']) if row.get('formal_statement') else None
        duplicate=seen_responses.get(row['response_sha256']) or (seen_statements.get(statement) if statement else None)
        if row['uid'] not in clean:report['exclusion']='protected_screen';continue
        if duplicate:report.update(exclusion='duplicate',duplicate_of=duplicate);continue
        seen_responses[row['response_sha256']]=row['uid']
        if statement:seen_statements[statement]=row['uid']
        report['admitted']=True;admitted.append(row)
    tokens=[];output=[]
    for row in admitted:
        token=row.pop('_tokens');token['index']=len(tokens);tokens.append(token);output.append(row)
    text=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output);(data/'training.jsonl').write_text(text)
    torch.save(tokens,data/'tokens.pt')
    write(data/'token_manifest.json',[{k:v for k,v in t.items() if k!='ids'}|dict(ids_sha256=sha(json.dumps(t['ids']).encode())) for t in tokens])
    queues={pool:[i for i,r in enumerate(tokens) if r['pool']==pool] for pool,_ in pools}
    for n,q in enumerate(queues.values()):random.Random(SEED+n).shuffle(q)
    # Proportional stratified interleaving: shorter sources are spread through the entire epoch.
    positions={i:(position+0.5)/len(q) for q in queues.values() for position,i in enumerate(q)}
    schedule_order=sorted(range(len(tokens)),key=lambda i:(positions[i],tokens[i]['pool']))
    batches=[];consumed=0
    for i in range(0,len(schedule_order),2):
        indices=schedule_order[i:i+2];consumed+=sum(tokens[j]['loss_tokens'] for j in indices)
        batches.append(dict(indices=indices,cumulative_loss_tokens=consumed))
    assert sorted(i for b in batches for i in b['indices'])==list(range(len(tokens)))
    write(data/'schedule.json',batches)
    keys=['uid','task_id','pool','source','admitted','source_sha256','unannotated_sha256','proof_basis','format','loss_tokens','total_tokens','exclusion','duplicate_of']
    with (data/'row_results.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(reports)
    sourcefiles=['assemble.py','train.py','pipeline.py','PROTOCOL.md']
    receipt=dict(status='PASS',prepared_unix=time.time(),seed=SEED,rows=len(tokens),by_pool=dict(collections.Counter(t['pool'] for t in tokens)),by_source=dict(collections.Counter(t['source'] for t in tokens)),loss_tokens=consumed,steps=len(batches),longest_sequence=max(len(t['ids']) for t in tokens),training_sha256=digest(data/'training.jsonl'),tokens_sha256=digest(data/'tokens.pt'),schedule_sha256=digest(data/'schedule.json'),initial=str(START),initial_manifest_sha256=digest(data/'initial_manifest.json'),protected_references=764,protected_exact=screening['n_exact'],protected_near=screening['n_near'],exclusions=dict(collections.Counter(r['exclusion'] for r in reports if 'exclusion' in r)),source_sha256={n:digest(HERE/n) for n in sourcefiles},test_split_opened=False)
    write(data/'prepare_receipt.json',receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
