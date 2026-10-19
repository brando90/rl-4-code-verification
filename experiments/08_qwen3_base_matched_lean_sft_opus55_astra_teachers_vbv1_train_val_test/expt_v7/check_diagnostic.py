"""Check every generated tiny package with the frozen kernel inspector and independent Python cases."""
from __future__ import annotations
import argparse
import concurrent.futures
import csv
from dataclasses import asdict
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = Path(os.environ.get('TINY_RUN_ROOT','/lfs/skampere1/0/eth127/rl4cv_tiny_training'))
ROOT = RUN/'diagnostic_seen_fresh_v7'
GRADE = RUN/'grading'
SCORER = REPO/'external/veribench_scorer'
sys.path[:0] = [str(REPO/'src'),str(HERE.parent/'expt_v1/scripts')]
from score_teacher_files import vacuity

spec = importlib.util.spec_from_file_location('diagnostic_kernel_axioms',SCORER/'scripts/scsc/kernel_axioms.py')
kernel = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = kernel
spec.loader.exec_module(kernel)

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    tmp.replace(path)

def literal(value,kind=''):
    if value is None:return '(none : Option Int)'
    if kind=='int | None':return f'(some ({value}) : Option Int)'
    if isinstance(value,bool):return 'true' if value else 'false'
    if isinstance(value,int):return f'({value})'
    if kind.startswith('tuple'):return '('+', '.join(literal(v) for v in value)+')'
    if isinstance(value,list):return '['+', '.join(literal(v) for v in value)+']'
    raise TypeError((value,kind))

def await_capacity():
    deadline = time.monotonic()+7200
    while True:
        active = 0
        for p in (RUN/'execution').glob('*/score_*.json'):
            d = json.loads(p.read_text())
            if d.get('status')=='RUNNING':
                try:
                    ticks = Path(f"/proc/{d['pid']}/stat").read_text().rsplit(') ',1)[1].split()[19]
                    active += ticks == d.get('start_ticks')
                except FileNotFoundError:
                    pass
        if active<=6:return
        if time.monotonic()>deadline:raise TimeoutError('original scorers retained CPU priority for two hours')
        time.sleep(5)

def run_lean(path):
    await_capacity()
    env = dict(os.environ,PATH=str(RUN/'bin')+':'+os.environ['PATH'],CUDA_VISIBLE_DEVICES='')
    try:
        p = subprocess.run(['lake','env','lean',str(path)],cwd=GRADE,env=env,
                           capture_output=True,text=True,timeout=45)
        return dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or '')
        return dict(exit_code=124,stdout=out,stderr='45-second diagnostic compiler timeout')

