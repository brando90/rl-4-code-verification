"""Admit fixed selected-test coverage through the unchanged validated hosted judge transport and aggregation."""
from __future__ import annotations

import argparse,json
from pathlib import Path

from selected_coverage_inputs import authority as selected_authority,verify_evidence
from selected_coverage import helper,validate,combine,SUITE,SYSTEM
from coverage_controls import CONFIGS,REPO
from technical_ledger import published
from technical_driver import read
from training_checkpoint import digest
from rl4cv.valkyrie_transport import Transport

HERE=Path(__file__).resolve().parent


def authorize(plan):
    lock=published(plan['lock'],plan['repository'])
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=('SELECTED_TEST_COVERAGE_HOSTED','v2-S2','FROZEN'):
        raise ValueError('published selected-test hosted input lock required')
    selection=lock['selection_plan'];tasks,score,score_lock,data=selected_authority(selection)
    if selection['repository']!=plan['repository']:raise ValueError('selected-test repository authority changed')
    main=published(selection['L2'],plan['repository']);science={b['path']:b['sha256'] for b in main['bindings']}
    sources=[Path(__file__).resolve(),HERE/'selected_coverage.py',HERE/'selected_coverage_inputs.py',HERE/'coverage_pack.py',
        HERE/'hosted_coverage.py',HERE/'coverage_controls.py',REPO/'src/rl4cv/valkyrie_transport.py']
    if any(science.get(str(p))!=digest(p) for p in sources):raise ValueError('selected-test hosted implementation not frozen before main')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('selected-test hosted binding changed')
    config=lock['configuration'];required={str(p) for p in sources}|{config[k] for k in ('prepared','inputs','test_ids','route_identity')}
    if not required<=set(bound):raise ValueError('selected-test hosted executable or input unbound')
    inputs=json.loads(Path(config['inputs']).read_text());allowed=Path(config['test_ids']).read_text().splitlines();table=validate(inputs,allowed)
    if set(allowed)!={t['task_id'] for t in tasks} or any(inputs[k]!=selection['run'][k] for k in ('arm','run_seed','boundary')):
        raise ValueError('hosted population differs from selected checkpoint')
    verify_evidence(inputs,tasks,data,score_lock['configuration']['root'],selection['run'])
    prepared=json.loads(Path(config['prepared']).read_text())
    if prepared['configuration']!=config:raise ValueError('prepared hosted configuration changed')
    prepared_bound={b['path']:b['sha256'] for b in prepared['bindings']}
    if len(prepared_bound)!=len(prepared['bindings']) or any(digest(p)!=sha for p,sha in prepared_bound.items()):
        raise ValueError('prepared selected-test judge pack changed')
    controls=published(lock['coverage_controls_result'],plan['repository'])
    original=published(lock['coverage_controls_lock'],plan['repository'])
    if controls.get('status')!='PASS' or controls.get('condition')!='v2-S2' or controls.get('actual_bundle_verified') is not True:
        raise ValueError('validated hosted controls unavailable')
    for b in original['bindings']:
        if digest(b['path'])!=b['sha256']:raise ValueError('validated route binding changed')
    for key in ('bundle','route_identity','registry_catalog','migration_provenance'):
        if config[key]!=original['configuration'][key]:raise ValueError('selected-test judge differs from validated route')
    module=helper(config);manifest=json.loads(Path(module.suite_spec(SUITE)['pack_receipt']).read_text())
    for path in [Path(module.suite_spec(SUITE)['pack_receipt']),*[Path(config['bundle'])/name for name in ('judge_call.py','setup.sh','contract.yaml')]]:
        if prepared_bound.get(str(path))!=digest(path):raise ValueError('selected judge pack or bundle unbound')
    expected={(cell['cell_id'],repeat) for cell in inputs['cells'] if table[cell['cell_id']]['compile'] is True for repeat in (1,2,3)}
    observed={(c['selected_cell_id'],c['repeat']) for c in manifest['cells']}
    if (manifest.get('verdict')!='PASS' or manifest.get('split')!='test' or manifest.get('declared')!=222
            or manifest['n_declared_ratings']!=lock['declared_ratings'] or lock['members']!=list(CONFIGS)
            or manifest['repeats']!=[1,2,3] or manifest['configs']!=list(CONFIGS)
            or len(manifest['cells'])!=len(expected) or observed!=expected
            or manifest['n_declared_ratings']!=len(expected)*2
            or any(manifest[k]!=selection['run'][k] for k in ('arm','run_seed','boundary'))
            or prepared['pack_sha256']!=digest(module.suite_spec(SUITE)['pack_receipt'])):
        raise ValueError('selected-test compiled population or repeats changed')
    transport=Transport(Path(config['work'])/'private/unused.yaml');transport.preflight()
    route=json.loads(Path(config['route_identity']).read_text());transport.require_receipt(route)
    if route.get('verdict')!='PASS' or not route.get('vals_managed_credential_provenance_verified'):
        raise ValueError('hosted Vals route provenance unresolved')
    return lock,config,module,transport,manifest


def admit(plan,member):
    from hosted_coverage import admit as shared_admit
    return shared_admit(plan,member,authorize=authorize,suite=SUITE,system=SYSTEM,label_prefix='e13v2-S2-selected-test-')


def collect(plan):
    """Adapt legacy parameter names only; selected-test authority and all data retain their test split."""
    from hosted_coverage import collect as shared_collect
    def compatible_authority(plan):
        lock,config,module,transport,manifest=authorize(plan)
        # The frozen shared collector reads generic inputs through these legacy
        # train-audit names. Both aliases point to the already-authorized test
        # population; no train task or processor measurement is substituted.
        compatible={**config,'train_ids':config['test_ids'],'cpu_rows':config['inputs']}
        return lock,compatible,module,transport,manifest
    def compatible_combine(inputs,second_read,fsc,*,train):
        if inputs!=second_read:raise ValueError('selected-test collector input alias changed')
        return combine(inputs,fsc,test_ids=train)
    return shared_collect(plan,authorize=compatible_authority,combine=compatible_combine,suite=SUITE,system=SYSTEM,stage='SELECTED_TEST_HOSTED')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['admit','collect'])
    parser.add_argument('--plan',required=True,type=Path);parser.add_argument('--member',choices=CONFIGS)
    args=parser.parse_args();plan=json.loads(args.plan.read_text())
    result=admit(plan,args.member) if args.action=='admit' else collect(plan)
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','repeat_variability')},sort_keys=True))
