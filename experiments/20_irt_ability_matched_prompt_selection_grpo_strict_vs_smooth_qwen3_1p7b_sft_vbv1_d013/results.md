# Experiment 20 results: CPU Phase 0 complete, G0 PASS; trainer FAILED

**Doc link:** <https://github.com/brando90/rl-4-code-verification/blob/e20-irt-prompt-selection/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/results.md>

**TLDR:** The post-stop CPU calibration is complete: gate G0 **PASS**, area under the receiver operating characteristic curve (AUC) **0.9313 [0.9093, 0.9519], p-val=0.0001**, on 539 train tasks in 400 groups. The trainer remains **FAILED**; whether item response theory (IRT) prompt selection improves held-out validation strict pass@1 is unmeasured.

**Status:** COMPLETE: post-stop pre-registered Phase 0 (CPU only, dispatcher instruction 10-21-2026). Overall experiment verdict **FAILED at trainer gate**; no pilot or downstream training/evaluation was run.

**Last updated:** 10-21-2026 20:37:02 PDT

## Post-stop completion of pre-registered Phase 0 (CPU only, dispatcher instruction 10-21-2026)

1. **G0 PASS, with the registered point-estimate criteria unchanged.** The selected explanatory two-parameter logistic model has AUC **0.9313 [0.9093, 0.9519], p-val=0.0001** versus the 0.70 null. Active-group log loss is **0.3044 [0.2761, 0.3325], p-val=n/a**, versus **0.4812 [0.4554, 0.5081], p-val=n/a** for the in-fold population Beta(1,1) baseline. Paired baseline-minus-model gain is **0.1768 [0.1533, 0.2011], p-val=0.0001** versus zero. G0 requires point AUC ≥0.70 and lower log loss (runbook §6.4 / protocol §3); confidence bounds, calibration error and alternatives do not gate it. All intervals here use 10,000 paired bootstraps over the 400 D-013 train groups, conditional on the saved predictions and model selection; no nested refitting or prior-selection uncertainty. These predictions are held out within five folds of the train split; no validation outcome is used. [Full calibration report](RESULTS_phase0_calibration.md), [ranking/calibration plot](expt_v1/results/phase0b/g0_ranking_calibration.png), [539 held-out predictions](expt_v1/results/phase0b/primary_g0_predictions.csv).
2. **Ranking passes, but active-group probability is overpredicted.** Expected calibration error (ECE, ten equal-width bins) is **0.1122 [0.0978, 0.1375], p-val=n/a**. Predicted active share is **0.2485 [0.2273, 0.2694]**, versus observed **0.1373 [0.1068, 0.1691]** (74/539 tasks; active means 1–7 strict successes of eight), both p-val=n/a. Mean absolute error is **0.2366 [0.2173, 0.2554]**, and mean bias (prediction minus observation) is **+0.1112 [0.0884, 0.1335]**, both p-val=n/a. Alternatives beside the selected model: features-only AUC **0.9243 [0.9018, 0.9470]**, explanatory one-parameter logistic model (1PL) **0.9335 [0.9122, 0.9535]**, both p-val=0.0001 versus 0.70; scalar panel pass-rate ranking **0.8632 [0.8226, 0.9010], p-val=n/a**. The panel score is ranking-only, not an active-probability forecast. Full log-loss, ECE, priors and random-intercept comparisons are in the report; these results do not establish a downstream advantage for IRT.
3. **All 4,312 saved generations scored; item parameters frozen for all 539 tasks.** Strict successes: **191/4,312 = 4.4295% [3.3537%, 5.5478%], p-val=n/a** (10,000 train-group bootstrap draws). Smooth credit is known for **4,202/4,312** cells: 3,203 measured plus 999 registered malformed-source zeros. The **110 duplicate fully qualified declaration identities** remain missing, never zero-imputed. Known-cell smooth mean: **0.079069 [0.066681, 0.091684], p-val=n/a**; full-manifest missing-outcome bounds **[0.077052, 0.102562]** are separate from that conditional interval. Formal specification coverage (FSC) and its three-factor aggregate remain unmeasured; no judge calls were made. The graded fit is **available**; dimensionality is **available**, retaining numerical gates and the limitation of one policy represented by eight sample-index respondents. The three Base-model sensitivity has G0 **PASS**, selected **explanatory**, AUC **0.9332 [0.9117, 0.9533], p-val=0.0001** versus 0.70; both analyses are reported, without replacing the primary panel based on outcomes. The native `freeze_forecast` / `verify_forecast` check passed; frozen probabilities target future draws, not the already observed Phase 0 data. [Per-cell table](expt_v1/results/phase0_cells_e20.csv), [scoring summary](expt_v1/results/phase0_scoring_summary.json), [frozen parameters](expt_v1/forecasts/phase0_item_parameters_e20.json), [input pins](expt_v1/input_pins_e20.json).
4. **Saved smoke remains FAILED; the analogous experiment 13 v4 T1 comparison also fails.** Update 2 has **22,654/864,717 = 2.61982%** mismatched token positions: **22,459 finite in-support errors above 0.05 + 195 unsupported actions**. Unsupported actions are 0.02255% of tokens and 0.86078% of mismatches; update 1 has 167 unsupported actions. The frozen trainer limit is ≤1% mismatch. T1 requires zero unsupported actions, so the analogous comparison is **FAIL**. The all-token median is bounded above by **0.00841008 <0.01**; exact median and 99th percentile were not saved, and the ≤0.10 percentile criterion is undecidable. Task, rollout, token-identity and token-position slices are unavailable. These are exact descriptive counts from two updates of one smoke run, p-val=n/a; no new run or gate change. [Full saved-receipt analysis](RESULTS_saved_smoke_t1.md).
5. **Evidence and deterministic verification are complete.** Normal-partition CPU scoring used the frozen scorer at `59059a2`, `--skip-tc`, `-c 1 --mem 16G`. D-109 audit verified **11,859 compiler calls**, **224 original output files**, and **64/64 completion receipts**, with zero audit errors. Intact completed nonzero compiler exits retain native failure scores; absent/incomplete evidence stays unavailable. All original attempts, timeouts and identical-resource retries are preserved. Independent bootstrap replay matched every requested interval; final artifact verification is **PASS** with **0 failed checks**. The latest full `make test` passed **1,415 tests, 17 skipped, 6 subtests**, with all 46 tested source hashes unchanged. [Import audit](expt_v1/results/receipts/phase0_cpu_import_verification.json), [bootstrap replay](expt_v1/results/receipts/bootstrap_replay_receipt.json), [final verification](expt_v1/results/receipts/final_phase0_verification.json), [run receipt](expt_v1/results/receipts/phase0b_run_receipt.json). The driver completed all 571 numerical fits and native freezing, then exited 1 on a duplicate `trainer_status` keyword in its terminal progress logger. A separately verified [metadata-only recovery](expt_v1/results/phase0b/phase0b_completion_recovery_receipt.json) finalized progress; the original failure, source, input pins, numerical outputs and frozen forecast are preserved unchanged.

