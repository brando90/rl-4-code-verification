"""Execute one published train calibration and freeze its artifacts and F2 before independent batch 2."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import time

from panel import digest
from anchor_storage import write_new,mkdir
from g1_driver import verify_publication,verify_fit_lock,json_safe
from calibration_inputs import anchor_arrays,BATCHES,pattern_report
from calibration_fit import fit_marginals,fit_strict_forecast,reward_variance


def verify(plan):
    method=verify_publication(plan['method_lock'],plan['repository'],plan['method_revision'])
    inputs=verify_publication(plan['input_lock'],plan['repository'],plan['input_revision'])
    for lock,gate in ((method,'CALIBRATION_S2_METHOD'),(inputs,'CALIBRATION_S2_INPUTS')):
        if lock.get('gate')!=gate or lock.get('status')!='FROZEN' or lock.get('condition')!='v2-S2':
            raise ValueError('unfrozen or wrong-condition calibration lock')
        for b in lock['bindings']:
            if digest(b['path'])!=b['sha256']:raise ValueError('calibration binding changed: '+b['path'])
    if inputs['method_sha256']!=digest(plan['method_lock']):raise ValueError('calibration inputs name another method')
    required={str(Path(__file__).resolve()),*[str(Path(__file__).with_name(n).resolve()) for n in
        ('calibration_inputs.py','calibration_fit.py','calibration_controls.py')]}
    required.update((method['g1_lock'],method['B_reward_source']))
    if not required<={b['path'] for b in method['bindings']}:raise ValueError('calibration execution code is unbound')
    verify_fit_lock(method['g1_lock'],plan['repository'],method['g1_revision'])
    if method['F2']!=.75 or method['variance_threshold']!=.15:
        raise ValueError('calibration forecast or gate threshold changed')
    bound={b['path'] for b in inputs['bindings']};config=inputs['configuration']
    if not config['full2_must_not_exist'] or config['full2_must_not_exist']!=method['full2_must_not_exist']:
        raise ValueError('independent full2 chronology guard is absent or changed')
    if any(Path(p).exists() for p in config['full2_must_not_exist']):
        raise ValueError('independent full2 already started before calibration freeze')
    if not {config['train_ids'],config['train_features'],config['LP1_result']}<=bound:
        raise ValueError('calibration allowlist, groups or admission is unbound')
    lp1=verify_publication(config['LP1_result'],plan['repository'],config['LP1_revision'])
    if lp1.get('status')!='PASS' or lp1.get('condition')!='v2-S2' or not lp1.get('admission_statistics_computed'):
        raise ValueError('calibration requires final S2 LP-1 PASS')
    if set(config['scoring'])!=set(BATCHES):raise ValueError('three connected train policies required')
    for batch,scoring in config['scoring'].items():
        if not {scoring['report'],scoring['cells'],scoring['generation_lock']}<=bound:
            raise ValueError('unbound scored panel')
        report=verify_publication(scoring['report'],plan['repository'],scoring['revision'])
        if (report.get('condition')!='v2-S2' or report.get('batch')!=batch
                or report.get('declared')!=4312 or report.get('accounted')!=4312
                or report.get('generation_lock_sha256')!=digest(scoring['generation_lock'])
                or report.get('status') not in ('COMPLETE','INCOMPLETE')
                or report.get('cells_sha256')!=digest(scoring['cells'])):
            raise ValueError('scoring receipt does not establish the complete S2 panel')
    return method,config


def load_arrays(config):
    tasks=Path(config['train_ids']).read_text().splitlines()
    if len(tasks)!=539 or len(set(tasks))!=539:raise ValueError('calibration is the complete 539-task train panel')
    rows=[]
    for batch,record in config['scoring'].items():
        cells=[json.loads(line) for line in Path(record['cells']).read_text().splitlines()]
        if len(cells)!=4312 or any(r['batch']!=batch for r in cells):raise ValueError('scoring manifest changed')
        if any(r['status'] in ('integrity_defect','unresolved_cleanup') for r in cells):
            raise ValueError('integrity or cleanup defect must be resolved before any calibration')
        rows.extend(cells)
    arrays=anchor_arrays(rows,tasks)
    features=json.loads(Path(config['train_features']).read_text())
    if set(features)!=set(tasks):raise ValueError('train group coverage differs from calibration manifest')
    arrays['groups']=[features[t]['group_id'] for t in tasks]
    return arrays


def placebo(arrays,reward_source):
    """Use the exact frozen B implementation, with every missing full1 slot disclosed."""
    spec=importlib.util.spec_from_file_location('e13_calibration_frozen_B',reward_source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    values=[];missing=[]
    for task in arrays['tasks']:
        for sample in range(8):
            row=arrays['table'][('full1',task,sample)]
            if row['status']=='measured':values.append(module.family_reward(row,row['strict']))
            else:missing.append(row['cell_id'])
    return {'condition':'v2-S2','source':'full1 fixed B distribution','values':values,
            'measured':len(values),'declared':len(arrays['tasks'])*8,'missing_cells':missing,
            'scope':'empirical distribution on measured calibration outputs; missing cells are not assigned zero',
            'reward_source_sha256':digest(reward_source)}


def run(plan_path):
    plan=json.loads(Path(plan_path).read_text());method,config=verify(plan)
    arrays=load_arrays(config);root=Path(plan['root']);mkdir(root)
    write_new(root/'attempt.json',{'condition':'v2-S2','started_unix':time.time(),'retries':0,
        'method_sha256':digest(plan['method_lock']),'inputs_sha256':digest(plan['input_lock']),
        'g1_lock_sha256':digest(method['g1_lock'])})
    def save(name,value):write_new(root/(name+'.json'),json_safe(value))
    result={'condition':'v2-S2','status':'INCOMPLETE','retries':0,'F2':.75,
            'method_sha256':digest(plan['method_lock']),'inputs_sha256':digest(plan['input_lock']),
            'g1_lock_sha256':digest(method['g1_lock']),'C_calibration_admitted':False}
    try:
        counts=pattern_report(arrays);save('denominator_patterns',counts)
        distribution=placebo(arrays,method['B_reward_source']);save('placebo_distribution',distribution)
        models,marginal,numerical=fit_marginals(arrays,save)
        strict=fit_strict_forecast(arrays,save);save('strict_forecast',strict)
        variance=reward_variance(arrays,models);save('reward_variance',variance)
        save('item_parameters',{'condition':'v2-S2','tasks':arrays['tasks'],'models':models,
            'item_parameters_fixed':True,'scale':'three anchor policies, mean zero/variance one per component',
            'marginal_component_independence_claim':False})
        predicted=strict['probabilities']
        save('H2_predictions',{'condition':'v2-S2','tasks':arrays['tasks'],'groups':arrays['groups'],
            'strict_probability':predicted,'mixed_group_probability':None if predicted is None else 1-predicted**8-(1-predicted)**8,
            'forecast_admitted':strict['admitted'],'source_batch':'full1','target_batch':'full2'})
        from rl4cv.forecast import freeze_forecast
        forecast=freeze_forecast({'experiment':'13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013',
            'version':'v2-S2','name':'F2','target':'train mixed-strict-group AUC on independent full2',
            'prediction':.75,'admission_threshold':.70,'declared_train_tasks':539,'samples_per_task':8,
            'method_revision':plan['method_revision'],'inputs_sha256':digest(plan['input_lock']),
            'observed_information':'Base, half and full1 train calibration only; full2 not generated or scored'},
            root/'forecast','F2_S2',outcomes_observed=False)
        result.update(status='FROZEN',C_calibration_admitted=bool(all(r['admitted'] for r in marginal.values())
            and strict['admitted'] and variance['status']=='PASS'),marginal_admission={k:r['admitted'] for k,r in marginal.items()},
            strict_forecast_admitted=strict['admitted'],variance_status=variance['status'],
            placebo_measured=distribution['measured'],placebo_declared=distribution['declared'],F2_forecast=forecast,
            observed_cells=counts['measured'],declared_cells=counts['declared'],
            global_C_admission='still requires G1 and independent H2',
            artifacts=[{'path':str(p),'sha256':digest(p)} for p in sorted(root.rglob('*.json')) if p.name!='result.json'])
    except BaseException as exc:
        result.update(error_type=type(exc).__name__,error=str(exc));raise
    finally:
        result['ended_unix']=time.time();save('result',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',type=Path,required=True)
    print(json.dumps(run(parser.parse_args().plan),sort_keys=True))
