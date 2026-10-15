"""Evaluate the frozen independent mixed-group forecast once, bounding every missing train outcome."""
from __future__ import annotations

import numpy as np
from g1_bounds import bound_association_interval,bound_linear,coefficients


def mixed_labels(rows,tasks):
    tasks=list(tasks);table={}
    for row in rows:
        key=(row['task_id'],row['sample_idx'])
        if (row['split']!='train' or row['batch']!='full2' or row['policy']!='sft_4B_f1p0'
                or row['task_id'] not in tasks or type(row['sample_idx']) is not int
                or not 0<=row['sample_idx']<8 or key in table
                or row['cell_id']!=f"full2/{key[0]}/{key[1]}"):
            raise ValueError('independent batch identity or split mismatch')
        if row['status'] in ('integrity_defect','unresolved_cleanup'):
            raise ValueError('unresolved integrity or cleanup defect blocks H2')
        if row['status']=='measured' and row['strict'] not in (False,True,0,1):
            raise ValueError('observed strict outcome is not binary')
        table[key]=row
    if set(table)!={(t,s) for t in tasks for s in range(8)}:
        raise ValueError('independent batch does not account for every declared slot')
    labels=[];known_responses=0;fully_measured=0
    for task in tasks:
        known=[table[(task,s)]['strict'] for s in range(8) if table[(task,s)]['status']=='measured']
        known_responses+=len(known);fully_measured+=int(len(known)==8)
        labels.append(1. if len(set(known))==2 else 0. if len(known)==8 else np.nan)
    return np.asarray(labels),{'declared_tasks':len(tasks),'fully_measured_tasks':fully_measured,
        'identified_mixed_labels':int(np.isfinite(labels).sum()),'unknown_mixed_labels':int(np.isnan(labels).sum()),
        'measured_responses':known_responses,'declared_responses':len(tasks)*8}


def evaluate(rows,tasks,prediction,groups,*,forecast_admitted,draws=10000,seed=1302031):
    """AUC bounds reuse the published exact A3 association algorithm; predictions never refit."""
    y,counts=mixed_labels(rows,tasks)
    result={'condition':'v2-S2','gate':'H2','status':'INCONCLUSIVE','disable_arm_C':True,
        'threshold':.70,'threshold_source':'PROTOCOL section 4','F2':.75,'forecast_admitted':forecast_admitted,
        'counts':counts,'p_value':None,'p_value_reason':'fixed prospective admission threshold, no null-hypothesis test',
        'uncertainty':'paired task-group bootstrap conditional on fixed train-calibrated predictions; no fit uncertainty'}
    if prediction is None:
        return {**result,'reason':'train strict forecast unavailable; no substitute forecast'}
    p=np.asarray(prediction,float);groups=np.asarray(groups)
    if p.shape!=y.shape or groups.shape!=y.shape or not np.isfinite(p).all() or np.any((p<0)|(p>1)):
        raise ValueError('unaligned or invalid frozen H2 predictions')
    auc=bound_association_interval(y,p,groups,'auc',draws=draws,seed=seed)
    result['auc']=auc;result['diagnostics']={}
    for metric in ('predicted_mean','observed_mean','mean_bias','mean_absolute_error'):
        a,b=coefficients(p,metric)
        result['diagnostics'][metric]=bound_linear(y,a,b,groups,draws=draws,seed=seed)[0]
    if auc['maximum'] is not None and auc['maximum']<.70:
        result.update(status='FAIL',reason='maximum feasible AUC is below .70')
    elif (forecast_admitted and not auc['undefined_possible'] and auc['minimum'] is not None
          and auc['minimum']>=.70):
        result.update(status='PASS',disable_arm_C=False,reason='minimum feasible AUC clears .70')
    else:
        result['reason']='undefined/unidentified forecast or completion range cannot certify admission'
    result['F2_observed_minus_forecast_bounds']=[None if auc[k] is None else auc[k]-.75 for k in ('minimum','maximum')]
    return result


