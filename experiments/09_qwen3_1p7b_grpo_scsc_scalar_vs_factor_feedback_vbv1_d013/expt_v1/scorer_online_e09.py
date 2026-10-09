"""TLDR: Bounded owned compiler transport and exact-six-rating FSC callback for real rollouts."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from rl4cv.rewards import ScoredResponse, needs_judge, reward_kernel_binary
from rl4cv.veribench.exp103 import build_prompt, extract_lean
from rl4cv.veribench.jobs import materialize_jobs
from scorer_worker_e09 import load_adapter, REPO, HERE
from two_turn_env import MeasuredAnswer, scalar_score, strict_target
from train_schedule_e09 import PACK, SPLIT
import owned_processes as children


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_once(path, value):
    with path.open('x') as out:
        out.write(json.dumps(value, indent=2, sort_keys=True) + '\n')


def response_from_native(native, compiler_records, extracted, truncated):
    """No unavailable compiler/kernel measurement is converted into reward zero."""
    if not extracted:
        return ScoredResponse(False, False, 0, 0, 0, truncated=truncated), ''
    if len(compiler_records) != 1:
        raise RuntimeError('Missing/duplicate actual compile result')
    compile_result = compiler_records[0]['result']
    if not compile_result['success'] and (compile_result['log'] == 'timeout' or compile_result['errors'] == 0):
        raise RuntimeError('Compiler infrastructure failure, not a measured zero')
    if native.get('unparseable_theorem_types'):
        raise RuntimeError('Unparseable theorem type: nonvacuity unmeasured')
    if compile_result['success'] and str(native.get('kernel_probe_ok')).lower() != 'true':
        raise RuntimeError('Required kernel probe missing/failed')
    if native.get('kernel_n_unknown'):
        raise RuntimeError('Unresolved theorem kernel measurements')
    answer = ScoredResponse(True, native['compiles'], native['n_examples'],
                            native['n_theorems_stated'], native['n_theorems_proved'],
                            vacuous_theorems=native['n_vacuous'], truncated=truncated)
    assert answer.ic_tests == native['IC_tests']
    assert abs(answer.ic_proofs - native['IC_proofs']) < 1e-9
    return answer, compile_result['log']


class OnlineScorer:
    """One environment owns this bounded queue; every arm uses identical eligibility."""
    def __init__(self, root, fsc_queue, admission_check, workers=4):
        assert 1 <= workers <= 8
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.queue, self.admission_check, self.workers = fsc_queue, admission_check, workers
        self.allowed_ids = set(SPLIT.read_text().splitlines())
        self.adapter = load_adapter()
        bindings = {'scorer': self.adapter.check_frozen(), 'vacuity': self.adapter.vacuity_evidence(),
                    'extraction_sha256': sha((REPO / 'src/rl4cv/veribench/exp103.py').read_bytes()),
                    'single_call_sha256': sha((REPO / 'external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/scripts/valkyrie_single_call_agent/single_call.py').read_bytes()),
                    'lake': {n: sha((children.ROOT / 'lean_runtime' / n).read_bytes())
                             for n in ('lean-toolchain', 'lake-manifest.json', 'lakefile.lean')}}
        self.fingerprint = sha(json.dumps(bindings, sort_keys=True).encode())
        if not (self.root / 'source_identity.json').exists():
            write_once(self.root / 'source_identity.json', bindings)

    def compile_one(self, pair):
        metadata, candidate = pair
        self.admission_check()
        task_id = metadata['task_id']
        assert task_id in self.allowed_ids, 'Training scorer may not open a held-out task'
        if '__' not in task_id or '/' in task_id or '..' in task_id:
            raise ValueError('Invalid canonical task identity')
        turn = int(metadata.get('turn', 0)) + 1
        cell_id = sha(f"{metadata['rollout_id']}:{turn}".encode())
        directory = self.root / cell_id
        directory.mkdir(exist_ok=False)
        start = time.monotonic()
        prompt = build_prompt((PACK / task_id / 'instruction.md').read_text(), root=REPO / 'external/veribench')
        extraction = extract_lean(candidate, prompt.required_paths, root=REPO / 'external/veribench')
        lean = extraction.lean or ''
        truncated = bool(metadata.get('generated_tokens', 0) >= 8192 and metadata.get('last_generated_token_id') != 151645)
        cell = {'task_id': task_id, 'sample_idx': 0, 'model': 'e09', 'lean': lean,
                'extraction': extraction.method, 'truncated': truncated,
                'served': True, 'measured': True, 'generated_tokens': metadata.get('generated_tokens')}
        (directory / 'assistant.txt').write_text(candidate)
        write_once(directory / 'input.json', {**cell, 'rollout_id': metadata['rollout_id'], 'turn': turn,
                                              'candidate_sha256': sha(candidate.encode())})
        job = materialize_jobs([cell], directory / 'jobs', 'e09')[0]
        # Restrict both scorer discovery and reference mapping to this task. The
        # training scorer never opens the validation/test reference pool.
        domain, name = task_id.split('__', 1)
        gold = self.adapter.GOLD_DIR / domain / (name + '.lean')
        dataset_gold = self.adapter.DATASET_GOLD / domain / (name + '.lean')
        assert gold.read_bytes() == dataset_gold.read_bytes(), 'Frozen reference identity differs'
        assert gold.read_bytes() == (PACK / task_id / 'tests/gold.lean').read_bytes(), 'Judge-pack reference identity differs'
        gold_view = directory / 'gold' / domain
        gold_view.mkdir(parents=True)
        (gold_view / gold.name).symlink_to(gold)
        pack_view = self.adapter.pack_view(Path('/lfs/skampere1/0/brando9/rl4cv_e08/pack_train539'),
                                           [task_id], directory / 'pack')
        scores = directory / 'scores'
        records_path = directory / 'compiler_records.jsonl'
        env = self.adapter.scorer_env()
        env.update(E09_COMPILER_RECORDS=str(records_path), PYTHONPATH=str(REPO / 'src'),
                   OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        args = [sys.executable, str(HERE / 'scorer_worker_e09.py'), '--job-dir', str(job),
                '--pack', str(pack_view), '--name', 'e09', '--gold-dir', str(directory / 'gold'),
                '--lake-dir', str(children.ROOT / 'lean_runtime'), '--skip-tc', '--out-dir', str(scores)]
        with (directory / 'scorer.log').open('ab') as log:
            proc = children.spawn(args, kind='e09_cpu_scorer', env=env,
                                  stdin=-3, stdout=log, stderr=-2, start_new_session=True)
            record = children.identity(proc.pid)
            try:
                rc = proc.wait(timeout=1500)
            finally:
                # Synchronous job done or bounded timeout: never another owner's group.
                if proc.poll() is None:
                    children.stop(record)
                else:
                    with children.registry() as data:
                        data['processes'] = [r for r in data['processes'] if r.get('pid') != proc.pid]
        if rc:
            raise RuntimeError(f'Canonical scorer exit {rc}; cell {cell_id} blocked')
        rows = self.adapter.per_task_rows(scores)
        assert set(rows) == {task_id}
        native = self.adapter.scored_cell(cell, rows[task_id], lean)
        records = [json.loads(line) for line in records_path.read_text().splitlines()] if records_path.exists() else []
        answer, compiler = response_from_native(native, records, bool(lean), truncated)
        write_once(directory / 'compiler_result.json', {'native': native, 'response': asdict(answer),
                                                       'seconds': time.monotonic() - start})
        return {'directory': directory, 'metadata': metadata, 'lean': lean, 'gold': gold,
                'answer': answer, 'compiler': compiler, 'native': native}

    def score_many(self, metadata, candidates):
        from judge_batch_e09 import prepare_payload, load_bridge
        assert len(metadata) == len(candidates)
        self.admission_check()
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            results = list(pool.map(self.compile_one, zip(metadata, candidates)))
        eligible = [r for r in results if needs_judge(r['answer'], 'scsc')]
        payloads = []
        for result in eligible:
            task_id = result['metadata']['task_id']
            payloads.append(prepare_payload(task_id, result['lean'], result['gold'].read_text(),
                                           load_bridge().python_of(task_id), self.fingerprint))
        judgments = self.queue.request_many(payloads).result() if payloads else []
        assert len(judgments) == len(eligible)
        for result, judgment in zip(eligible, judgments):
            result['answer'] = replace(result['answer'], fsc=judgment['fsc'])
            write_once(result['directory'] / 'fsc.json', judgment)
        measured = []
        for result in results:
            answer = result['answer']
            status = 'measured' if needs_judge(answer, 'scsc') else 'not_required'
            measurement = MeasuredAnswer(answer, result['compiler'], status)
            write_once(result['directory'] / 'measurement.json', {'measurement': asdict(measurement),
                'S': scalar_score(answer), 'H': strict_target(answer), 'kernel_binary': reward_kernel_binary(answer)})
            measured.append(measurement)
        return measured
