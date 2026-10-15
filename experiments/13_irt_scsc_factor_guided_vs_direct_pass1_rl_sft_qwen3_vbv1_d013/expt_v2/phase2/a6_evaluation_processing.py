"""Publish full evaluation accounting, freeze all strict-scoring inputs and retain bounded unchanged-oracle results."""
from __future__ import annotations

import fcntl
import json
from pathlib import Path

from a6_evaluation_authority import authorize
from evaluation_ledger import scan
from evaluation_contract import strict_summary
from score_evaluation import score_manifest
from technical_ledger import published
from technical_driver import bindings,read
from training_checkpoint import digest,write_new
from costs import snapshot as cost_snapshot,stage_cost

HERE=Path(__file__).resolve().parent


def context(plan):
    lp,execution,config,snapshot=authorize(plan)
    bound={b['path']:b['sha256'] for b in execution['bindings']}
    for name in ('a6_evaluation_processing.py','evaluation_ledger.py','score_evaluation.py','evaluation_contract.py','costs.py'):
        path=HERE/name
        if bound.get(str(path))!=digest(path):raise ValueError('evaluation processor was not frozen before main')
    root=Path(snapshot['configuration']['root']);manifest=json.loads(Path(snapshot['configuration']['manifest']).read_text())
    terminal=json.loads((root/'generation_terminal.json').read_text())
    current=scan(root,manifest,Path(snapshot['configuration']['allowlist']).read_text().splitlines(),plan['snapshot_lock']['sha256'])
    if (terminal.get('snapshot_sha256')!=plan['snapshot_lock']['sha256'] or terminal.get('status') not in ('COMPLETE','INCOMPLETE')
            or terminal.get('cleanup_unresolved')!=0 or current['cleanup_unresolved'] or current['unfinished_stage'] is not None
            or terminal['generation']!=current['generation'] or terminal['attempts']!=current['attempts']):
        raise ValueError('evaluation generation is not fully reconciled and clean')
    return snapshot,config,root,manifest,terminal


def generation_report(plan):
    snapshot,config,root,manifest,value=context(plan)
    fields=('condition','purpose','status','declared','completed','missing','known_generated_tokens',
            'tokens_in_missing_responses_unknown','identical_retries','cleanup_unresolved','missing_cost_receipts','stop_reason')
    result={k:value[k] for k in fields}
    result.update(stage='EVALUATION_GENERATION',**{k:snapshot[k] for k in ('arm','run_seed','boundary','LP_sha256','L2_sha256',
        'model_binding_sha256','boundary_receipt_sha256','evaluation_contract_sha256')},
        snapshot_sha256=plan['snapshot_lock']['sha256'],
        private_result={'path':str(root/'generation_terminal.json'),'sha256':digest(root/'generation_terminal.json')})
    write_new(Path(plan['output']),result);return result


def prepare_score(plan):
    snapshot,config,root,manifest,value=context(plan);run=plan['learning']['run']
    report=published(plan['generation_result'],run['repository'])
    expected={'stage':'EVALUATION_GENERATION','condition':'v2-S2','snapshot_sha256':plan['snapshot_lock']['sha256'],
        **{k:snapshot[k] for k in ('arm','run_seed','boundary','LP_sha256','L2_sha256','model_binding_sha256')}}
    if any(report.get(k)!=v for k,v in expected.items()) or report['private_result']['sha256']!=digest(root/'generation_terminal.json'):
        raise ValueError('published evaluation generation belongs to another snapshot')
    inputs={'condition':'v2-S2','snapshot_sha256':plan['snapshot_lock']['sha256'],'generation':value['generation']}
    destination=root/'scoring_inputs';destination.mkdir(exist_ok=False);write_new(destination/'generation.json',inputs)
    paths={Path(b['path']) for b in snapshot['bindings']}|{root/'generation_terminal.json',Path(plan['generation_result']['path']),destination/'generation.json'}
    paths.update(Path(ref['path']) for ref in value['generation'].values() if ref)
    for stage in value['stages']:
        folder=root/stage['stage_key'];paths.update([root/(stage['stage_key']+'.json'),folder/'runtime.json',Path(stage['result']['path'])])
    paths.update(Path(ref['path']) for ref in value['costs'])
    scoring={**config['scoring'],'root':str(root/'strict/cells'),'allowlist':snapshot['configuration']['allowlist'],
        'split':snapshot['purpose'],'purpose':snapshot['purpose']}
    lock={'condition':'v2-S2','gate':'EVALUATION_SCORE_INPUTS','status':'FROZEN',
        **{k:snapshot[k] for k in ('arm','run_seed','boundary','purpose','LP_sha256','L2_sha256','model_binding_sha256')},
        'snapshot_sha256':plan['snapshot_lock']['sha256'],'snapshot_lock':plan['snapshot_lock'],
        'generation_result':plan['generation_result'],'generation_inputs':str(destination/'generation.json'),
        'bindings':bindings(paths),'configuration':scoring,'declared':len(manifest['cells']),
        'maximum_attempts_per_cell':2,'timeout_seconds':3600,'address_space_bytes':64*1024**3,'model_calls':0}
    target=HERE.parent/'locks'/f"EVALUATION_SCORE_S2_{snapshot['arm']}_{snapshot['run_seed']}_{snapshot['purpose']}_b{snapshot['boundary']}.json"
    write_new(target,lock);return {'status':'PREPARED_FOR_PUBLICATION','path':str(target),'sha256':digest(target),'model_calls':0}


