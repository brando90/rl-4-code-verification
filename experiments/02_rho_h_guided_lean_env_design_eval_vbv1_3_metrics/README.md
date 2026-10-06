# Experiment 02 — ρ–H-guided Lean environment design, evaluated on VeriBench V1's three metrics (Varun's question)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/02_rho_h_guided_lean_env_design_eval_vbv1_3_metrics/README.md>

**TLDR:** Varun's question: can the paper's pre-RL ρ–H equation choose Lean RL environments and rewards that raise VeriBench's three metrics (IC_tests, IC_proofs and FSC)? The equation uses usable signal density ρ and effective coverage H, both measured before any RL. Phase A builds the Lean environments and measures ρ and H. Phase B is the "if we can" gate: it tests prospectively whether the frozen equation predicts Lean RL gains. Phase C adds judge-gated FSC rewards for the third metric. Phase D trains the recipe the equation ranks best and reports VeriBench V1, which is only ever the held-out target.

Numbered experiments 02, 03, 04 and the planned 06 before 09-30-2026 ([D-007](../../docs/DECISIONS.md)).

## Current execution status

As of 10-06-2026, the bounded [phase-A version-2 source study](phase_a_lean_env_pools_warm_start_rho_h_probes/expt_v2/results.md) is published: external candidates were screened and allocated outcome-blind into 141 train, 24 validation and 24 test tasks. These remain candidate-only. The linked endpoint study in `04_scsc_factor_guided_repair_and_rl_eval_vbv1_vbv2` passed 24/24 authored checker controls but found 0/24 real tasks supported by the generic adapter required by its 20/24 gate. Authored controls do not certify external references.

The [phase-B version-2 readiness receipt](phase_b_prospective_2x2_forecast_check/expt_v2/results/training_readiness_manifest_2026-10-06.json) is `NOT_ADMITTED`, with forecast `NOT_FROZEN` and 0/4 training trajectories launched. Accepted external references, a Lean rollout/scoring adapter, verified executable training source and configuration, measured probes, and numeric forecast coefficients remain prerequisites. The larger phase designs below are not launched allocations.

## Phases

| Phase | Question | Gate to start | Its own gate | Status |
|---|---|---|---|---|
| [02A — Lean environment pools, warm start, ρ–H probes](phase_a_lean_env_pools_warm_start_rho_h_probes/README.md) | Can policy-relative 2×2 cells be built in Lean at each scale, and what are their ρ and H? (the Lean analogue of paper Table 5) | Gate G1 from [experiment 01](../01_small_open_models_veribench_v1_single_call_baseline/README.md); D-103, D-104, D-105 (D-102 for FSC channels) | Gate G2: at least one family where all four cells have ρ > 0 at every scale, fresh-confirmation success spread ≤ 3 points and admission contrast ≥ 15 points | v2 source preparation published; candidates not admitted; warm starts and probes unmeasured |
| [02B — prospective 2×2 forecast check](phase_b_prospective_2x2_forecast_check/README.md) | Does the Eq. 7 ρ–H model, refit on Lean at small scales and frozen, predict untouched larger-scale Lean curves? (levels L1, L2, L3 and L5: the crux) | Gate G2; D-103 (about 500–700 B200 GPU-hours), D-105 | Frozen and hashed 8B and 14B forecasts, scored | v2 readiness published; NOT_ADMITTED; no frozen forecast or training trajectory |
| [02C — reward channel for FSC: kernel vs judge](phase_c_reward_channel_for_fsc_kernel_vs_judge/README.md) | Do ρ and H measured under each reward predict which reward most improves VeriBench SCSC and FSC? (level L4, and Azalea's reward-design question) | 02A's cells and 02B's contract; the D-102 judge (decided 09-30-2026) | Rank agreement across channels | designed |
| [02D — train the forecast-selected recipe, report VeriBench V1](phase_d_train_forecast_selected_env_report_vbv1/README.md) | Train the predicted-best family and reward at the largest affordable scale | 02B and 02C | VeriBench SCSC and FSC gains with a regression panel for unintended effects | stub |

## How the phases connect

- 02A's pools, frozen 1,000-task within-source panel and Lean warm starts feed 02B and 02C.
- [Experiment 03](../03_rl_on_never_solved_lean_prompts_binary_vs_dense_reward_eval_vbv1/README.md) (Allen's coverage question) reuses 02A's probes and warm starts and 02B's RL contract.
- 02B reports every prospective test, including failed ones, as the paper reported its own 8B miss. Its levels decide whether the form (L2) or the coefficients (L3) of the equation transfer to Lean, or neither.
- The plan's hypotheses and levels are in [PLAN §3](../../docs/PLAN.md#3-hypotheses-what-counts-as-the-law-generalizes); the integrity rules, starting with "VeriBench is held out", are in [CLAUDE.md](../../CLAUDE.md).