def check(task,generation,base=None):
    tid = task['task_id']
    folder = (base or ROOT/'checks')/tid
    folder.mkdir(parents=True,exist_ok=True)
    path = folder/'Solution.lean'
    lean = generation.get('lean') or ''
    path.write_text(lean)
    result = dict(task_id=tid,cohort=task.get('cohort','control'),topic=task.get('topic','control'),
        generated_tokens=generation.get('generated_tokens'),truncated=bool(generation.get('truncated')),
        extracted=bool(lean.strip()),clean_finish=generation.get('finish_reason') in ('stop','eos'),
        under_1000_tokens=int(generation.get('generated_tokens',1000))<1000,
        compiles=False,kernel_honest=False,nonvacuous=False,required_declarations=False,
        differential_pass=False,differential_cases=0,functional_proof_success=False,strict_success=False,
        status='scored',error=None)
    try:
        if not lean.strip():
            result['error']='no Lean extracted'
            return result
        stripped = kernel.strip_comments(lean)
        names = re.findall(r'\b(?:theorem|lemma)\s+([A-Za-z_][A-Za-z_0-9]*)',stripped)
        examples = len(re.findall(r'\bexample\s*(?:\(|:|\{)',stripped))
        result.update(anonymous_examples=examples,source_theorems=len(names))
        result['required_declarations'] = examples>=1 and any(n.startswith('spec_') for n in names) and sum(n.startswith('test_') for n in names)>=2 and all(n.startswith(('spec_','test_')) for n in names)
        v = vacuity(lean)
        write(folder/'nonvacuity.json',v)
        result['nonvacuous'] = v['n_vacuous']==0 and not v['unparseable']
        await_capacity()
        old_path = os.environ.get('PATH','')
        # The main process sets the inherited wrapper PATH before creating workers.
        report = kernel.check_file(str(path),str(GRADE),timeout=45,
                                   allow_native_decide=False,keep_dir=str(folder/'kernel'))
        write(folder/'kernel.json',asdict(report))
        result.update(compiles=report.compile_rc==0,kernel_theorems=report.n_theorems,
            kernel_honest_theorems=report.n_honest,
            kernel_honest=report.probe_ok and report.n_theorems>=1 and report.n_honest==report.n_theorems)
        if not result['compiles']:
            result['error']='Lean compilation failed'
            return result
        # Random markers bind actual output to this invocation and hidden tests.
        marker = 'VBDIFF_'+secrets.token_hex(12)+':'
        commands = []
        for case in task['tests']:
            args = ' '.join(literal(case['inputs'][a],task['arg_types'][a]) for a in task['args'])
            commands.append('#eval IO.println ("'+marker+'" ++ Lean.Json.compress (Lean.toJson (Tiny.solution '+args+')))')
        diff = folder/'Differential.lean'
        diff.write_text(lean.rstrip()+'\n'+'\n'.join(commands)+'\n')
        evaluated = run_lean(diff)
        write(folder/'differential_compile.json',evaluated)
        actual = [json.loads(line[len(marker):]) for line in evaluated['stdout'].splitlines() if line.startswith(marker)]
        expected = json.loads(json.dumps([t['expected'] for t in task['tests']]))
        result.update(differential_cases=len(actual),differential_pass=evaluated['exit_code']==0 and actual==expected)
        write(folder/'differential.json',dict(actual=actual,expected=expected,pass_all=result['differential_pass']))
        result['functional_proof_success'] = result['compiles'] and result['kernel_honest'] and result['nonvacuous'] and result['differential_pass']
        result['strict_success'] = result['functional_proof_success'] and result['required_declarations'] and result['clean_finish'] and not result['truncated'] and result['under_1000_tokens']
        if not result['kernel_honest']:result['error']='kernel proof gate failed'
        elif not result['nonvacuous']:result['error']='non-vacuity gate failed'
        elif not result['differential_pass']:result['error']='Python differential check or entry-point interface failed'
        elif not result['required_declarations']:result['error']='required declarations missing'
        elif not result['under_1000_tokens']:result['error']='response exceeds prompt token limit'
        elif result['truncated']:result['error']='generation token limit reached'
    except Exception as exc:
        result.update(status='checker_error',error=f'{type(exc).__name__}: {exc}')
    finally:
        write(folder/'result.json',result)
    return result

