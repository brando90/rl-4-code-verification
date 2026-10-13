# Experiment 14 results: IRT ability versus pass@1 on half A as forecasts of held-out pass@1 (SWE-bench Verified, 164 systems × 424 tasks)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/results.md>

**TLDR:** Experiment 14 (Q1 of the VeriBench IRT idea page): 164 SWE-bench Verified systems × 424 tasks, experiment 07's 2,000 splits per size, zero model calls. Verdict: **CONTINUE**.

- **Level (P2): large, robust win.** At n_A = 50, the 2PL forecast of each system's held-out pass@1 has mean absolute error (MAE) 0.0344 against 0.0554 for pass@1 on half A, a difference of +0.0210 [+0.0195, +0.0224], p-val=0.001. It also beats a non-IRT regression forecast from the same reference systems.
- **Rank (P1): small win by experiment 07's frozen Spearman rule.** Median Δ +0.0040 [+0.0016, +0.0066]; Δ > 0 in 1,623/2,000 splits. The share's bootstrap interval touches the 0.60 threshold, Kendall τ-b is slightly lower, and the rank gain vanishes by n_A = 250.

**Status:** DONE (10-12-2026 22:43 PDT; locked run on `skampere1`, exit 0)

**Last updated:** 10-12-2026 22:55 PDT (worker `ccv-vb-irt-q1-pass1-forecast`, Claude Code `claude-opus-5-5`, effort max, Vals profile)

## Phases

| Phase | Status | Evidence |
|---|---|---|
| Design, protocol draft, code, tests | DONE (draft r1, `1dad751`) | [PROTOCOL.md](PROTOCOL.md), `expt_v1/`, `tests/test_e14_irt.py` |
| Pre-lock check: experiment 07 H2 reproduction on the replayed splits | DONE (10-12-2026 15:50 PDT) | 07's `held_out_prediction` on the replayed stream equals the published H2 block exactly. At n_A = 50 the replay gives −0.012139 and 92/2000, as published |
| Light QA (one round, Codex GPT-6 Astra, ultra) | DONE (review 16:07 PDT; fixes 20:38–21:50 PDT) | [Review](reviews/light_qa_codex_gpt6_astra_ultra_10-12-2026.md): `VERDICT: FAIL` (CRITICAL 2, MAJOR 4, MINOR 1). [Resolution](reviews/light_qa_resolution_10-12-2026.md): `VERDICT: FIXED`, 7 fixes with regression tests, no re-review. The review ran on the personal Codex account, because Codex-Vals was at its usage limit and the Stanford account was read-only |
| Lock protocol revision 2 and freeze the forecast | DONE (10-12-2026 21:54:40 PDT, `9c42166`) | `expt_v1/forecasts/e14_forecast.json`, SHA-256 `33de7cd2268f60ed4d4d828d6eec7f5c5b79a9ce457cc8da881f5d54dc706890`, 21 predictions |
| Locked run | DONE (21:55:46–22:43:14 PDT, 2,831 s) | `skampere1`, tmux `ccv-rl4cv14-irt-q1-run`, checkout at `9c42166`, 64 processes, Python 3.12.14, numpy 2.2.6, scipy 1.16.3, one thread each. Outputs: [`expt_v1/results/`](expt_v1/results/), full tables in [`results_tables_e14.md`](expt_v1/results/results_tables_e14.md); console log (gitignored) at `/lfs/skampere1/0/brando9/rl4cv_e14/experiments/14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems/expt_v1/results/run_e14.log`, ending `RUN_EXIT=0` |

## Headline

**rl4cv / experiment `14_irt_2pl_ability_vs_heldout_pass1_forecast_swebench_verified_164_systems`.** Hypothesis being de-risked: does item response theory (IRT) ability estimated from the n_A tasks of half A forecast each system's pass@1 on the held-out half B better than its pass@1 on half A does? Measured via Δ Spearman for rank and mean absolute error (MAE) for level, on experiment 07's 164 × 424 SWE-bench Verified matrix and its exact 2,000 H2 splits at n_A = 50.

