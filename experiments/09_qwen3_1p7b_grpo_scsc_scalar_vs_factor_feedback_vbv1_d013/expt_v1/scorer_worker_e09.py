#!/usr/bin/env python3
"""TLDR: Frozen scorer CLI with compile-log instrumentation; no scientific definitions changed."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True  # Never write into the reused experiment08 source.

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCORER = REPO / 'external/veribench_scorer'
CANONICAL = SCORER / 'experiments/71_E2_valkyrie_harbor_vals_ai_eval_code/scripts/score_scsc.py'
SOURCE_ADAPTER = Path('/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts/score_teacher_files.py')


def load_adapter():
    spec = importlib.util.spec_from_file_location('e09_readonly_frozen_scorer_adapter', SOURCE_ADAPTER)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    adapter.REPO_ROOT = REPO
    adapter.SCORER = SCORER
    adapter.SCORE_SCSC = CANONICAL
    adapter.GOLD_DIR = SCORER / 'veribench_dataset/lean_src/veribench'
    adapter.DATASET_GOLD = REPO / 'external/veribench/veribench_dataset/lean_src/veribench'
    adapter.VACUITY_SOURCES = {'rl4cv_rewards': REPO / 'src/rl4cv/rewards.py',
        'veribench_nonvacuous_test': REPO / 'external/veribench/tests/test_reference_specs_nonvacuous.py'}
    adapter.check_frozen()
    return adapter


def main():
    load_adapter()  # Fail closed on source-pin/hash mismatch before any compile.
    assert '--skip-tc' in sys.argv, 'This process may never invoke a judge'
    assert '--skip-compile' not in sys.argv
    spec = importlib.util.spec_from_file_location('e09_canonical_score_cli', CANONICAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    original = mod.S.compile_lean_file
    log_path = Path(os.environ['E09_COMPILER_RECORDS'])
    def observed_compile(*args, **kwargs):
        result = original(*args, **kwargs)
        # Pure observation: return the exact original result without modifying it.
        with log_path.open('a') as out:
            out.write(json.dumps({'file': str(args[0]), 'source_sha256': hashlib.sha256(Path(args[0]).read_bytes()).hexdigest(),
                                  'result': asdict(result)}, sort_keys=True) + '\n')
        return result
    mod.S.compile_lean_file = observed_compile
    return mod.main()


if __name__ == '__main__':
    raise SystemExit(main())