def verify(plan):
    """Require published pre-fit methods, frozen predictions and an accounted independent panel."""
    from pathlib import Path
    from panel import digest
    from g1_driver import verify_publication,verify_fit_lock
    method=verify_publication(plan['method_lock'],plan['repository'],plan['method_revision'])
    lock=verify_publication(plan['input_lock'],plan['repository'],plan['input_revision'])
    for value,gate in ((method,'CALIBRATION_S2_METHOD'),(lock,'H2_S2_INPUTS')):
        if value.get('gate')!=gate or value.get('condition')!='v2-S2' or value.get('status')!='FROZEN':
            raise ValueError('unfrozen or wrong-condition H2 lock')
        for binding in value['bindings']:
            if digest(binding['path'])!=binding['sha256']:raise ValueError('H2 binding changed')
    if lock['method_sha256']!=digest(plan['method_lock']):raise ValueError('H2 inputs name another method')
    if str(Path(__file__).resolve()) not in {b['path'] for b in method['bindings']}:
        raise ValueError('H2 executable is unbound')
    verify_fit_lock(method['g1_lock'],plan['repository'],method['g1_revision'])
    config=lock['configuration'];bound={b['path'] for b in lock['bindings']}
    if not {config[k] for k in ('calibration','predictions','F2','cells','scoring_report','train_ids','train_features')}<=bound:
        raise ValueError('H2 input or provenance is unbound')
    calibration=verify_publication(config['calibration'],plan['repository'],config['calibration_revision'])
    if (calibration.get('status')!='FROZEN' or calibration.get('condition')!='v2-S2'
            or calibration.get('F2')!=.75 or calibration.get('method_sha256')!=digest(plan['method_lock'])):
        raise ValueError('H2 requires this published calibration and F2')
    artifacts={b['path']:b['sha256'] for b in calibration['artifacts']}
    if any(artifacts.get(config[k])!=digest(config[k]) for k in ('predictions','F2')):
        raise ValueError('H2 predictions are not the frozen calibration artifacts')
    report=verify_publication(config['scoring_report'],plan['repository'],config['scoring_revision'])
    if (report.get('condition')!='v2-S2' or report.get('batch')!='full2'
            or report.get('declared')!=4312 or report.get('accounted')!=4312
            or report.get('status') not in ('COMPLETE','INCOMPLETE')
            or report.get('cells_sha256')!=digest(config['cells'])
            or report.get('calibration_sha256')!=digest(config['calibration'])):
        raise ValueError('independent scoring receipt or calibration chronology mismatch')
    return config


def run(plan_path):
    """One final H2 evaluation; completed or interrupted attempts cannot silently repeat."""
    import json,time
    from pathlib import Path
    from panel import digest
    from anchor_storage import mkdir,write_new
    from g1_driver import json_safe
    plan=json.loads(Path(plan_path).read_text());config=verify(plan)
    tasks=Path(config['train_ids']).read_text().splitlines()
    if len(tasks)!=539 or len(set(tasks))!=539:raise ValueError('H2 requires all 539 train tasks')
    prediction=json.loads(Path(config['predictions']).read_text())
    features=json.loads(Path(config['train_features']).read_text())
    if (prediction.get('condition')!='v2-S2' or prediction['tasks']!=tasks
            or prediction.get('source_batch')!='full1' or prediction.get('target_batch')!='full2'
            or set(features)!=set(tasks) or prediction['groups']!=[features[t]['group_id'] for t in tasks]):
        raise ValueError('frozen train prediction alignment changed')
    f2=json.loads(Path(config['F2']).read_text())
    if f2.get('version')!='v2-S2' or f2.get('prediction')!=.75 or f2.get('admission_threshold')!=.70:
        raise ValueError('F2 prediction or admission threshold changed')
    root=Path(plan['root']);mkdir(root)
    write_new(root/'attempt.json',{'condition':'v2-S2','started_unix':time.time(),'retries':0,
        'method_sha256':digest(plan['method_lock']),'input_sha256':digest(plan['input_lock']),
        'predictions_sha256':digest(config['predictions'])})
    result={'condition':'v2-S2','gate':'H2','status':'INCOMPLETE','disable_arm_C':True,'retries':0}
    try:
        rows=[json.loads(line) for line in Path(config['cells']).read_text().splitlines()]
        result.update(evaluate(rows,tasks,prediction['mixed_group_probability'],prediction['groups'],
                               forecast_admitted=prediction['forecast_admitted']))
    except BaseException as exc:
        result.update(error_type=type(exc).__name__,error=str(exc));raise
    finally:
        result.update(ended_unix=time.time(),calibration_sha256=digest(config['calibration']),
                      input_sha256=digest(plan['input_lock']))
        write_new(root/'result.json',json_safe(result))
    return result


if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',required=True,type=Path)
    print(json.dumps(run(parser.parse_args().plan),sort_keys=True))
