"""Advance one published technical gate through bounded local stages and one final evaluation."""
from __future__ import annotations

import argparse
import copy
import fcntl
import json
from pathlib import Path
import socket
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'phase1'))
from anchor_storage import atomic_json
from training_checkpoint import digest, write_new
from technical_ledger import pilot_lock, published, admit, check_preflight, evaluate_once, PREVIOUS
from technical_resources import reserve
from technical_stage import prepare, launch_local
from pilot_configuration import select_arms
from costs import snapshot, stage_cost

ORDER = {'T1': ('generate', 'probabilities'),
         'T2': ('generate_update', 'score', 'update', 'export', 'generate_refit', 'probabilities_refit'),
         'T3': ('replay',), 'T4': ('evaluation_generate','evaluation_score')}
KINDS = {'generate': 'generate', 'probabilities': 'probabilities', 'generate_update': 'generate',
         'update': 'update', 'export': 'export', 'generate_refit': 'generate',
         'probabilities_refit': 'probabilities', 'replay': 'replay', 'preflight': 'preflight',
         'evaluation_generate':'evaluation_generate'}


def reference(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path)}


def bindings(paths):
    return [reference(p) for p in sorted({Path(p).resolve() for p in paths})]


def read(reference):
    if digest(reference['path']) != reference['sha256']: raise ValueError('input receipt changed')
    return json.loads(Path(reference['path']).read_text())


def authorize(plan):
    lock, science = pilot_lock(plan['LP'], plan['repository'])
    config_path = Path(plan['configuration'])
    bound = {str(Path(b['path']).resolve()): b['sha256'] for b in lock['bindings']}
    for path in (config_path.resolve(), Path(__file__).resolve(), HERE/'technical_resources.py',
                 HERE/'technical_stage.py', HERE/'technical_measurements.py', HERE/'rollout_groups.py', HERE/'costs.py'):
        if bound.get(str(path)) != digest(path): raise ValueError('technical driver/configuration is not bound')
    configuration = json.loads(config_path.read_text())
    if configuration['condition'] != 'v2-S2' or configuration['host'] != socket.gethostname().split('.')[0]:
        raise ValueError('technical configuration is not for this local S2 route')
    phase1 = {k: published(v, plan['repository']) for k, v in lock['phase1_results'].items()}
    transition = select_arms(*(phase1[k] for k in ('G0', 'LP1', 'calibration', 'G1', 'H2')))
    if transition['eligible_arms'] != lock['eligible_arms']: raise ValueError('Phase 1 transition changed')
    # The public parent additionally binds each result's calibration provenance.
    for key in ('probability_probe', 'update_probe'):
        read(lock['science'][key])
    from resource_lease import verify_allocation
    allocation, _ = verify_allocation(plan['resource_plan']['allocation_plan'])
    if set(allocation['routes']) != {configuration['host']}:
        raise ValueError('this driver requires a fully bound local-only allocation')
    if any(k in configuration['runtime'] for k in ('checkpoint', 'generation_root', 'source_update', 'groups_path')):
        raise ValueError('base runtime cannot inject a dynamic predecessor')
    for key in ('probability_probe', 'update_probe'):
        if configuration[key] != lock['science'][key]:
            raise ValueError('technical probe differs from the scientific lock')
    if 'source_update' in configuration:
        raise ValueError('future T2 outcome cannot be injected into the prospective configuration')
    gate = plan['gate']
    if gate not in ORDER or set(plan['prerequisites']) != set(PREVIOUS[gate]):
        raise ValueError('technical prerequisite set changed')
    prior = {k: published(v, plan['repository']) for k, v in plan['prerequisites'].items()}
    for name, result in prior.items():
        if (result.get('gate') != name or result.get('condition') != 'v2-S2'
                or result.get('status') != 'PASS' or result.get('science_sha256') != science
                or result.get('admission_statistics_computed') is not True):
            raise ValueError('preceding gate has no published same-science PASS')
    if gate == 'T4':
        for name in ('evaluation_generation.py','evaluation_contract.py','score_evaluation.py','cost_recipe.py'):
            source=HERE/name
            if bound.get(str(source))!=digest(source):raise ValueError('T4 executable dependency unbound')
        for key in ('evaluation_probe','cost_recipe'):
            if configuration[key]!=lock['science'][key]:raise ValueError('T4 prospective inputs differ from LP')
            read(configuration[key])
    if gate == 'T3':
        # Resolve a future result through its published T2 input inventory; its
        # unknown hash must not be fabricated in the prospective LP lock.
        result = prior['T2']
        source = Path(configuration['work_root'])/'T2'/f"attempt_{result['attempt']}"/'update/output'
        expected = next((b['sha256'] for b in result['inputs']
                         if Path(b['path']).resolve() == (source/'result.json').resolve()), None)
        if expected is None or digest(source/'result.json') != expected:
            raise ValueError('published T2 does not bind its actual source update')
        configuration['source_update'] = {'path': str(source), 'result_sha256': expected}
    return lock, configuration, science


