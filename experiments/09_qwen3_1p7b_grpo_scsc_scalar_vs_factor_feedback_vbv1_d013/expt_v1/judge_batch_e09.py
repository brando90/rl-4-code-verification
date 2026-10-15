"""TLDR: Owned three-repeat/two-member FSC batches using unchanged vb103 prompts and Valkyrie CLI transport."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

from fsc_queue import CONFIGS, six_rating_result

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'src'))
from rl4cv import valkyrie_hosted as hosted  # noqa: E402  run-start remap of the gateway secret (10-14-2026)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_bridge():
    from judge_e09 import bridge
    return bridge


def prepare_payload(task_id: str, candidate: str, reference: str, source: str,
                    scorer_fingerprint: str) -> dict:
    b = load_bridge()
    digest = sha(json.dumps([task_id, candidate, reference, source], ensure_ascii=False).encode())
    directory = b.PRIVATE / 'online_inputs' / digest
    directory.mkdir(parents=True, exist_ok=True)
    for name, contents in [('gold.lean', reference), ('source.py', source)]:
        path = directory / name
        if path.exists() and path.read_text() != contents:
            raise RuntimeError('Immutable judge input changed')
        if not path.exists():
            path.write_text(contents)
    item = {'item': digest, 'task': task_id, 'split': task_id.split('__', 1)[0],
            'gold_file_name': 'gold.lean', 'ref_ann_path': b.relative(directory / 'gold.lean'),
            'py_ann_path': b.relative(directory / 'source.py')}
    system, user = b.prompts.render(b.RUBRIC, item, candidate, 'solution.lean')
    bindings = {'rubric': b.RUBRIC, 'rubric_fingerprint': b.prompts.rubric_fingerprint(b.RUBRIC),
                'configs': {c: b.judge_config(c) for c in CONFIGS},
                'judge_bundle_sha256': sha((b.E103 / 'scripts/valkyrie_judge_agent/judge_call.py').read_bytes()),
                'rendered_prompt_sha256': sha((system + '\n\n' + user).encode()),
                'scorer_extraction_fingerprint': scorer_fingerprint,
                'aggregation': 'mean(two medians of three integer ratings)/5'}
    return {'task_id': task_id, 'candidate': candidate, 'reference': reference, 'source': source,
            'judge_fingerprint': sha(json.dumps(bindings, sort_keys=True).encode()),
            'bindings': bindings, 'rendered': {'system': system, 'user': user}}


def build_batch(payloads: list[dict]) -> dict:
    b = load_bridge()
    assert payloads and len({p['key'] for p in payloads}) == len(payloads)
    batch_id = sha('\n'.join(sorted(p['key'] for p in payloads)).encode())
    directory = b.PRIVATE / 'online_batches' / batch_id
    pack = directory / 'pack'
    if pack.exists():
        raise FileExistsError('Existing batch pack must be adopted, not rebuilt/readmitted')
    pack.mkdir(parents=True)
    rows = []
    for payload in payloads:
        prompt_hash = sha((payload['rendered']['system'] + '\n\n' + payload['rendered']['user']).encode())
        assert prompt_hash == payload['bindings']['rendered_prompt_sha256']
        for repeat in (1, 2, 3):
            record = {'cell': f"{payload['key']}__r{repeat}", 'item': payload['key'], 'repeat': repeat,
                      'kind': 'main', 'candidate_sha256': sha(payload['candidate'].encode()),
                      'prompt_sha256': prompt_hash}
            row = b.judge_pack.emit(pack, 'e09', record, payload['rendered'])
            row.update(system=batch_id, task_id_vb=payload['task_id'], sample_idx=0,
                       judge_fingerprint=payload['judge_fingerprint'])
            rows.append(row)
    manifest = {'batch_id': batch_id, 'pack_abs': str(pack), 'cells': rows,
                'control_cells': [], 'smoke_cells': [], 'configs': list(CONFIGS),
                'n_declared_ratings': 6 * len(payloads), 'n_tasks': len(rows),
                'benchmark': 'veribench-rl4cv-e09-batch-' + batch_id[:16]}
    manifest['round_trip'] = b.judge_pack.verify(pack, manifest)
    if manifest['round_trip']['failures']:
        raise RuntimeError('Frozen prompt pack round-trip mismatch')
    manifest['verdict'] = 'PASS'
    b.write_json(directory / 'manifest.json', manifest)
    return manifest


def admit_exact(b, suite, batch, manifest, ids_file):
    """The frozen CLI routing parameters, with explicitly experiment09 labels."""
    state = b.load_state()
    if state.get('runs'):
        raise RuntimeError('Recorded admissions must be adopted, not submitted again')
    for name in CONFIGS:
        cfg = b.judge_config(name)
        kwargs = {'judge_config': name, 'max_tokens': str(cfg['max_tokens']),
                  'benchmark': f'rl4cv-e09-{batch[:16]}-{name}'}
        for key in ('reasoning_effort', 'compute_effort'):
            if cfg.get(key):
                kwargs[key] = cfg[key]
        args = ['run', 'start', '--agent', b.AGENT, '--benchmark', manifest['benchmark'],
                '--dataset', 'default', '--model', cfg['selector'], '--concurrency', '8',
                '--label', f'rl4cv-e09-{batch[:16]}-{name}', '--task-ids-file', str(ids_file), *hosted.secret_args()]
        for key, value in kwargs.items():
            args += ['-k', key, value]
        entry = {'config': name, 'selector': cfg['selector'], 'kwargs': kwargs,
                 'expected_cells': len(manifest['cells']), 'suite': suite,
                 'benchmark': manifest['benchmark'], 'admitted_at': b.stamp(),
                 'phase': 'admitting', 'command': args, 'task_ids_sha256': sha(ids_file.read_bytes())}
        state['runs'][batch + '/' + name] = entry
        b.save_state(state)
        result = b.cli(args)
        found = b.UUID_RE.findall(result.stdout + result.stderr)
        if result.returncode or not found:
            entry.update(phase='admission_failed', returncode=result.returncode)
            b.save_state(state)
            raise RuntimeError('CLI admission failed; preserve unknown/partial admission without replay')
        entry.update(phase='running', run_id=found[0])
        b.save_state(state)


class ValkyrieBatchTransport:
    """Serialize all measured batch operations; no provider API and no rating retry.

    Caller must deploy/register an owned collect-only service for this exact pack.
    The injected lifecycle keeps service/process identity bookkeeping in the driver.
    Existing completed controls are never passed to admit or polled by this object.
    """
    def __init__(self, deploy, finish, admission_check, timeout_seconds=7200):
        self.deploy, self.finish = deploy, finish
        self.admission_check = admission_check
        self.timeout_seconds = timeout_seconds

    def __call__(self, payloads):
        b = load_bridge()
        manifest = build_batch(payloads)
        root = Path(manifest['pack_abs']).parent
        result_dir = root / 'receipts'
        result_dir.mkdir()
        receipt = result_dir / 'pack.json'
        b.write_json(receipt, manifest)
        batch = manifest['batch_id']
        suite = 'e09:' + batch
        old_results, old_state, old_spec = b.RESULTS, b.STATE, b.suite_spec
        b.RESULTS, b.STATE = result_dir, result_dir / 'state.json'
        def owned_spec(value):
            if value != suite:
                raise ValueError('Foreign suite rejected by experiment09 transport')
            return {'suite': suite, 'system': batch, 'benchmark': manifest['benchmark'],
                    'pack_receipt': receipt, 'key_prefix': batch + '/', 'part_field': 'cells'}
        b.suite_spec = owned_spec
        ids_file = result_dir / f'task_ids_{batch}.txt'
        ids_file.write_text(''.join(row['task_id'] + '\n' for row in manifest['cells']))
        terminal = False
        try:
            self.admission_check()
            # The budget reservation is already durable in BatchFSCQueue before
            # this transport can admit the first of the six constituent ratings.
            self.deploy(manifest)
            admit_exact(b, suite, batch, manifest, ids_file)
            state = b.load_state()
            if any(not state['runs'].get(batch + '/' + c, {}).get('run_id') for c in CONFIGS):
                raise RuntimeError('Incomplete CLI admission; adopt native run IDs, never readmit')
            until = time.monotonic() + self.timeout_seconds
            while True:
                self.admission_check()
                if b.poll() == 0:
                    terminal = True
                    break
                if time.monotonic() >= until:
                    raise TimeoutError('Validated-route batch deadline reached; preserve healthy runs')
                time.sleep(30)  # Status only: no model invocation per poll.
            b.harvest(suite, list(CONFIGS))
            results = {p['key']: {'ratings': [], 'judge_fingerprint': p['judge_fingerprint']} for p in payloads}
            for config in CONFIGS:
                harvest = b.read_json(result_dir / 'harvests' / f'cells_{batch}__{config}.json')
                if not harvest:
                    raise RuntimeError('Missing native harvest')
                artifact_root = b.WORK / 'judge/raw' / f'{batch}__{config}' / 'artifacts'
                native_receipts = {}
                for path in artifact_root.rglob('receipt.json'):
                    native = json.loads(path.read_text())
                    native_receipts[native.get('task_id') or path.parent.name] = native
                cfg = b.judge_config(config)
                for rating in harvest['cells']:
                    if rating['item'] not in results:
                        raise RuntimeError('Foreign response in batch')
                    native = native_receipts.get(rating['task_id'], {})
                    delivered = native.get('config', {})
                    verified = (native.get('selector') == cfg['selector'] and
                                native.get('judge_config') == config and
                                delivered.get('max_tokens') == cfg['max_tokens'] and
                                not native.get('fallback') and
                                all(delivered.get(k) == cfg.get(k) for k in ('reasoning_effort', 'compute_effort')))
                    row = {**rating, 'run_id': harvest['run_id'],
                           'selector': native.get('selector'),
                           'reasoning_effort': delivered.get('reasoning_effort'),
                           'compute_effort': delivered.get('compute_effort'),
                           'delivery_verified': verified}
                    if not verified:
                        row['status'] = 'unverified_delivery'
                    results[rating['item']]['ratings'].append(row)
            # Preserve native partial/error cells even if exact-six validation fails.
            b.write_json(root / 'native_results.json', results)
            return {key: six_rating_result(result) for key, result in results.items()}
        finally:
            if terminal:
                self.finish(manifest)
            b.RESULTS, b.STATE, b.suite_spec = old_results, old_state, old_spec