- **Old result.** Experiment [`07_scs4c_vs_pass1_swebench_across_models`](../07_scs4c_vs_pass1_swebench_across_models/results.md)'s smooth partial-credit score SCS4C-T failed this exact rank test: median Δ −0.012, 92/2000 splits positive. This run reproduced that number exactly before computing anything new.
- **Instrument.** There is no judge and no model call. The 2PL model is fitted by marginal maximum a posteriori on a 1,201-node ability grid.
  - Rank arm: the model is refitted for each split on half A of all 164 systems, with no half-B data.
  - Level arm: item parameters come from the systems in the other 9 of 10 folds.
  - Numerical gates all passed by wide margins:
    - 0 of 16,000 within-half fits failed;
    - all 30 primary fold fits met the gradient bound (≤ 1e-4) on both grids, with a largest check-grid gradient of 8.5e-7;
    - posterior endpoint mass was at most 9.8e-27;
    - check-grid rescoring changed values by at most 1.1e-12.

  The Rasch tie check gave Δ = 0 exactly in all 8,000 splits.
- **P1, rank (frozen rule: median Δ > 0 and share ≥ 0.60).**
  - Median Δ +0.0040 [+0.0016, +0.0066], p-val=0.001 (system-cluster bootstrap, 2,000 draws, null: median Δ = 0).
  - Δ > 0 in 1,623/2,000 splits = 0.811 [0.600, 0.839], p-val=0.052 (bootstrap, null: share = 0.60).
  - Median Spearman 0.9574 for 2PL against 0.9532 for pass@1 on A.
  - **Holds.** No within-half fit failed, so the worst-case and best-case bounds agree.
- **P2, level (frozen rule: MAE lower, with the 95% interval excluding 0).**
  - MAE 0.0554 (pass@1 on A) against 0.0344 (2PL): a difference of +0.0210 [+0.0195, +0.0224], p-val=0.001 (system-cluster bootstrap, null: zero mean difference).
  - 2PL is closer for 159/164 systems and has the lower MAE in 1,972/2,000 splits.
  - Mean bias (forecast minus held-out pass@1): pass@1 on A +0.0001, 2PL −0.0007 (means 0.5732 forecast versus 0.5739 held out).
  - **Holds.**
- **Is the level gain IRT, or just using other systems?** 2PL also beats non-IRT forecasts built from the same reference systems:
  - linear regression of pass@1 on B on pass@1 on A: +0.0022 [+0.0015, +0.0028], p-val=0.001, 2PL closer for 133/164 systems;
  - a mean difficulty shift: +0.0052 [+0.0043, +0.0059].

  By the frozen interpretation rule, the level gain includes item-level IRT information. Most of it, however (MAE 0.0554 → 0.0366), is already captured by the regression control.
- **Verdict? CONTINUE (both rules hold).** Three qualifications:
  1. **The rank gain is small and fragile.**
     - Its size: +0.004 in Spearman.
     - Its share interval reaches the 0.60 threshold (p-val=0.052).
     - The median Kendall τ-b is *lower* for 2PL than for pass@1 on A (0.8259 against 0.8306). Pass@1 on 50 tasks leaves many systems tied, and τ-b counts those pairs as tied rather than misordered.
     - It shrinks as n_A grows: +0.0071 at n_A = 25, +0.0012 at 100, −0.0005 at 250.
     - In the one-system-per-base-model subset (73 systems) it is +0.0016, with a share of 0.619.
  2. **The level gain is large and consistent.** It holds at every size: +0.0313 at n_A = 25, +0.0154 at 100, +0.0126 at 250, all with intervals excluding 0. It holds for all five fold seeds (+0.0209 to +0.0210) and in the 73-system subset (+0.0165 [+0.0137, +0.0191]).
  3. **Scope.** The data are public single-run submissions, conditional on this 164 × 424 cohort. The intervals hold the fitted parameters and the task splits fixed.
- **Next step:** per the VeriBench idea page, Q1 positive unblocks Q2. Q2 asks whether an IRT fit on earlier supervised fine-tuning (SFT) checkpoints forecasts when a policy starts giving RL signal, using rl4cv 05/08 per-task files; it costs zero model calls. Experiment 13 remains blocked on Brando's decision.

## Secondary results (n_A = 50 unless stated; full tables in [`results_tables_e14.md`](expt_v1/results/results_tables_e14.md))

