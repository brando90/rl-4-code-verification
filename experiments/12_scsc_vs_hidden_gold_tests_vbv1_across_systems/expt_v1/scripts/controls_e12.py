"""Run every frozen C1–C4 control under Amendment A2 on the same 50 tasks, retaining per-task receipts and all failures."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
from adapter_e12 import TOP, renamed_control, strip_comments, declarations
from extract_hidden_tests import PHASE
from runtime_e12 import Runtime
from mutation_helpers_e12 import reachable_helpers
from rl4cv.forecast import verify_forecast

WORK=Path('/lfs/skampere1/0/brando9/rl4cv_e12/controls_round5')


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
    defs,_=declarations(source);events=list(TOP.finditer(clean));names={s['full_name'] for s in symbols}
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
    if receipt.exists():return json.loads(receipt.read_text())
    rt=Runtime(WORK);raw=Path(row['path']).read_text()
    assert hashlib.sha256(raw.encode()).hexdigest()==row['sha256']
    renamed,renames=renamed_control(raw,row['symbols'])
    result={'task_id':row['task_id'],'n_tests':row['n_tests'],'gold_sha256':row['sha256'],'rename_map':renames}
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
    receipt.write_text(json.dumps(result,indent=1)+'\n');return result


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
    return {'round':5,'attempt':'5','n_selected':len(selected),'n_completed':len(rows),'complete':complete,**controls,
            'all_controls_pass':all(c['passes'] for c in controls.values()),
            'selected_tasks':[r['task_id'] for r in selected],'rows':sorted(rows,key=lambda r:r['task_id']),
            'source_hashes':{f:hashlib.sha256((PHASE/'scripts'/f).read_bytes()).hexdigest() for f in ['extract_hidden_tests.py','fixture_inputs_e12.py','adapter_e12.py','runtime_e12.py','controls_e12.py','mutation_helpers_e12.py']}}


def main():
    for name in ('e12_phase_a_forecast','e12_phase_a_forecast_amendment_A1','e12_phase_a_forecast_amendment_A2'):
        assert verify_forecast(PHASE/'forecasts'/(name+'.json'))
    assert json.loads((PHASE/'results/compile_reproduction_A1.json').read_text())['passes']
    manifest=json.loads((PHASE/'results/hidden_tests_manifest.json').read_text())
    selected=sorted([r for r in manifest['tasks'] if r['n_tests']],key=lambda r:hashlib.sha256(('rl4cv-e12-ctl:'+r['task_id']).encode()).hexdigest())[:50]
    assert [r['task_id'] for r in selected]==json.loads((PHASE/'results/control_selection.json').read_text())['tasks']
    Runtime(WORK);rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(check,(r,selected[(i+1)%50])) for i,r in enumerate(selected)]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result());summary=report(rows,selected)
            (PHASE/'results/controls_e12_progress.json').write_text(json.dumps(summary,indent=1)+'\n')
            print(json.dumps({k:summary[k] for k in ('n_completed','C1','C2','C3','C4')}),flush=True)
    summary=report(rows,selected)
    (PHASE/'results/controls_e12.json').write_text(json.dumps(summary,indent=1)+'\n')
    raise SystemExit(0 if summary['all_controls_pass'] else 2)


if __name__=='__main__':main()
