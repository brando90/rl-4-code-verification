# Experiment 02B v2 — prospective external pilot preflight runbook

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/RUNBOOK.md>

**TLDR:** This runbook blocks a remote launch until source, reference, adapter, model, and budget receipts are all present. The recommended next command is phase-A CPU-only screening; no NeMo RL or `verl` training command is issued because the available reusable launcher is math-specific and cannot score Lean tasks safely.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

Use the exact phase-A command in its sibling `RUNBOOK.md`; it names this worker's owned checkout, transferred input, pinned protected corpus and a new remote manifest output.

Before GPU training, create a launch receipt that verifies: (1) all 24 references have Lean 4.22.0 compile, allowed-axiom, and non-vacuity receipts; (2) a Lean adapter keeps references, scorer, and judge outside the rollout sandbox; (3) the selected Qwen3 Base checkpoint has an immutable revision; (4) both arms share exact limits; and (5) the forecast exists and verifies before outcomes. A bounded 2-arm × 2-seed × 64-step pilot is provisionally estimated as 4 short 1.7B GRPO trajectories on four 80 GB-class GPUs, but duration and GPU-hours are unmeasured because Lean response lengths and adapter throughput are unavailable; a baseline must measure them before allocation.
