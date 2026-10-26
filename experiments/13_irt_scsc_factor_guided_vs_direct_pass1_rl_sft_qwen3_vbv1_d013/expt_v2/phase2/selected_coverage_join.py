"""Join selected-test independent metrics to the published strict population without replacing missing samples."""
from pathlib import Path
from selected_analysis_driver import collect as collect_strict
from selected_coverage_inputs import IDENTITY
from technical_ledger import published
from technical_driver import read
from training_checkpoint import digest


def table(rows, expected):
    found={r['cell_id']:r for r in rows}
    if len(found)!=222 or len(rows)!=222 or set(found)!=set(expected):
        raise ValueError('all 222 fixed samples required exactly once')
    for cell_id,row in found.items():
        if any(row.get(k)!=expected[cell_id].get(k) for k in IDENTITY):
            raise ValueError('coverage crossed its selected sample or checkpoint')
    return found


def execution(lock_ref, run, kind, L2_sha, repository):
    lock=published(lock_ref,repository)
    if (lock.get('gate'),lock.get('condition'),lock.get('status'))!=(kind,'v2-S2','FROZEN'):
        raise ValueError('published independent coverage execution required')
    plan=lock['selection_plan']
    if (plan['repository']!=repository or plan['L2']['sha256']!=L2_sha
            or plan['selection']!=run['selection'] or plan['score']!=run['test_score']):
        raise ValueError('coverage execution differs from the selected strict score')
    selected=published(run['selection'],repository)
    if plan['run']!={k:selected[k] for k in ('arm','run_seed','boundary')}:
        raise ValueError('coverage execution checkpoint changed')
    bound={b['path']:b['sha256'] for b in lock['bindings']}
    if len(bound)!=len(lock['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):
        raise ValueError('independent coverage execution input changed')
    return lock


def unavailable(ref,run,metric,L2_sha,boundary,repository):
    result=published(ref,repository)
    expected={'condition':'v2-S2','stage':'SELECTED_TEST_COVERAGE_UNAVAILABLE','status':'NOT_EVALUATED',
        'metric':metric,'L2_sha256':L2_sha,'arm':run['arm'],'run_seed':run['run_seed'],'boundary':boundary}
    if any(result.get(k)!=v for k,v in expected.items()) or not isinstance(result.get('reason'),str) or not result['reason']:
        raise ValueError('missing coverage needs a same-checkpoint published reason')
    return result['reason']


def collect(runs,tasks,arms,L2_sha,contract_sha,repository):
    strict,sources,availability=collect_strict(runs,tasks,arms,L2_sha,contract_sha,repository)
    output=[];reasons=[]
    for run,available in zip(runs,availability):
        arm,seed=run['arm'],run['run_seed'];boundary=available['boundary']
        chosen=[r for r in strict if r['arm']==arm and r['run_seed']==seed and r['sample_idx']==0]
        if len(chosen)!=222:raise ValueError('strict population lost its fixed sample')
        absent=available['not_evaluated_reason'];hidden=None;hosted=None
        if absent:
            if run.get('hidden_result') or run.get('hosted_result'):
                raise ValueError('unavailable strict selection cannot supply independent measurements')
            reasons.append({'arm':arm,'run_seed':seed,'all_metrics':absent})
        else:
            expected={r['cell_id']:r for r in chosen}
            score=published(run['test_score'],repository)
            if run.get('hidden_result'):
                lock=execution(run['hidden_lock'],run,'SELECTED_TEST_COVERAGE_CPU',L2_sha,repository)
                value=published(run['hidden_result'],repository)
                header={'condition':'v2-S2','stage':'SELECTED_TEST_HIDDEN','status':'ACCOUNTED',
                    'arm':arm,'run_seed':seed,'boundary':boundary,'L2_sha256':L2_sha,
                    'model_binding_sha256':score['model_binding_sha256'],'execution_sha256':run['hidden_lock']['sha256'],
                    'declared':222,'accounted':222,'cleanup_unresolved':0,'automatic_retries':0}
                if any(value.get(k)!=v for k,v in header.items()):raise ValueError('hidden result authority changed')
                if value['rows_sha256']!=value['rows']['sha256']:raise ValueError('hidden row hash changed')
                hidden=table(read(value['rows']),expected)
                sources.extend([run['hidden_lock'],run['hidden_result'],value['rows']])
                for row in hidden.values():
                    if row.get('cleanup_verified') is not True:raise ValueError('hidden worker cleanup unresolved')
                    if row.get('hidden_receipt'):
                        actual=read(row['hidden_receipt']);sources.append(row['hidden_receipt'])
                        measured=actual.get('hidden_pass_rate') if actual.get('fully_applicable') or actual['status']=='compile_failure' else None
                        if row.get('hidden_test_coverage')!=measured:raise ValueError('hidden summary detached from saved measurement')
                    elif row.get('hidden_test_coverage') is not None:raise ValueError('hidden value has no measurement receipt')
            else:
                ref=run['hidden_unavailable'];reason=unavailable(ref,run,'hidden_test_coverage',L2_sha,boundary,repository)
                sources.append(ref);reasons.append({'arm':arm,'run_seed':seed,'hidden_test_coverage':reason})
            if run.get('hosted_result'):
                lock=execution(run['hosted_lock'],run,'SELECTED_TEST_COVERAGE_HOSTED',L2_sha,repository)
                value=published(run['hosted_result'],repository)
                if (value.get('condition'),value.get('stage'),value.get('declared'),value.get('lock_sha256'))!=('v2-S2','SELECTED_TEST_HOSTED',222,run['hosted_lock']['sha256']):
                    raise ValueError('hosted result authority changed')
                hosted=table(value['rows'],expected);sources.extend([run['hosted_lock'],run['hosted_result']])
                for cell_id,row in hosted.items():
                    original=expected[cell_id];gate=original.get('compile') if original['status']=='measured' else None
                    if row.get('compile') is not gate:raise ValueError('hosted compilation gate differs from strict evidence')
                    metric=row.get('formal_specification_coverage')
                    if gate is False and metric!=0 or gate is None and metric is not None:
                        raise ValueError('hosted compile-gating convention changed')
                    if gate is True and metric is not None:
                        rating=row.get('ratings')
                        if (value.get('actual_bundle_verified') is not True or value.get('requested_identity_verified') is not True
                                or not rating or not rating.get('complete_3x2') or metric!=rating.get('FSC')):
                            raise ValueError('hosted value lacks its complete validated judge receipt')
            else:
                ref=run['hosted_unavailable'];reason=unavailable(ref,run,'formal_specification_coverage',L2_sha,boundary,repository)
                sources.append(ref);reasons.append({'arm':arm,'run_seed':seed,'formal_specification_coverage':reason})
        for original in chosen:
            item={k:original[k] for k in ('condition','arm','run_seed','task_id','split','sample_idx','boundary')}
            measured=original['status']=='measured';count=original.get('p',{}).get('denominator') if measured else None
            item.update(theorem_count=count,
                hidden_test_coverage=hidden[original['cell_id']].get('hidden_test_coverage') if hidden else None,
                formal_specification_coverage=hosted[original['cell_id']].get('formal_specification_coverage') if hosted else None)
            if absent:item.update(status='not_evaluated',reason=absent)
            output.append(item)
    return output,sources,reasons