**Next step:** [p 8/10] Review [pull request #20](https://github.com/brando90/rl-4-code-verification/pull/20) for the calibration decision input; any future trainer work requires a separate instruction because its stop remains in force.

## Live phase table

| Phase | Final state | GPU-hours used / cap |
|---|---|---|
| Setup and protocol | Original frozen draft; never pilot-locked | 0 |
| Phase 0a generation | 4,312/4,312 train generations saved | 7.2358 / 10 |
| Phase 0a scoring | COMPLETE: 4,312 strict outcomes; 4,202 known / 110 missing smooth | 0 additional |
| Phase 0b and G0 | COMPLETE; G0 PASS; 539 item parameters frozen | CPU only |
| Trainer smoke | FAILED after two updates; historical allocation includes infrastructure failures | 0.5900 / 15 pilot cap |
| Pilot A/C/S | NOT RUN | 0 additional / 15 |
| Main arms A/S/E/C/B/D | NOT RUN | 0 / 130 |
| Validation evaluation | NOT RUN | 0 / 80 |
| Total | All GPU jobs terminal; test split closed | 7.8258 / 200 |

Sherlock CPU allocation is **198.2292 CPU-hours** (713,625 allocated CPU-seconds across 78 charged rows), including every failure and retry; all 16 owned roots are terminal. Local four-worker Phase 0b wall time is **2873.98 seconds**, with **2.2394 actual process CPU-hours** (7,888.42 user + 173.59 system seconds), accounted separately from allocated Sherlock time in [runtime](expt_v1/results/phase0b_runtime.txt). API spend **$0**. [CPU accounting](expt_v1/results/receipts/cpu_final_accounting.json), [GPU accounting](expt_v1/results/receipts/final_accounting.json).

## Scope, provenance and missing outcomes

Hypotheses H1 (IRT versus uniform), H3 (IRT versus scalar and dynamic sampling), H2 (online mechanism), and H4 (smooth reward interaction), validation pass@1/pass@8, learning curves, ability tracking and the smooth-reward training audit remain **unmeasured**, with estimates, confidence intervals and p-values unavailable. There is no causal training-effect NULL or positive result. Calibration and saved-smoke plots replace unavailable learning curves; no test data were opened.

The [historical trainer-stop closure](https://github.com/brando90/rl-4-code-verification/blob/79d02c82ddd578ebeedc556569195c706b30378c/experiments/20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013/results.md) retains the early-smoke chronology and implementation deviations. Its `E20_FINISHED.txt` is preserved. Scoring was committed and pushed before fits in `d4614fd7e49414c83b739f0b46eb23a9c7eb6f66`. `G0_FINISHED.txt` records this CPU completion's G0 verdict, AUC interval and immutable results commit; subsequent notification receipts can follow that commit. [Current checkpoint](CKPT_codex-rl4cv-e20-irt-prompt-selection.md), [experiment checkpoint](CKPT_e20.md), [runbook](expt_v1/cc.md), [Google experiment log](https://docs.google.com/document/d/1KKKabJJArClVmXcaxfTF5jxk8nF1oHmCH08d44jbqUg/edit).

**Copy-ready collaborator message:** I finished the CPU calibration: IRT passes the registered ranking/log-loss gate, but it overpredicts active groups and the features-only alternative ranks almost as well. The trainer still fails its consistency gate, so we have not tested whether IRT improves held-out strict pass@1.

**TLDR-end:** [rl4cv: expt20 IRT prompt selection for GRPO] `20_irt_ability_matched_prompt_selection_grpo_strict_vs_smooth_qwen3_1p7b_sft_vbv1_d013` has completed the authorized CPU Phase 0, with G0 PASS and 539 frozen item parameters. Trainer FAILED remains binding; the downstream IRT benefit is unmeasured.

**Snapshot:**

- G0: PASS; AUC 0.9313 [0.9093, 0.9519].
- Active-group log loss: 0.3044; baseline 0.4812.
- ECE: 0.1122; predicted / observed active share: 24.85% / 13.73%.
- Calibration cells: 4,312 strict; 4,202 known / 110 missing smooth.
- Frozen item parameters: 539; native hash verification passed.
- Saved smoke: 22,459 finite mismatches + 195 unsupported actions in update 2.
- Trainer verdict: FAILED; T1 analogue: FAIL.
- Resources: 198.2292 Sherlock CPU-hours; 7.8258 GPU-hours; $0 API.
- Publication: PR #20, unmerged.
