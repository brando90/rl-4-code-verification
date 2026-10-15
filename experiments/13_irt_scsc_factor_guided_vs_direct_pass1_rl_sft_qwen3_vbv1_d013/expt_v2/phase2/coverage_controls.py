"""Reuse the frozen judge controls through hosted Valkyrie, with private manifests and one admission per member."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(REPO/'src'))
from rl4cv.valkyrie_transport import Transport
from training_checkpoint import digest,write_new

HELPER=REPO/'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v2/scripts/judge_rl4cv_e08v2.py'
CONFIGS=('H2_sol_high','H2_opus55_max')
SUITE='rl4cv-e08v2-controls'  # Internal selector in the unchanged helper, never a reused execution.


def helper(config):
    spec=importlib.util.spec_from_file_location('e13_frozen_judge_helper',HELPER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    work=Path(config['work'])
    module.WORK=work;module.EXP=work/'view/expt_v2'
    module.RESULTS=work/'private/results';module.STATE=module.RESULTS/'state.json'
    module.PRIVATE=module.E103/'private/judge/rl4cv_e13v2_S2'
    module.BENCH_PREFIX=config['benchmark_prefix']
    module.request_benchmark=lambda spec,name:f"rl4cv-e13v2-S2-controls-{name}"
    # Every scientific builder, mutation, prompt renderer, parser, envelope check
    # and score criterion remains the imported frozen implementation.
    return module


def prepare(config_path):
    config=json.loads(Path(config_path).read_text());work=Path(config['work'])
    work.mkdir(parents=True,exist_ok=False)
    m=helper(config)
    pinned=json.loads((REPO/'external/deps.lock.json').read_text())['veribench']['commit']
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=m.EXT,text=True).strip()
    if actual!=pinned:raise ValueError('judge dependency revision changed')
    train=Path(config['train_ids']);target=m.EXP.parent/'expt_v1/results/split/vbv1_train_task_ids.txt'
    target.parent.mkdir(parents=True);shutil.copyfile(train,target)
    manifest=m.build_controls()
    allowed=set(train.read_text().splitlines())
    if manifest['split']!='train' or len(manifest['tasks'])!=5 or not set(manifest['tasks'])<=allowed:
        raise ValueError('control selection must use the five frozen train families')
    if manifest['verdict']!='PASS' or len(manifest['control_cells'])!=25:
        raise ValueError('frozen route control pack is incomplete')
    catalog=json.loads(Path(config['registry_catalog']).read_text())['models']
    estimates={}
    for name in CONFIGS:
        cfg=m.judge_config(name);model=catalog[cfg['selector']]
        if model.get('provider_properties',{}).get('fallback_models'):raise ValueError('judge route has a fallback')
        if cfg.get('reasoning_effort') and model['default_parameters'].get('reasoning_effort')!=cfg['reasoning_effort']:
            raise ValueError('judge selector effort changed')
        estimates[name]=sum(m.judge_run.worst_cost(model,c['instruction_bytes'],cfg['max_tokens']) for c in manifest['control_cells'])
    files=[Path(config_path),train,HELPER,Path(__file__).resolve(),REPO/'src/rl4cv/valkyrie_transport.py',
           HERE/'training_checkpoint.py',REPO/'external/deps.lock.json',Path(config['registry_catalog']),
           Path(config['route_identity']),Path(config['migration_provenance']),m.prompts.HUMAN_MD]
    files+=list((m.X100/'scripts').glob('*.py'))+list((m.X100/'configs').glob('H2_*.json'))
    # Freeze every text resource under the validated judge's input/rubric trees,
    # not only Python imports. No new test outcome is opened by this operation.
    for directory in ('rubrics','inputs'):
        files += [p for p in (m.X100/directory).rglob('*') if p.is_file()]
    for task in manifest['tasks']:
        files.extend([m.PACK/task/'instruction.md',m.PACK/task/'tests/gold.lean'])
    files += [m.E103/'scripts/judge_pack.py']
    files += list((m.common.GATEWAY_DIR/'canonical').glob('*.py'))
    for item in m.common.load_items('train'):
        for key in ('candidate_path','ref_ann_path','py_ann_path'):
            files.append(m.X100/item[key])
    files += [p for p in m.PRIVATE.rglob('*') if p.is_file()]
    files += [p for p in (work/'private/results').rglob('*') if p.is_file()]
    files += [Path(config['bundle'])/name for name in ('contract.yaml','judge_call.py','setup.sh')]
    bindings=[{'path':str(p.resolve()),'sha256':digest(p)} for p in sorted(set(files))]
    report={'condition':'v2-S2','stage':'train-only hosted judge route controls','status':'PREPARED',
        'train_tasks':5,'control_kinds':5,'repeats_per_control_per_member':1,'members':list(CONFIGS),
        'declared_ratings':50,'scientific_settings':'unchanged frozen experiment-100/103 judge and experiment-08 route controls',
        'rubric':m.RUBRIC,'rubric_fingerprint':manifest['rubric_fingerprint'],
        'private_manifest_sha256':digest(m.suite_spec(SUITE)['pack_receipt']),
        'worst_case_estimate_usd_by_member':estimates,'model_calls':0,
        'bindings':bindings,'configuration':config}
    write_new(work/'prepared.json',report)
    return report


def published(plan_path):
    plan=json.loads(Path(plan_path).read_text());lock_path=Path(plan['lock'])
    lock=json.loads(lock_path.read_text())
    if lock.get('gate')!='TRAIN_COVERAGE_ROUTE_CONTROLS' or lock.get('status')!='FROZEN' or lock.get('condition')!='v2-S2':
        raise ValueError('route controls have no frozen S2 lock')
    subprocess.run(['git','merge-base','--is-ancestor',plan['published_revision'],'origin/main'],cwd=REPO,check=True)
    data=subprocess.check_output(['git','show',plan['published_revision']+':'+str(lock_path.relative_to(REPO))],cwd=REPO)
    if data!=lock_path.read_bytes():raise ValueError('route-control lock is not published')
    for binding in lock['bindings']:
        if digest(binding['path'])!=binding['sha256']:raise ValueError('control input or implementation changed')
    prepared_path=Path(lock['private_prepared'])
    if not any(Path(b['path'])==prepared_path for b in lock['bindings']):
        raise ValueError('private control manifest is not bound')
    prepared=json.loads(prepared_path.read_text())
    for binding in prepared['bindings']:
        if digest(binding['path'])!=binding['sha256']:raise ValueError('private control binding changed')
    config=lock['configuration']
    if config!=prepared['configuration'] or prepared['declared_ratings']!=50:
        raise ValueError('private control configuration changed')
    m=helper(config)
    if set(CONFIGS)!=set(lock['members']) or lock['declared_ratings']!=50:raise ValueError('control denominator changed')
    transport=Transport(Path(config['work'])/'private/unused.yaml');transport.preflight()
    route=json.loads(Path(config['route_identity']).read_text());transport.require_receipt(route)
    if route['verdict']!='PASS' or not route['vals_managed_credential_provenance_verified']:
        raise ValueError('hosted Vals route identity remains unverified')
    return plan,lock,config,m,transport


def admit(plan_path,name):
    if name not in CONFIGS:raise ValueError('unregistered judge member')
    plan,lock,config,m,transport=published(plan_path)
    spec=m.suite_spec(SUITE);manifest=m.read_json(spec['pack_receipt'])
    transport.endpoint(spec['benchmark'],Path(config['work'])/'private')
    with (m.RESULTS/'admission.lock').open('a') as guard:
        fcntl.flock(guard,fcntl.LOCK_EX)
        state=m.load_state();key='controls/'+name
        attempt_path=m.RESULTS/(name+'_attempt.json')
        if key in state['runs'] or attempt_path.exists():
            raise ValueError('prior admission exists; recover its receipt, never resubmit')
        ids=m.RESULTS/('task_ids_'+name+'.txt');ids.write_text(''.join(c['task_id']+'\n' for c in manifest['control_cells']))
        cfg=m.judge_config(name);kwargs={'judge_config':name,'max_tokens':str(cfg['max_tokens']),
                                      'benchmark':m.request_benchmark(spec,name)}
        for field in ('reasoning_effort','compute_effort'):
            if cfg.get(field):kwargs[field]=cfg[field]
        args=['run','start','--agent','vb103_judge','--benchmark',spec['benchmark'],'--dataset','default',
              '--model',cfg['selector'],'--concurrency',str(lock['concurrency']),
              '--label','e13v2-S2-controls-'+name,'--task-ids-file',str(ids)]
        for k,v in kwargs.items():args+=['-k',k,v]
        entry={'config':name,'selector':cfg['selector'],'kwargs':kwargs,'expected_cells':25,
            'suite':SUITE,'benchmark':spec['benchmark'],'phase':'admitting','admitted_at':m.stamp(),
            'command':args,'task_ids_sha256':digest(ids),'lock_sha256':digest(plan['lock']),**transport.identity()}
        write_new(attempt_path,entry)  # fsync before the hosted command, even if the summary state is lost.
        state['runs'][key]=entry;m.save_state(state)
        try:
            result=transport.run(args,timeout=180)
            (m.RESULTS/(name+'_admission.log')).write_text(result.stdout+result.stderr)
            found=re.search(r'Run ID:\s*([a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12})',result.stdout)
            if result.returncode or not found:raise RuntimeError('ambiguous or failed hosted admission; receipt recovery required')
            entry.update(phase='running',run_id=found.group(1));m.save_state(state)
        except BaseException as exc:
            entry.update(phase='admission_failed',error_type=type(exc).__name__,automatic_retry=False);m.save_state(state)
            raise
        return {'condition':'v2-S2','member':name,'run_id':entry['run_id'],'declared_ratings':25}


def collect(plan_path):
    _,lock,config,m,_=published(plan_path)
    if m.poll()!=0:raise RuntimeError('both control members must reach a terminal state before collection')
    state=m.load_state()
    if set(state['runs'])!={'controls/'+n for n in CONFIGS}:raise ValueError('control member missing')
    m.harvest(SUITE,list(CONFIGS))
    # Verify the uploaded executable bytes actually supplied to each hosted run.
    expected={n:digest(Path(config['bundle'])/n) for n in ('judge_call.py','setup.sh','contract.yaml')}
    for name in CONFIGS:
        archives=list((Path(config['work'])/'judge/raw'/('controls__'+name)/'artifacts').glob('vb103_judge.zip'))
        if len(archives)!=1:raise ValueError('actual hosted agent bundle unavailable')
        with zipfile.ZipFile(archives[0]) as archive:
            for name,want in expected.items():
                matches=[n for n in archive.namelist() if Path(n).name==name]
                if len(matches)!=1 or hashlib.sha256(archive.read(matches[0])).hexdigest()!=want:
                    raise ValueError('actual hosted judge bundle differs from the freeze')
    root=Path(config['work']);write_new(root/'evaluation_attempt.json',{'condition':'v2-S2','started_unix':time.time(),
        'admission_statistics_computed':True,'automatic_retry':False})
    m.controls_check()
    raw=m.read_json(m.RESULTS/'controls_check.json')
    out={'condition':'v2-S2','gate':'TRAIN_COVERAGE_ROUTE_CONTROLS','status':raw['verdict'],
         'declared_ratings':50,'train_tasks':5,'configs':raw['configs'],
         'actual_bundle_verified':True,'admission_statistics_computed':True,
         'aggregation':'route controls: one rating per member/control; actual coverage remains three repeats/member',
         'source_sha256':digest(m.RESULTS/'controls_check.json')}
    for name in CONFIGS:
        harvest=m.read_json(m.RESULTS/'harvests'/('cells_controls__'+name+'.json'))
        costs=[c['cost_usd'] for c in harvest['cells']]
        out['configs'][name]['reported_charge_cells']=sum(c is not None for c in costs)
        out['configs'][name]['charges_usd']=sum(costs) if all(c is not None for c in costs) else None
    write_new(root/'result.json',out);return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','admit','collect'))
    parser.add_argument('--config',type=Path);parser.add_argument('--plan',type=Path)
    parser.add_argument('--member',choices=CONFIGS)
    args=parser.parse_args()
    result=prepare(args.config) if args.action=='prepare' else admit(args.plan,args.member) if args.action=='admit' else collect(args.plan)
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','configuration')},sort_keys=True))


if __name__=='__main__':main()
