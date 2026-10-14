# Experiment 15: can a 2PL item response theory fit on earlier SFT rungs forecast when a Qwen3 Base policy starts producing RL signal? (VeriBench V1 validation split, zero model calls)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/README.md>

**TLDR:** This folder, `15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation`, is Q2 of the VeriBench item response theory (IRT) idea page, run with zero model calls on data that already exists: experiment 05's Qwen3 Base 1.7B/4B/8B results and experiment 08's supervised fine-tuning (SFT) checkpoint ladder (1.7B, 4B, 8B, 14B at 12.5 / 25 / 50 / 75 / 100% of one matched token budget, plus experiment 08's own Base 14B run), all restricted to the 135 validation-split tasks of decision D-013 with 8 attempts per task. For each size it fits a two-parameter logistic (2PL) IRT model on the earlier rungs, with ability linear in log SFT tokens as Item Response Scaling Laws does, and forecasts the next rung's per-task success probability p and its expected mixed-group share 1 − p⁸ − (1 − p)⁸, the quantity that says whether group-relative reinforcement learning (RL, GRPO) would get learning signal. Two baselines: the last rung carried forward and one scalar scaling curve per size with no task difficulty. Status is in [results.md](results.md); the locked plan is [PROTOCOL.md](PROTOCOL.md).

## Goal

- **Brando's question (10-09-2026):** can an IRT decomposition of evaluation metrics guide RL? The idea page ([`experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance`](https://github.com/brando90/veribench/blob/main/experiments/ideas/irt_latent_factors_for_scsc_vs_pass1_and_rl_guidance/README.md) in the VeriBench repository) lists Q2 as the next zero-call test after Q1: "Fit θ linear in log SFT tokens for each model size … on the earlier rungs. Forecast the next rung's per-task p and its expected mixed-group share 1 − p⁸ − (1 − p)⁸. Baselines: the last rung carried forward, and one scalar scaling curve with no task difficulty. Success: IRT's forecast error is lower than both baselines on the next rung. Then use IRT to choose the SFT stopping point and the RL prompt pool."
- **Why it decides something.** Experiment 08 measured directly how many SFT tokens each size needs before its validation mixed-group share reaches 0.05 (its RL-readiness gate). That measurement cost a full generation and kernel-scoring pass per rung. If an IRT fit on the *earlier* rungs forecasts the next rung's per-task p and mixed share better than carrying the last rung forward, the ladder can stop earlier, the SFT stopping point can be chosen from a forecast, and the RL prompt pool can be chosen as the tasks forecast near p = 0.5 (the prompts where a GRPO group is most likely mixed). If it does not beat the last rung carried forward, IRT adds nothing for onset forecasting on this data, and the measured ladder stays the only tool.
- **Order of work.** Q1 ([`14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems`](../14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/README.md), DONE 10-12-2026, CONTINUE) unblocked Q2. Q5, the RL comparison with an IRT reward, is [`13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013`](../13_irt_scsc_factor_guided_vs_direct_pass1_rl_sft_qwen3_vbv1_d013/README.md), BLOCKED; this experiment needs no trainer.

## Hypotheses and decision criterion

- **H1 (primary).** At the final rung (100% of the SFT budget), the 2PL forecast fitted on rungs 0–75% has a lower mean absolute error (MAE) of per-task p over the 135 validation tasks than both baselines, averaged over the eligible sizes, with each paired task-bootstrap difference's 95% interval excluding 0.
- **H2 (secondary).** The same holds at every rolling-origin rung (25, 50, 75%) and for the mixed-group share and the pooled success rate; the 1PL (Rasch) sensitivity and the log-tokens trend form agree with the primary; the graded secondary outcome (proof fraction) agrees.
- **Verdict (frozen in PROTOCOL.md and in the forecast):** **SUCCESS** if H1 holds against both baselines; **NO ADVANTAGE** if either comparison fails; **INCONCLUSIVE** if fewer than 2 sizes are eligible (a size is eligible when it has at least 3 rungs and a non-degenerate final rung) or if more than 10% of the eligible sizes' target rungs are degenerate (zero successes over 135 × 8 attempts, which forces the mixed-share target to 0). Thresholds are agent-suggested and were frozen before any outcome was computed.
- **Known ceiling.** When the policy barely moves between rungs, carrying the last rung forward is hard to beat; IRT can win only by smoothing sampling noise through pooled item difficulties and by extrapolating a trend in ability. When a size never solves anything, no method can forecast onset from its own rungs, which is why degenerate rungs are counted rather than dropped silently.

## Structure

```
15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/
├── README.md            design (this file)
├── PROTOCOL.md          locked data, rungs, models, baselines, statistics, decision rules
├── results.md           live results ledger
├── CKPT_e15_q2.md       Rule 44 checkpoint
└── expt_v1/
    ├── irt_e15.py              binomial-count 1PL / 2PL IRT: marginal MAP on a fixed ability grid, EAP scoring
    ├── analyze_e15.py          data (validation split only), rolling-origin forecasts, baselines, bootstrap, outputs (--synthetic for tests)
    ├── pin_inputs_e15.py       writes input_pins_e15.json (SHA-256 of every input file)
    ├── input_pins_e15.json     the pins the analyzer enforces
    ├── freeze_forecast_e15.py  writes the frozen forecast once
    ├── forecasts/              e15_forecast.json, SHA-256 sidecar, ledger
    └── results/                analysis_e15.json, per_rung_e15.csv, per_task_forecasts_e15.csv.gz, results_tables_e15.md
```

Tests: `tests/test_e15_irt.py` (gradient check, binomial-versus-Bernoulli equivalence, parameter recovery, baseline correctness, bootstrap plumbing, the validation-split restriction with a smuggled test id, degenerate-rung accounting, the decision rule, a synthetic end-to-end run). They run on synthetic data only.

## Method in brief

- **Data (all committed, zero model calls).** Rung 0 (0 SFT tokens) is Qwen3 Base: experiment 05's receipts for 1.7B/4B/8B restricted to the validation split by experiment 08 (`ladder/base_*_e05_validation_per_task.csv`), and experiment 08's own Base 14B validation run (`ladder/base14b_validation_per_task.csv`, same sampler and seed). Rungs 12.5–100% are experiment 08's trained checkpoints (`ladder/sft_<size>_f<frac>_validation_per_task.csv`). The outcome is `k_kernel_binary` out of `samples_known` (8) per task; `mean_proof_fraction` is the graded secondary.
- **Rungs.** The matched schedule from experiment 08's `sft_schedule.json`: 0; 720,775; 1,442,549; 2,884,708; 4,318,781; 5,752,936 assistant loss tokens. Covariate x = log(1 + tokens / 720,775), so Base sits at x = 0 and the 12.5% rung at log 2 (primary); x = log(tokens) with Base outside the trend is the sensitivity.
- **Model.** One difficulty and one discrimination per task, pooled across sizes and rungs; one ability per size-rung; k-of-8 binomial likelihood; marginal maximum a posteriori on experiment 14's 1,201-node grid with experiment 14's priors. For each target rung r the item parameters are fitted on every size-rung with index below r; each size's abilities are regressed on x and extrapolated to the target rung; per-task p follows from the item curves.
- **Baselines.** B1: the same size's last observed rung, per task. B2: a logistic line in x through the size's pooled (continuity-corrected) success rates, the same value for every task.
- **Statistics.** MAE and Brier over tasks × attempts, expected versus realized mixed share, pooled rate; 95% paired task-bootstrap intervals (10,000 draws, seed 20261014, tasks as the resampling unit, one index draw shared by all sizes); every comparison as x [lo, hi] p-val=n/a; monotonicity over training; seed variance declared unavailable (one SFT run and one sampling seed per rung).

## Dependencies

- Experiments 05 and 08's committed validation-split files; no Valkyrie, no GPU, no network.
- numpy, scipy, `rl4cv.forecast`. CPU seconds to minutes on a laptop.

## Status

See [results.md](results.md) and [CKPT_e15_q2.md](CKPT_e15_q2.md). Created 10-14-2026 by the Claude Code worker of the ultracode round (claude-fable-5-1, effort max) during the Valkyrie outage; the design was chosen without human review (Rule 57) and its agent-suggested thresholds are frozen in the forecast.
