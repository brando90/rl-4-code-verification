"""Run the unchanged historical G1 fit once under A6's published batch-2 waiver."""
from __future__ import annotations
import argparse,json,time,traceback
from pathlib import Path
from g1_driver import (verify_publication,verify_fit_lock,digest,write_new,json_safe,
                       combined_status,load,run_forecast)


def check_order(prerequisites, lock):
    if set(prerequisites)!={'lp1','calibration','h2_f2_a6'}:
        raise ValueError('A6 requires LP-1, frozen calibration and the published H2/F2 waiver')
    values={}
    for name,b in prerequisites.items():
        if digest(b['path'])!=b['sha256']:raise ValueError('prerequisite hash mismatch: '+name)
        values[name]=json.loads(Path(b['path']).read_text())
    lp=values['lp1'];cal=values['calibration'];waiver=values['h2_f2_a6']
    if lp.get('status')!='PASS' or lp.get('admission_statistics_computed')is not True:
        raise ValueError('LP-1 statistics did not pass')
    if cal.get('status')!='FROZEN' or cal.get('F2')!=.75 or cal.get('g1_lock_sha256')!=lock['self_sha256']:
        raise ValueError('original calibration and G1 freeze required')
    if cal.get('strict_forecast_admitted')is not False or cal.get('C_calibration_admitted')is not False:
        raise ValueError('A6 waiver requires unavailable strict forecast and disabled C')
    if (waiver.get('condition')!='v2-S2' or waiver.get('calibration_sha256')!=prerequisites['calibration']['sha256']
            or waiver.get('H2')!={'status':'UNAVAILABLE','predictor':None,'auc':None}
            or waiver.get('F2')!={'status':'UNAVAILABLE','prospectively_frozen_value':.75,'observed':None}
            or waiver.get('batch2')!={'status':'SKIPPED_A6','responses':0,'armed':False}
            or waiver.get('disable_arm_C')is not True):
        raise ValueError('A6 unavailable predictor waiver changed')
    return values


def verify(lock_path,repository,revision):
    successor=verify_publication(lock_path,repository,revision)
    if successor.get('gate')!='G1_A6' or successor.get('status')!='FROZEN':raise ValueError('published A6 G1 lock required')
    for b in successor['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('A6 execution binding changed')
    bound={str(Path(b['path']).resolve()):b['sha256']for b in successor['bindings']}
    if bound.get(str(Path(__file__).resolve()))!=digest(__file__):raise ValueError('A6 wrapper not bound')
    amendment=Path(successor['amendment']['path'])
    import subprocess,hashlib
    blob=subprocess.check_output(['git','show',successor['amendment']['revision']+':'+str(amendment.relative_to(repository))],cwd=repository)
    subprocess.run(['git','merge-base','--is-ancestor',successor['amendment']['revision'],'origin/main'],cwd=repository,check=True,capture_output=True)
    if hashlib.sha256(blob).hexdigest()!=digest(amendment) or bound.get(str(amendment))!=digest(amendment):raise ValueError('adopted amendment changed')
    old=successor['original_G1'];lock,paths=verify_fit_lock(old['path'],repository,old['revision'])
    if digest(old['path'])!=old['sha256']:raise ValueError('original G1 method changed')
    lock['self_sha256']=digest(old['path'])
    prerequisites=successor['prerequisites']
    for b in prerequisites.values():verify_publication(b['path'],repository,revision if b['published_revision']=='SELF' else b['published_revision'])
    if json.loads(Path(prerequisites['h2_f2_a6']['path']).read_text())['amendment_sha256']!=digest(amendment):raise ValueError('waiver names another amendment')
    check_order(prerequisites,lock)
    return successor,lock,paths


def run(lock_path,repository,revision,root):
    successor,lock,paths=verify(lock_path,repository,revision)
    prerequisites=successor['prerequisites']
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    write_new(root/'attempt.json',{'started_unix':time.time(),'lock_sha256':lock['self_sha256'],
              'revision':revision,'prerequisites':prerequisites,'retries':0,'completion_refits':False})
    result={'gate':'G1','status':'INCONCLUSIVE','disable_arm_C':True,'retries':0,'completion_refits':False}
    try:
        systems=json.loads(paths['policy_metadata'].read_text())['systems']
        rows,excluded,groups=load(lock['input_bindings'],systems)
        source=json.loads(paths['validation_features'].read_text())
        if set(source)!=set(groups) or any(source[t]['group_id']!=groups[t] for t in groups):
            raise ValueError('feature task/group denominator differs from prediction grid')
        features={t:source[t]['features'] for t in source}
        def sink(forecasts):
            write_new(root/(forecasts['scheme']+'.forecasts.json'),json_safe(forecasts))
        outputs=run_forecast(rows,systems,features,groups,excluded_ids=excluded,
                             draws=lock['bootstrap']['draws'],forecast_sink=sink)
        status=combined_status(outputs)
        write_new(root/'outputs.json',json_safe(outputs))
        result.update(status=status,disable_arm_C=status!='PASS',declared_historical_cells=len(rows),
                      excluded_alias_cells=len(excluded),tasks=len(groups),
                      schemes={name:data['evaluation'] for name,data in outputs.items()},
                      outputs_sha256=digest(root/'outputs.json'))
    except BaseException as exc:
        (root/'error.txt').write_text(traceback.format_exc())
        result.update(error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        write_new(root/'result.json',json_safe(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('lock','repository','root'):p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--published-revision',required=True);a=p.parse_args()
    print(json.dumps(run(a.lock,a.repository,a.published_revision,a.root),allow_nan=False))