def dynamic_config(config, gate, key, root, lease):
    """Materialize only predetermined paths and newly completed predecessor receipts."""
    value = copy.deepcopy(config['runtime'])
    stage = KINDS[key]; stage_root = root/key
    value.update(stage=stage, stage_root=str(stage_root/'output'), attempt_root=str(stage_root/'health'),
                 lease_path=str(stage_root/'lease.json'), lease_id=lease['id'],
                 ray_temp=str(stage_root/'ray'))
    if gate=='T4':
        stage='evaluation_preflight' if key=='preflight' else 'evaluation_generate'
        value.update(stage=stage,manifest=config['evaluation_probe']['path'],allowlist=value['train_ids'],max_model_len=32768)
    value['provenance'] = {'condition': 'v2-S2', 'gate': gate, 'stage': stage,
                           'attempt_root': str(root), 'run_seed': value.get('run_seed')}
    probe = 'update_probe' if key == 'generate_update' else 'probability_probe'
    value['cells_path'] = config[probe]['path']
    if key == 'probabilities': value['generation_root'] = str(root/'generate/output')
    if key == 'update': value['groups_path'] = str(root/'score/groups.json')
    if key == 'export': value['checkpoint'] = str(root/'update/output/after')
    if key in ('generate_refit', 'probabilities_refit'):
        value['model'] = str(root/'export/output')
    if key == 'probabilities_refit':
        value['generation_root'] = str(root/'generate_refit/output')
        value['checkpoint'] = str(root/'update/output/after')
    if key == 'replay':
        source = Path(config['source_update']['path'])
        if digest(source/'result.json') != config['source_update']['result_sha256']:
            raise ValueError('T2 source update changed before replay')
        value['source_update'] = str(source)
    if any(digest(b['path']) != b['sha256'] for b in value['bindings']):
        raise ValueError('immutable runtime input changed before materialization')
    paths = {Path(b['path']) for b in value['bindings']}
    paths.add(Path(value['cells_path']))
    if gate=='T4':paths.add(Path(value['manifest']))
    if key == 'update': paths.add(Path(value['groups_path']))
    for field in ('generation_root', 'checkpoint', 'source_update'):
        if value.get(field): paths.update(p for p in Path(value[field]).rglob('*') if p.is_file())
    if key in ('generate_refit', 'probabilities_refit'):
        paths.update(p for p in Path(value['model']).iterdir() if p.is_file())
    value['bindings'] = bindings(paths)
    stage_root.mkdir(parents=True, exist_ok=False)
    write_new(stage_root/'lease.json', lease)
    # Health runtime writes its receipt here; other stage roots are created by
    # their isolated runtime primitives with exclusive directory creation.
    (stage_root/'health').mkdir()
    write_new(stage_root/'runtime.json', value)
    return stage_root/'runtime.json'


def cpu_scores(config, root, execution):
    from score_training import score_batch
    from rollout_groups import assemble
    cells = read(config['update_probe'])
    generation_root = root/'generate_update/output'
    terminal = json.loads((generation_root/'result.json').read_text())
    if terminal['status'] != 'COMPLETE' or terminal['completed'] != 256:
        raise ValueError('complete fixed technical update generation required')
    generations = [json.loads((generation_root/f'{i:05d}.generation.json').read_text()) for i in range(256)]
    paths = [generation_root/f'{i:05d}.generation.json' for i in range(256)]
    score_config = {**config['scoring'], 'root': str(root/'score/cells'), 'generation_root': str(generation_root)}
    scoring = score_batch(cells, score_config, {str(p): digest(p) for p in paths}, digest(execution))
    groups = assemble(cells, generations, scoring['rows'],
                      train_ids=Path(config['runtime']['train_ids']).read_text().splitlines(), technical=True)
    path = root/'score/groups.json'; write_new(path, groups)
    return {'status': 'COMPLETE', 'groups': reference(path), 'scoring': reference(Path(score_config['root'])/'result.json')}


def evaluation_scores(config,root,execution):
    from score_evaluation import score_manifest
    manifest=read(config['evaluation_probe']);generation=root/'evaluation_generate/output'
    terminal=json.loads((generation/'result.json').read_text())
    if terminal.get('status')!='COMPLETE' or terminal.get('completed')!=8:
        raise ValueError('complete train-only evaluation cost probe required')
    sources={cell['cell_id']:reference(generation/f'{i:05d}.generation.json') for i,cell in enumerate(manifest['cells'])}
    scoring={**config['scoring'],'root':str(root/'evaluation_score'),'purpose':'T4_train_cost','split':'train',
             'allowlist':config['runtime']['train_ids']}
    return score_manifest(manifest,scoring,sources,digest(execution))


