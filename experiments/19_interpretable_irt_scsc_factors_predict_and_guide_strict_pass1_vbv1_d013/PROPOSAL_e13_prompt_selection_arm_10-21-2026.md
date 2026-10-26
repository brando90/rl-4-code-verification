# Proposal to experiment 13's owner: a prompt-selection arm (frozen 10-21-2026)

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/main/experiments/19_interpretable_irt_scsc_factors_predict_and_guide_strict_pass1_vbv1_d013/PROPOSAL_e13_prompt_selection_arm_10-21-2026.md>

**TLDR:** Experiment 19 found that forecasts made without any start-policy rollout pick the prompts on which experiment 13's start policy gives mixed strict groups. On the validation split they roughly triple the gradient-carrying groups per update. Under experiment 19's pre-registered rule the evidence is not IRT-specific, so the proposed arm uses the simpler panel-pass-rate heuristic. This is a proposal only. Experiment 13's frozen v4 protocol is untouched, and adopting any of this is the owner's decision, made as a numbered amendment before the data it affects.

## Evidence (experiment 19, zero model calls)

Prompt-selection performance on the 135 validation tasks (32 mixed, 103 not; 100 bootstrap groups):

| Forecast (no start-policy outcome used) | AUC for a mixed group of 8 [95% CI] | Top-quarter mixed share [95% CI] |
|---|---|---|
| Random-intercept 2PL from 11 VeriBench systems (G1 primary) | 0.862 [0.792, 0.925] | 0.706 [0.433, 0.853] |
| Panel strict pass rate per task (heuristic) | 0.852 [0.781, 0.916] | 0.647 [0.424, 0.794] |
| Task features only (exploratory) | 0.954 [0.909, 0.987] | 0.794 [0.531, 0.919] |
| Uniform | 0.5 | 0.237 |

- **Gate:** G1 passes 13's own F2 gate (AUC ≥ 0.70). It is a point-estimate gate on this validation sample, while F2 was written for 539 train tasks. 0 of 10,000 bootstrap draws fall at or below 0.70.
- **IRT-specific contrasts (both fail):** IRT minus panel strict rate +0.011 [−0.004, +0.027] p-val=0.15; IRT minus panel mean smooth +0.006 [−0.014, +0.025] p-val=0.58.
- **Yield and calibration:** at G = 8 a top-quarter pool gives about 22.6 mixed groups per 256-rollout update against 7.6 uniform. The forecasts overstate the level of the mixed probability: predicted 0.482 vs observed 0.237.
- **Token-cap sensitivity:** dropping the 13 tasks with ≥ 4 of 8 samples at the 12,288-token cap leaves the primary AUC at 0.845 [0.768, 0.915].

## Proposed arm (for the owner to accept, change or decline)

- **A-sel:** strict reward, recipe identical to arm A.
- **Prompts:** each update draws its prompt groups uniformly from a fixed pool, the top quarter (135) of the 539 train tasks ranked by panel strict pass rate (`per_task.panel_strict_rate` in `expt_v1/forecasts/e19_g3_forecast_v4_g0.json`, ties broken by task id). The pool is frozen before any v4 generation.
- **Variant:** the features-only ranking (same file, `features_only_q_mixed_G8`) is the stronger but exploratory choice. 13's original arm-C 50/50 mixture is a milder option (validation mixed share 0.312 vs 0.237).
- **Comparison:** A-sel minus A on the validation strict mean at matched tokens. The same seeds, checkpoint selection and single test evaluation as v4.

## Risks and what experiment 19 does not show

- **Population:** the evidence is on validation tasks, which have no SFT exposure. Train tasks do have it (476/539 have teacher examples), and that can change which prompts are mixed. The frozen G3 forecasts test this on V4-G0's 32 train tasks.
- **Precondition only:** a pool with more learning signal is the precondition for higher strict pass@1, not evidence of it. Experiment 19's frozen judgement puts P(A-sel beats A) = 0.60.
- **Narrow pool:** a narrow pool can overfit. The arm would report validation strict mean on the full validation split.

## Scoring available to 13 now, without an extra arm

When V4-G0 publishes per-task strict counts for its 32 seeded train tasks, score experiment 19's frozen forecasts (`e19_g3_forecast_v4_g0.json`, sha256 abb0cb31…, frozen 2026-10-21T01:58:55Z). For each forecast, compute the Spearman correlation with the unbiased per-task G = 8 mixed probability, and the AUC for 1 ≤ s ≤ 31.
