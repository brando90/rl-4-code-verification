"""Analyze fixed independent-coverage samples once through the published pre-main method and complete evidence bindings."""
from pathlib import Path
from selected_coverage_analysis import evaluate,validate
from selected_coverage_join import collect
from selected_test_analysis import SEEDS
from technical_ledger import published
from technical_driver import read
from training_checkpoint import digest,write_new

HERE=Path(__file__).resolve().parent


def run(plan):
    repo=plan['repository'];inputs=published(plan['inputs'],repo);method=published(inputs['method'],repo);main=published(inputs['L2'],repo)
    if (inputs.get('gate'),inputs.get('condition'),inputs.get('status'))!=('SELECTED_TEST_COVERAGE_ANALYSIS_INPUTS','v2-S2','FROZEN'):
        raise ValueError('published selected-test analysis input lock required')
    if (method.get('gate'),method.get('condition'),method.get('status'))!=('SELECTED_TEST_COVERAGE_ANALYSIS','v2-S2','FROZEN'):
        raise ValueError('published pre-main test-analysis method required')
    bound={b['path']:b['sha256'] for b in inputs['bindings']};science={b['path']:b['sha256'] for b in main['bindings']}
    method_bound={b['path']:b['sha256'] for b in method['bindings']}
    if len(method_bound)!=len(method['bindings']) or any(digest(p)!=sha for p,sha in method_bound.items()):
        raise ValueError('pre-main test-analysis binding changed')
    if method_bound.get(method['tasks']['path'])!=method['tasks']['sha256']:
        raise ValueError('test population metadata must be bound before main')
    if len(bound)!=len(inputs['bindings']) or any(digest(p)!=sha for p,sha in bound.items()):raise ValueError('selected-test input changed')
    if science.get(inputs['method']['path'])!=inputs['method']['sha256']:raise ValueError('test-analysis method was not frozen before main')
    for path in (Path(__file__).resolve(),HERE/'selected_coverage_analysis.py',HERE/'selected_coverage_join.py',
                 HERE/'selected_analysis_driver.py',HERE/'selected_test_analysis.py',HERE/'evaluation_contract.py'):
        if science.get(str(path))!=digest(path) or method_bound.get(str(path))!=digest(path):raise ValueError('test-analysis implementation changed after main')
    if (main.get('gate'),main.get('condition'),main.get('status'))!=('L2','v2-S2','FROZEN'):
        raise ValueError('main execution is not frozen')
    if method['arms']!=main['eligible_arms'] or method['seeds']!=list(SEEDS) or main['main_seeds']!=list(SEEDS) or method['bootstrap_seed']!=1302301 or method.get('sample_idx')!=0:
        raise ValueError('pre-main paired analysis population or randomness changed')
    tasks=read(method['tasks']);rows,sources,availability=collect(inputs['runs'],tasks,method['arms'],inputs['L2']['sha256'],digest(HERE/'evaluation_contract.py'),repo)
    if any(bound.get(ref['path'])!=ref['sha256'] for ref in sources):raise ValueError('analysis omitted published or raw outcome bindings')
    validate(rows,tasks,method['arms'])
    root=Path(plan['output']);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'attempt.json',{'condition':'v2-S2','method':inputs['method'],'inputs':plan['inputs'],'automatic_retry':False})
    write_new(root/'rows.json',rows)
    result=evaluate(rows,tasks,method['arms'],bootstrap_seed=method['bootstrap_seed'])
    result.update(stage='SELECTED_TEST_INDEPENDENT_COVERAGE_ANALYSIS',method_sha256=inputs['method']['sha256'],inputs_sha256=plan['inputs']['sha256'],
        L2_sha256=inputs['L2']['sha256'],run_availability=availability,rows_sha256=digest(root/'rows.json'))
    write_new(root/'result.json',result);return result