def evaluate_cost(plan,config,root,admission):
    from cost_recipe import materialize,gate
    prepared=published(plan['cost_inputs'],plan['repository'])
    if (prepared.get('gate'),prepared.get('condition'),prepared.get('status'))!=('T4_COST_INPUTS','v2-S2','FROZEN'):
        raise ValueError('published T4 measurement inputs required')
    if prepared.get('LP_sha256')!=plan['LP']['sha256'] or prepared.get('attempt_sha256')!=digest(admission):
        raise ValueError('T4 cost inputs belong to another admitted attempt')
    if prepared['recipe']!=config['cost_recipe']:raise ValueError('T4 prospective projection recipe changed')
    sources=prepared['sources'];artifacts=[Path(plan['cost_inputs']['path']),Path(config['cost_recipe']['path'])]
    for ref in sources.values():
        read(ref);artifacts.append(Path(ref['path']))
    measurements=read(prepared['measurements']);artifacts.append(Path(prepared['measurements']['path']))
    # The cost-input publication includes the actual T4 generation/scoring and
    # timed stage costs, not only a hand-written aggregate measurement table.
    required=[root/'evaluation_generate/output/result.json',root/'evaluation_score/result.json',
              root/'costs/evaluation_generate.json',root/'costs/evaluation_score.json']
    supplied={str(Path(ref['path']).resolve()):ref['sha256'] for ref in sources.values()}
    if any(supplied.get(str(path.resolve()))!=digest(path) for path in required):
        raise ValueError('T4 measured cost probe provenance missing')
    recipe=read(config['cost_recipe'])
    return evaluate_once(Path(admission).parent,bindings(artifacts),lambda:gate(materialize(recipe,sources),measurements))


def evaluate(gate, config, root, admission, *, plan=None):
    if gate=='T4':return evaluate_cost(plan,config,root,admission)
    from technical_measurements import t1, t2, t3
    cells = read(config['probability_probe']); expected = [c['cell_id'] for c in cells]
    artifacts = []
    if gate in ('T1', 'T2'):
        key = 'probabilities' if gate == 'T1' else 'probabilities_refit'
        directory = root/key/'output'
        terminal = json.loads((directory/'result.json').read_text())
        if terminal['status'] != 'COMPLETE' or terminal['completed'] != len(cells):
            raise ValueError('technical probability receipt is incomplete')
        paths = [directory/f'{i:05d}.probability.json' for i in range(len(cells))]
        rows = [json.loads(p.read_text()) for p in paths]
        for cell, row in zip(cells, rows):
            if any(row[k] != cell[k] for k in ('cell_id', 'task_id', 'split', 'seed', 'prompt_token_ids')):
                raise ValueError('technical probability probe identity changed')
        artifacts += paths+[directory/'result.json']
    if gate == 'T1': callback = lambda: t1(rows, expected_cells=expected, eos_token_ids=[151643, 151645])
    elif gate == 'T2':
        path = root/'update/output/result.json'; update = json.loads(path.read_text()); artifacts.append(path)
        callback = lambda: t2(update, rows, expected_cells=expected, eos_token_ids=[151643, 151645])
    else:
        original = Path(config['source_update']['path'])/'result.json'; replay = root/'replay/output/result.json'
        if digest(original) != config['source_update']['result_sha256']:
            raise ValueError('published T2 source result changed before final replay comparison')
        first = json.loads(original.read_text()); second = json.loads(replay.read_text()); artifacts += [original, replay]
        callback = lambda: t3(first, second, source_result_sha256=digest(original))
    return evaluate_once(Path(admission).parent, bindings(artifacts), callback)


