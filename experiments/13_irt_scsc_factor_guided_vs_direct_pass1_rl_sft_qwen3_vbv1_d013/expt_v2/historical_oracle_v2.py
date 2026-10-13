#!/usr/bin/env python3
"""Execute the frozen scorer and source-specific historical readback, independent of v2 components."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import os
import sys

from rl4cv.rewards import reward_kernel_binary
from rl4cv.veribench.jobs import scored_response

REPO = Path(__file__).resolve().parents[3]
E08 = REPO / 'experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def oracle(source, *, lake_dir, scorer_root, evidence, family='ladder', known=True, truncated=False):
    """Keep full raw subprocess streams while preserving the frozen functions and their returns."""
    source, evidence = Path(source).resolve(), Path(evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    if family not in {'base', 'ladder'} or type(known) is not bool or type(truncated) is not bool:
        raise ValueError('invalid oracle identity/status metadata')
    sys.dont_write_bytecode = True
    original_hash = digest(source)
    sys.path.insert(0, str(scorer_root / 'scripts/scsc'))
    scorer = load('e13v2_frozen_scorer', scorer_root / 'scripts/scsc/run_real_eval.py')
    vacuity = load('score_teacher_files', E08 / 'score_teacher_files.py')
    vacuity.SCORER = scorer_root
    scorer.LAKE_DIR = str(lake_dir)
    raw_run = subprocess.run
    calls = []

    def observed_run(*args, **kwargs):
        index = len(calls)
        calls.append({'index': index, 'argv': args[0] if args else kwargs.get('args')})
        try:
            result = raw_run(*args, **kwargs)
        except subprocess.TimeoutExpired as exc:
            calls[index]['status'] = 'timeout'
            for stream in ('stdout', 'stderr'):
                value = getattr(exc, stream) or b''
                (evidence / f'{index}.{stream}').write_bytes(value.encode() if isinstance(value, str) else value)
            raise
        calls[index]['returncode'] = result.returncode
        for stream in ('stdout', 'stderr'):
            value = getattr(result, stream) or b''
            (evidence / f'{index}.{stream}').write_bytes(value.encode() if isinstance(value, str) else value)
        return result

    prior_tempdir = tempfile.tempdir
    tempfile.tempdir = str(evidence)
    subprocess.run = observed_run
    try:
        analysis, tests, proofs, _ = scorer._compute_agent_compile_scores('e13v2', str(source), 'core', {}, False)
    finally:
        subprocess.run = raw_run
        tempfile.tempdir = prior_tempdir
        (evidence / 'subprocesses.json').write_text(json.dumps(calls, indent=2) + '\n')
    kernel = analysis.kernel or {}
    row = {'task': 'fixture', 'agent_compiles': analysis.compiles, 'agent_n_ex': analysis.n_examples,
           'agent_n_thm': analysis.n_theorems, 'IC_tests': tests, 'IC_proofs': proofs,
           'kernel_n_theorems': kernel.get('n_theorems'), 'kernel_n_honest': kernel.get('n_honest')}
    text = source.read_text(encoding='utf-8')
    scored = scored_response(row, {'lean': text, 'truncated': truncated})
    if family == 'base':
        value, status = (reward_kernel_binary(scored), 'scored') if known else (None, 'unmeasured')
    else:
        # Invoke the historical ladder reader itself, using one owned receipt and a symlink
        # to unchanged source bytes. No historical validation/test collection is opened.
        ladder = load('e13v2_frozen_ladder', E08 / 'analyze_ladder.py')
        ladder.WORK = evidence
        score_dir = evidence / 'ladder/train/scored'
        score_dir.mkdir(parents=True)
        target = evidence / 'ladder/train/jobs/fixture_g8_s0/fixture/verifier'
        target.mkdir(parents=True)
        (target / 'solution.lean').symlink_to(source)
        receipt = {**asdict(scored), 'task_id': 'fixture', 'sample_idx': 0,
                   'status': 'scored' if known else 'unmeasured', 'IC_tests': tests, 'IC_proofs': proofs}
        (score_dir / 'scored_fixture_g8.jsonl').write_text(json.dumps(receipt) + '\n')
        cells, _ = ladder.cells_for({'source': 'e08', 'label': 'fixture'}, ['fixture'], 'train')
        cell = cells[('fixture', 0)]
        value, status = cell['kernel_binary'], 'scored' if cell['known'] else 'unmeasured'
    if digest(source) != original_hash:
        raise ValueError('integrity defect: source changed during oracle execution')
    vac = vacuity.vacuity(text) if text.strip() else {'n_vacuous': 0, 'unparseable': [], 'pattern_hits': {}, 'vacuous_types': []}
    result = {'value': value, 'status': status, 'family': family, 'compile': analysis.compiles,
              'kernel': kernel, 'vacuity': vac, 'source_sha256': original_hash,
              'scored_response': asdict(scored), 'calls': calls}
    (evidence / 'oracle.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
