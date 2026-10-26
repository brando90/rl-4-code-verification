"""Screen verified examples against protected references and assemble the short warm-start training dataset."""
import collections
import ast
import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
import tarfile
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
from check_example import REPO,VB,messages_for
sys.path.insert(0,str(REPO/'src'))
from rl4cv.screens import norm_hash,screen

def main():
    out=ROOT/'runtime/admission_staging'/uuid.uuid4().hex;out.mkdir(parents=True)
    tasks=[json.loads(l) for l in (ROOT/'manifest.jsonl').read_text().splitlines()]
    policy=VB/'tests/test_reference_specs_nonvacuous.py';ns={'re':re}
    for node in ast.parse(policy.read_text()).body:
        if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='VACUOUS' for x in node.targets):exec(compile(ast.Module(body=[node],type_ignores=[]),str(policy),'exec'),ns)
    split=REPO/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/results/split/vbv1_split_manifest.csv'
    protected={}
    for row in csv.DictReader(split.open()):
        if row['split'] in ['validation','test']:
            protected[row['task_id']+'/python']=(VB/'veribench_dataset/py_src'/row['py_relpath']).read_text()
            protected[row['task_id']+'/lean']=(VB/'veribench_dataset/lean_src/veribench'/row['gold_relpath']).read_text()
    if len(protected)!=714:raise RuntimeError('protected corpus count differs from frozen protocol')
    candidates={};pool={};missing=[]
    for t in tasks:
        folder=ROOT/'workers'/t['topic']/'examples'/t['task_id']
        receipt=folder/'receipts/verification.json';rowpath=folder/'training.json'
        if not receipt.exists() or not rowpath.exists():missing.append({'task_id':t['task_id'],'reason':'missing verification or training row'});continue
        receipt=json.loads(receipt.read_text())
        if not receipt.get('accepted'):missing.append({'task_id':t['task_id'],'reason':receipt.get('error','verification failed')});continue
        row=json.loads(rowpath.read_text());lean=(folder/'Solution.lean').read_text()
        if hashlib.sha256(lean.encode()).hexdigest()!=receipt['lean_sha256']:missing.append({'task_id':t['task_id'],'reason':'Lean bytes changed after verification'});continue
        code=re.sub(r'/\-.*?\-/|--[^\n]*','',lean,flags=re.S)
        invalid=[label for label,pattern in ns['VACUOUS'].items() if pattern.search(code)]
        if invalid:missing.append({'task_id':t['task_id'],'reason':'reference nonvacuity: '+', '.join(invalid)});continue
        try:
            expected,prompt=messages_for(t,lean)
            if row['messages']!=expected:raise ValueError('training messages changed or evaluated Lean differs from response')
        except Exception as e:missing.append({'task_id':t['task_id'],'reason':str(e)});continue
        candidates[t['task_id']]={'row':row,'lean':lean,'python':t['python'],'receipt':receipt,'folder':str(folder)}
        pool[t['task_id']+'/python']=t['python'];pool[t['task_id']+'/lean']=lean;pool[t['task_id']+'/assistant']=row['messages'][-1]['content']
    report=screen(pool,protected,n=5,threshold=.7)
    flagged={x['item_id'].rsplit('/',1)[0] for x in report['exact']+report['near']}
    seen={};duplicates=[];accepted=[];records=[]
    for t in tasks:
        tid=t['task_id']
        if tid not in candidates:continue
        c=candidates[tid];fingerprint=norm_hash(c['lean'])
        if tid in flagged:records.append({'task_id':tid,'admitted':False,'reason':'protected_reference_overlap'});continue
        if fingerprint in seen:
            duplicates.append({'task_id':tid,'duplicate_of':seen[fingerprint]});records.append({'task_id':tid,'admitted':False,'reason':'duplicate_lean'});continue
        seen[fingerprint]=tid;accepted.append(c['row']);records.append({'task_id':tid,'admitted':True,'assistant_tokens':c['receipt']['assistant_tokens'],'artifact_dir':c['folder'],'lean_sha256':c['receipt']['lean_sha256']})
        dest=out/'examples'/tid;dest.mkdir(parents=True)
        (dest/'Solution.lean').write_text(c['lean'])
        (dest/'solution.py').write_text(c['python'])
        (dest/'intent.txt').write_text(t['intent']+'\n')
        (dest/'tests.json').write_text(json.dumps(t['tests'],indent=2))
        (dest/'verification.json').write_text(json.dumps(c['receipt'],indent=2))
        (dest/'training.json').write_text(json.dumps(c['row'],indent=2))
        for name in ['compile.json','differential.json']:
            source=Path(c['folder'])/'receipts'/name
            if source.exists():(dest/name).write_bytes(source.read_bytes())
        evaluated=Path(c['folder'])/'receipts/AxiomCheck.lean'
        if evaluated.exists():
            (dest/'Evaluated.lean').write_bytes(evaluated.read_bytes())
            differential=Path(c['folder'])/'receipts/Differential.lean'
            if '#eval ' not in evaluated.read_text() and differential.exists():(dest/'Differential.lean').write_bytes(differential.read_bytes())
    (out/'training.jsonl').write_text(''.join(json.dumps(row,sort_keys=True)+'\n' for row in accepted))
    (out/'admission.json').write_text(json.dumps({'records':records,'missing_or_failed':missing,'duplicates':duplicates},indent=2))
    (out/'contamination.json').write_text(json.dumps(report,indent=2))
    tactics=collections.Counter()
    for row in accepted:
        lean=candidates[row['task_id']]['lean']
        for tactic in ['rfl','simp','simpa','rw','calc','intro','apply','exact','constructor','rcases','cases','by_cases','induction','omega','norm_num','ring','linarith','aesop']:
            if re.search(r'\b'+tactic+r'\b',lean):tactics[tactic]+=1
    tokens=[r['n_assistant_tokens'] for r in accepted]
    pyfamilies=collections.Counter(norm_hash(t['python']+'\n'+json.dumps(t['natural_inputs'])) for t in tasks)
    summary={'declared':500,'locally_verified':len(candidates),'admitted':len(accepted),'missing_or_failed':len(missing),'protected_overlap_tasks':len(flagged),'duplicate_lean':len(duplicates),'topics':dict(collections.Counter(r['topic'] for r in accepted)),'assistant_tokens':{'min':min(tokens),'median':statistics.median(tokens),'mean':statistics.mean(tokens),'max':max(tokens),'total':sum(tokens)} if tokens else None,'tactic_example_counts':dict(tactics),'distinct_python_and_domain_families':len(pyfamilies),'source_credential_alias':'LAB_OPENAI_API_KEY','model':'gpt-5.6-terra','reasoning_effort':'high'}
    usage=collections.Counter()
    for log in (ROOT/'workers').glob('*/codex_attempt_*.jsonl'):
        for line in log.read_text(errors='replace').splitlines():
            try:d=json.loads(line)
            except json.JSONDecodeError:continue
            if d.get('type')=='turn.completed':usage.update(d.get('usage',{}))
    summary['reported_cli_usage']=dict(usage)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    subprocess.run([str(ROOT/'runtime/venv/bin/python'),str(ROOT/'verify_1p7_format.py')],check=True)
    result=json.loads((ROOT/'runtime/format_1p7_verification.json').read_text())
    if not result['passed']:raise RuntimeError('1.7B format verification failed')
    (out/'format_1p7_verification.json').write_text(json.dumps(result,indent=2))
    (out/'manifest.jsonl').write_bytes((ROOT/'manifest.jsonl').read_bytes())
    (out/'PROTOCOL.md').write_bytes((ROOT/'PROTOCOL.md').read_bytes())
    (out/'lean-toolchain').write_text('leanprover/lean4:v4.22.0\n')
    (out/'lakefile.toml').write_text('name = "tiny_curriculum"\n\n[[require]]\nname = "mathlib"\ngit = "https://github.com/leanprover-community/mathlib4.git"\nrev = "v4.22.0"\n')
    (out/'README.md').write_text('# Short Python to Lean warm-start examples\n\nEach row of training.jsonl has the exact system, user and assistant messages. Every admitted assistant span is below 1000 Qwen tokens. examples/<task_id>/ contains the actual Lean file, Python source, intent, fixed comparison inputs, training row and compilation/comparison receipts. These files contain no symlinks. See PROTOCOL.md and summary.json for provenance, pins, counts and exclusions. Training has not started.\n')
    sums=[]
    for p in sorted(out.rglob('*')):
        if p.is_file():sums.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(out)))
    (out/'SHA256SUMS').write_text('\n'.join(sums)+'\n')
    previous=ROOT/'final'
    if previous.exists():
        history=ROOT/'admission_history';history.mkdir(exist_ok=True)
        previous.rename(history/(time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'_'+uuid.uuid4().hex[:8]))
    out.rename(previous)
    if len(accepted)==500:
        archive=ROOT/'runtime/tiny_curriculum_500.tar.gz'
        with tarfile.open(archive,'w:gz') as tf:tf.add(previous,arcname='dataset')
        (ROOT/'runtime/export_receipt.json').write_text(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'admitted':500},indent=2))
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
