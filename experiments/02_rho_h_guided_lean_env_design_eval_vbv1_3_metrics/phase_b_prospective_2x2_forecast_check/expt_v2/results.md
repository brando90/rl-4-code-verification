# Experiment 02B v2 — live prospective external-pilot results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/results.md>

**TLDR:** The prospective external pilot now has outcome-blind candidate partitions and a concrete readiness manifest, but remains correctly blocked: the independent endpoint admits 0 / 24 tasks, no Lean rollout adapter exists, and no numeric forecast may be frozen.

**Status:** BLOCKED_PRELAUNCH.

| Preflight gate | Status | Evidence |
|---|---|---|
| External source identity and screen | Ready for remote rerun | Phase-A v2 manifest builder |
| 24 accepted Lean references | Blocked | Released FVAPPS `spec` field has `sorry` stubs |
| Lean 4.22.0 toolchain | Available locally | VeriBench `lean-toolchain` pins `leanprover/lean4:v4.22.0` |
| Lean RL adapter/scorer isolation | Blocked | `rl-env-scaling` commit `7118b86` launcher is math/Math-Verify-specific |
| Numeric ρ–H forecast | Not created | Exact law equation and coefficients are not established; it must precede any arm outcome |
| Equal-compute trajectories | Not launched | 2 environments × 2 seeds × 64 frozen steps after preflight |

## Execution readiness update

- Candidate-only VERINA partitions are frozen at 141 train / 24 validation / 24 test, with no model, compile-success, judge, repair, or human outcome used to allocate them.
- The candidate initial checkpoint is locally reachable as `Qwen/Qwen3-1.7B-Base` revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`; no warm-start checkpoint is available.
- The required `rl-env-scaling` pin `7118b86…bbd015` is absent from the reachable checkout, whose head is `c75755c…4892390`; its `example_grpo_pilot.yaml` is explicitly a placeholder and has no Lean rollout adapter.
- The concrete post-admission layout would be four 64-step trajectories (two environments × two seeds) on four 80 GB A100 devices, or 256 optimizer steps total. A duration and graphics-processor-hour estimate is unknown until a one-device Lean rollout/scoring baseline exists, so no allocation is admitted.
- `rl4cv.forecast.freeze_forecast` was not called: no numeric ρ–H forecast can be honestly specified before accepted references, measured probes, and verified coefficients exist.

The machine-readable blocker and resource receipt is `results/training_readiness_manifest_2026-10-06.json`.

**TLDR-end:** [rl4cv: experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics prospective external training] This version defines the minimal equal-compute non-VeriBench prospective pilot, but it correctly remains prelaunch until valid external references and a Lean-safe trainer exist.

**Snapshot:**
```text
candidate external panel: 24 FVAPPS rows
accepted references: 0 / 24
forecast frozen: no
training trajectories launched: 0 / 4
reusable trainer: math-specific GRPO only (commit 7118b86)
```
