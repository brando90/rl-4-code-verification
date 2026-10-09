"""Evaluate every frozen primary and secondary cell after all four controls pass and the protocol is locked, caching identical task/code pairs."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import time
from extract_hidden_tests import PHASE
from runtime_e12 import Runtime
from rl4cv.forecast import verify_forecast

WORK=Path('/lfs/skampere1/0/brando9/rl4cv_e12')
OUT=WORK/'cells_e12.jsonl'


def cell_key(row):
    return (row['panel'],row['system'],row['task_id'],row.get('sample_idx',0))



def infra_failure(value):
    if isinstance(value,dict):
        if value.get('status')=='error' and (value.get('returncode',0) or 0) in (-9,-15,137,143):return True
        return any(infra_failure(v) for v in value.values())
    if isinstance(value,list):return any(infra_failure(v) for v in value)
    return False


def archive_logs(value,directory):
    directory.mkdir(parents=True,exist_ok=True)
    if isinstance(value,dict):
        out={k:archive_logs(v,directory) for k,v in value.items()}
        if isinstance(value.get('log'),str):
            old=Path(value['log']);new=directory/old.name
            if old.exists():shutil.copyfile(old,new);out['log']=str(new)
        return out
    if isinstance(value,list):return [archive_logs(v,directory) for v in value]
    return value


def recover_jsonl(path):
    """Newline is the commit boundary; archive an interrupted final write before truncating it."""
    raw=path.read_bytes()
    if raw and not raw.endswith(b'\n'):
        stop=raw.rfind(b'\n')+1;tail=path.with_name(path.name+'.partial_tail.'+str(time.time_ns()))
        tail.write_bytes(raw[stop:])
        # Validate all committed lines before changing the log.
        rows=[json.loads(line) for line in raw[:stop].splitlines()]
        with path.open('r+b') as stream:stream.truncate(stop)
        print(json.dumps({'recovered_interrupted_tail':str(tail),'bytes':len(raw)-stop}),flush=True)
        return rows
    return [json.loads(line) for line in raw.splitlines()]


def summary(rows,declared):
    panels={}
    for r in rows:
        d=panels.setdefault(r['panel'],{'n_cells':0,'n_compiling':0,'n_applicable':0,'n_hidden_all_pass':0,'n_hidden_missing':0,'n_no_tests':0})
        d['n_cells']+=1;d['n_compiling']+=r['compiles'] is True;d['n_applicable']+=r['applicable']
        d['n_hidden_all_pass']+=r['hidden_all_pass']==1;d['n_hidden_missing']+=r['hidden_all_pass'] is None
        d['n_no_tests']+=r['status']=='no_tests'
    return {'n_declared':declared,'n_completed':len(rows),'complete':len(rows)==declared,'panels':panels}


def main():
    for name in ('e12_phase_a_forecast','e12_phase_a_forecast_amendment_A1','e12_phase_a_forecast_amendment_A2'):
        assert verify_forecast(PHASE/'forecasts'/(name+'.json'))
    protocol=(PHASE.parent/'PROTOCOL.md').read_text()
    assert '**Lock line:** `LOCKED ' in protocol
    controls=json.loads((PHASE/'results/controls_e12.json').read_text());assert controls['all_controls_pass']
    for name,digest in controls['source_hashes'].items():assert hashlib.sha256((PHASE/'scripts'/name).read_bytes()).hexdigest()==digest
    lock=json.loads((PHASE/'results/protocol_lock.json').read_text())
    for name,digest in lock['input_hashes'].items():assert hashlib.sha256((PHASE/'results'/name).read_bytes()).hexdigest()==digest
    rows=[]
    for name in ['input_manifest_A1.json','secondary_manifest_A1.json']:
        rows+=json.loads((PHASE/'results'/name).read_text())['cells']
    assert len(rows)==43840 and len({cell_key(r) for r in rows})==43840
    suites={r['task_id']:r for r in json.loads((PHASE/'results/hidden_tests_manifest.json').read_text())['tasks']}
    run_manifest=WORK/'evaluation_run_manifest.json'
    provenance={'protocol_lock_sha256':hashlib.sha256((PHASE/'results/protocol_lock.json').read_bytes()).hexdigest(),
                'evaluator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'n_declared':len(rows),'infrastructure_retry_limit':1}
    if run_manifest.exists():assert json.loads(run_manifest.read_text())==provenance
    else:run_manifest.write_text(json.dumps(provenance,indent=2)+'\n')
    records={}
    if OUT.exists():
        for r in recover_jsonl(OUT):
            assert cell_key(r) not in records;records[cell_key(r)]=r
    assert set(records)<={cell_key(r) for r in rows}
    groups={};rt=Runtime(WORK/'evaluation_A2');done=0
    def base(row):
        return {**row,'compiles':row['recorded_compiles'],'n_tests':suites[row['task_id']]['n_tests']}
    def outcome(row,status,napp=0,npass=0,allpass=None,diagnostics=None,receipt=None):
        return {**base(row),'status':status,'applicable':napp>0,'n_applicable':napp,'n_pass':npass,
                'n_unknown':suites[row['task_id']]['n_tests']-napp,'hidden_all_pass':allpass,
                'hidden_pass_rate':npass/napp if napp else (0 if status=='noncompiling' else None),
                'mapping_steps':[d['step'] for d in (diagnostics or []) if d['status']=='mapped'],
                'all_mappings_unambiguous':bool(diagnostics) and all(d['step'] in (1,2) for d in diagnostics),
                'receipt':receipt}
    with OUT.open('a') as stream:
        def emit(record):
            key=cell_key(record);assert key not in records
            stream.write(json.dumps(record,separators=(',',':'))+'\n');stream.flush();records[key]=record
        for row in rows:
            if cell_key(row) in records:continue
            if not suites[row['task_id']]['n_tests']:emit(outcome(row,'no_tests'))
            elif row['join_status'] in ('file_missing','join_ambiguous'):emit(outcome(row,row['join_status']))
            elif row['recorded_compiles'] is False:emit(outcome(row,'noncompiling',allpass=0))
            elif row['recorded_compiles'] is None:emit(outcome(row,'unmeasured_compile'))
            else:
                key=hashlib.sha256((row['task_id']+':'+row['sha256']).encode()).hexdigest()
                groups.setdefault(key,[]).append(row)
        def evaluate(item):
            key,group=item;row=group[0];receipt=rt.root/(key+'.json')
            if receipt.exists():return key,json.loads(receipt.read_text())
            raw=Path(row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
            result=rt.evaluate(suites[row['task_id']],raw.decode(),'E12Eval'+key[:24])
            if infra_failure(result):
                previous=archive_logs(result,rt.root/'infrastructure_attempts'/key)
                result=rt.evaluate(suites[row['task_id']],raw.decode(),'E12Eval'+key[:24])
                result['infrastructure_retries']=[previous]
            result['task_id']=row['task_id'];result['input_sha256']=row['sha256']
            receipt.write_text(json.dumps(result,indent=1)+'\n');return key,result
        initial=summary(list(records.values()),len(rows));initial['n_unique_pending_compilations']=len(groups)
        (PHASE/'results/evaluation_progress.json').write_text(json.dumps(initial,indent=1)+'\n');print(json.dumps(initial),flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(evaluate,item) for item in groups.items()]
            for future in concurrent.futures.as_completed(futures):
                try:key,result=future.result()
                except Exception as error:
                    print(json.dumps({'fatal_evaluation_error':repr(error),'n_completed':len(records)}),flush=True)
                    pool.shutdown(wait=True,cancel_futures=True)
                    raise
                napp=result['n_applicable'];npass=result['n_pass']
                status='evaluated' if napp else ('recompile_unknown' if result['compile']['status']!='ok' else 'not_applicable')
                for row in groups[key]:
                    emit(outcome(row,status,napp,npass,int(result['all_pass']) if napp else None,result['diagnostics'],str(rt.root/(key+'.json'))))
                done+=1
                if done%10==0 or done==len(groups):
                    report=summary(list(records.values()),len(rows));report['unique_jobs_completed']=done;report['unique_jobs_this_resume']=len(groups)
                    (PHASE/'results/evaluation_progress.json').write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report),flush=True)
    final=summary(list(records.values()),len(rows));assert final['complete']
    final['outcomes_sha256']=hashlib.sha256(OUT.read_bytes()).hexdigest();final['outcomes_path']=str(OUT)
    (PHASE/'results/evaluation_complete.json').write_text(json.dumps(final,indent=1)+'\n')


if __name__=='__main__':main()