| Analysis | Result |
|---|---|
| S2 graded model, partial credit as none / partial / resolved | Rank (refitted within half A): median Δ +0.0051 [+0.0020, +0.0080], p-val=0.002; share 0.838 [0.617, 0.872], p-val=0.032 against 0.60. **Holds.** Level: +0.0218 [+0.0205, +0.0231], p-val=0.001. **Holds.** It beats linear regression by +0.0030 [+0.0023, +0.0037]. Weighted by IRT, the partial credit that hurt in experiment 07 now helps slightly |
| Fold artifact (the reason for the protocol's design) | The K-fold arms that are monotone in pass@1 on A (1PL, mean shift, regression) have rank Δ of −0.0036, −0.0032 and −0.0039, with at most 3 of 2,000 splits positive. This confirms on real data the artifact seen on synthetic data before the lock. The K-fold 2PL rank Δ is +0.0036 (share 0.793) |
| S4 promotion gates, all 26,732 ordered pairs per split | Harmful-promotion rate: scalar gate 0.0763, paired-pass@1 one-SE gate 0.0291, IRT one-SE gate 0.0265 (base rate 0.4974). At matched counts the IRT gate is safer: +0.0049 [+0.0031, +0.0070] and +0.0050 [+0.0032, +0.0073], both p-val=0.001 (bootstrap conditional on each split's selections). Matched counts held in every split |
| S5 stability across random halves A | Mean per-system standard deviation of the forecast error: pass@1 on A 0.0693, 2PL 0.0386 (ratio 0.558 [0.544, 0.571]), graded model 0.0368 (0.531), regression 0.0445 (0.643). IRT estimates are *steadier* across random task subsets, not noisier. The Madaan et al. (2024) caution concerned IRT-*selected* subsets and per-run seed variance, which these single-run data cannot show |
| S5 fold seeds 0–4 (K-fold 2PL) | Median Δ +0.0033 to +0.0037; share 0.770 to 0.798; MAE difference +0.0209 to +0.0210; all fits converged |
| S5 item parameters across the 10 folds | 2PL location: Pearson mean 0.993 (minimum 0.981). 2PL slope: 0.965 (minimum 0.931). 1PL common slope 1.57–1.66 |
| S6 one system per base model (73 systems) | Rank: median Δ +0.0016, 1,238/2,000 = 0.619. Level: +0.0165 [+0.0137, +0.0191], p-val=0.001, 2PL closer for 67/73. 0 of 2,000 within-half fits failed |
| S7 held-out cell Brier score | 2PL 0.0967, item-only (reference pass rate) 0.1394, system-only (pass@1 on A) 0.2208. Per-task, per-system probabilities, the input an RL prompt sampler needs, are much better with IRT |
| Correlations with pass@1 on B (medians over splits) | pass@1 on A: Pearson 0.9638, Spearman 0.9532, Kendall τ-b 0.8306. 2PL within half A: 0.9527 (EAP ability is on the logit scale), 0.9574, 0.8259. K-fold 2PL forecast: 0.9670, 0.9571, 0.8251 |

## Frozen forecast versus outcome

The forecast was frozen at 10-12-2026 21:54:40 PDT, before any real-data IRT fit.

- **Numeric predictions:** 10 of 14 outcomes fell inside their 80% intervals.
  - Misses, all in IRT's favor: the K-fold 2PL rank Δ (forecast −0.001 [−0.005, +0.003]; outcome +0.0036), the graded-model rank Δ (−0.002 [−0.010, +0.004]; +0.0051), the matched gate difference (0.000 [−0.004, +0.004]; +0.0049), and the error-spread ratio (0.75 [0.60, 0.90]; 0.558).
- **Probabilistic predictions** (Brier score 0.186 over 7 events):
  - P1 rank holds, forecast 0.40: occurred.
  - P2 level holds, 0.85: occurred.
  - Q1 continue, 0.88: occurred.
  - Q1 inconclusive, 0.04: did not occur.
  - Level gain beyond the reference panel, 0.45: occurred.
  - Graded-model rank holds, 0.25: occurred.
  - Graded-model level holds, 0.80: occurred.
- **Reading:** the forecaster expected the rank gain to be near zero, and it was small but positive.

## Deviations

None from the locked protocol (revision 2). The run used 64 processes, as the protocol states, and finished in 47 minutes against the protocol's estimate of 1–2 hours. Pre-lock deviations from draft revision 1 (grid, gates, rules, process pool) are recorded in protocol revision 2 and in the [QA resolution](reviews/light_qa_resolution_10-12-2026.md).

**TLDR-end:** [rl4cv: expt14 IRT-vs-held-out-pass@1 forecast (Q1)] On experiment 07's 164 × 424 SWE-bench Verified matrix, 2PL ability from 50 tasks forecasts held-out pass@1 much better in level (MAE 0.034 vs 0.055) and slightly better in rank (Spearman +0.004, share 0.81, interval touching 0.60), so Q1's verdict is CONTINUE. Most of the level gain comes from using the other systems' data, and the rank gain is small and size-dependent.
