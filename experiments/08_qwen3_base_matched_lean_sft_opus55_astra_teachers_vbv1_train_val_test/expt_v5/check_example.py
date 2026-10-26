"""Compile, check axioms, differential-test, and encode a tiny curriculum example with the pinned Qwen template."""
import argparse
import ast
import concurrent.futures
import fcntl
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(os.environ.get('TINY_ROOT',str(Path(__file__).parent)))
BIN=Path(os.environ.get('TINY_LEAN_BIN','/lfs/skampere1/0/brando9/.elan/toolchains/leanprover--lean4---v4.22.0/bin'))
GRADE=Path(os.environ.get('TINY_GRADING_ROOT','/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src'))
VB=Path(os.environ.get('TINY_VERIBENCH_ROOT','/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/external/veribench'))
REPO=Path(os.environ.get('TINY_REPO_ROOT',str(VB.parent.parent)))
sys.path.insert(0,str(REPO/'src'))
sys.path.insert(0,str(REPO/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts'))

def stamp():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def sha(s):return hashlib.sha256(s.encode()).hexdigest()

def lean_literal(v,kind=''):
    if v is None:return '(none : Option Int)'
    if kind=='int | None':return f'(some ({v}) : Option Int)'
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,int):return f'({v})'
    if kind.startswith('tuple'):return '('+', '.join(lean_literal(x) for x in v)+')'
    if isinstance(v,list):return '['+', '.join(lean_literal(x) for x in v)+']'
    raise ValueError(type(v))

def compile_lean(path,seconds=45):
    slots=ROOT/'runtime/compiler_slots';slots.mkdir(parents=True,exist_ok=True)
    lock=None
    while lock is None:
        for i in range(8):
            f=(slots/str(i)).open('a')
            try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);lock=f;break
            except BlockingIOError:f.close()
        if lock is None:time.sleep(.2)
    env=os.environ.copy()
    libs=[p/'.lake/build/lib/lean' for p in (GRADE/'.lake/packages').iterdir() if p.is_dir()]
    libs+=[GRADE/'.lake/build/lib/lean']
    env['LEAN_PATH']=':'.join(str(p) for p in libs if p.is_dir())
    try:
        p=subprocess.run([str(BIN/'lean'),'-j','1',str(path)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=seconds,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_CORE,(0,0)))
        return {'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired as e:return {'exit':124,'stdout':str(e.stdout or ''),'stderr':'compile timeout'}
    finally:lock.close()

def make_instruction(t):
    path='/home/user/lean_project/Veribench/'+t['task_id']+'.lean'
    return (f'Translate this Python function to a concise, complete Lean 4 file at `{path}`.\n\n'
        f'Intent: {t["intent"]}\n\n```python\n{t["python"]}```\n\n'
        'Use namespace Tiny and define solution with arguments in the Python signature order. '
        'Use Int for Python integers, Nat for explicitly nonnegative inputs and length/count results, '
        'Bool for Boolean results, List for Python lists, Prod for pairs, and Option Int for optional results. '
        'List operations preserve order and multiplicity. Python // and % use floor division with positive divisors. '
        'Prove at least one general meaningful specification theorem and two executable example theorems. '
        'Every theorem must be named spec_<descriptive_name> or test_<descriptive_name>. '
        'Keep the complete assistant response below 1000 Qwen tokens. Prefer the shortest clear, idiomatic complete solution; '
        'use meaningful names, standard tactics, and only necessary helpers. Avoid obfuscation, redundant comments, '
        'unnecessary abstractions, and dense tactic chains used solely to save tokens. Preserve all semantics, edge cases, proofs, and tests. '
        'Use import Mathlib. Do not use sorry, admit, declared axioms, native_decide, partial, unsafe, '
        'or local modifications of standard definitions or notation.\n')

def messages_for(t,lean):
    from rl4cv.veribench.exp103 import build_prompt,extract_lean
    instruction=make_instruction(t)
    p=build_prompt(instruction,root=VB)
    if p.system_prompt_sha256!='dc051963de1199dd4f77c9f8f96218eb45be331c819b8e76693b063b206143cd':raise ValueError('frozen system prompt hash changed')
    if p.addendum_sha256!='a7a0fc1b7be6b4ede41fd6b31e1e1dcae3d2fd320a6cddf9b311cf55855a18f5':raise ValueError('frozen addendum hash changed')
    assert len(p.required_paths)==1,p.required_paths
    response=f'FILE: {p.required_paths[0]}\n```lean\n'+lean+('' if lean.endswith('\n') else '\n')+'```\n'
    ext=extract_lean(response,p.required_paths,root=VB)
    if ext.lean is None or ext.lean!=lean:raise ValueError('extractor byte round trip failed; use one final newline')
    return p.messages()+[{'role':'assistant','content':response}],p

def get_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained('Qwen/Qwen3-8B-Base',revision='49e3418fbbbca6ecbdf9608b4d22e5a407081db4',cache_dir=str(ROOT/'runtime/huggingface'),local_files_only=True)

def validate(t,folder,tok=None):
    folder=Path(folder); receipts=folder/'receipts';receipts.mkdir(exist_ok=True)
    result={'task_id':t['task_id'],'topic':t['topic'],'checked_at':stamp(),'accepted':False,'checks':{}}
    try:
        p=folder/'Solution.lean';lean=p.read_text()
        result['lean_sha256']=sha(lean)
        stripped=re.sub(r'/\-.*?\-/|--[^\n]*','',lean,flags=re.S)
        if re.search(r'\b(sorry|admit|axiom|native_decide|partial|unsafe|opaque)\b',stripped):raise ValueError('forbidden proof or implementation construct')
        if not re.search(r'\bnamespace\s+Tiny\b',stripped) or not re.search(r'\bdef\s+solution\b',stripped):raise ValueError('missing Tiny.solution')
        names=re.findall(r'^\s*theorem\s+([A-Za-z_][A-Za-z_0-9]*)',stripped,re.M)
        if not names or any(not n.startswith(('spec_','test_')) for n in names):raise ValueError('theorem naming/coverage')
        if not any(n.startswith('spec_') for n in names) or sum(n.startswith('test_') for n in names)<2:raise ValueError('need one general spec and two examples')
        if re.search(r':\s*True\s*:=',stripped):raise ValueError('vacuous True specification')
        policy=VB/'tests/test_reference_specs_nonvacuous.py'
        tree=ast.parse(policy.read_text());namespace={'re':re}
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='VACUOUS' for x in node.targets):
                exec(compile(ast.Module(body=[node],type_ignores=[]),str(policy),'exec'),namespace)
        for label,pattern in namespace['VACUOUS'].items():
            if pattern.search(stripped):raise ValueError('reference nonvacuity check: '+label)
        messages,prompt=messages_for(t,lean)
        if tok is None:tok=get_tokenizer()
        response=messages[-1]['content'];response_tokens=len(tok.encode(response,add_special_tokens=False))
        assistant_tokens=len(tok.encode('<think>\n\n</think>\n\n'+response+'<|im_end|>\n',add_special_tokens=False))
        result.update(response_tokens=response_tokens,assistant_tokens=assistant_tokens)
        if assistant_tokens>=1000:raise ValueError(f'assistant token cap: {assistant_tokens} >= 1000')
        from template_check import render
        template=render(tok,messages[0]['content'],messages[1]['content'],response)
        if not all(template[k] for k in ['byte_prefix_ok','token_prefix_ok','span_matches_expected','within_cap']):raise ValueError('chat-template check failed: '+repr(template))
        assistant_tokens=template['n_assistant_tokens'];result['assistant_tokens']=assistant_tokens
        if assistant_tokens>=1000:raise ValueError(f'assistant token cap: {assistant_tokens} >= 1000')
        result['template']=template
        result['checks']['format']='PASS'
        evaluations=[]
        for sample in t['tests']:
            args=' '.join(lean_literal(sample['inputs'][a],t['arg_types'][a]) for a in t['args'])
            evaluations.append('#eval IO.println (Lean.Json.compress (Lean.toJson (Tiny.solution '+args+')))')
        audit=lean.rstrip()+'\n'+''.join('#print axioms Tiny.'+name+'\n' for name in names)+'\n'.join(evaluations)+'\n'
        audit_path=receipts/'AxiomCheck.lean';audit_path.write_text(audit)
        checked=compile_lean(audit_path);(receipts/'compile.json').write_text(json.dumps(checked,indent=2))
        if checked['exit']!=0:raise ValueError('Lean compilation failed; see receipts/compile.json')
        allowed={'propext','Classical.choice','Quot.sound'}
        for group in re.findall(r'depends on axioms:\s*\[([^]]*)\]',checked['stdout']):
            found={x.strip() for x in group.split(',') if x.strip()}
            if not found<=allowed:raise ValueError('disallowed kernel axioms: '+str(found-allowed))
        result['checks']['compile_and_axioms']='PASS'
        dc=checked;(receipts/'differential.json').write_text(json.dumps(dc,indent=2))
        actual=[]
        for line in dc['stdout'].splitlines():
            try:actual.append(json.loads(line))
            except json.JSONDecodeError:pass
        expected=json.loads(json.dumps([s['expected'] for s in t['tests']]))
        if actual!=expected:raise ValueError('Python/Lean mismatch: '+repr({'actual':actual[:3],'expected':expected[:3],'actual_count':len(actual)}))
        result['checks']['differential']={'status':'PASS','cases':len(expected)}
        (folder/'solution.py').write_text(t['python'])
        (folder/'intent.txt').write_text(t['intent']+'\n')
        seed_hashes={sha(p.read_text()):p.name for p in (ROOT/'prototypes').glob('*.lean')}
        row={'source':'tiny_curriculum_v1','task_id':t['task_id'],'topic':t['topic'],'teacher':'openai','model':'gpt-5.6-terra','reasoning_effort':'high','coordinator_prototype_reused':seed_hashes.get(sha(lean)),'messages':messages,'lean_sha256':sha(lean),'response_sha256':sha(response),'n_assistant_tokens':assistant_tokens,'system_prompt_sha256':prompt.system_prompt_sha256,'addendum_sha256':prompt.addendum_sha256,'nonvacuity_policy_sha256':sha(policy.read_text())}
        (folder/'training.json').write_text(json.dumps(row,indent=2))
        result['accepted']=True
    except Exception as e:result['error']=str(e)
    (receipts/'verification.json').write_text(json.dumps(result,indent=2))
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--topic');ap.add_argument('--task');ap.add_argument('--folder');a=ap.parse_args()
    tasks=[json.loads(l) for l in (ROOT/'manifest.jsonl').read_text().splitlines()]
    chosen=[t for t in tasks if (not a.topic or t['topic']==a.topic) and (not a.task or t['task_id']==a.task)]
    if not chosen:raise SystemExit('unknown task/topic')
    tok=get_tokenizer()
    results=[]
    for t in chosen:
        folder=Path(a.folder) if a.folder else ROOT/'workers'/t['topic']/'examples'/t['task_id']
        folder.mkdir(parents=True,exist_ok=True)
        r=validate(t,folder,tok);results.append(r);print(json.dumps(r),flush=True)
    raise SystemExit(0 if all(r['accepted'] for r in results) else 1)

if __name__=='__main__':main()