def tick(plan):
    """Run until a device wait or final gate; publication of the next gate is external."""
    lock, config, science = authorize(plan)
    gate = plan['gate']
    if gate not in ORDER: raise ValueError('unregistered technical gate')
    root = Path(config['work_root'])/gate/f"attempt_{plan['attempt']}"
    root.mkdir(parents=True, exist_ok=True)
    with (root/'controller.lock').open('a') as handle:
        try: fcntl.flock(handle, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return {'status': 'ALREADY_SUPERVISED'}
        state_path = root/'state.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else {
            'condition': 'v2-S2', 'gate': gate, 'status': 'READY', 'next_stage': 'preflight',
            'LP_sha256': plan['LP']['sha256'], 'configuration_sha256': digest(plan['configuration'])}
        if state['LP_sha256'] != plan['LP']['sha256'] or state['configuration_sha256'] != digest(plan['configuration']):
            raise ValueError('technical execution changed while resuming')
        if state['status'] in ('COMPLETE', 'HALTED', 'RESOURCE_EXHAUSTED'): return state
        if state['status'] == 'RUNNING':
            return {**state, 'status': 'RECOVERY_REQUIRED', 'reason': 'adopt existing stage evidence; no automatic replay'}
        (root/'costs').mkdir(exist_ok=True)
        while True:
            key = state['next_stage']
            if key == 'evaluate':
                if gate=='T4' and plan.get('cost_inputs') is None:
                    state['status']='WAIT_FOR_COST_INPUT_PUBLICATION';atomic_json(state_path,state);return state
                result = evaluate(gate, config, root, state['admission'],plan=plan) if gate=='T4' else evaluate(gate,config,root,state['admission'])
                state.update(status='COMPLETE', result=result); atomic_json(state_path, state); return state
            if key in ('score','evaluation_score'):
                state.update(status='RUNNING'); atomic_json(state_path, state)
                before = snapshot(root)
                try:
                    if key=='score':
                        result = cpu_scores(config, root, state['admission'])
                        write_new(root/'score/result.json', result)
                    else:evaluation_scores(config,root,state['admission'])
                finally:
                    write_new(root/'costs'/f'{key}.json', stage_cost(before, snapshot(root), stage=key))
            else:
                seconds = config['stage_seconds'][gate][key]
                resource_plan = {**plan['resource_plan'], 'LP': plan['LP'], 'repository': plan['repository']}
                reserved = reserve(resource_plan, gate=gate, attempt=plan['attempt'], stage_key=key, seconds=seconds)
                if reserved['status'] != 'RESERVED':
                    state.update(status=reserved['status']); atomic_json(state_path, state); return state
                lease = reserved['lease']
                state.update(status='RUNNING', lease_id=lease['id']); atomic_json(state_path, state)
                before = snapshot(root)
                # Preparation failure precedes a process launch; release that
                # unused owned lease, preserving the reserved stage identity.
                try:
                    runtime = dynamic_config(config, gate, key, root, lease)
                    stage_plan = prepare(LP=plan['LP'], repository=plan['repository'], gate=gate,
                        stage_key=key, config_path=runtime, maximum_seconds=seconds,
                        preparation_root=root/key/'dispatch',
                        attempt_path=state.get('admission'), preflight=state.get('preflight'))
                    result = launch_local(stage_plan, lease_root=resource_plan['lease_root'], route_environment=config['environment'])
                finally:
                    # The stage helper normally retires its own lease. Also
                    # cover errors before it reaches its cleanup block.
                    from resource_lease import release
                    from lp1 import cleanup
                    canonical = json.loads((Path(resource_plan['lease_root'])/(lease['id']+'.json')).read_text())
                    if canonical['status'] != 'RELEASED':
                        cleaned = cleanup(lease['id'])
                        release(resource_plan['lease_root'], lease['id'], cleanup_verified=cleaned['verified'])
                        (root/key).mkdir(parents=True, exist_ok=True)
                        write_new(root/key/'parent_cleanup.json', cleaned)
                    else:
                        cleanup_path = root/key/'dispatch/dispatch_cleanup.json'
                        cleaned = json.loads(cleanup_path.read_text()) if cleanup_path.exists() else None
                    canonical = json.loads((Path(resource_plan['lease_root'])/(lease['id']+'.json')).read_text())
                    write_new(root/'costs'/f'{key}.json', stage_cost(before, snapshot(root), stage=key,
                              lease=canonical, cleanup=cleaned))
                if result['status'] != 'RUNTIME_FINISHED':
                    state.update(status='HALTED', stage_result=result); atomic_json(state_path, state); return state
            if key == 'preflight':
                health = reference(root/'preflight/health/preflight.json'); check_preflight(health)
                attempt_root, admitted = admit(lock['configuration']['technical_ledger'], gate,
                    LP=plan['LP'], repository=plan['repository'], preflight=health,
                    prerequisites=plan['prerequisites'], successor=plan.get('successor'))
                if admitted['attempt'] != plan['attempt']: raise ValueError('prospective attempt number differs from actual admission')
                state.update(preflight=health, admission=str(attempt_root/'attempt.json'), next_stage=ORDER[gate][0])
            else:
                order = ORDER[gate]; offset = order.index(key)+1
                state['next_stage'] = order[offset] if offset < len(order) else 'evaluate'
            state.update(status='READY', last_stage=key); atomic_json(state_path, state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--plan', required=True, type=Path)
    print(json.dumps(tick(json.loads(parser.parse_args().plan.read_text())), sort_keys=True))
