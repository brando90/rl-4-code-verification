"""Freeze all independent selected-test inputs and validated hosted packs without making measurements."""
from __future__ import annotations

import copy,json
from pathlib import Path

from selected_coverage_inputs import authority,prepare as normalize,verify_evidence
from selected_coverage import build,helper,SUITE
from hidden_controls import extract,E12
from coverage_controls import CONFIGS
from technical_ledger import published
from technical_driver import bindings,read,reference
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def source_authority(selection,extra):
    tasks,score,score_lock,data=authority(selection);main=published(selection['L2'],selection['repository'])
    science={b['path']:b['sha256'] for b in main['bindings']}
    sources=[Path(__file__).resolve(),*extra]
    if any(science.get(str(p))!=digest(p) for p in sources):raise ValueError('independent coverage preparation must precede main')
    return tasks,score,score_lock,data,main


def prepare_hidden(plan):
    """Only selected-checkpoint authority can open named test reference files; no outcomes or fitting here."""
    selection=copy.deepcopy(plan['selection_plan']);repo=selection['repository']
    sources=[HERE/name for name in ('selected_hidden.py','hidden_runtime.py','selected_coverage_inputs.py','selected_coverage.py')]
    sources.append(E12/'expt_v1/scripts/extract_hidden_tests.py')
    tasks,score,score_lock,data,main=source_authority(selection,sources)
    controls=published(plan['hidden_controls_result'],repo);original=published(plan['hidden_controls_lock'],repo)
    if controls.get('status')!='PASS' or controls.get('cleanup_verified') is not True:
        raise ValueError('independent hidden controls must pass before test preparation')
    for b in original['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('validated hidden control dependency changed')
    root=Path(score_lock['configuration']['root']).parent.parent/'independent_coverage';root.mkdir(exist_ok=False)
    selection['output']=str(root/'normalized');inputs=normalize(selection)
    verify_evidence(inputs,tasks,data,score_lock['configuration']['root'],selection['run'])
    allowed=root/'test_ids.txt';allowed.write_text(''.join(t['task_id']+'\n' for t in sorted(tasks,key=lambda t:t['task_id'])))
    config=original['configuration'];suites=root/'suites';suites.mkdir();source_paths=[]
    for index,cell in enumerate(inputs['cells']):
        gold=Path(config['pack'])/cell['task_id']/'tests/gold.lean';suite=extract(gold.read_text())
        path=suites/f'{index:03d}.json';write_new(path,suite);cell['suite']=reference(path);cell['gold']=reference(gold)
        source_paths.extend([gold,path])
    inputs_path=root/'hidden_inputs.json';write_new(inputs_path,inputs)
    execution={'root':str(root/'hidden'),'controller_fence':str(root/'hidden_controller.lock'),
        'test_ids':str(allowed),'lake':config['lake'],'lake_bin':config['lake_bin']}
    refs=[plan['hidden_controls_result'],plan['hidden_controls_lock'],*[selection[k] for k in ('L2','method','selection','score','score_lock')]]
    paths={Path(b['path']) for b in main['bindings']+original['bindings']}
    paths.update(Path(ref['path']) for ref in refs);paths.update([inputs_path,allowed,*source_paths])
    paths.update((root/'normalized').iterdir());paths.add(Path(score['scoring']['path']))
    for cell in inputs['cells']:
        strict=read(cell['strict'])
        for ref in (cell.get('source'),strict['strict_receipt'],strict.get('oracle_receipt'),strict.get('frontend')):
            if ref:paths.add(Path(ref['path']))
    locked={'gate':'SELECTED_TEST_COVERAGE_CPU','condition':'v2-S2','status':'FROZEN','selection_plan':selection,
        'configuration':execution,'inputs':reference(inputs_path),'hidden_controls_result':plan['hidden_controls_result'],
        'hidden_controls_lock':plan['hidden_controls_lock'],'declared':222,'sample_idx':0,
        'maximum_attempts_per_cell':1,'maximum_workers':8,'timeout_seconds':3600,'address_space_bytes':64*1024**3,
        'model_calls':0,'bindings':bindings(paths)}
    run=selection['run'];target=HERE.parent/'locks'/f"SELECTED_TEST_COVERAGE_CPU_S2_{run['arm']}_{run['run_seed']}_b{run['boundary']}.json"
    write_new(target,locked);return {'status':'PREPARED_FOR_PUBLICATION','lock':reference(target),'model_calls':0}


def prepare_hosted(plan):
    """Prepare formal coverage independently of hidden outcomes, from the same published sample inputs."""
    repo=plan['repository'];cpu=published(plan['cpu_lock'],repo)
    if (cpu.get('gate'),cpu.get('condition'),cpu.get('status'))!=('SELECTED_TEST_COVERAGE_CPU','v2-S2','FROZEN'):
        raise ValueError('published selected-test coverage input lock required')
    selection=cpu['selection_plan']
    sources=[HERE/name for name in ('selected_hosted.py','selected_coverage.py','hosted_coverage.py','coverage_pack.py','coverage_controls.py')]
    tasks,score,score_lock,data,main=source_authority(selection,sources)
    for b in cpu['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('selected-test shared coverage inputs changed')
    controls=published(plan['coverage_controls_result'],repo);original=published(plan['coverage_controls_lock'],repo)
    if controls.get('status')!='PASS' or controls.get('actual_bundle_verified') is not True:
        raise ValueError('validated hosted controls unavailable')
    for b in original['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('validated hosted control dependency changed')
    inputs=read(cpu['inputs']);verify_evidence(inputs,tasks,data,score_lock['configuration']['root'],selection['run'])
    work=Path(cpu['configuration']['root']).parent/'hosted';work.mkdir(exist_ok=False)
    run=selection['run'];name=f"{run['arm'].lower()}-{run['run_seed']}-b{run['boundary']}"
    config=copy.deepcopy(original['configuration'])
    config.update(work=str(work),private_namespace='rl4cv_e13v2_S2_selected_'+name.replace('-','_'),
        benchmark_prefix='veribench-rl4cv-e13v2-s2-'+name,prepared=str(work/'prepared.json'),
        inputs=cpu['inputs']['path'],test_ids=cpu['configuration']['test_ids'])
    config_path=work/'configuration.json';write_new(config_path,config)
    manifest=build(config,inputs);module=helper(config);catalog=json.loads(Path(config['registry_catalog']).read_text())['models'];estimates={}
    for member in CONFIGS:
        cfg=module.judge_config(member);model=catalog[cfg['selector']]
        if model.get('provider_properties',{}).get('fallback_models'):raise ValueError('judge selector has a fallback')
        if cfg.get('reasoning_effort') and model['default_parameters'].get('reasoning_effort')!=cfg['reasoning_effort']:
            raise ValueError('judge selector effort changed')
        estimates[member]=sum(module.judge_run.worst_cost(model,c['instruction_bytes'],cfg['max_tokens']) for c in manifest['cells'])
    paths={Path(b['path']) for previous in (cpu,main,original) for b in previous['bindings']}
    paths.update([config_path,*[Path(plan[k]['path']) for k in ('cpu_lock','coverage_controls_result','coverage_controls_lock')]])
    paths.update(Path(config[k]) for k in ('inputs','test_ids','route_identity','registry_catalog','migration_provenance'))
    paths.update(Path(b['path']) for b in manifest['source_bindings'])
    paths.update(p for folder in (module.PRIVATE,module.RESULTS) for p in folder.rglob('*') if p.is_file())
    paths.update(Path(config['bundle'])/name for name in ('judge_call.py','setup.sh','contract.yaml'))
    prepared={'condition':'v2-S2','status':'PREPARED_NOT_ADMITTED','configuration':config,
        'pack_sha256':digest(module.suite_spec(SUITE)['pack_receipt']),'bindings':bindings(paths),
        'declared':222,'declared_ratings':manifest['n_declared_ratings'],'compiled_files':manifest['compiled_files'],
        'estimated_maximum_single_attempt_usd_by_member':estimates,'estimated_maximum_two_attempt_usd':2*sum(estimates.values()),
        'model_calls':0,'model_funding':'validated Vals-managed hosted route; reverify before admission'}
    write_new(work/'prepared.json',prepared);paths.add(work/'prepared.json')
    lock={'gate':'SELECTED_TEST_COVERAGE_HOSTED','condition':'v2-S2','status':'FROZEN','selection_plan':selection,
        'configuration':config,'cpu_input_lock':plan['cpu_lock'],'coverage_controls_result':plan['coverage_controls_result'],
        'coverage_controls_lock':plan['coverage_controls_lock'],'members':list(CONFIGS),'concurrency':5,'declared':222,
        'declared_ratings':manifest['n_declared_ratings'],'repeats_per_member':3,'request_attempts_per_rating':2,
        'one_admission_per_member':True,'bindings':bindings(paths),
        'estimated_maximum_single_attempt_usd_by_member':estimates,'estimated_maximum_two_attempt_usd':2*sum(estimates.values())}
    target=HERE.parent/'locks'/f"SELECTED_TEST_COVERAGE_HOSTED_S2_{run['arm']}_{run['run_seed']}_b{run['boundary']}.json"
    write_new(target,lock);return {'status':'PREPARED_FOR_PUBLICATION','lock':reference(target),'model_calls':0,
        'estimated_maximum_two_attempt_usd':prepared['estimated_maximum_two_attempt_usd']}
