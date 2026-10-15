"""Verify one published evaluation snapshot and its exact pre-main method before reserving device work."""
from __future__ import annotations

import json
from pathlib import Path

from learning_driver import authorize as learning_authority
from learning_report import checkpoint
from evaluation_snapshot import selection_authority
from technical_ledger import published
from technical_driver import read
from training_checkpoint import digest

HERE=Path(__file__).resolve().parent
SOURCES=('evaluation_authority.py','evaluation_snapshot.py','evaluation_runtime.py','evaluation_supervisor.py',
         'evaluation_generation.py','evaluation_contract.py','learning_report.py','evaluation_selection.py')


def authorize(plan):
    learning=plan['learning'];lp,execution,config=learning_authority(learning);run=learning['run']
    if run['phase']!='main':raise ValueError('evaluation requires a main execution')
    scientific={b['path']:b['sha256'] for b in execution['bindings']}
    for name in SOURCES:
        if scientific.get(str(HERE/name))!=digest(HERE/name):raise ValueError('evaluation implementation not bound before main')
    snapshot=published(plan['snapshot_lock'],run['repository'])
    if (snapshot.get('gate'),snapshot.get('condition'),snapshot.get('status'))!=('EVALUATION_SNAPSHOT','v2-S2','FROZEN'):
        raise ValueError('published evaluation snapshot required')
    if any(snapshot.get(k)!=v for k,v in {'arm':run['arm'],'run_seed':run['run_seed'],
            'LP_sha256':run['LP']['sha256'],'L2_sha256':run['execution_lock']['sha256']}.items()):
        raise ValueError('evaluation snapshot belongs to another main execution')
    inputs={b['path']:b['sha256'] for b in snapshot['bindings']}
    if len(inputs)!=len(snapshot['bindings']) or any(digest(p)!=sha for p,sha in inputs.items()):
        raise ValueError('evaluation snapshot binding changed')
    if any(inputs.get(p)!=sha for p,sha in scientific.items()):raise ValueError('evaluation snapshot omitted pre-main bindings')
    main=published(snapshot['main_result'],run['repository'])
    expected={'condition':'v2-S2','stage':'MAIN_TRAINING','status':'COMPLETE','arm':run['arm'],'run_seed':run['run_seed'],
        'L2_sha256':run['execution_lock']['sha256'],'boundaries_accounted':4,'cleanup_unresolved':0}
    if any(main.get(k)!=v for k,v in expected.items()):raise ValueError('complete clean main publication required')
    selected=selection_authority({**snapshot,'learning':learning},main,execution,run['repository'])
    boundary=read(selected);model_sha=checkpoint(boundary,config,scientific)
    if (model_sha!=snapshot['model_binding_sha256'] or selected['sha256']!=snapshot['boundary_receipt_sha256']
            or boundary['model']!=snapshot['model']):raise ValueError('evaluation checkpoint differs from its selected main boundary')
    settings=snapshot['configuration'];evaluation=config['evaluation'];purpose=snapshot['purpose']
    expected_root=Path(evaluation['root'])/run['arm']/str(run['run_seed'])/f"{purpose}_b{snapshot['boundary']}"
    if (Path(settings['root'])!=expected_root or settings['manifest']!=str(expected_root/'freeze/manifest.json')
            or settings['allowlist']!=evaluation['allowlists'][purpose]['path']
            or settings['learning_configuration']!=learning['configuration']):
        raise ValueError('evaluation snapshot moved from its pre-main configuration')
    if inputs.get(settings['manifest'])!=digest(settings['manifest']):raise ValueError('evaluation manifest was not frozen')
    return lp,execution,config,snapshot
