"""Freeze already verified strict annotated examples for fresh-base V23; never generate proofs or compile Lean."""
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

RUN=Path('/lfs/skampere1/0/eth127/rl4cv_tiny_training');REPO=RUN/'repo';EXP=Path('experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test');HERE=REPO/EXP/'expt_v23';ROOT=RUN/'corpus_training_v23';START=Path('/lfs/skampere1/0/brando9/rl4cv_e08/cache/huggingface/hub/models--Qwen--Qwen3-1.7B-Base/snapshots/ea980cb0a6c2ae4b936e82123acc929f1cec04c1');SEED=20261019
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
 kernelpath=REPO/'external/veribench_scorer/scripts/scsc/kernel_axioms.py';assert digest(kernelpath)==KERNEL_SHA;kernel=module('v23_kernel',kernelpath)
 prep=module('v23_source_mask',RUN/'public_gap_sources_v14/prepare_candidates.py');annotation=module('v23_comment_annotation',REPO/EXP/'expt_v14/admit_verified.py');integrity=module('v23_comment_integrity',REPO/EXP/'expt_v8/comment_integrity.py')
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
 current=RUN/'corpus_training_v20/base/data';prior=json.loads((current/'prepare_receipt.json').read_text());assert prior['status']=='PASS' and digest(current/'training.jsonl')==prior['training_sha256']=='0882a88925e862b44fd79b7592d8d525829aec1f2ac1bd12afa1fd43fc6a5de7'
 for name,h in prior['source_sha256'].items():assert digest(FROZEN/name)==h,name
 authority={r['uid']:r for r in csv.DictReader((current/'row_results.csv').open()) if r['admitted']=='True'}
 original_authority={r['uid']:r for r in csv.DictReader((RUN/'corpus_training_v12/current/data/row_results.csv').open())}
 tiny_sources={};tiny_manifests={};rows=[dict(row,_authority='v20') for row in read(current/'training.jsonl')]
 for kind,filename,expected,count in [('v21','tiny_training.jsonl','f757a318cbcf5b8ddae32d26ad582df0bbbfc224f02179ac75bd22c5d2850f57',470),('v22','repaired_tiny_training.jsonl','b4d9b103158515af58005856658432bf23190c68588e01d7d552a83974bf52a8',30)]:
  folder=RUN/('lean_corpus_'+kind)/'final';completion=json.loads((folder/'completion.json').read_text())
  assert completion['accepted']==count and completion['no_automated_fallbacks'] and completion['protected_references']==764 and completion['protected_exact']==completion['protected_near']==0
  assert digest(folder/filename)==completion['training_sha256']==expected
  assert digest(folder/'proof_receipts_manifest.json')==completion['proof_receipts_manifest_sha256']
  tiny_sources[kind]=folder;tiny_manifests[kind]={entry['example_index']:entry for entry in json.loads((folder/'proof_receipts_manifest.json').read_text())}
  selected=read(folder/filename);assert len(selected)==count;rows.extend(dict(row,_authority=kind) for row in selected)
 extras=RUN/'gx10_port_v19/extra_verified_explicit_workbook_rows.jsonl';assert digest(extras)=='519630792882fe86b0cca072e2416de342f014b9b1605a333ba2adb15441593d'
 for row in read(extras):rows.append(dict(row,uid=row['existing_verified_alternative_inventory']['prior_uid'],pool='workbook',_authority='alternative'))
 assert len(rows)==4193
 assert {row['example_index'] for row in rows if row['_authority'] in ('v21','v22')}==set(range(500))
 tok=AutoTokenizer.from_pretrained(START,local_files_only=True);reference=AutoTokenizer.from_pretrained(RUN/'onep7/runs/mixed/hf',local_files_only=True)
 assert tok.get_chat_template()==reference.get_chat_template(),'Base tokenizer chat template changed';assert tok.get_vocab()==reference.get_vocab(),'Base vocabulary differs'
 initial={p.name:digest(p) for p in START.iterdir() if p.is_file()};write(data/'initial_manifest.json',initial)
 reports=[];candidates=[];seen=set();statements=set()
 for position,row in enumerate(rows):
  row=dict(row);kind=row.pop('_authority');uid=row.get('uid',kind+':'+row['task_id']);report=dict(uid=uid,task_id=row['task_id'],pool=row.get('pool','public_proof'),source=row['source'],authority=kind,admitted=False)
  try:
   messages=row['messages'];answer=messages[-1]['content'];assert sha(answer)==row['response_sha256'];marker=re.search(r'^FILE:\s*([^\n]+)',answer,re.M);assert marker
   lean=extract_lean(answer,[marker[1].strip()],root=REPO/'external/veribench').lean;assert lean and sha(lean)==row['lean_sha256']
   if kind=='v20':assert authority[uid]['source_sha256']==sha(lean)
   elif kind=='alternative':
    old=original_authority[uid];assert old['source_sha256']==sha(lean) and old['exclusion']=='duplicate' and old['proof_basis'] in ('v9_pinned_kernel','v10_pinned_kernel'),old
   else:
    folder=tiny_sources[kind];entry=tiny_manifests[kind][row['example_index']];meta=row['automation_cleanup_'+kind]
    assert meta['no_automated_fallback'] and meta['header_proof_sketch'] and meta['english_inline_proof_comments']>0
    assert entry['source_sha256']==sha(lean) and digest(folder/entry['portable_receipt'])==entry['receipt_sha256']==meta['receipt_sha256']
    fm=folder/entry['files_manifest'];assert digest(fm)==entry['files_manifest_sha256']
    for filename,expected_sha in json.loads(fm.read_text()).items():assert digest(fm.parent/filename)==expected_sha,filename
    checked_source=(fm.parent/'CheckedSolution.lean').read_text();annotated=(fm.parent/'Solution.lean').read_text();assert annotated==lean
    check=json.loads((folder/entry['portable_receipt']).read_text());assert check['passed'] and kernel.valid_report(check['kernel_report'])
    assert check['kernel_report']['source_sha256']==sha(checked_source)==entry['kernel_checked_source_sha256']
    assert kernel.strip_comments(checked_source,keep_literals=True).split()==kernel.strip_comments(lean,keep_literals=True).split()
    if checked_source!=lean:
     binding=json.loads((folder/entry['portable_comment_binding']).read_text());assert binding['checked_source_sha256']==sha(checked_source) and binding['annotated_source_sha256']==sha(lean) and binding['original_bytes_preserved'] and binding['noncomment_tokens_unchanged']
   hits,anonymous=tactics(lean);assert not hits,'automation:'+','.join(hits)
   if not comments(lean):
    annotated,added,operations=annotation.annotate(lean,prep,integrity);assert prep.mask_comments_strings(lean).split()==prep.mask_comments_strings(annotated).split();report['mechanical_comments_added']=len(added);report['pre_comment_source_sha256']=sha(lean);answer=answer.replace(lean,annotated,1);lean=annotated;messages=[dict(m) for m in messages];messages[-1]['content']=answer
   assert comments(lean),'Missing required proof sketch/inline commentary'
   bodykey=' '.join(prep.mask_comments_strings(lean).split());statement=row.get('formal_statement');statementkey=re.sub(r'\b(theorem|lemma)\s+\S+',r'\1 TARGET',statement).split() if statement else None;statementkey=' '.join(statementkey) if statementkey else None
   assert sha(bodykey) not in seen and (not statementkey or statementkey not in statements),'duplicate'
   checked=render(tok,messages[0]['content'],messages[1]['content'],answer);assert all(checked[k] for k in ['byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap'])
   prefix=tok.apply_chat_template(messages[:2],tokenize=False,add_generation_prompt=True,enable_thinking=True);pids=tok.encode(prefix,add_special_tokens=False);aids=tok.encode('<think>\n\n</think>\n\n'+answer+'<|im_end|>\n'+tok.eos_token,add_special_tokens=False);assert len(pids)+len(aids)<=16384 and len(aids)==checked['n_assistant_tokens']+1
   if report['pool']=='tiny':assert checked['n_assistant_tokens']<1000,'Tiny assistant-token cap'
   seen.add(sha(bodykey))
   if statementkey:statements.add(statementkey)
   row.update(uid=uid,pool=report['pool'],messages=messages,response_sha256=sha(answer),lean_sha256=sha(lean),v23_authority=kind);report.update(source_sha256=sha(lean),anonymous_native_test_exceptions=anonymous,loss_tokens=len(aids),total_tokens=len(pids)+len(aids))
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
 assert sum(t['pool']=='tiny' for t in tokens)==500,'Not all declared500 tiny rows survived admission'
 assert sum(r.get('v23_authority')=='v20' for r in output)==3568,'Frozen V20 source cohort lost rows'
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
 receipt=dict(status='PASS',seed=SEED,rows=len(tokens),by_pool=dict(Counter(t['pool'] for t in tokens)),by_source=dict(Counter(t['source'] for t in tokens)),loss_tokens=consumed,steps=len(batches),longest_sequence=max(len(t['ids']) for t in tokens),initial=str(START),initial_model='Qwen/Qwen3-1.7B-Base',initial_revision=START.name,initial_manifest_sha256=digest(data/'initial_manifest.json'),training_sha256=digest(data/'training.jsonl'),tokens_sha256=digest(data/'tokens.pt'),schedule_sha256=digest(data/'schedule.json'),source_sha256=prior['source_sha256'],v23_source_sha256={name:digest(HERE/name) for name in ['assemble.py','entry.py','pipeline.py','summarize.py','PROTOCOL.md']},automation_policy=list(policy),anonymous_native_test_exceptions=sum(r.get('anonymous_native_test_exceptions',0) for r in reports if r['admitted']),protected_references=764,protected_exact_retained=0,protected_near_retained=0,source_screen_exact=screening['n_exact'],source_screen_near=screening['n_near'],exclusions=dict(Counter(r['exclusion'] for r in reports if 'exclusion' in r)),fresh_optimizer=True,sft_weights_reused=False,test_split_evaluated=False,no_proof_generation=True,no_lean_compilation=True,v20_prepare_receipt_sha256=digest(current/'prepare_receipt.json'),v21_completion_sha256=digest(tiny_sources['v21']/'completion.json'),v22_completion_sha256=digest(tiny_sources['v22']/'completion.json'),extra_alternatives_sha256=digest(extras),prepared_unix=time.time())
 # Pin compatible existing SciPy bytes in an owned overlay before future generation.
 import shutil
 source_overlay=RUN/'corpus_training_v20/recovery_3/scipy_overlay';overlay=ROOT/'generation_env/scipy_overlay';overlay.parent.mkdir(parents=True,exist_ok=True)
 shutil.copytree(source_overlay,overlay)
 manifest=json.loads((RUN/'corpus_training_v20/recovery_3/scipy_overlay_manifest.json').read_text())
 for name,expected in manifest['files'].items():assert digest(overlay/name)==expected,name
 write(ROOT/'generation_env/scipy_overlay_manifest.json',manifest)
 receipt['generation_scipy_overlay_manifest_sha256']=digest(ROOT/'generation_env/scipy_overlay_manifest.json')
 write(data/'prepare_receipt.json',receipt);print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
