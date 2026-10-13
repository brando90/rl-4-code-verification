# Experiment 14: does IRT ability from half A forecast held-out pass@1 better than pass@1 on half A? (SWE-bench Verified, 164 systems)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/README.md>

**TLDR:** This experiment is Q1 of the VeriBench item response theory (IRT) idea page, run on experiment 07's 164 SWE-bench Verified systems × 424 tasks with zero model calls. On experiment 07's exact 2,000 random task splits per size, it asks whether IRT ability estimated from the n_A tasks of half A forecasts each system's pass@1 on the other tasks better than its pass@1 on half A does. There are two tests: rank (Spearman across systems, experiment 07's frozen rule) and level (absolute error, with a system-bootstrap interval). Status is in [results.md](results.md); the locked plan is [PROTOCOL.md](PROTOCOL.md).

## Goal

- **Brando's question (10-09-2026):** can an IRT decomposition of evaluation metrics guide RL, and does it track the metric people report (pass@1)? His instruction at 16:45 PDT that day: plan it, have Codex GPT-6 Astra (ultra) do one light QA round, and run it to completion.
- **Origin:** the planning page [`experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance`](https://github.com/brando90/veribench/blob/main/experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md) in the VeriBench repository.
  - Q1 is its cheapest test. It was meant as an arm of [`10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs`](../10_hebe_promotion_gate_scalar_vs_factor_matrix_replay_swebench_verified_logs/README.md), which locked on 10-09-2026 without it.
  - The session that planned it died on 10-10-2026, so this folder was created by its Vals-account replacement on 10-12-2026.
- **Why it decides something:** [`07_scs4c_vs_pass1_swebench_across_models`](../07_scs4c_vs_pass1_swebench_across_models/results.md) showed that a smooth partial-credit score ranks systems slightly *worse* by held-out pass@1 than pass@1 itself (median Δ −0.012 at 50 tasks).
  - If IRT, the standard way to weight items, adds nothing either, it should not be used to shrink evaluations or to pick RL prompts on this kind of data.
  - If it does add something, Q2 and Q5 on the idea page, and rl4cv [`13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`](../13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/README.md), have a measured footing.

## Hypotheses and decision criterion

- **P1 (rank):** 2PL ability, refitted on half A of all systems, ranks systems by pass@1 on half B better than pass@1 on half A does. Holds if, at n_A = 50, the median Δ > 0 and Δ > 0 in ≥ 60% of 2,000 splits (experiment 07's frozen H2 rule).
- **P2 (level):** the 2PL posterior-predictive pass@1 on half B is closer to the truth than pass@1 on half A. Item parameters come from systems in other folds. Holds if the mean absolute error is lower at n_A = 50 with a 95% system-bootstrap interval excluding 0.
- **Q1 verdict:** CONTINUE if P1 or P2 holds; NO ADVANTAGE otherwise. A level win counts as information from IRT itself only if 2PL also beats a non-IRT linear-regression forecast built from the same reference systems.
- **Known ceiling:** Rasch ability is a monotone function of the count solved, so it can only tie pass@1 in rank. That tie is checked exactly in every split.

## Structure

```
14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/
├── README.md        design (this file)
├── PROTOCOL.md      locked data, splits, models, arms, statistics and decision rules
├── results.md       live results ledger
├── reviews/         the single light QA review (Codex GPT-6 Astra, ultra) and its resolution
└── expt_v1/
    ├── cc.md                    run instructions for the executing agent
    ├── irt_e14.py               1PL / 2PL / graded response model: marginal MAP fit on a fixed grid, EAP scoring
    ├── analyze_e14.py           data, split replay, arms, statistics, outputs (--synthetic for pipeline tests)
    ├── freeze_forecast_e14.py   writes the frozen forecast once
    ├── forecasts/               e14_forecast.json, its SHA-256 sidecar and the ledger
    └── results/                 analysis_e14.json, per_split_e14.csv.gz, fits_e14.json.gz, results_tables_e14.md
```

Tests: `tests/test_e14_irt.py`. They cover gradient checks, Rasch sufficiency and tie exactness, parameter recovery, the replay of experiment 07's random stream against 07's own bootstrap code, ranks and gate statistics.

## Method in brief

- **Data:** experiment 07's per-cell file (pinned by SHA-256): 69,536 cells, all measured. Targets are `resolved`. Partial credit comes from 07's per-test FAIL_TO_PASS and PASS_TO_PASS fractions, used as an ordered category (none, partial, resolved).
- **Splits:** experiment 07's own H2 random stream is replayed exactly, and its published H2 numbers must be reproduced before anything else runs.
- **Models:** 1PL, 2PL and a three-category graded response model, fitted by marginal maximum a posteriori on a 401-node ability grid, with abilities from expected a posteriori.
- **Arms:**
  - Rank arms refit the model on half A of every system for each split (about 16,000 small fits).
  - Level arms use 10-fold system cross-fitting, because forecasting half B needs half-B item parameters from other systems.
  - Two non-IRT controls use the same reference systems: a mean shift and a linear regression.
- **Secondary analyses:** the graded model (does IRT-weighted partial credit help where 07's unweighted partial credit hurt?); promotion gates (an IRT one-standard-error gate against the scalar and paired-pass@1 gates); stability (per-system spread across splits, fold seeds 0–4, item-parameter agreement); one system per base model (73 systems); held-out cell Brier scores.

## Dependencies

- **Data:** experiment 07's committed results (no network, no Valkyrie, no model calls).
- **Software:** numpy and scipy (scipy is needed only by this experiment) and `rl4cv.scs4c` / `rl4cv.forecast`.
- **Compute:** CPU on `skampere1`, about 30–60 minutes with 32 processes.

## Status

**DONE (10-12-2026 22:43 PDT): Q1 verdict CONTINUE.** At n_A = 50, the 2PL level forecast has MAE 0.0344 against 0.0554 for pass@1 on half A: a difference of +0.0210 [+0.0195, +0.0224], which also beats a non-IRT regression forecast from the same reference systems (+0.0022 [+0.0015, +0.0028]). The rank gain is small: Spearman Δ +0.0040 [+0.0016, +0.0066], share 0.811 [0.600, 0.839]; Kendall τ-b is slightly lower, and the gain vanishes by n_A = 250. Details: [results.md](results.md). Kept under `experiments/` because the verdict gates Q2–Q4 on the VeriBench IRT idea page and informs [`13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`](../13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/README.md).