def score(plan):
    snapshot,config,root,manifest,terminal=context(plan);run=plan['learning']['run'];lock=published(plan['score_lock'],run['repository'])
    expected={'gate':'EVALUATION_SCORE_INPUTS','condition':'v2-S2','status':'FROZEN',
        'snapshot_sha256':plan['snapshot_lock']['sha256'],**{k:snapshot[k] for k in ('arm','run_seed','boundary','purpose','L2_sha256')}}
    if any(lock.get(k)!=v for k,v in expected.items()):raise ValueError('evaluation scoring freeze belongs to another snapshot')
    expected_configuration={**config['scoring'],'root':str(root/'strict/cells'),'allowlist':snapshot['configuration']['allowlist'],
        'split':snapshot['purpose'],'purpose':snapshot['purpose']}
    if lock['configuration']!=expected_configuration:raise ValueError('evaluation scorer configuration differs from its pre-main settings')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('evaluation scoring input changed')
    inputs=json.loads(Path(lock['generation_inputs']).read_text())
    if inputs['snapshot_sha256']!=plan['snapshot_lock']['sha256'] or inputs['generation']!=terminal['generation']:
        raise ValueError('scoring omitted or changed a declared evaluation output')
    output=root/'strict';output.mkdir(exist_ok=True)
    with (output/'parent_controller.lock').open('a') as fence:
        fcntl.flock(fence,fcntl.LOCK_EX)
        final=output/'terminal.json'
        if final.exists():
            result=json.loads(final.read_text())
            if result['scoring_lock_sha256']!=plan['score_lock']['sha256'] or result['scoring_sha256']!=digest(output/'cells/result.json'):
                raise ValueError('retained evaluation score changed')
            return result
        attempt=output/'parent_attempt.json';identity={'score_lock_sha256':plan['score_lock']['sha256']};resumed=attempt.exists()
        if resumed:
            if json.loads(attempt.read_text())!=identity:raise ValueError('evaluation scoring parent changed')
        else:write_new(attempt,identity)
        before=cost_snapshot(output)
        value=score_manifest(manifest,lock['configuration'],inputs['generation'],plan['score_lock']['sha256'])
        cost=stage_cost(before,cost_snapshot(output),stage='evaluation_'+snapshot['purpose']+'_strict')
        cost['cumulative_timing_complete']=not resumed
        if not (output/'cost.json').exists():write_new(output/'cost.json',cost)
        summary=strict_summary(manifest['cells'],value['rows'])
        result={'condition':'v2-S2','stage':'VALIDATION_SCORE' if snapshot['purpose']=='validation' else 'SELECTED_TEST_SCORE',
            'status':'COMPLETE' if summary['missing']==0 and value['cleanup_unresolved']==0 else 'INCOMPLETE',
            **{k:snapshot[k] for k in ('arm','run_seed','boundary','purpose','LP_sha256','L2_sha256','model_binding_sha256',
                'boundary_receipt_sha256','evaluation_contract_sha256')},'summary':summary,
            'snapshot_sha256':plan['snapshot_lock']['sha256'],'scoring_lock_sha256':plan['score_lock']['sha256'],
            'generation_sha256':digest(root/'generation_terminal.json'),'scoring_sha256':digest(output/'cells/result.json'),
            'scoring':{'path':str(output/'cells/result.json'),'sha256':digest(output/'cells/result.json')},
            'cleanup_unresolved':value['cleanup_unresolved'],'identical_retries':value['identical_retries'],
            'cost':{'path':str(output/'cost.json'),'sha256':digest(output/'cost.json')}}
        write_new(final,result);return result
