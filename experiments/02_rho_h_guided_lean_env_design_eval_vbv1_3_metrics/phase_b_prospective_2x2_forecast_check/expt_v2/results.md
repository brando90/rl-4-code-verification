# Experiment 02B v2 — live prospective external-pilot results

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/results.md>

**TLDR:** The prospective external pilot is designed but blocked before launch: the selected FVAPPS records have screened source text but no accepted Lean reference implementations or proofs, and the available `rl-env-scaling` launcher does not implement Lean scoring or forecasting. No forecast, rollout, training checkpoint, or evaluation outcome exists.

**Status:** BLOCKED_PRELAUNCH.

| Preflight gate | Status | Evidence |
|---|---|---|
| External source identity and screen | Ready for remote rerun | Phase-A v2 manifest builder |
| 24 accepted Lean references | Blocked | Released FVAPPS `spec` field has `sorry` stubs |
| Lean 4.22.0 toolchain | Available locally | VeriBench `lean-toolchain` pins `leanprover/lean4:v4.22.0` |
| Lean RL adapter/scorer isolation | Blocked | `rl-env-scaling` commit `7118b86` launcher is math/Math-Verify-specific |
| Numeric ρ–H forecast | Not created | Exact law equation and coefficients are not established; it must precede any arm outcome |
| Equal-compute trajectories | Not launched | 2 environments × 2 seeds × 64 frozen steps after preflight |

**TLDR-end:** [rl4cv: experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics prospective external training] This version defines the minimal equal-compute non-VeriBench prospective pilot, but it correctly remains prelaunch until valid external references and a Lean-safe trainer exist.

**Snapshot:**
```text
candidate external panel: 24 FVAPPS rows
accepted references: 0 / 24
forecast frozen: no
training trajectories launched: 0 / 4
reusable trainer: math-specific GRPO only (commit 7118b86)
```
