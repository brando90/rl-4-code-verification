# Experiment 02B v2 — minimal prospective external-environment replication protocol

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/phase_b_prospective_2x2_forecast_check/expt_v2/PROTOCOL.md>

**TLDR:** This is the smallest informative prospective design once phase A supplies accepted external Lean references: freeze pre-training environment measurements and the forecast, then run equal-compute training only on non-VeriBench tasks. It is not runnable until a Lean adapter and accepted external references exist, so it cannot select a checkpoint on VeriBench or treat FVAPPS stubs as gold.

## Question and fixed design

The consequential uncertainty is whether pre-training environment measurements make a correct prospective *environment* choice under fixed RL compute, rather than whether an uncontrolled full scale grid improves a held-out target. Use one fixed public Qwen3 Base checkpoint at its recorded Hugging Face revision, one Lean 4.22.0 verifier, one static training policy, and two seeds per arm.

| Arm | Distinct external train environment | Reward | Equal-compute control |
|---|---|---|---|
| `full_file` | accepted, screened FVAPPS-derived full-file verification tasks | fixed `kernel_binary` | same steps, group size, response cap, rollout-token cap, optimizer updates, model, and seeds |
| `theorem_completion` | accepted, screened external theorem-completion tasks, disjoint from `full_file` | the identical fixed `kernel_binary` | same as `full_file` |

Hold out 24 source-hash-selected external tasks as the shared test split. Freeze the train/test allocation, all source and screen hashes, model revision, response cap, prompt template, and per-arm token/step budget before the first rollout. No VeriBench task, source, reference, metric, or outcome may enter training, feedback design, tuning, or checkpoint selection.

## Prospective chronology

1. Materialize accepted references and rerun the phase-A screen at the remote checkout.
2. Draw the train and 24-task test allocation in source-hash order, freeze both manifests, and measure the starting checkpoint on the 24-task external test split.
3. Measure pre-RL ρ (usable signal density) and H (effective coverage) on both environments. Once the exact equation and coefficients are independently established, write its numeric prediction identifying the winning environment and expected test delta, then freeze it with `rl4cv.forecast.freeze_forecast` before either arm trains.
4. Train both environments to their identical declared limits; preserve both seed outcomes and every failure in the denominator.
5. Score only the external 24-task test split for the causal decision. VeriBench may be measured later as a separately declared final held-out transfer evaluation, never for selection.

## Decision rule and bound

This pilot continues only if all fixed references pass, every declared cell has a receipt, and the numeric forecast is hash-verifiable. It reports the two-seed environment difference with the task-level raw outcomes and the seed as the independent training replicate; it makes no scale-law claim. Start with 2 environments × 2 seeds × a predeclared 64 optimizer steps and stop at the frozen cap. This is a falsifiable prospective environment-selection preflight, not the original 32-trajectory multi-scale replication.

## Blocking dependencies

- FVAPPS has no accepted implementations or proofs in its released row schema; the current external-24 manifest is therefore candidate-only. VERINA commit `66b3ce5014edafb20cb26b87c681e7f31847249f` is a separate candidate source for a theorem-completion environment but must receive lineage, exact-hash, word-5-gram, Lean 4.22.0, and reference-acceptance receipts before use.
- `/Users/brandomiranda/rl-env-scaling` commit `7118b86` supplies a math-specific `verl` / GRPO launcher but no Lean task adapter, external fixed-reference scorer, or prospective forecast integration.
- The paper's exact warm-start replication remains unconfirmed under D-105; this novel pilot still records a public Qwen3 Base revision before launch.
