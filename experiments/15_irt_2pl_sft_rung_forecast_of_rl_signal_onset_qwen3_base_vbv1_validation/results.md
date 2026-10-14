# Experiment 15 results: 2PL IRT rung forecast of RL-signal onset (Qwen3 Base SFT ladder, VeriBench V1 validation split)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/results.md>

**TLDR:** `15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation` ran on 10-14-2026 with zero model calls (13.7 s on Brando's Mac). **Verdict under the frozen rule: NO ADVANTAGE.** At the final rung (100% of the matched SFT budget), the two-parameter logistic (2PL) item response theory (IRT) forecast of per-task success probability is *not* closer than the last rung carried forward (B1): mean absolute error (MAE) difference B1 − IRT = −0.0066 [−0.0169, +0.0038] p-val=n/a (paired task bootstrap, 10,000 draws, 135 validation tasks, averaged over all four sizes), while it is far closer than the scalar scaling curve with no task difficulty (B2): +0.1151 [+0.0992, +0.1300] p-val=n/a. All four sizes were eligible (none of the 16 target rungs was degenerate; only Base 1.7B and Base 8B had zero successes). Reading for Brando: task difficulty is very stable across rungs and sizes (that is the whole win over B2), but extrapolating ability along log SFT tokens overshoots the plateaus in the real ladders, so IRT does not tell us earlier than the last measured rung when a size becomes RL-ready; it even called the 0.05 mixed-share gate two rungs early for 1.7B. The frozen forecast (P(SUCCESS) = 0.45) was wrong in the direction it leaned, and underestimated every realized mixed share by 2–10×.

## Verdict (frozen rule, PROTOCOL.md revision 1)

| Rule | Measured | Outcome |
|---|---|---|
| Eligibility (≥ 3 rungs, non-degenerate final rung) | 1.7B, 4B, 8B, 14B all eligible (6 rungs each; 53 / 100 / 104 / 130 successes of 1,080 at 100%) | 4 of 4 eligible |
| INCONCLUSIVE guard (< 2 eligible sizes or > 10% degenerate target rungs) | 0 of 16 target rungs degenerate (share 0.000); degenerate rungs are Base 1.7B (0/1,080) and Base 8B (0/1,080) only | not triggered |
| Validity (all fits pass both gradient gates) | 112 of 112 fits converged; max abs gradient 3.2e-7 (base grid), 7.3e-7 (check grid) | valid |
| SUCCESS needs IRT 2PL MAE below B1 **and** B2 at the final rung, intervals excluding 0 | vs B1: −0.0066 [−0.0169, +0.0038] p-val=n/a (fails); vs B2: +0.1151 [+0.0992, +0.1300] p-val=n/a (holds) | **NO ADVANTAGE** |

Positive differences mean IRT is closer. Intervals are 95% percentile intervals from a paired task bootstrap (10,000 draws, seed 20261014, tasks resampled, one index draw shared by all sizes); no p-value is computed (p-val=n/a). Source of each threshold: PROTOCOL.md → Decision rules (agent-suggested, frozen in `expt_v1/forecasts/e15_forecast.json`, SHA-256 `06847d32…31d5`, frozen at 20:10:53 UTC before the first real-data fit at 20:11 UTC).

## Primary comparison at the final rung, per size (kernel_binary, trend x = log(1 + tokens / t_12.5%))

| Size | Successes / 1,080 at 100% | MAE IRT 2PL | MAE IRT 1PL | MAE B1 | MAE B2 | B1 − IRT 2PL | B2 − IRT 2PL |
|---|---|---|---|---|---|---|---|
| 1.7B | 53 | 0.0354 | 0.0392 | 0.0250 | 0.0858 | −0.0104 [−0.0207, −0.0007] | +0.0504 [+0.0396, +0.0618] |
| 4B | 100 | 0.0484 | 0.0490 | 0.0667 | 0.1330 | +0.0183 [+0.0044, +0.0339] | +0.0847 [+0.0668, +0.1033] |
| 8B | 104 | 0.0794 | 0.1339 | 0.0509 | 0.2739 | −0.0285 [−0.0495, −0.0069] | +0.1945 [+0.1625, +0.2228] |
| 14B | 130 | 0.0699 | 0.0538 | 0.0639 | 0.2006 | −0.0060 [−0.0270, +0.0141] | +0.1307 [+0.1033, +0.1570] |
| **Mean over sizes** | | 0.0583 | 0.0690 | 0.0516 | 0.1733 | **−0.0066 [−0.0169, +0.0038]** | **+0.1151 [+0.0992, +0.1300]** |

All p-val=n/a. Brier score (over tasks × 8 attempts), pooled over sizes at the final rung: B1 − IRT 2PL +0.0024 [−0.0034, +0.0086]; B2 − IRT 2PL +0.0342 [+0.0240, +0.0449] (2,000 draws). B1 wins at 1.7B and 8B, IRT 2PL wins at 4B, 14B is a tie.

## Rolling origin: every target rung (pooled over the four sizes, 2,000 draws, kernel_binary)

| Target rung (fitted on rungs below it) | B1 − IRT 2PL, MAE | B2 − IRT 2PL, MAE | B1 − IRT 1PL, MAE | B1 − IRT 2PL, Brier |
|---|---|---|---|---|
| 25% (fit: Base, 12.5%) | −0.0093 [−0.0153, −0.0030] | +0.0304 [+0.0232, +0.0374] | −0.0367 [−0.0499, −0.0240] | +0.0007 [−0.0031, +0.0042] |
| 50% (fit: Base–25%) | −0.0344 [−0.0466, −0.0227] | +0.1110 [+0.0911, +0.1288] | −0.0828 [−0.0947, −0.0712] | −0.0149 [−0.0252, −0.0060] |
| 75% (fit: Base–50%) | −0.0270 [−0.0395, −0.0158] | +0.0944 [+0.0748, +0.1134] | −0.0451 [−0.0578, −0.0327] | −0.0126 [−0.0205, −0.0056] |
| 100% (fit: Base–75%) | −0.0066 [−0.0169, +0.0039] | +0.1151 [+0.0994, +0.1306] | −0.0173 [−0.0302, −0.0051] | +0.0024 [−0.0034, +0.0086] |

IRT 2PL is worse than B1 at every earlier target rung with intervals excluding 0, and only ties at the final rung. The 1PL (one common slope) sensitivity is worse than 2PL everywhere in this trend form. All p-val=n/a.

**Mechanism (descriptive).** With Base at x = 0 and steep early gains (Base → 12.5% → 25%), the ordinary-least-squares ability trend is steep (fitted slopes +1.4 to +2.2 per unit x for 8B and 14B at the 50–75% targets) while the real ladders plateau (4B: 45, 42, 40 successes at 25 / 50 / 75%; 8B: 75, 77, 89), so the 2PL forecast overshoots. Example: 8B at the 50% target, forecast θ̃ = +0.62, expected mixed share 0.303 against realized 0.215, MAE 0.111 against 0.033 for B1. B2 overshoots much more (expected mixed share 0.991 there), because it also lacks task difficulty.

## Sensitivities

- **Trend form log(tokens) with the Base rung outside the trend** (first forecastable rung 50%): B1 − IRT 2PL MAE at 50%: −0.0414 [−0.0557, −0.0289]; 75%: −0.0117 [−0.0200, −0.0035]; **100%: +0.0048 [−0.0028, +0.0135]**, with Brier +0.0077 [+0.0034, +0.0131] in IRT's favour; B2 − IRT 2PL at 100%: +0.0902 [+0.0760, +0.1059]. Without the Base anchor most of the overshoot disappears and IRT matches or slightly beats B1 at the final rung; this was not the frozen primary and is reported as a sensitivity only.
- **1PL:** worse than 2PL in the primary form (table above); equal to 2PL in the log-tokens form (final rung B1 − IRT 1PL +0.0052 [−0.0023, +0.0135]).
- **Graded secondary outcome (proof fraction):** identical conclusions (final rung B1 − IRT 2PL −0.0064 [−0.0173, +0.0041]; B2 − IRT 2PL +0.1128 [+0.0968, +0.1275]). Its pooled rates equal the strict outcome at every rung: on these systems the proof fraction carries no partial credit beyond kernel_binary, as experiment 13's zero-call design evidence already found.

## The mixed-group share (the RL-signal quantity), final rung

| Size | Realized share of mixed groups (0 < k < 8) | Expected, IRT 2PL | Expected, IRT 1PL | Expected, B1 | Expected, B2 |
|---|---|---|---|---|---|
| 1.7B | 0.148 | 0.172 (error +0.023) | 0.221 (+0.073) | 0.102 (−0.046) | 0.349 (+0.201) |
| 4B | 0.237 | 0.229 (−0.008) | 0.218 (−0.019) | 0.129 (−0.109) | 0.483 (+0.246) |
| 8B | 0.237 | 0.300 (+0.063) | 0.369 (+0.132) | 0.207 (−0.030) | 0.935 (+0.698) |
| 14B | 0.289 | 0.303 (+0.014) | 0.303 (+0.014) | 0.215 (−0.074) | 0.787 (+0.498) |
| Mean absolute error | | **0.027** | 0.060 | 0.065 | 0.411 |

IRT 2PL runs slightly high, B1 runs low (it cannot anticipate growth), B2 is useless for this target. **Post hoc (not in the frozen protocol, no verdict; `expt_v1/posthoc_mixed_share_e15.py`, 10,000 draws):** absolute mixed-share error B1 − IRT 2PL at 100%: +0.0378 [−0.0089, +0.0684] p-val=n/a (IRT closer on average, interval includes 0); at 25 / 50 / 75%: +0.0049 [−0.0328, +0.0410], −0.0174 [−0.0598, +0.0285], +0.0130 [−0.0321, +0.0496]. B2 − IRT 2PL at 100%: +0.3836 [+0.3167, +0.4354].

**Onset against experiment 08's 0.05 gate (post hoc).** First rung whose *realized* mixed share reaches 0.05: 14B at Base (0.052; 9/1,080 successes), 8B at 12.5% (0.074), 4B at 25% (0.156), 1.7B at 50% (0.082). First *target* rung at which each forecast says ≥ 0.05 (targets start at 25%): IRT 2PL says 25% for every size, which is two rungs early for 1.7B; B1 says 75% for 1.7B and 50% for 4B (one rung late each) and 25% for 8B and 14B. Neither forecaster is reliable for onset on this ladder: IRT is over-eager, B1 lags. (Experiment 08's PARTIAL selection also applied format and truncation gates, which this experiment does not use, so these onset rungs are not experiment 08's verdicts.)

## Degenerate-rung accounting, monotonicity, seed variance

| Size | Successes / 1,080 at Base, 12.5, 25, 50, 75, 100% | Realized mixed share at the same rungs | Pooled-rate decreases | Mixed-share decreases |
|---|---|---|---|---|
| 1.7B | 0, 4, 1, 19, 44, 53 | 0.000, 0.022, 0.007, 0.081, 0.119, 0.148 | 1 (12.5 → 25%) | 1 |
| 4B | 3, 6, 45, 42, 40, 100 | 0.022, 0.030, 0.156, 0.163, 0.156, 0.237 | 2 (25 → 50 → 75%) | 1 |
| 8B | 0, 14, 75, 77, 89, 104 | 0.000, 0.074, 0.170, 0.215, 0.244, 0.237 | 0 | 1 (75 → 100%) |
| 14B | 9, 40, 72, 111, 101, 130 | 0.052, 0.148, 0.185, 0.222, 0.259, 0.289 | 1 (50 → 75%) | 0 |

- Degenerate rungs (zero successes): Base 1.7B and Base 8B only; both are fitting data, never targets. 0 of 16 target rungs degenerate.
- The Base 14B rung is experiment 08's own generation (same sampler and seed as experiment 05), not an experiment 05 receipt; it is the only Base rung above the 0.05 gate.
- Seed variance: unavailable (one SFT run per size, one sampling seed per rung). Monotonicity is imperfect at every size but 8B's pooled rate.

## Frozen forecast against outcomes (`analysis_e15.json` → `forecast_evaluation`)

- 25 predictions. 16 numeric with 80% intervals: 8 inside, 8 outside (an 80% interval should hold about 13). 9 probability forecasts: mean Brier 0.105.
- Wrong direction: P(SUCCESS) = 0.45 against the realized NO ADVANTAGE (Brier 0.20); the B1 difference forecast +0.008 [−0.004, +0.020] against −0.0066 (outside); P(1.7B ineligible) = 0.55 against eligible; number of eligible sizes 3 [2, 3] against 4.
- Right: B2 difference +0.06 [+0.02, +0.12] against +0.115 (inside); P(IRT beats B2 with interval excluding 0) = 0.90 (held); P(INCONCLUSIVE) = 0.20 (did not occur); 8B IRT and B1 MAE inside; all fits converged (P = 0.85).
- Largest miss: realized mixed shares at 100% (0.148 / 0.237 / 0.237 / 0.289 for 1.7B / 4B / 8B / 14B) against forecasts of 0.005 / 0.02 / 0.08 / 0.15. Successes are spread thinly over many tasks (pooled rate 0.05–0.12), which makes the mixed share 2–3× the pooled rate; the forecaster reasoned from pooled rates.

## Plain-English reading for Brando

- **Does IRT tell us earlier when SFT is RL-ready?** No, not from this ladder. The frozen test says carrying the last measured rung forward predicts each validation task's next-rung success rate as well as or better than the IRT trend (−0.0066 [−0.0169, +0.0038]), IRT was worse at every earlier rung, and for onset it called the 0.05 gate at the first forecastable rung for every size (two rungs early for 1.7B). On the mixed-share number itself IRT 2PL is closer than B1 on average at 100% (0.027 against 0.065 absolute error) but not with an interval excluding 0 (+0.038 [−0.009, +0.068], post hoc). The measured ladder stays the tool for the stopping point.
- **What IRT does establish.** Task difficulty is very stable across rungs and sizes: a scalar curve with no task difficulty is 0.115 [0.099, 0.130] MAE worse per task and predicts mixed shares of 0.35–0.94 against realized 0.15–0.29. The pooled item difficulties from earlier rungs do say *which* validation tasks the next checkpoint will solve, which is what an RL prompt-pool choice needs (tasks forecast near p = 0.5). The weak part is the ability trend (how fast θ grows with tokens), not the item side; without the Base anchor (log-tokens form) IRT ties B1 at the final rung.
- **The 1.7B / 4B deficits.** Both sizes do produce kernel-verified files on the validation split. On the mixed-share criterion alone, 14B is above 0.05 already at Base (0.052), 8B at 12.5% (0.074), 4B at 25% (0.156) and 1.7B only at 50% (0.082). 1.7B is late and still rising at 100% (44 → 53 successes, mixed share 0.119 → 0.148 from 75% to 100%), so more SFT tokens would likely keep helping it. 4B is flat from 25% to 75% (45, 42, 40 successes) and then jumps to 100 at 100%: a step that no smooth log-token trend forecasts, which is why B1 (0.129) and IRT (0.229) both missed its realized 0.237 in different directions. Pooled success at 100% orders 14B (0.120) > 8B (0.096) ≈ 4B (0.093) > 1.7B (0.049).
- **Caveats.** 135 validation tasks; one SFT run and one sampling seed per rung; intervals are conditional on the fitted item parameters and trends; the thresholds were agent-suggested without human review; nothing here touches the test split.

## Deviations from the protocol

- None in the primary analysis or the frozen rule.
- Additions after the frozen run, labelled post hoc and carrying no verdict: `expt_v1/posthoc_mixed_share_e15.py` (mixed-share error intervals and the onset table).
- The INCONCLUSIVE guard was made precise in the protocol (share over target rungs of eligible sizes) before the lock; it did not bind.

## Files and reproduction

- `expt_v1/results/analysis_e15.json` (everything above plus every per-rung arm statistic and the forecast evaluation), `per_rung_e15.csv` (one row per outcome × trend form × target rung × size), `per_task_forecasts_e15.csv.gz` (per-task truth and the four arms' p), `results_tables_e15.md` (generated tables), `posthoc_mixed_share_e15.json`.
- Reproduce: `python experiments/15_irt_2pl_sft_rung_forecast_of_rl_signal_onset_qwen3_base_vbv1_validation/expt_v1/analyze_e15.py` then `python .../expt_v1/posthoc_mixed_share_e15.py`; tests `python -m pytest -q tests/test_e15_irt.py` (14 tests, synthetic data only). Environment: numpy 2.2.6, scipy 1.16.3, Brando's Mac; 13.65 s wall.

## Next steps (not started)

1. If onset forecasting still matters: a new `expt_v2` or a prospective frozen forecast on experiment 08 v3's ladders using the log-tokens form (Base outside the trend), the only variant that tied B1 here; it must be frozen before those rungs are scored.
2. Use the pooled item difficulties for the RL prompt pool (tasks forecast nearest p = 0.5 for the chosen checkpoint) as a frozen forecast in experiment 13's phase 2 or experiment 08 v3, not as a retrospective claim.
3. Add one status line to the VeriBench idea page (Q2: rl4cv experiment 15, 10-14-2026, NO ADVANTAGE) in brando90/veribench.
