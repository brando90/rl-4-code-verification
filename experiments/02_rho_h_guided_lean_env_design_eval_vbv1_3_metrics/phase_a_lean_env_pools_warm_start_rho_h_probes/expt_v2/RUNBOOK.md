# Experiment 02A v2 — external-pool preflight runbook

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/RUNBOOK.md>

**TLDR:** Run this CPU-only preflight on the execution checkout before any probe or RL training. It uses the transferred immutable FVAPPS source, verifies its bytes, screens it against the local VeriBench corpus, and writes the fixed candidate manifest; it does not make a task reference accepted.

SNAP PRE-APPROVAL (Brando, 2026-09-14): you run with full access (permission prompts and sandbox bypassed). Every command, install, Docker/GPU use, file and git operation (branch, commit, push, PR, merge per Rule 46) and every budgeted experiment call needed for this task is already approved. Never stop to ask for permission or confirmation; treat any approval step as granted, proceed, and log what you did. Pause only for a real blocker (missing credential, exhausted budget, a human-only login step).

```bash
set -euo pipefail
cd /lfs/skampere1/0/brando9/rl4cv_azalia_execute/rl-4-code-verification
python3 experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/scripts/build_fvapps_external24.py \
  --fvapps-train /lfs/skampere1/0/brando9/rl4cv_azalia_execute/inputs/fvapps_train_3552a173.jsonl \
  --veribench-root /lfs/skampere1/0/brando9/rl4cv_e01/rl-4-code-verification/external/veribench \
  --out experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/results/fvapps_external24_snap_manifest.json
```

The preflight costs no graphics processing unit time. A later reference-construction stage must use Lean 4.22.0 and record per-task compilation, allowed-axiom, non-vacuity, and allocation receipts before this panel can be used for the factor-versus-scalar feedback study or any RL outcome.

The coordinator transfers the 11-megabyte source from its authenticated download; the script verifies its exact hash. If missing, retrieve the pinned dataset through the supported Hugging Face dataset-download command (`--repo-type dataset`), using existing authorized access without printing credentials. Do not overwrite any earlier manifest.
