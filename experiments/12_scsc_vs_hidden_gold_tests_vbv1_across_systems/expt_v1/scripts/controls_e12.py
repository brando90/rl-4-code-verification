"""Run frozen gold and renamed-gold adapter admission controls with real Lean compilation and fail closed on ambiguity."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from adapter_e12 import bridge, map_symbols, renamed_control
from compile_reproduction import LAKE, LAKE_BIN
from extract_hidden_tests import PHASE
from rl4cv.forecast import verify_forecast

WORK=Path('/lfs/skampere1/0/brando9/rl4cv_e12/controls_round1')


def lean(path,extra=()):
    start=time.monotonic();env=os.environ.copy();env['LEAN_PATH']=str(WORK/'modules')
    p=subprocess.Popen(['nice','-n','10',LAKE_BIN,'env','lean','-j','1',*extra,str(path)],cwd=LAKE,
                       env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
    try:
        out,_=p.communicate(timeout=600);status='ok' if p.returncode==0 else 'error'
    except subprocess.TimeoutExpired:
        os.killpg(p.pid,signal.SIGKILL);out,_=p.communicate();status='timeout'
    log=path.with_suffix('.log');log.write_text(out)
    return {'status':status,'returncode':p.returncode,'seconds':time.monotonic()-start,
            'log':str(log),'outputs':{int(i):value=='true' for i,value in re.findall(r'^E12_TEST_(\d+)=(true|false)$',out,re.M)}}


def check(row):
    key=hashlib.sha256(row['task_id'].encode()).hexdigest()[:20];receipt=WORK/(key+'.json')
    if receipt.exists():return json.loads(receipt.read_text())
    raw=Path(row['path']).read_text();assert hashlib.sha256(raw.encode()).hexdigest()==row['sha256']
    renamed,renames=renamed_control(raw,row['symbols']);result={'task_id':row['task_id'],'n_tests':row['n_tests'],'gold_sha256':row['sha256']}
    for kind,source in [('C1',raw),('C2',renamed)]:
        module='E12'+kind+key;path=WORK/'modules'/(module+'.lean');path.write_text(source)
        compiled=lean(path,('--root='+str(WORK/'modules'),'-o',str(path.with_suffix('.olean'))))
        mapping,diagnostics=map_symbols(row['symbols'],source)
        fully_mapped=len(mapping)==len(row['symbols'])
        record={'compile':compiled,'mapping':mapping,'diagnostics':diagnostics,'all_symbols_mapped':fully_mapped,
                'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(), 'candidate_path':str(path)}
        if compiled['status']=='ok' and mapping:
            probe=WORK/(module+'_Bridge.lean');probe.write_text(bridge(module,row['tests'],mapping))
            evaluated=lean(probe);record['evaluation']=evaluated
            outputs=evaluated['outputs'];record['n_applicable']=len(outputs);record['n_pass']=sum(outputs.values())
            record['all_pass']=len(outputs)==row['n_tests'] and all(outputs.values())
        else:record.update(n_applicable=0,n_pass=0,all_pass=False)
        result[kind]=record
    result['rename_map']=renames
    # Mapping-only wrong-task control is diagnostic here; C1/C2 are the sequential admission gates.
    receipt.write_text(json.dumps(result,indent=1)+'\n')
    return result


def report(rows,selected):
    ntests=sum(r['n_tests'] for r in rows);passed=sum(r['C1']['n_pass'] for r in rows)
    c1passed=[r for r in rows if r['C1']['all_pass']]
    c2success=sum(r['C2']['all_symbols_mapped'] and r['C2']['compile']['status']=='ok' for r in c1passed)
    return {'round':1,'n_selected':len(selected),'n_completed':len(rows),'complete':len(rows)==len(selected),
            'C1':{'n_tests':ntests,'n_pass':passed,'fraction':passed/ntests if ntests else None,'threshold':.98,
                  'passes':len(rows)==len(selected) and passed>=.98*ntests},
            'C2':{'n_C1_passing_tasks':len(c1passed),'n_recovered':c2success,
                  'fraction':c2success/len(c1passed) if c1passed else None,'threshold':.95,
                  'passes':len(rows)==len(selected) and bool(c1passed) and c2success>=.95*len(c1passed)},
            'C3':{'status':'NOT_RUN_PENDING_C1_C2_ADMISSION'},'C4':{'status':'NOT_RUN_PENDING_C1_C2_ADMISSION'},
            'selected_tasks':[r['task_id'] for r in selected],'rows':sorted(rows,key=lambda r:r['task_id']),
            'source_hashes':{f:hashlib.sha256((PHASE/'scripts'/f).read_bytes()).hexdigest() for f in ['extract_hidden_tests.py','adapter_e12.py','controls_e12.py']}}


def main():
    for name in ('e12_phase_a_forecast','e12_phase_a_forecast_amendment_A1'):
        assert verify_forecast(PHASE/'forecasts'/(name+'.json'))
    assert json.loads((PHASE/'results/compile_reproduction_A1.json').read_text())['passes']
    manifest=json.loads((PHASE/'results/hidden_tests_manifest.json').read_text())
    selected=sorted([r for r in manifest['tasks'] if r['n_tests']],key=lambda r:hashlib.sha256(('rl4cv-e12-ctl:'+r['task_id']).encode()).hexdigest())[:50]
    assert len(selected)==50
    (WORK/'modules').mkdir(parents=True,exist_ok=True)
    selection=PHASE/'results/control_selection.json';payload={'salt':'rl4cv-e12-ctl:','tasks':[r['task_id'] for r in selected],
                            'hidden_tests_manifest_sha256':hashlib.sha256((PHASE/'results/hidden_tests_manifest.json').read_bytes()).hexdigest()}
    if selection.exists():assert json.loads(selection.read_text())==payload
    else:selection.write_text(json.dumps(payload,indent=1)+'\n')
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(check,r) for r in selected]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result());summary=report(rows,selected)
            (PHASE/'results/controls_e12_progress.json').write_text(json.dumps(summary,indent=1)+'\n')
            print(json.dumps({k:summary[k] for k in ('n_completed','C1','C2')}),flush=True)
    summary=report(rows,selected)
    (PHASE/'results/controls_e12.json').write_text(json.dumps(summary,indent=1)+'\n')
    raise SystemExit(0 if summary['C1']['passes'] and summary['C2']['passes'] else 2)


if __name__=='__main__':main()
