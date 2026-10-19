"""Freeze already verified strict annotated examples for fresh-base V20; never generate proofs or compile Lean."""
import ast
from collections import Counter
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

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training');REPO=RUN/'repo';EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test');HERE=REPO/EXP/'expt_v20';ROOT=RUN/'corpus_training_v20';START=Path('/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1');SEED=20261019
FROZEN=REPO/EXP/'expt_v12';KERNEL_SHA='5dbbdcae75ba8b22911fcb43ab1fcde45a1475cf92742a39a29ebe41116de287'

def sha(value):return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
 return h.hexdigest()
def read(path):return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 os.environ['CUDA_VISIBLE_DEVICES']='';os.environ['TOKENIZERS_PARALLELISM']='false'
 import torch
 from transformers import AutoTokenizer
 sys.path[:0]=[str(REPO/'src'),str(REPO/EXP/'expt_v1/scripts')]
 from template_check import render
 from rl4cv.veribench.exp103 import extract_lean
 from rl4cv.screens import screen
 data=ROOT/'base/data';data.mkdir(parents=True,exist_ok=True);assert not (data/'prepare_receipt.json').exists()
 kernelpath=REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py';assert digest(kernelpath)==KERNEL_SHA;kernel=module('v20_kernel',kernelpath)
 prep=module('v20_source_mask',RUN/'public_gap_sources_v14/prepare_candidates.py');annotation=module('v20_comment_annotation',REPO/EXP/'expt_v14/admit_verified.py');integrity=module('v20_comment_integrity',REPO/EXP/'expt_v8/comment_integrity.py')
 policy=next(ast.literal_eval(n.value) for n in ast.parse((REPO/EXP/'expt_v9/prefer_explicit.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='AUTOMATION' for t in n.targets));assert len(policy)==40
 pattern=re.compile(r"(?<![A-Za-z0-9_'])('".replace("('","(")+'|'.join(re.escape(x) for x in sorted(policy,key=len,reverse=True))+r")(?![A-Za-z0-9_'])")
 decl=re.compile(r'^(?:(?:private|protected|noncomputable)\s+)?(theorem|lemma|example)\b',re.M)
 boundaries=re.compile(r'^(?:(?:private|protected|noncomputable)\s+)?(?:theorem|lemma|example|def|abbrev|instance|class|structure|inductive|axiom|opaque|namespace|section|end|open|variable|set_option)\b',re.M)
 def tactics(source):
  code=prep.mask_comments_strings(source);found=[];anonymous=0;targets=list(decl.finditer(code));assert targets,'No recognized proof declarations'
  for target in targets:
   start=prep.assignment(code,target.end())+2;nexts=[m.start() for m in boundaries.finditer(code,start)];end=nexts[0] if nexts else len(code);body=code[start:end];hits=set(pattern.findall(body))
   if target[1]=='example' and hits=={'native_decide'}:anonymous+=1;hits=set()
   found.extend(hits)
  return sorted(set(found)),anonymous
 def comments(source):
  header=re.search(r'proof\s+sketch\s*:',source,re.I)
  if not header:return False
  rest=source[header.end():];lines=re.findall(r'(?m)^\s*--\s+(.+)',rest)
  return any(len(re.findall('[A-Za-z]+',line))>=3 and not line.startswith('The original formal statements') for line in lines)
 current=RUN/'corpus_training_v12/current/data';prior=json.loads((current/'prepare_receipt.json').read_text());assert prior['status']=='PASS' and digest(current/'training.jsonl')==prior['training_sha256']=='6b0cce0608a11b2aa7d31e1343c6db0ba8ade08fdbd62ec68914884064a9df3e'
 for name,h in prior['source_sha256'].items():assert digest(FROZEN/name)==h,name
 authority={r['uid']:r for r in csv.DictReader((current/'row_results.csv').open()) if r['admitted']=='True'}
 originals=RUN/'lean_corpus_v18';completion=json.loads((originals/'completion.json').read_text());op=originals/'final/fully_cleaned_existing_training.jsonl';assert completion['state']=='USER_STOPPED_PARTIAL' and completion['accepted']==800 and completion['no_automated_fallbacks'] is True and digest(op)==completion['training_sha256']=='bc29f309b387cbf27f9e5e89c5ca66c81137d8a5fe67d617dff5738e6f93f998'
 public=RUN/'public_gap_sources_v14/admission_v2';pubcompletion=json.loads((public/'completion.json').read_text());assert pubcompletion['state']=='DONE' and digest(public/'training.jsonl')=='b7cdd07367612a5c2a95b6595fcc0606a6e4d4a970ded9125d575b53ae5f4f1a'
 rows=[dict(row,_authority='v12') for row in read(current/'training.jsonl') if row['pool']!='python']+[dict(row,_authority='v18') for row in read(op)]+[dict(row,uid='v14:'+row['task_id'],_authority='v14') for row in read(public/'training.jsonl')]
 tok=AutoTokenizer.from_pretrained(START,local_files_only=True);reference=AutoTokenizer.from_pretrained(RUN/'onep7/runs/mixed/hf',local_files_only=True)
 assert tok.get_chat_template()==reference.get_chat_template(),'Base tokenizer chat template changed';assert tok.get_vocab()==reference.get_vocab(),'Base vocabulary differs'
 initial={p.name:digest(p) for p in START.iterdir() if p.is_file()};write(data/'initial_manifest.json',initial)
 reports=[];candidates=[];seen=set();statements=set()
 for position,row in enumerate(rows):
  row=dict(row);kind=row.pop('_authority');uid=row.get('uid',kind+':'+row['task_id']);report=dict(uid=uid,task_id=row['task_id'],pool=row.get('pool','public_proof'),source=row['source'],authority=kind,admitted=False)
  try:
   messages=row['messages'];answer=messages[-1]['content'];assert sha(answer)==row['response_sha256'];marker=re.search(r'^FILE:\s*([^\n]+)',answer,re.M);assert marker
   lean=extract_lean(answer,[marker[1].strip()],root=REPO/'external/veribench').lean;assert lean and sha(lean)==row['lean_sha256']
   if kind=='v12':assert authority[uid]['source_sha256']==sha(lean) and authority[uid]['proof_basis']!='prior_original_pool_admission'
   elif kind=='v18':
    meta=row['automation_cleanup_v18'];receipt=Path(meta['receipt']);assert digest(receipt)==meta['receipt_sha256'];check=json.loads(receipt.read_text());assert check['passed'] and kernel.valid_report(check['kernel_report']) and check['kernel_report']['source_sha256']==sha(lean)
   else:
    receipt=Path(row['comment_binding_receipt']);assert digest(receipt)==row['comment_binding_receipt_sha256'];assert row['current_kernel_verified'] is True
    check=json.loads(Path(row['kernel_report_path']).read_text());assert kernel.valid_report(check)
   hits,anonymous=tactics(lean);assert not hits,'automation:'+','.join(hits)
   if not comments(lean):
    annotated,added,operations=annotation.annotate(lean,prep,integrity);assert prep.mask_comments_strings(lean).split()==prep.mask_comments_strings(annotated).split();report['mechanical_comments_added']=len(added);report['pre_comment_source_sha256']=sha(lean);answer=answer.replace(lean,annotated,1);lean=annotated;messages=[dict(m) for m in messages];messages[-1]['content']=answer
   assert comments(lean),'Missing required proof sketch/inline commentary'
   bodykey=' '.join(prep.mask_comments_strings(lean).split());statement=row.get('formal_statement');statementkey=re.sub(r'\b(theorem|lemma)\s+\S+',r'\1 TARGET',statement).split() if statement else None;statementkey=' '.join(statementkey) if statementkey else None
   assert sha(bodykey) not in seen and (not statementkey or statementkey not in statements),'duplicate'
   checked=render(tok,messages[0]['content'],messages[1]['content'],answer);assert all(checked[k] for k in ['byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'])
   prefix=tok.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True);pids=tok.encode(prefix,add_special_tokens=False);aids=tok.encode('<think>\n\n</think>\n\n'+answer+'<|im_end|>\n'+tok.eos_token,add_special_tokens=False);assert len(pids)+len(aids)<=16384 and len(aids)==checked['n_assistant_tokens']+1
   seen.add(sha(bodykey))
   if statementkey:statements.add(statementkey)
   row.update(uid=uid,pool=report['pool'],messages=messages,response_sha256=sha(answer),lean_sha256=sha(lean),v20_authority=kind);report.update(source_sha256=sha(lean),anonymous_native_test_exceptions=anonymous,loss_tokens=len(aids),total_tokens=len(pids)+len(aids))
   candidates.append((row,dict(uid=uid,task_id=row['task_id'],pool=row['pool'],source=row['source'],ids=pids+aids,prompt=len(pids),loss_tokens=len(aids)),report))
  except Exception as exc:report['exclusion']=str(exc)
  reports.append(report)
  if position%250==0:write(ROOT/'assembly_progress.json',dict(processed=position+1,total=len(rows),strict_candidates=len(candidates),observed_unix=time.time()))
 protected={};vb=REPO/'external/veribench'
 for item in csv.DictReader((REPO/EXP/'expt_v1/results/split/vbv1_split_manifest.csv').open()):
  if item['split'] in ['validation','test']:
   protected[item['task_id']+'/python']=(vb/'veribench_dataset/py_src'/item['py_relpath']).read_text();protected[item['task_id']+'/lean']=(vb/'veribench_dataset/lean_src/veribench'/item['gold_relpath']).read_text()
 for item in read(RUN/'diagnostic_seen_fresh_v7/manifest.jsonl'):
  if item['cohort']=='fresh':protected[item['task_id']+'/python']=item['python']
 assert len(protected)==764
 screening=screen({r['uid']:r['messages'][1]['content']+'\n'+r['messages'][2]['content'] for r,t,p in candidates},protected);write(data/'protected_screen.json',screening);clean=set(screening['clean_ids']);tokens=[];output=[]
 for row,token,report in candidates:
  if row['uid'] not in clean:report['exclusion']='protected_screen';continue
  report['admitted']=True;token['index']=len(tokens);tokens.append(token);output.append(row)
 assert tokens and sum(t['pool']=='python' for t in tokens)>0
 (data/'training.jsonl').write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in output));torch.save(tokens,data/'tokens.pt')
 queues={pool:[i for i,t in enumerate(tokens) if t['pool']==pool] for pool in sorted({t['pool'] for t in tokens})}
 for i,q in enumerate(queues.values()):random.Random(SEED+i).shuffle(q)
 positions={index:(j+.5)/len(q) for q in queues.values() for j,index in enumerate(q)};order=sorted(range(len(tokens)),key=lambda i:(positions[i],tokens[i]['pool']));batches=[];consumed=0
 for i in range(0,len(order),2):
  batch=order[i:i+2];consumed+=sum(tokens[j]['loss_tokens'] for j in batch);batches.append(dict(indices=batch,cumulative_loss_tokens=consumed))
 write(data/'schedule.json',batches);write(data/'token_manifest.json',[{k:v for k,v in t.items() if k!='ids'} for t in tokens])
 fields=sorted({key for report in reports for key in report})
 with (data/'row_results.csv').open('w') as stream:
  writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(reports)
 receipt=dict(status='PASS',seed=SEED,rows=len(tokens),by_pool=dict(Counter(t['pool'] for t in tokens)),by_source=dict(Counter(t['source'] for t in tokens)),loss_tokens=consumed,steps=len(batches),longest_sequence=max(len(t['ids']) for t in tokens),initial=str(START),initial_model='Qwen/Qwen3-1.7B-Base',initial_revision=START.name,initial_manifest_sha256=digest(data/'initial_manifest.json'),training_sha256=digest(data/'training.jsonl'),tokens_sha256=digest(data/'tokens.pt'),schedule_sha256=digest(data/'schedule.json'),source_sha256=prior['source_sha256'],v20_source_sha256={name:digest(HERE/name) for name in ['assemble.py','entry.py','pipeline.py','summarize.py','PROTOCOL.md']},automation_policy=list(policy),anonymous_native_test_exceptions=sum(r.get('anonymous_native_test_exceptions',0) for r in reports if r['admitted']),protected_references=764,protected_exact_retained=0,protected_near_retained=0,source_screen_exact=screening['n_exact'],source_screen_near=screening['n_near'],exclusions=dict(Counter(r['exclusion'] for r in reports if 'exclusion' in r)),fresh_optimizer=True,sft_weights_reused=False,test_split_evaluated=False,no_proof_generation=True,no_lean_compilation=True,v18_completion_sha256=digest(originals/'completion.json'),v14_completion_sha256=digest(public/'completion.json'),prepared_unix=time.time())
 write(data/'prepare_receipt.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
