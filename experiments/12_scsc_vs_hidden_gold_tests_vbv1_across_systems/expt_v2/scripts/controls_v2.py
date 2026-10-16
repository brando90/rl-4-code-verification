"""Run every frozen C1–C4 control with the frozen v2 adapter on the same 50 tasks, retaining per-task receipts and all failures."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
from adapter_v2 import TOP, strip_comments, declarations
from adapter_e12 import renamed_control
from support_v2 import PHASE, V1, WORK as DEFAULT_WORK, verify_inputs, atomic_json, workers_allowed, digest
from runtime_v2 import Runtime
from mutation_helpers_e12 import reachable_helpers
from rl4cv.forecast import verify_forecast

WORK=DEFAULT_WORK/'controls_v2'


def remove_propositions(source):
    source=strip_comments(source)  # Remove orphan docstrings together with proof declarations.
    events=list(TOP.finditer(source));remove=[]
    for i,m in enumerate(events):
        if m.group(1) in ('example','theorem','lemma'):
            remove.append((m.start(),events[i+1].start() if i+1<len(events) else len(source)))
    for a,b in reversed(remove):source=source[:a]+'\n'+source[b:]
    return source


def mutations(source,symbols,include_helpers=True):
    """Enumerate single operator/literal mutations in tested implementation bodies, by source position."""
    clean=strip_comments(source);clean=re.sub(r'"(?:\\.|[^"\\])*"',lambda m:' '*len(m.group()),clean)
    defs,_,_=declarations(source);events=list(TOP.finditer(clean));names={s['full_name'] for s in symbols}
    replacements={'==':'!=','!=':'==','≤':'<','≥':'>','<':'≤','>':'≥','+':'-','-':'+','*':'+',
                  '=':'≠','≠':'=','&&':'||','||':'&&','true':'false','false':'true'}
    for d in defs:
        if d['full_name'] not in names:continue
        end=min([m.start() for m in events if m.start()>d['start']] or [len(source)])
        for m in re.finditer(r'==|!=|&&|\|\||[≤≥<>+*≠]|(?<![:=])=(?!>)|(?<![>\w])-(?!>)|\b(?:true|false|[0-9]+)\b',clean[d['body_start']:end]):
            old=m.group();new=replacements.get(old,str(int(old)+1) if old.isdigit() else None)
            if new is None:continue
            offset=d['body_start']+m.start()
            yield source[:offset]+new+source[offset+len(old):],{'definition':d['full_name'],'offset':offset,'old':old,'new':new}


    # Deterministic fallback after all numeric/operator edits: one string literal.
    # It is reached only if no preceding edit compiles, never because a test survives.
    literal_source=strip_comments(source)
    for d in defs:
        if d['full_name'] not in names:continue
        end=min([m.start() for m in events if m.start()>d['start']] or [len(source)])
        for m in re.finditer(r'"(?:\\.|[^"\\])*"',literal_source[d['body_start']:end]):
            old=m.group();new='"e12_mutant'+old[1:];offset=d['body_start']+m.start()
            yield source[:offset]+new+source[offset+len(old):],{'definition':d['full_name'],'offset':offset,'old':old,'new':new,'fallback':'string_literal'}

    # Final fallback: implementation dependencies in source order; never fixtures
    # merely supplied by tests. Earlier successful mutant choices stay unchanged.
    if include_helpers:
        helpers=reachable_helpers(source,symbols)
        for mutant,metadata in mutations(source,helpers,include_helpers=False):
            yield mutant,{**metadata,'fallback':'reachable_helper'}


def check(pair):
    row,wrong=pair;key=hashlib.sha256(row['task_id'].encode()).hexdigest()[:20]
    receipt=WORK/(key+'.json')
    if receipt.exists():
        old=json.loads(receipt.read_text())
        assert old['runtime_hashes']==runtime_hashes()
        assert old['gold_sha256']==row['sha256']
        return old
    rt=Runtime(WORK);raw=Path(row['path']).read_text()
    assert hashlib.sha256(raw.encode()).hexdigest()==row['sha256']
    renamed,renames=renamed_control(raw,row['symbols'])
    result={'runtime_hashes':runtime_hashes(),'task_id':row['task_id'],'n_tests':row['n_tests'],'gold_sha256':row['sha256'],'rename_map':renames}
    result['C1']=rt.evaluate(row,raw,'E12C1'+key)
    result['C2']=rt.evaluate(row,renamed,'E12C2'+key)
    stripped=remove_propositions(raw);attempts=[]
    for i,(mutant,mutation) in enumerate(mutations(stripped,row['symbols'])):
        module='E12C3'+key+'m'+str(i);_,compiled=rt.compile(mutant,module)
        attempts.append({'mutation':mutation,'compile':compiled,'candidate_sha256':hashlib.sha256(mutant.encode()).hexdigest()})
        if compiled['status']=='ok':
            result['C3']=rt.evaluate(row,mutant,module,compiled)
            result['C3']['mutation']=mutation
            result['C3']['killed']=result['C3']['n_applicable']>result['C3']['n_pass']
            break
    if 'C3' not in result:result['C3']={'killed':False,'status':'no_compiling_mutant'}
    result['C3']['attempts']=attempts
    wrong_source=Path(wrong['path']).read_text();assert hashlib.sha256(wrong_source.encode()).hexdigest()==wrong['sha256']
    result['C4']=rt.evaluate(row,wrong_source,'E12C4'+key)
    result['C4']['wrong_task_id']=wrong['task_id'];result['C4']['wrong_gold_sha256']=wrong['sha256']
    result['C4']['rejected']=result['C4']['n_applicable']==0 or result['C4']['n_pass']<result['C4']['n_applicable']
    atomic_json(receipt,result);return result


def report(rows,selected):
    ntests=sum(r['n_tests'] for r in rows);passed=sum(r['C1']['n_pass'] for r in rows)
    eligible=[r for r in rows if r['C1']['all_pass']]
    recovered=sum(r['C2']['all_symbols_mapped'] and r['C2']['all_pass'] for r in eligible)
    complete=len(rows)==len(selected);mutants=sum(r['C3'].get('compile',{}).get('status')=='ok' for r in rows)
    killed=sum(r['C3']['killed'] for r in rows);rejected=sum(r['C4']['rejected'] for r in rows)
    controls={
      'C1':{'n_tests':ntests,'n_pass':passed,'fraction':passed/ntests if ntests else None,'threshold':.98,'passes':complete and passed>=.98*ntests},
      'C2':{'n_C1_passing_tasks':len(eligible),'n_recovered':recovered,'fraction':recovered/len(eligible) if eligible else None,'threshold':.95,'passes':complete and len(eligible)>0 and recovered>=.95*len(eligible)},
      'C3':{'n_compiling_mutants':mutants,'n_killed':killed,'fraction':killed/mutants if mutants else None,'threshold':.60,'passes':complete and mutants>=50 and killed>=.60*mutants},
      'C4':{'n_pairs':len(rows),'n_rejected':rejected,'fraction':rejected/len(rows) if rows else None,'threshold':.95,'passes':complete and rejected>=.95*len(rows)}}
    return {'version':'expt_v2','round':1,'attempt':'1','n_selected':len(selected),'n_completed':len(rows),'complete':complete,**controls,
            'all_controls_pass':all(c['passes'] for c in controls.values()),
            'selected_tasks':[r['task_id'] for r in selected],'rows':sorted(rows,key=lambda r:r['task_id']),
            'source_hashes':runtime_hashes()}


def runtime_hashes():
    return {f:digest(PHASE/'scripts'/f) for f in ('adapter_v2.py','runtime_v2.py','controls_v2.py','support_v2.py')}


def main():
    global WORK
    parser=argparse.ArgumentParser()
    parser.add_argument('--work',type=Path,default=WORK)
    parser.add_argument('--out',type=Path,default=PHASE/'results/controls_v2.json')
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args();WORK=args.work.resolve()
    workers_allowed(args.workers);verify_inputs()
    manifest=json.loads((V1/'results/hidden_tests_manifest.json').read_text())
    selected=sorted([r for r in manifest['tasks'] if r['n_tests']],key=lambda r:hashlib.sha256(('rl4cv-e12-ctl:'+r['task_id']).encode()).hexdigest())[:50]
    assert [r['task_id'] for r in selected]==json.loads((V1/'results/control_selection.json').read_text())['tasks']
    Runtime(WORK);rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(check,(r,selected[(i+1)%50])) for i,r in enumerate(selected)]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result());summary=report(rows,selected)
            atomic_json(args.out.with_name('controls_v2_progress.json'),summary)
            print(json.dumps({k:summary[k] for k in ('n_completed','C1','C2','C3','C4')}),flush=True)
    summary=report(rows,selected)
    atomic_json(args.out,summary)
    raise SystemExit(0 if summary['all_controls_pass'] else 2)


if __name__=='__main__':main()
