#!/usr/bin/env python3
"""TLDR: Run experiment09-owned judge artifacts through the frozen experiment08 vb103 CLI bridge."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

E08 = Path("/lfs/skampere1/0/brando9/rl4cv_e08")
BRIDGE = E08 / "rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts/judge_rl4cv_e08.py"
ROOT = Path("/lfs/skampere1/0/brando9/rl4cv_e09")
# `judge_pack` resolves candidate paths relative to the pinned experiment-103 checkout.
# This checkout belongs to experiment09, so this remains an owned mutable location.
PRIVATE = ROOT / "rl-4-code-verification/external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge/private/judge_e09"
RESULTS = ROOT / "receipts/judge_e09"

spec = importlib.util.spec_from_file_location("frozen_e08_bridge", BRIDGE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load frozen bridge {BRIDGE}")
bridge = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bridge
spec.loader.exec_module(bridge)

# The bridge's scientific constants, frozen imports and Valkyrie CLI transport remain unchanged.
# Only mutable state is redirected to this owned runtime; its private config stays read-only at E08.
bridge.PRIVATE = PRIVATE
bridge.RESULTS = RESULTS
bridge.STATE = RESULTS / "state.json"
bridge.WORK = ROOT
bridge.BENCH_PREFIX = "veribench-rl4cv-e09"
own_ext = ROOT / "rl-4-code-verification/external/veribench/experiments"
bridge.EXT = ROOT / "rl-4-code-verification/external/veribench"
bridge.E103 = own_ext / "103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
bridge.X100 = own_ext / "100_karpathy_recipe_tc_judge_search_human_train_val_test"
bridge.common.EXPT = bridge.X100
bridge.judge_pack.E = bridge.E103

if __name__ == "__main__":
    raise SystemExit(bridge.main())
