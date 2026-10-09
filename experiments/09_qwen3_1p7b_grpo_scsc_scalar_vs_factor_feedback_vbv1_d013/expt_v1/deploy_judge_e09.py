#!/usr/bin/env python3
"""TLDR: Deploy the experiment09-owned 25-control Valkyrie benchmark service without altering experiment08."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True  # Immutable experiment08 helper source reuse.

ROOT = Path("/lfs/skampere1/0/brando9/rl4cv_e09")
REPO = ROOT / "rl-4-code-verification"
E08_SCRIPT = Path("/lfs/skampere1/0/brando9/rl4cv_e08/rl-4-code-verification/experiments/08_qwen3_base_matched_lean_sft_opus55_astra_teachers_vbv1_train_val_test/expt_v1/scripts/deploy_service_e08.py")
os.environ["E08_WORK"] = str(ROOT)
spec = importlib.util.spec_from_file_location("frozen_e08_service", E08_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load deployment helper {E08_SCRIPT}")
service = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = service
spec.loader.exec_module(service)

# Keep the frozen service implementation and its platform runtime but redirect every mutable receipt,
# pack/config source and public artifact to experiment09's owned checkout/runtime.
service.REPO_ROOT = REPO
service.E103 = REPO / "external/veribench/experiments/103_single_call_baselines_all_models_vbv1_vbv2_valkyrie_validated_fsc_judge"
service.SERVICE_DIR = service.E103 / "scripts/vb_service_single_call"
service.KERNEL_AXIOMS = REPO / "external/veribench/scripts/scsc/kernel_axioms.py"
service.LAKE_DIR = Path("/lfs/skampere1/0/brando9/rl4cv_e08/grading/lean_src")  # immutable compiler source; collect-only service does not compile
service.PUBLIC_RECEIPT = REPO / "experiments/09_qwen3_1p7b_grpo_scsc_scalar_vs_factor_feedback_vbv1_d013/expt_v1/results/judge_service_e09.json"

if __name__ == "__main__":
    raise SystemExit(service.main())