def controls():
    task = dict(task_id='correct',args=['x','y'],arg_types={'x':'int','y':'int'},
                tests=[{'inputs':{'x':x,'y':y},'expected':x+y} for x,y in [(0,0),(1,2),(-2,3),(-3,-4)]])
    good = '''import Mathlib
namespace Tiny
def solution (x y : Int) : Int := x + y
theorem spec_add (x y : Int) : solution x y = x + y := by rfl
theorem test_zero : solution 0 0 = 0 := by decide
theorem test_negative : solution (-2) 3 = 1 := by decide
example : solution 1 2 = 3 := by decide
end Tiny
'''
    variants = {
        'correct':good,
        'wrong_implementation':good.replace('x + y','x - y').replace('(-2) 3 = 1','(-2) 3 = -5').replace('1 2 = 3','1 2 = -1'),
        'sorry_proof':good.replace(':= by rfl',':= by sorry',1),
        'missing_example':'\n'.join(s for s in good.splitlines() if not s.startswith('example'))+'\n',
        'broken_lean':good.replace('x + y','unknownOperation x y',1),
    }
    output = []
    for name,lean in variants.items():
        row = check(dict(task,task_id=name),dict(lean=lean,generated_tokens=150,finish_reason='stop'),ROOT/'controls')
        expected = (row['strict_success'] if name=='correct' else
                    row['compiles'] and row['kernel_honest'] and not row['differential_pass'] if name=='wrong_implementation' else
                    row['compiles'] and not row['kernel_honest'] if name=='sorry_proof' else
                    row['functional_proof_success'] and not row['strict_success'] if name=='missing_example' else
                    not row['compiles'])
        row['control_expectation_met'] = bool(expected) and row['status']=='scored'
        output.append(row)
    write(ROOT/'controls.json',output)
    assert all(r['control_expectation_met'] for r in output), output
    print(json.dumps({'controls':'PASS','n':len(output)}),flush=True)

def wilson(k,n):
    z=1.959963984540054
    center=(k/n+z*z/(2*n))/(1+z*z/n)
    half=z*math.sqrt((k/n*(1-k/n)+z*z/(4*n))/n)/(1+z*z/n)
    return [center-half,center+half]

def main():
    p=argparse.ArgumentParser();p.add_argument('--controls',action='store_true');args=p.parse_args()
    os.environ['PATH']=str(RUN/'bin')+':'+os.environ['PATH']
    os.environ['CUDA_VISIBLE_DEVICES']=''
    if args.controls:
        controls();return
    tasks=[json.loads(s) for s in (ROOT/'manifest.jsonl').read_text().splitlines()]
    gen=[json.loads(s) for s in (ROOT/'raw.jsonl').read_text().splitlines()]
    assert len(gen)==len(tasks)==100
    assert len({(r['task_id'],r['sample_idx']) for r in gen})==100
    by_id={r['task_id']:r for r in gen}
    assert set(by_id)=={t['task_id'] for t in tasks}
    rows=[]
    def execute(task):
        existing=ROOT/'checks'/task['task_id']/'result.json'
        if existing.exists():return json.loads(existing.read_text())
        return check(task,by_id[task['task_id']])
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(execute,t):t['task_id'] for t in tasks}
        for future in concurrent.futures.as_completed(futures):
            row=future.result();rows.append(row)
            write(ROOT/'checking_progress.json',dict(completed=len(rows),declared=100,last_task=row['task_id'],updated_unix=time.time()))
            print(json.dumps(row),flush=True)
    rows.sort(key=lambda r:r['task_id'])
    write(ROOT/'results.json',rows)
    fields=sorted({k for r in rows for k in r})
    with (ROOT/'per_task.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    summary={}
    for cohort in ['seen','fresh']:
        group=[r for r in rows if r['cohort']==cohort];assert len(group)==50
        summary[cohort]={'declared':50,'measured':sum(r['status']=='scored' for r in group)}
        for name in ['extracted','compiles','kernel_honest','nonvacuous','required_declarations','differential_pass','functional_proof_success','strict_success','truncated','under_1000_tokens']:
            k=sum(r[name] for r in group)
            summary[cohort][name]={'count':k,'denominator':50,'rate':k/50,'wilson95':wilson(k,50)}
    write(ROOT/'summary.json',dict(status='COMPLETE' if all(r['status']=='scored' for r in rows) else 'CHECKER_ERRORS',
        cohorts=summary,repetitions_per_task=1,p_value=None,uncertainty='95% Wilson per function; shared topic dependencies unmodeled',
        specification_coverage='not measured',benchmark_test_evaluated=False))
    print((ROOT/'summary.json').read_text(),flush=True)

if __name__=='__main__':
    main()
